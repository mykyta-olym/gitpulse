"""Student API endpoints (read-only + create via sync/import)."""

import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Query, Request, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.api.errors import (
    raise_conflict,
    raise_forbidden,
    raise_not_found,
    raise_unprocessable,
)
from app.dependencies import ApiTeacherAuth, DbSession
from app.models.student import Student
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.students import StudentCreate, StudentRead
from app.utils.constants import NO_LOGIN_HASH

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[StudentRead])
async def list_students(
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
    team_id: uuid.UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[Student]:
    """List students, optionally filtered by team."""
    from app.api.dashboard._access import can_manage_via_request
    from app.models.team import Team

    if team_id:
        # Scope the team filter so a teacher can't dump the roster of a group
        # in a course they don't teach. Bearer tokens + admins unrestricted.
        team = await db.get(Team, team_id)
        if not team or not await can_manage_via_request(request, db, team=team):
            raise_not_found("Group not found")
        stmt = (
            select(Student)
            .join(TeamMember)
            .where(TeamMember.team_id == team_id, TeamMember.is_active.is_(True))
            .order_by(Student.full_name)
            .offset(skip)
            .limit(limit)
        )
    else:
        # The unfiltered list is privileged: only a bearer token or an admin may
        # enumerate every student. A non-admin teacher must pass ?team_id= to
        # scope to a group they teach.
        if not await can_manage_via_request(request, db):
            raise_forbidden("Listing all students requires admin access or a team_id filter")
        stmt = select(Student).order_by(Student.full_name).offset(skip).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Student:
    """Create a new student (teacher/admin only)."""
    # Handle field aliases from UI
    full_name = data.full_name or data.name

    # If the caller wants to drop the student into a team, they must be allowed
    # to manage that team's course - otherwise a teacher could inject members
    # into a group in a course they don't teach. Bearer + admin unrestricted.
    if data.team_id is not None:
        from app.api.dashboard._access import can_manage_via_request
        from app.models.team import Team

        _target_team = await db.get(Team, data.team_id)
        if not _target_team or not await can_manage_via_request(request, db, team=_target_team):
            raise_not_found(f"Group {data.team_id} not found")

    # Check for existing student by gitlab_user_id, email, or gitlab_username
    existing: Student | None = None
    if data.gitlab_user_id:
        stmt = select(Student).where(Student.gitlab_user_id == data.gitlab_user_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
    if not existing and data.email:
        stmt = select(Student).where(Student.email == data.email)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
    if not existing and data.gitlab_username:
        stmt = select(Student).where(Student.gitlab_username == data.gitlab_username)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

    if existing:
        # If team_id provided, just add to team
        if data.team_id:
            await _add_to_team(db, existing, data.team_id)
        return existing

    # Derive gitlab_username
    gitlab_username = data.gitlab_username
    if not gitlab_username and data.email:
        # Strip +tag suffixes and use only the local part before @
        local_part = data.email.split("@")[0]
        gitlab_username = local_part.split("+")[0]
    if not gitlab_username:
        raise_unprocessable("Either gitlab_username or email is required to create a student")

    # Create new student
    student = Student(
        gitlab_user_id=data.gitlab_user_id or None,
        gitlab_username=gitlab_username,
        full_name=full_name,
        email=data.email,
    )
    db.add(student)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        # Concurrent insert - re-query by all unique fields
        existing = None
        if data.gitlab_user_id:
            stmt = select(Student).where(Student.gitlab_user_id == data.gitlab_user_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
        if not existing and data.email:
            stmt = select(Student).where(Student.email == data.email)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
        if not existing and gitlab_username:
            stmt = select(Student).where(Student.gitlab_username == gitlab_username)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
        if existing:
            if data.team_id:
                await _add_to_team(db, existing, data.team_id)
            return existing
        raise_conflict("Student already exists")

    # Add to team if specified
    if data.team_id:
        await _add_to_team(db, student, data.team_id)

    logger.info("student_created", student_id=str(student.id), name=full_name)
    return student


async def _add_to_team(db: DbSession, student: Student, team_id: uuid.UUID) -> None:
    """Helper to add student to team with proper role assignment."""
    from app.models.team import Team

    # Validate team exists
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found(f"Group {team_id} not found")

    now = datetime.now(UTC)

    # Check if already member (may be inactive / previously removed)
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.student_id == student.id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        if existing.is_active:
            return  # Already an active member
        # Reactivate previously-removed member
        existing.is_active = True
        existing.left_at = None
        existing.membership_source = "manual"
        existing.last_synced_at = now
        await db.flush()
    else:
        membership = TeamMember(
            team_id=team_id,
            student_id=student.id,
            membership_source="manual",
            is_active=True,
            last_synced_at=now,
        )
        db.add(membership)
        await db.flush()

    # Upsert RBAC user role
    await _upsert_user_role(
        db,
        username=student.gitlab_username,
        email=student.email,
        full_name=student.full_name,
        role="student",
        gitlab_user_id=student.gitlab_user_id,
    )


async def _upsert_user_role(
    db: DbSession,
    *,
    username: str,
    email: str | None,
    full_name: str | None = None,
    role: str,
    gitlab_user_id: int | None = None,
) -> None:
    """Upsert RBAC user role for manually-added members.

    Keeps explicit/admin roles intact - only upgrades when new role has higher priority.
    """
    role_priority = {"student": 0, "teacher": 2, "admin": 3}
    normalized = username.strip().lower() if username else ""
    if not normalized:
        return

    stmt = (
        select(User)
        .where(or_(User.gitlab_username == normalized, User.username == normalized))
        .limit(1)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        from app.services.gitlab_import.service import is_bot_user

        db.add(
            User(
                username=normalized,
                gitlab_username=normalized,
                email=email,
                full_name=full_name,
                password_hash=NO_LOGIN_HASH,
                role=role,
                is_active=True,
                gitlab_user_id=gitlab_user_id,
                is_bot=is_bot_user(normalized),
            )
        )
        await db.flush()
        return

    if email and not existing_user.email:
        existing_user.email = email
    if full_name and not existing_user.full_name:
        existing_user.full_name = full_name
    if not existing_user.gitlab_username:
        existing_user.gitlab_username = normalized
    if gitlab_user_id and not existing_user.gitlab_user_id:
        existing_user.gitlab_user_id = gitlab_user_id
    existing_user.is_active = True

    if (
        role_priority.get(role, 0) > role_priority.get(existing_user.role, 0)
        and not existing_user.role_locked
    ):
        existing_user.role = role
    await db.flush()


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(
    student_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Student:
    student = await db.get(Student, student_id)
    if not student:
        raise_not_found("Student not found")

    # Scope: a teacher may only read a student who shares one of their courses
    # (bearer tokens + admins unrestricted). 404-on-denial keeps foreign student
    # UUIDs unenumerable.
    from app.api.dashboard._access import can_view_student_via_request

    if not await can_view_student_via_request(request, db, student):
        raise_not_found("Student not found")
    return student
