"""User management API endpoints (admin-only).

OAuth-only mode: Users are created automatically on first GitLab login.
Admins can change roles and deactivate users.
Name / email / avatar are synced from GitLab and cannot be edited.
"""

import uuid

import structlog
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.errors import raise_bad_request, raise_not_found, raise_service_unavailable
from app.config import get_settings
from app.dependencies import ApiAdminAuth, DbSession
from app.models.student import Student
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.users import UserRead, UserUpdate

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(
    db: DbSession,
    _auth: ApiAdminAuth,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[User]:
    """List all users (admin only).

    Users are created automatically when they log in via GitLab OAuth.
    """
    settings = get_settings()
    if not settings.feature_rbac:
        raise_service_unavailable("RBAC feature is disabled")
    result = await db.execute(
        select(User).where(User.is_bot.is_(False)).order_by(User.username).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, db: DbSession, _auth: ApiAdminAuth) -> User:
    """Get a specific user by ID (admin only)."""
    settings = get_settings()
    if not settings.feature_rbac:
        raise_service_unavailable("RBAC feature is disabled")

    user = await db.get(User, user_id)
    if not user:
        raise_not_found("User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: DbSession,
    _auth: ApiAdminAuth,
) -> User | JSONResponse:
    """Update user role or active status (admin only).

    Name, email, and avatar are synced from GitLab on every login
    and cannot be changed manually.
    """
    settings = get_settings()
    if not settings.feature_rbac:
        raise_service_unavailable("RBAC feature is disabled")

    user = await db.get(User, user_id)
    if not user:
        raise_not_found("User not found")

    update_data = data.model_dump(exclude_unset=True)

    # Capture old values for audit
    _old_values = {
        k: getattr(user, k)
        for k in ("role", "is_active", "role_locked", "is_bot")
        if k in update_data
    }

    # Prevent demoting the last admin.
    #
    # The count is taken under a row lock, not as a bare aggregate. Reading it
    # unlocked is a time-of-check/time-of-use race with a real consequence: two
    # admins demoting each other at the same moment would both see a count of
    # two, both pass this guard, and leave the installation with no admin at
    # all and no way back in. `SELECT ... FOR UPDATE` over the admin rows makes
    # the second request wait for the first to commit and then see one.
    #
    # It has to select the ROWS - Postgres refuses FOR UPDATE alongside an
    # aggregate - so the count is taken in Python. The set is every active
    # human admin, which is small by definition.
    if "role" in update_data and user.role == "admin" and update_data["role"] != "admin":
        admin_ids = await db.execute(
            select(User.id)
            .where(User.role == "admin", User.is_active.is_(True), User.is_bot.is_(False))
            .with_for_update()
        )
        if len(admin_ids.scalars().all()) <= 1:
            raise_bad_request(
                "Cannot demote the last active admin. Promote another user to admin first."
            )

    # Only role, is_active, role_locked, is_bot are app-managed; name/email come from GitLab
    allowed_fields = {"role", "is_active", "role_locked", "is_bot"}
    for key, value in update_data.items():
        if key in allowed_fields:
            setattr(user, key, value)

    # Lock role when admin explicitly sets it - prevents auto-sync override
    # (unless admin explicitly sent role_locked=false to unlock)
    if "role" in update_data and "role_locked" not in update_data:
        user.role_locked = True

        # Propagate role change to TeamMember.is_teacher for all
        # team memberships so the effect is immediate (no need to wait
        # for next sync cycle).
        new_is_teacher = update_data["role"] in ("teacher", "admin")
        gitlab_username = user.gitlab_username or user.username
        if gitlab_username:
            student_stmt = select(Student.id).where(
                Student.gitlab_username == gitlab_username.lower()
            )
            student_result = await db.execute(student_stmt)
            student_ids = [row[0] for row in student_result.all()]
            if student_ids:
                tm_stmt = select(TeamMember).where(
                    TeamMember.student_id.in_(student_ids),
                    TeamMember.is_active.is_(True),
                )
                tm_result = await db.execute(tm_stmt)
                for tm in tm_result.scalars().all():
                    tm.is_teacher = new_is_teacher

    await db.flush()

    from app.services.audit import write_audit

    _new_values = {k: getattr(user, k) for k in _old_values}
    _changes = {
        k: {"old": _old_values[k], "new": _new_values[k]}
        for k in _old_values
        if _old_values[k] != _new_values[k]
    }
    if _changes:
        await write_audit(
            db,
            action="user_role_update",
            actor=_auth or "admin",
            entity_type="user",
            entity_id=user_id,
            detail={"changes": _changes, "username": user.username},
        )

    logger.info("user_updated", user_id=str(user_id), updates=list(update_data))

    # -- Email notifications for significant changes --
    if _changes:
        from app.services.email_notifications import (
            notify_account_reactivated,
            notify_role_change,
        )

        actor_name = _auth or "admin"

        if "role" in _changes:
            notify_role_change(
                username=user.username,
                old_role=str(_changes["role"]["old"]),
                new_role=str(_changes["role"]["new"]),
                changed_by=actor_name,
                to_email=user.email,
            )

        if "is_active" in _changes and _changes["is_active"]["new"] is True:
            notify_account_reactivated(
                username=user.username,
                reactivated_by=actor_name,
                to_email=user.email,
            )

    # Warn admin when demoting a course owner/teacher to student
    warning: str | None = None
    if "role" in update_data and update_data["role"] == "student":
        from app.models.course_membership import CourseMembership

        cm_result = await db.execute(
            select(CourseMembership.role)
            .where(
                CourseMembership.user_id == user.id,
                CourseMembership.role.in_(["owner", "teacher"]),
            )
            .limit(1)
        )
        if cm_result.scalar_one_or_none():
            warning = (
                "This user is a course owner/teacher. "
                "With role_locked=true they will NOT be elevated - "
                "transfer course ownership first if needed."
            )

    if warning:
        user_data = UserRead.model_validate(user).model_dump(mode="json")
        user_data["_warning"] = warning
        return JSONResponse(content=user_data)
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_put(
    user_id: uuid.UUID, data: UserUpdate, db: DbSession, _auth: ApiAdminAuth
) -> User | JSONResponse:
    """Update user (admin only, PUT alias for PATCH)."""
    return await update_user(user_id, data, db, _auth)
