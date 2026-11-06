"""What the MR and the issue enrichment jobs share."""

import logging
from typing import Any

from sqlalchemy import select

from app.utils.time_utils import parse_gitlab_datetime

logger = logging.getLogger(__name__)


async def student_id(session: Any, gitlab_user_id: Any) -> Any:
    """The Student row id of a GitLab user, when one exists."""
    from app.models.student import Student

    if not gitlab_user_id:
        return None
    s = (
        await session.execute(select(Student).where(Student.gitlab_user_id == gitlab_user_id))
    ).scalar_one_or_none()
    return s.id if s else None


async def course_of(session: Any, project: Any) -> Any:
    """The course a project's group belongs to."""
    from app.models.course import Course
    from app.models.team import Team

    team = await session.get(Team, project.team_id)
    return await session.get(Course, team.course_id) if team else None


def before_semester(
    created_at_raw: Any, course_settings: Any, kind: str, project_gitlab_id: int, iid: int
) -> bool:
    """Whether the item was created before the active semester - and is left
    alone. The sync's ``since=`` / ``updated_after=`` filters and the
    dashboards' ``>= semester_start`` say the same, so a webhook or a back-fill
    for an old item cannot bring it into the semester's scope."""
    from app.utils.semester import semester_floor_utc

    floor = semester_floor_utc(course_settings)
    if floor is None:
        return False
    created = parse_gitlab_datetime(created_at_raw)
    if created is None or created >= floor:
        return False
    logger.info(
        "Skipping pre-semester %s (project=%s iid=%s created=%s floor=%s)",
        kind,
        project_gitlab_id,
        iid,
        created.isoformat(),
        floor.isoformat(),
    )
    return True
