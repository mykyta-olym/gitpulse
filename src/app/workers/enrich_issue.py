"""Job 2: enrich_issue - re-fetch issue data from GitLab API and update DB.

Triggered after process_event for issue webhooks, or during periodic
enrichment sweeps.  Fetches the canonical issue state from the GitLab API
(labels, assignees, milestone, time tracking, related MRs) and merges it
into the local ``issues`` row.

Idempotency
-----------
Pure UPSERT on ``(project_id, gitlab_iid)`` - running twice produces the
same row state because GitLab API returns the current truth.

When to call
------------
- Immediately after ``process_event`` stores a new/updated issue.
- During scheduled enrichment sweep (catches label changes, reassignments
  that didn't generate a webhook).
"""

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import select

from app.services.gitlab.token_health import gitlab_token_guarded
from app.utils.time_utils import parse_gitlab_datetime
from app.workers.enrich_common import before_semester, course_of, student_id
from app.workers.idempotency import idempotent_job

logger = logging.getLogger(__name__)


@gitlab_token_guarded
@idempotent_job
def enrich_issue(project_gitlab_id: int, issue_iid: int) -> None:
    """RQ job: enrich a single issue from GitLab API."""

    from app.observability.metrics import ENRICHMENT_DURATION, ENRICHMENT_TOTAL

    t0 = time.monotonic()
    try:
        asyncio.run(_enrich_async(project_gitlab_id, issue_iid))
        ENRICHMENT_TOTAL.labels(entity_type="issue", status="ok").inc()
    except Exception:
        ENRICHMENT_TOTAL.labels(entity_type="issue", status="error").inc()
        raise
    finally:
        ENRICHMENT_DURATION.labels(entity_type="issue").observe(time.monotonic() - t0)


async def _enrich_async(project_gitlab_id: int, issue_iid: int) -> None:
    from app.models.project import GitLabProject
    from app.services.gitlab.client import GitLabClient
    from app.workers.bootstrap import worker_session

    async with worker_session() as (session, settings):
        project = (
            await session.execute(
                select(GitLabProject).where(GitLabProject.gitlab_project_id == project_gitlab_id)
            )
        ).scalar_one_or_none()
        if project is None:
            logger.warning(
                "Project gitlab_id=%s not registered - skip enrich",
                project_gitlab_id,
            )
            return
        course = await course_of(session, project)
        if course and not course.is_active:
            logger.info(
                "Skipping issue enrichment for archived course (project=%s)",
                project_gitlab_id,
            )
            return

        async with GitLabClient(
            base_url=str(settings.gitlab_url),
            private_token=settings.gitlab_api_token,
        ) as gl:
            api_issue = await gl.get_issue(project_gitlab_id, issue_iid)
            if api_issue is None:
                logger.warning("Issue %s#%s not found via API", project_gitlab_id, issue_iid)
                return
            notes_data = await gl.get_issue_notes(project_gitlab_id, issue_iid)

        if before_semester(
            api_issue.get("created_at"),
            course.settings if course else None,
            "issue",
            project_gitlab_id,
            issue_iid,
        ):
            return

        issue = await _upsert_issue(session, project, issue_iid, api_issue)
        await session.flush()
        notes_ingested = await _ingest_issue_notes(session, issue, notes_data)
        await session.commit()
        logger.info(
            "Enriched issue %s#%s (%s) - %d notes ingested",
            project_gitlab_id,
            issue_iid,
            issue.state,
            notes_ingested,
        )


async def _upsert_issue(
    session: Any, project: Any, issue_iid: int, api_issue: dict[str, Any]
) -> Any:
    """The issue from the API: author, assignees (GitLab allows several - the
    first is the assignee), who closed it, labels and timestamps."""
    from app.models.issue import Issue

    author_gitlab_id = api_issue.get("author", {}).get("id")
    author_student_id = await student_id(session, author_gitlab_id)
    assignees = api_issue.get("assignees") or []
    all_assignee_gitlab_ids = [a["id"] for a in assignees if "id" in a]
    assignee_gitlab_id = assignees[0]["id"] if assignees else None
    assignee_student_id = await student_id(session, assignee_gitlab_id)
    closed_by_gitlab_id = (api_issue.get("closed_by") or {}).get("id")
    closed_by_student_id = await student_id(session, closed_by_gitlab_id)
    labels = [lb["name"] if isinstance(lb, dict) else lb for lb in (api_issue.get("labels") or [])]

    issue = (
        await session.execute(
            select(Issue).where(Issue.project_id == project.id, Issue.gitlab_iid == issue_iid)
        )
    ).scalar_one_or_none()
    if issue is None:
        issue = Issue(
            project_id=project.id,
            gitlab_iid=issue_iid,
            gitlab_id=api_issue["id"],
            title=api_issue.get("title", ""),
            description=api_issue.get("description") or "",
            state=api_issue.get("state", "opened"),
            created_at=parse_gitlab_datetime(api_issue.get("created_at")),
        )
        session.add(issue)
    else:
        issue.title = api_issue.get("title", issue.title)
        issue.description = api_issue.get("description") or issue.description
        issue.state = api_issue.get("state", issue.state)
    issue.author_gitlab_id = author_gitlab_id
    issue.author_id = author_student_id
    issue.assignee_gitlab_id = assignee_gitlab_id
    issue.assignee_id = assignee_student_id
    issue.all_assignee_gitlab_ids = all_assignee_gitlab_ids
    issue.closed_by_gitlab_id = closed_by_gitlab_id
    issue.closed_by_id = closed_by_student_id
    issue.labels = labels
    issue.updated_at = parse_gitlab_datetime(api_issue.get("updated_at"))
    issue.closed_at = parse_gitlab_datetime(api_issue.get("closed_at"))
    return issue


async def _ingest_issue_notes(session: Any, issue: Any, notes_data: Any) -> int:
    """The issue's discussion notes not stored yet; how many were added."""
    from app.models.issue_note import IssueNote
    from app.utils.text_analysis import char_count, word_count

    added = 0
    for note_data in notes_data or []:
        if note_data.get("system"):
            continue
        note_gl_id = note_data.get("id")
        if not note_gl_id:
            continue
        existing = await session.execute(
            select(IssueNote).where(IssueNote.gitlab_note_id == note_gl_id)
        )
        if existing.scalar_one_or_none() is not None:
            continue  # already stored
        body = note_data.get("body") or ""
        author_info = note_data.get("author", {}) or {}
        author_gl = author_info.get("id")
        session.add(
            IssueNote(
                issue_id=issue.id,
                gitlab_note_id=note_gl_id,
                author_gitlab_id=author_gl,
                author_id=await student_id(session, author_gl),
                author_username=author_info.get("username"),
                body=body,
                word_count=word_count(body),
                char_count=char_count(body),
                is_system=False,
                created_at=parse_gitlab_datetime(note_data.get("created_at")),
                updated_at=parse_gitlab_datetime(note_data.get("updated_at")),
            )
        )
        added += 1
    return added
