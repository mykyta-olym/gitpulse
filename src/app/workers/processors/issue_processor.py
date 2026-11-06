"""Process GitLab issue webhook events."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue
from app.models.project import GitLabProject
from app.utils.time_utils import parse_gitlab_datetime
from app.workers.processors._common import is_stale_update
from app.workers.processors.student_resolver import resolve_student

logger = logging.getLogger(__name__)


async def process_issue_event(
    session: AsyncSession,
    payload: dict[str, Any],
    gitlab_project_id: int,
) -> None:
    """Upsert an issue from a webhook payload."""
    obj = payload.get("object_attributes", {})
    if not obj:
        logger.warning("Issue event missing object_attributes")
        return

    # Find internal project
    project_stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
    project_result = await session.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if not project:
        logger.warning("Project %d not registered, skipping issue event", gitlab_project_id)
        return

    gitlab_iid = obj.get("iid")
    gitlab_id = obj.get("id")
    if not gitlab_iid or not gitlab_id:
        return

    # Resolve author - try user object, author object, or direct author_id
    author_info = payload.get("user") or obj.get("author") or {}
    author_gitlab_id = author_info.get("id") or obj.get("author_id")
    author_username = author_info.get("username")
    author_id = await resolve_student(session, author_gitlab_id, author_username)

    # Resolve assignee (first one)
    assignees = payload.get("assignees") or obj.get("assignees") or []
    assignee_info = assignees[0] if assignees else {}
    assignee_gitlab_id = assignee_info.get("id") if assignee_info else None
    assignee_username = assignee_info.get("username") if assignee_info else None
    assignee_id = await resolve_student(session, assignee_gitlab_id, assignee_username)

    # Upsert
    issue_stmt = select(Issue).where(Issue.project_id == project.id, Issue.gitlab_iid == gitlab_iid)
    issue_result = await session.execute(issue_stmt)
    issue = issue_result.scalar_one_or_none()

    # -- Guard against out-of-order / re-delivered issue events --
    # A stale ``reopen``/``update`` (state=opened) redelivered after the
    # ``close`` event would otherwise regress issue.state and flip R11 (issue
    # closure) for the assignee. Skip the stale payload for an issue we already
    # hold newer state for; new issues and equal-timestamp full syncs apply.
    incoming_updated_at = parse_gitlab_datetime(obj.get("updated_at"))
    if issue is not None and is_stale_update(issue.updated_at, incoming_updated_at):
        logger.info(
            "Skipping stale out-of-order issue webhook: project=%d iid=#%s "
            "incoming_updated_at=%s < stored=%s",
            gitlab_project_id,
            gitlab_iid,
            incoming_updated_at,
            issue.updated_at,
        )
        return

    if issue is None:
        issue = Issue(
            project_id=project.id,
            gitlab_id=gitlab_id,
            gitlab_iid=gitlab_iid,
        )
        session.add(issue)

    issue.title = obj.get("title")
    issue.description = obj.get("description")
    issue.state = obj.get("state", "opened")
    issue.author_gitlab_id = author_gitlab_id
    issue.author_id = author_id
    issue.assignee_gitlab_id = assignee_gitlab_id
    issue.assignee_id = assignee_id
    raw_labels = payload.get("labels") or obj.get("labels") or []
    if raw_labels and isinstance(raw_labels[0], dict):
        issue.labels = [lbl.get("title", "") for lbl in raw_labels]
    else:
        issue.labels = [str(lbl) for lbl in raw_labels]
    # Only overwrite a timestamp we actually parsed, so an unparseable payload
    # cannot wipe what a full sync stored - and a NULL updated_at would switch
    # off the stale-event guard above, which needs it to spot a late redelivery.
    # closed_at is deliberately NOT guarded: GitLab sends it as null when an
    # issue is reopened, and clearing it then is correct.
    if (incoming_created_at := parse_gitlab_datetime(obj.get("created_at"))) is not None:
        issue.created_at = incoming_created_at
    issue.closed_at = parse_gitlab_datetime(obj.get("closed_at"))
    if incoming_updated_at is not None:
        issue.updated_at = incoming_updated_at

    await session.flush()
    logger.debug(
        "Issue upserted: project=%d iid=#%d state=%s", gitlab_project_id, gitlab_iid, issue.state
    )
