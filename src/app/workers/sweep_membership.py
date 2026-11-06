"""Membership sync sweep jobs split out from sweep.py for SRP."""

from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy.orm import selectinload

from app.services.gitlab.token_health import gitlab_token_guarded
from app.workers.idempotency import idempotent_job

logger = logging.getLogger(__name__)


@gitlab_token_guarded
@idempotent_job
def sync_single_team_members(team_id: str) -> int:
    """Sync members for a single team - called on-demand from push events."""
    return asyncio.run(_sync_single_team_async(team_id))


async def _sync_single_team_async(team_id: str) -> int:

    from app.models.team import Team
    from app.services.gitlab.client import GitLabClient
    from app.services.member_sync import sync_team_members
    from app.workers.bootstrap import worker_session

    async with worker_session() as (session, settings):
        team = await session.get(Team, uuid.UUID(team_id), options=[selectinload(Team.projects)])
        if not team or not team.is_active:
            return 0

        async with GitLabClient(
            base_url=str(settings.gitlab_url),
            private_token=settings.gitlab_api_token,
        ) as gl:
            sync_result = await sync_team_members(session, gl, team, source="push_triggered")
            changes = (
                sync_result.members_added + sync_result.members_removed + sync_result.roles_changed
            )
            if changes:
                logger.info(
                    "Push-triggered member sync team=%s: +%d -%d ~%d",
                    team.name,
                    sync_result.members_added,
                    sync_result.members_removed,
                    sync_result.roles_changed,
                )
                from app.workers.progress import publish_dashboard_update

                publish_dashboard_update(
                    "team",
                    str(team.id),
                    "member_changed",
                    extra={
                        "added": sync_result.members_added,
                        "removed": sync_result.members_removed,
                        "source": "push_triggered",
                    },
                )
                if team.course_id:
                    publish_dashboard_update(
                        "course",
                        str(team.course_id),
                        "member_changed",
                        extra={"team_id": str(team.id), "source": "push_triggered"},
                    )
            await session.commit()
            return changes
