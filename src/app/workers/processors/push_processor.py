"""Process GitLab push webhook events - minimal: log branch activity."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import GitLabProject

logger = logging.getLogger(__name__)


async def process_push_event(
    session: AsyncSession,
    payload: dict[str, Any],
    gitlab_project_id: int,
) -> None:
    """Log push events for branch tracking.

    Push events are primarily used for:
    - Tracking branch creation (R02 branch naming)
    - Detecting force pushes
    - Counting commits per student

    For MVP, we rely on MR source_branch for branch naming checks.
    Full push tracking is post-MVP.
    """
    ref = payload.get("ref", "")
    branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
    before = payload.get("before", "")
    after = payload.get("after", "")
    total_commits = payload.get("total_commits_count", 0)
    user = payload.get("user_username", "unknown")

    # Detect force push (before is not a parent of after; non-zero before/after heuristic)
    is_new_branch = before == "0" * 40
    is_delete = after == "0" * 40

    logger.info(
        "Push event: project=%d branch=%s user=%s commits=%d new=%s delete=%s",
        gitlab_project_id,
        branch,
        user,
        total_commits,
        is_new_branch,
        is_delete,
    )

    # -- Resolve project once (shared by conflict & commit sub-steps) --
    project = None
    if is_new_branch or not is_delete:
        stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()

    # -- Store individual commits --
    if not is_delete and project:
        await _process_push_commits(session, payload, project, branch)

        # -- R13: immediate compliance refresh after new commits --
        if project.team_id:
            from app.services.events import enqueue_metrics_refresh

            enqueue_metrics_refresh(str(project.team_id))


async def _process_push_commits(
    session: AsyncSession,
    payload: dict[str, Any],
    project: GitLabProject,
    branch: str,
) -> None:
    """Extract and store individual commits from push event."""
    from app.workers.processors.commit_processor import process_commit

    commits = payload.get("commits", [])
    if not commits:
        return

    # Process each commit in the push
    processed = 0
    for commit_data in commits:
        # Webhook commit format differs slightly from API
        commit_info = {
            "id": commit_data.get("id"),
            "title": commit_data.get("title") or commit_data.get("message", "").split("\n")[0],
            "message": commit_data.get("message"),
            "author_name": commit_data.get("author", {}).get("name"),
            "author_email": commit_data.get("author", {}).get("email"),
            "timestamp": commit_data.get("timestamp"),
            "stats": {
                # Webhook doesn't include stats, estimate from file lists
                "additions": 0,
                "deletions": 0,
                "total": len(
                    commit_data.get("added", [])
                    + commit_data.get("modified", [])
                    + commit_data.get("removed", [])
                ),
            },
            "parent_ids": [],  # Not available in webhook
        }

        commit = await process_commit(session, commit_info, str(project.id), branch)
        if commit:
            processed += 1

    if processed > 0:
        logger.info(
            "Stored %d commits from push to branch %s (project=%d)",
            processed,
            branch,
            project.gitlab_project_id,
        )
