"""Shared lightweight helpers for API route modules."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.errors import raise_forbidden

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.user import User

logger = structlog.get_logger(__name__)


def get_actor(request: Request, fallback: str = "session") -> str:
    """Extract username from session cookie safely (no crash for API-only calls)."""
    try:
        from app.config import get_settings as _gs
        from app.security.session_auth import get_current_session

        s = _gs()
        sess = get_current_session(
            request,
            s.secret_key,
            max_age=s.session_max_age_seconds,
            app_base_url=s.app_base_url,
            session_absolute_max_age=s.session_absolute_max_age_seconds,
        )
        if sess:
            return sess.get("user", fallback)
    except Exception:
        logger.debug("failed to extract actor from session")
    return fallback


async def _session_caller(request: Request, db: AsyncSession) -> tuple[User | None, str]:
    """Validate session and resolve the calling User + role.

    Returns (caller_user_or_none, role_string).
    Raises 403 if session is expired.
    """
    from app.config import get_settings
    from app.dependencies import _validate_session
    from app.models.user import User

    settings = get_settings()
    session_data = _validate_session(request, settings)
    if not session_data:
        raise_forbidden("Session expired")

    role = session_data.get("role", "student")
    gl = session_data.get("gitlab_username", "")
    usr = session_data.get("user", "")
    if role == "admin":
        return None, role
    user_stmt = select(User).where((User.gitlab_username == gl) | (User.username == usr)).limit(1)
    caller = (await db.execute(user_stmt)).scalar_one_or_none()
    return caller, role


async def check_course_access(
    course: object,
    auth_kind: str,
    request: Request,
    db: AsyncSession,
    *,
    action_label: str = "modify this course",
) -> None:
    """Verify the caller is an teacher of *course* (or admin/bearer).

    Uses CourseMembership to check course-level role.
    """
    if auth_kind == "api_token":
        return

    from app.security.course_roles import is_course_staff

    caller, role = await _session_caller(request, db)
    if role == "admin":
        return

    if caller and await is_course_staff(db, course, caller):
        return

    raise_forbidden(f"You cannot {action_label}")


async def _resolve_caller(
    request: Request,
    db: AsyncSession,
    auth_kind: str,
) -> tuple[User | None, str]:
    """Return (User, role) for the current request."""
    if auth_kind == "api_token":
        return None, "admin"

    return await _session_caller(request, db)


# ---------------------------------------------------------------------------
# Reusable micro-helpers extracted from per-module copy-paste
# ---------------------------------------------------------------------------


async def lookup_user_email(db: AsyncSession, username: str) -> str | None:
    """Return the email for a user identified by ``gitlab_username`` or ``username``.

    Used by notification helpers that resolve a username to an email address.
    Returns ``None`` when the user is not found or has no email set.
    """
    from app.models.user import User

    row = await db.execute(
        select(User.email)
        .where((User.gitlab_username == username) | (User.username == username))
        .limit(1)
    )
    return row.scalar()


async def course_staff_emails(
    db: AsyncSession, course_id: uuid.UUID, *, active_only: bool = True
) -> list[str]:
    """Return email addresses for all owner/teacher members of a course."""
    from app.models.course_membership import CourseMembership
    from app.models.user import User

    conditions = [
        CourseMembership.course_id == course_id,
        CourseMembership.role.in_(("owner", "teacher")),
        User.email.isnot(None),
    ]
    if active_only:
        conditions.append(User.is_active.is_(True))

    stmt = (
        select(User.email)
        .join(CourseMembership, CourseMembership.user_id == User.id)
        .where(*conditions)
    )
    return [e for (e,) in (await db.execute(stmt)).all() if e]


async def require_course_staff(
    db: AsyncSession,
    course_id: uuid.UUID | None,
    user: User,
    *,
    msg: str = "Not a teacher for this course",
) -> Course:
    """Verify *user* is staff on course *course_id*.

    Returns the ``Course`` on success, raises 403 otherwise (including when
    *course_id* is ``None``). Replaces the 20+ inline
    ``if not course or not await is_course_staff(...)`` guard blocks scattered
    across the support and compliance endpoints - several of which carry an optional
    course id, hence the ``UUID | None`` parameter.
    """
    from app.models.course import Course as _Course
    from app.security.course_roles import is_course_staff

    if course_id is None:
        raise_forbidden(msg)
    course = await db.get(_Course, course_id)
    if not course or not await is_course_staff(db, course, user):
        raise_forbidden(msg)
    return course
