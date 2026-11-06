"""Current student cohort shared by course-wide compliance reports."""

import uuid

from sqlalchemy import Select, or_, select

from app.models.team import Team
from app.models.team_member import TeamMember


def scored_student_ids(course_id: int | uuid.UUID) -> Select[tuple[uuid.UUID]]:
    """Count a student once if they have an active, included membership.

    Teaching/mentoring roles apply across the requested course; roles and
    exclusions in other courses do not affect it. Archived courses retain
    their active teams and can still report their final results.
    """
    staff = (
        select(TeamMember.student_id)
        .join(Team, TeamMember.team_id == Team.id)
        .where(
            Team.course_id == course_id,
            or_(TeamMember.is_teacher.is_(True), TeamMember.is_mentor.is_(True)),
        )
    )
    return (
        select(TeamMember.student_id)
        .join(Team, TeamMember.team_id == Team.id)
        .where(
            Team.course_id == course_id,
            Team.is_active.is_(True),
            TeamMember.is_active.is_(True),
            TeamMember.excluded_from_scoring.is_(False),
            ~TeamMember.student_id.in_(staff),
        )
        .distinct()
    )
