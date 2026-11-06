"""Shared utility for resolving GitLab users to internal student records."""

import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select, update

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student

logger = logging.getLogger(__name__)


async def resolve_student(
    session: "AsyncSession",
    gitlab_user_id: int | None,
    gitlab_username: str | None = None,
    update_stale_id: bool = True,
) -> uuid.UUID | None:
    """Resolve a GitLab user to our internal student UUID.

    Strategy:
    1. First try matching by gitlab_user_id (fast path)
    2. If not found and username provided, try matching by gitlab_username
    3. If found by username with a stale/placeholder gitlab_user_id, update it

    This handles the case where students were imported from roster (with placeholder
    negative gitlab_user_id) and later appear in GitLab events with their real ID.

    Args:
        session: Database session
        gitlab_user_id: GitLab user ID from event/API
        gitlab_username: GitLab username from event/API (fallback)
        update_stale_id: If True, update student's gitlab_user_id when found by username

    Returns:
        Student UUID if found, None otherwise
    """
    if gitlab_user_id is None and not gitlab_username:
        return None

    # Fast path: match by gitlab_user_id
    if gitlab_user_id is not None:
        stmt = select(Student.id).where(Student.gitlab_user_id == gitlab_user_id)
        result = await session.execute(stmt)
        student_id = result.scalar_one_or_none()
        if student_id:
            return student_id

    # Fallback: try matching by username
    if gitlab_username:
        stmt2 = select(Student.id, Student.gitlab_user_id).where(
            Student.gitlab_username == gitlab_username
        )
        result = await session.execute(stmt2)
        row = result.one_or_none()

        if row:
            found_student_id: uuid.UUID
            current_gitlab_id: int | None
            found_student_id, current_gitlab_id = row

            # Update stale gitlab_user_id if we have a valid new one
            # Legacy placeholder GitLab IDs are negative.
            if (
                update_stale_id
                and gitlab_user_id is not None
                and (current_gitlab_id is None or current_gitlab_id < 0)
            ):
                await session.execute(
                    update(Student)
                    .where(Student.id == found_student_id)
                    .values(gitlab_user_id=gitlab_user_id)
                )
                logger.info(
                    "Updated student %s gitlab_user_id: %s -> %s",
                    gitlab_username,
                    current_gitlab_id,
                    gitlab_user_id,
                )

            return found_student_id

    return None
