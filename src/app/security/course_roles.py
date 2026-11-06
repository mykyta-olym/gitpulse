"""Course-level role hierarchy helpers - per-course RBAC.

Role Architecture
-----------------
The platform uses a **dual role system**:

1. **System-level** (``User.role``): ``admin`` | ``teacher`` | ``student``
   - Determined at OAuth login via group membership / allowlists.
   - ``admin`` bypasses ALL course-level checks (no membership needed).

2. **Course-level** (``CourseMembership.role``): ``owner`` | ``teacher`` | ``student``
   - Per (user, course) pair.  owner > teacher > student.
   - A system ``student`` with course ``teacher`` membership is
     temporarily elevated to ``teacher`` for the dashboard session
     (see ``_enforce_db_role`` in ``dependencies.py``).

Quick reference
---------------
``role_gte(role, min_role)``
    Synchronous comparison: is *role* ≥ *min_role*?

``get_course_role(db, user_id, course_id)``
    Async lookup - returns the role string or ``None``.

"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_membership import COURSE_ROLE_WEIGHT, CourseMembership

# Re-export for convenience
COURSE_ROLES = ("student", "teacher", "owner")

# Minimum role constants for common operations
ROLE_VIEW_COURSE = "student"
ROLE_VIEW_STUDENTS = "teacher"
ROLE_EDIT_CONTENT = "teacher"
ROLE_MANAGE_COURSE = "owner"


# -- Synchronous helpers ------------------------------------------------------


def role_gte(role: str, min_role: str) -> bool:
    """Return ``True`` if *role* is at least as privileged as *min_role*."""
    return COURSE_ROLE_WEIGHT.get(role, -1) >= COURSE_ROLE_WEIGHT.get(min_role, 0)


# -- Async DB helpers ---------------------------------------------------------


async def is_course_staff(
    db: AsyncSession,
    course: object,
    user: object,
    min_role: str = "teacher",
) -> bool:
    """Check if *user* is staff on *course* (admin or CourseMembership).

    Combines two checks in priority order:
    1. System admin bypass (``User.role == "admin"``).
    2. CourseMembership with at least *min_role*.
    """
    # 1. System admin bypass
    if getattr(user, "role", "") == "admin":
        return True

    # 2. CourseMembership check
    user_id = getattr(user, "id", None)
    course_id = getattr(course, "id", None)
    if user_id and course_id:
        actual = await get_course_role(db, user_id, course_id)
        if actual and role_gte(actual, min_role):
            return True

    return False


async def get_course_role(
    db: AsyncSession,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
) -> str | None:
    """Return the user's role in *course_id*, or ``None`` if no membership."""
    stmt = select(CourseMembership.role).where(
        CourseMembership.user_id == user_id,
        CourseMembership.course_id == course_id,
    )
    return (await db.execute(stmt)).scalar_one_or_none()


# -- Membership management ----------------------------------------------------


async def set_course_membership(
    db: AsyncSession,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
    role: str,
) -> CourseMembership:
    """Create or update a CourseMembership.  Returns the membership row.

    Raises ``ValueError`` if *role* is not one of the defined course roles.
    """
    if role not in COURSE_ROLE_WEIGHT:
        raise ValueError(f"Invalid course role {role!r}; expected one of {COURSE_ROLES}")
    stmt = select(CourseMembership).where(
        CourseMembership.user_id == user_id,
        CourseMembership.course_id == course_id,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        existing.role = role
        return existing
    membership = CourseMembership(user_id=user_id, course_id=course_id, role=role)
    db.add(membership)
    return membership


async def remove_course_membership(
    db: AsyncSession,
    user_id: uuid.UUID,
    course_id: uuid.UUID,
) -> None:
    """Remove a user's membership from a course."""
    stmt = delete(CourseMembership).where(
        CourseMembership.user_id == user_id,
        CourseMembership.course_id == course_id,
    )
    await db.execute(stmt)
