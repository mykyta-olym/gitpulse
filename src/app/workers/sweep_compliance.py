"""Post-sync compliance snapshot job.

Houses ``compliance_snapshot_for_team`` - the per-team compliance snapshot
capture enqueued by ``sync_job`` after a team sync. It stays module-level so
the RQ string-path ``app.workers.sweep.compliance_snapshot_for_team`` keeps
resolving via the re-export in sweep.py.
"""

from __future__ import annotations

import asyncio
import logging
import uuid as _uuid

logger = logging.getLogger(__name__)


def compliance_snapshot_for_team(team_id: str) -> int:
    """Capture the compliance snapshots of one team (post-sync trigger)."""
    return asyncio.run(_compliance_snapshot_for_team_async(team_id))


async def _compliance_snapshot_for_team_async(team_id: str) -> int:

    from app.config import get_settings
    from app.models.team import Team
    from app.services.compliance_history import ComplianceHistoryService
    from app.workers.bootstrap import worker_session

    settings = get_settings()
    if not settings.compliance_auto_snapshot:
        return 0

    async with worker_session() as (session, _settings):
        team = await session.get(Team, _uuid.UUID(team_id))
        if not team or not team.is_active:
            return 0

        history = ComplianceHistoryService(session)
        try:
            week = await history.current_week(team.course_id)
            recorded = await history.capture_team_snapshots(
                team_id=team.id,
                course_id=team.course_id,
                week=week,
            )
            await session.commit()
            if recorded:
                logger.info("Post-sync compliance: %d snapshot(s) for team %s", recorded, team_id)
            return recorded
        except Exception:
            logger.exception("Post-sync compliance snapshot failed for team %s", team_id)
            return 0
