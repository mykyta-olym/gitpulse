"""Dashboard cache invalidation helpers used by GitLab sync jobs."""

import uuid
from contextlib import suppress
from typing import Any

from sqlalchemy import select

from app.models.team import Team
from app.models.team_member import TeamMember
from app.services.page_cache import invalidate_cascade


async def _invalidate_dashboard_cache_after_sync(
    session: Any,
    *,
    team_id: uuid.UUID | None,
    course_id: uuid.UUID | str | None = None,
    project_id: uuid.UUID | None = None,
) -> None:
    """Drop rendered dashboard fragments affected by a completed GitLab sync."""
    if team_id is None:
        invalidate_cascade(project_id=project_id, course_id=course_id)
        return

    resolved_course_id = course_id
    if resolved_course_id is None:
        with suppress(Exception):
            resolved_course_id = (
                await session.execute(select(Team.course_id).where(Team.id == team_id))
            ).scalar_one_or_none()

    student_ids: list[uuid.UUID] = []
    with suppress(Exception):
        rows = (
            await session.execute(
                select(TeamMember.student_id).where(
                    TeamMember.team_id == team_id,
                    TeamMember.left_at.is_(None),
                )
            )
        ).all()
        student_ids = [sid for (sid,) in rows if sid is not None]

    invalidate_cascade(
        project_id=project_id,
        team_id=team_id,
        course_id=resolved_course_id,
        student_ids=student_ids,
    )
