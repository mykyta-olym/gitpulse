"""Project refresh worker helpers.

Houses on-demand incremental refresh of a single project's issues/MRs
(``_incremental_project_refresh``, enqueued from manual project sync).

Functions stay module-level so RQ string-paths
``app.workers.sweep.<name>`` continue to resolve via the re-exports in sweep.py.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import select

from app.services.gitlab.token_health import gitlab_token_guarded
from app.utils.constants import DEFAULT_BRANCH
from app.workers.idempotency import idempotent_job

logger = logging.getLogger(__name__)


@gitlab_token_guarded
@idempotent_job
def _incremental_project_refresh(project_id: str, gitlab_project_id: int) -> int:
    """Refresh issues and MRs for a single stale project from GitLab API."""
    return asyncio.run(_incremental_refresh_async(project_id, gitlab_project_id))


@gitlab_token_guarded
@idempotent_job
def refresh_project_gitlab_intel(gitlab_project_id: int) -> bool:
    """Refresh the stored GitLab intelligence snapshot for one project."""
    return asyncio.run(_refresh_project_gitlab_intel_async(gitlab_project_id))


async def _refresh_project_gitlab_intel_async(gitlab_project_id: int) -> bool:

    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.services.gitlab.client import GitLabClient
    from app.services.page_cache import invalidate_cascade
    from app.workers.bootstrap import worker_session
    from app.workers.progress import publish_dashboard_update
    from app.workers.sync_common import fetch_gitlab_intel_snapshot

    async with worker_session() as (session, settings):
        stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
        project = (await session.execute(stmt)).scalar_one_or_none()
        if project is None:
            return False

        async with GitLabClient(
            base_url=str(settings.gitlab_url),
            private_token=settings.gitlab_api_token,
        ) as gl:
            intel = await fetch_gitlab_intel_snapshot(
                gl,
                int(project.gitlab_project_id),
                project.default_branch,
            )
        if not intel:
            return False

        project.gitlab_intel = intel
        await session.commit()

        team = await session.get(Team, project.team_id)
        course_id = team.course_id if team else None
        invalidate_cascade(project_id=project.id, team_id=project.team_id, course_id=course_id)
        publish_dashboard_update(
            "project",
            str(project.id),
            "gitlab_intel_refreshed",
            extra={"gitlab_project_id": gitlab_project_id},
        )
        publish_dashboard_update(
            "team",
            str(project.team_id),
            "gitlab_intel_refreshed",
            extra={"project_id": str(project.id), "gitlab_project_id": gitlab_project_id},
        )
        if course_id:
            publish_dashboard_update(
                "course",
                str(course_id),
                "gitlab_intel_refreshed",
                extra={"team_id": str(project.team_id), "project_id": str(project.id)},
            )
        return True


async def _incremental_refresh_async(project_id: str, gitlab_project_id: int) -> int:

    from app.models.issue import Issue
    from app.models.merge_request import MergeRequest
    from app.models.project import GitLabProject
    from app.services.events import get_queue as _get_queue
    from app.services.gitlab.client import GitLabClient
    from app.workers.bootstrap import worker_session
    from app.workers.sweep import _SWEEP_RETRY

    count = 0
    async with worker_session() as (session, settings):
        pid = uuid.UUID(project_id)

        # -- Sync project metadata (name, path, default_branch) from GitLab --
        try:
            async with GitLabClient(
                base_url=str(settings.gitlab_url),
                private_token=settings.gitlab_api_token,
            ) as gl:
                gl_data = await gl.get_project(gitlab_project_id)
                if gl_data:
                    proj = await session.get(GitLabProject, pid)
                    if proj:
                        new_name = gl_data.get("name", "")
                        new_path = gl_data.get("path_with_namespace", "")
                        new_branch = gl_data.get("default_branch", DEFAULT_BRANCH)
                        changed = False
                        if new_name and proj.gitlab_project_name != new_name:
                            proj.gitlab_project_name = new_name
                            changed = True
                        if new_path and proj.gitlab_project_path != new_path:
                            proj.gitlab_project_path = new_path
                            changed = True
                        if new_branch and proj.default_branch != new_branch:
                            proj.default_branch = new_branch
                            changed = True
                        if changed:
                            await session.commit()
                            logger.info(
                                "Updated metadata for project %s (gitlab_id=%d)",
                                project_id,
                                gitlab_project_id,
                            )
        except Exception:
            logger.debug("Metadata sync skipped for project %s", project_id, exc_info=True)

        # Enrich all known issues
        i_stmt = select(Issue.gitlab_iid).where(Issue.project_id == pid)
        i_res = await session.execute(i_stmt)
        issue_iids = [row[0] for row in i_res.all()]

        # Enrich all known MRs
        m_stmt = select(MergeRequest.gitlab_iid).where(MergeRequest.project_id == pid)
        m_res = await session.execute(m_stmt)
        mr_iids = [row[0] for row in m_res.all()]

        try:
            queue = _get_queue("default")
            for iid in issue_iids:
                queue.enqueue(
                    "app.workers.enrich_issue.enrich_issue",
                    gitlab_project_id,
                    iid,
                    job_timeout=settings.job_timeout_event_seconds,
                    retry=_SWEEP_RETRY,
                )
                count += 1
            for iid in mr_iids:
                queue.enqueue(
                    "app.workers.enrich_mr.enrich_mr",
                    gitlab_project_id,
                    iid,
                    job_timeout=settings.job_timeout_enrich_seconds,
                    retry=_SWEEP_RETRY,
                )
                count += 1
        except Exception:
            logger.exception("Failed to enqueue refresh for project %s", project_id)

    if count:
        logger.info("Incremental refresh enqueued %d jobs for project %s", count, project_id)
    return count
