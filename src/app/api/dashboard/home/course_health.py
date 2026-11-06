"""Per-course health helpers for the dashboard home page."""

import uuid

from sqlalchemy import func, select

from app.api.dashboard._helpers import logger
from app.api.dashboard._stats import latest_team_snapshot_subquery
from app.dependencies import DbSession
from app.models.team import Team
from app.models.team_metric_snapshot import TeamMetricSnapshot

CourseHealth = dict[str, dict[str, int]]


async def _build_course_health(
    active_ids: list[uuid.UUID],
    db: DbSession,
) -> CourseHealth:
    """Return per-course RED-team counts for teacher/admin course cards."""
    if not active_ids:
        return {}

    health: CourseHealth = {}
    try:
        latest_health_sq = latest_team_snapshot_subquery(active_ids)
        red_stmt = (
            select(Team.course_id, func.count(func.distinct(Team.id)))
            .select_from(Team)
            .join(
                TeamMetricSnapshot,
                TeamMetricSnapshot.team_id == Team.id,
            )
            .join(
                latest_health_sq,
                (TeamMetricSnapshot.team_id == latest_health_sq.c.team_id)
                & (TeamMetricSnapshot.computed_at == latest_health_sq.c.max_at),
            )
            .where(
                Team.course_id.in_(active_ids),
                TeamMetricSnapshot.overall_traffic_light == "RED",
            )
            .group_by(Team.course_id)
        )
        result = await db.execute(red_stmt)
        for cid, cnt in result.all():
            health[str(cid)] = {"red_teams": cnt}
    except Exception:
        logger.debug("course health build failed", exc_info=True)
    return health
