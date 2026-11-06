"""Process GitLab note (MR comment) webhook events."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue
from app.models.issue_note import IssueNote
from app.models.merge_request import MergeRequest
from app.models.mr_note import MRNote
from app.models.project import GitLabProject
from app.models.review_activity import ReviewActivity
from app.utils.gitlab_patterns import extract_commit_refs
from app.utils.text_analysis import char_count, is_meaningful_comment, word_count
from app.workers.processors.student_resolver import resolve_student

logger = logging.getLogger(__name__)


async def process_note_event(
    session: AsyncSession,
    payload: dict[str, Any],
    gitlab_project_id: int,
) -> None:
    """Process a note event - store note and update review activity aggregate."""
    obj = payload.get("object_attributes", {})
    if not obj:
        return

    # Only process MR or Issue notes
    noteable_type = obj.get("noteable_type", "")
    if noteable_type not in {"MergeRequest", "Issue"}:
        logger.debug("Skipping non-MR/Issue note: noteable_type=%s", noteable_type)
        return

    # Find project
    stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        return

    gitlab_note_id = obj.get("id")
    if not gitlab_note_id:
        return

    noteable = await _find_noteable(session, project, payload, obj, noteable_type)
    if noteable is None:
        return

    # Resolve note author
    author_info = payload.get("user") or obj.get("author") or {}
    author_gitlab_id = author_info.get("id")
    author_username = author_info.get("username")
    author_id = await resolve_student(session, author_gitlab_id, author_username)

    # Analyze note content (webhook uses "note", REST API uses "body")
    body = obj.get("note") or obj.get("body") or ""
    is_system = obj.get("system", False)

    if isinstance(noteable, MergeRequest):
        mr = noteable
        note = await _upsert_note(
            session,
            select(MRNote).where(
                MRNote.merge_request_id == mr.id,
                MRNote.gitlab_note_id == gitlab_note_id,
            ),
            MRNote(merge_request_id=mr.id, gitlab_note_id=gitlab_note_id),
            "MR",
            gitlab_note_id,
        )
        if note is None:
            return
        _fill_note(note, author_gitlab_id, author_id, author_username, body, is_system, obj)
        commit_refs = extract_commit_refs(body) if not is_system else []
        note.is_resolvable = obj.get("resolvable", False)
        note.is_resolved = obj.get("resolved")
        note.discussion_id = obj.get("discussion_id")
        note.noteable_type = noteable_type
        note.note_type = obj.get("type")  # DiffNote, DiscussionNote, or null
        # Store diff position for inline code comments
        position = obj.get("position") or {}
        note.position_path = position.get("new_path") or position.get("old_path")
        note.position_new_line = position.get("new_line")
        note.position_old_line = position.get("old_line")
        note.contains_commit_ref = len(commit_refs) > 0
        note.commit_refs = commit_refs
        await session.flush()

        # -- Update review activity aggregate --
        # Only for non-system notes by someone other than the MR author
        if not is_system and author_id and author_id != mr.author_id:
            await update_review_activity(session, mr.id, author_id)

        logger.debug(
            "Note upserted: note_id=%d mr=!%d author=%s system=%s words=%d",
            gitlab_note_id,
            mr.gitlab_iid,
            author_info.get("username"),
            is_system,
            note.word_count,
        )
        return

    issue = noteable
    issue_note = await _upsert_note(
        session,
        select(IssueNote).where(
            IssueNote.issue_id == issue.id,
            IssueNote.gitlab_note_id == gitlab_note_id,
        ),
        IssueNote(issue_id=issue.id, gitlab_note_id=gitlab_note_id),
        "Issue",
        gitlab_note_id,
    )
    if issue_note is None:
        return
    _fill_note(issue_note, author_gitlab_id, author_id, author_username, body, is_system, obj)
    await session.flush()
    logger.debug(
        "Issue note upserted: note_id=%d issue=#%s author=%s system=%s words=%d",
        gitlab_note_id,
        (payload.get("issue") or {}).get("iid") or issue.gitlab_iid,
        author_info.get("username"),
        is_system,
        issue_note.word_count,
    )


async def _find_noteable(
    session: AsyncSession,
    project: GitLabProject,
    payload: dict[str, Any],
    obj: dict[str, Any],
    noteable_type: str,
) -> MergeRequest | Issue | None:
    """The MR or issue a note belongs to, when it is already stored."""
    if noteable_type == "MergeRequest":
        mr_iid = payload.get("merge_request", {}).get("iid")
        if not mr_iid:
            return None
        mr = (
            await session.execute(
                select(MergeRequest).where(
                    MergeRequest.project_id == project.id,
                    MergeRequest.gitlab_iid == mr_iid,
                )
            )
        ).scalar_one_or_none()
        if not mr:
            logger.warning("MR !%d not found for note, skipping", mr_iid)
        return mr

    issue_data = payload.get("issue", {})
    issue_iid = issue_data.get("iid")
    issue_gitlab_id = issue_data.get("id") or obj.get("noteable_id")
    if issue_iid:
        issue_stmt = select(Issue).where(
            Issue.project_id == project.id, Issue.gitlab_iid == issue_iid
        )
    elif issue_gitlab_id:
        issue_stmt = select(Issue).where(
            Issue.project_id == project.id, Issue.gitlab_id == issue_gitlab_id
        )
    else:
        return None
    issue = (await session.execute(issue_stmt)).scalar_one_or_none()
    if not issue:
        logger.warning("Issue note not matched to issue, skipping")
    return issue


async def _upsert_note(
    session: AsyncSession, stmt: Any, new: Any, kind: str, gitlab_note_id: int
) -> Any:
    """The stored note, or ``new`` inserted - re-read when a concurrent
    process inserted the same note first (the IntegrityError)."""
    note = (await session.execute(stmt)).scalar_one_or_none()
    if note is not None:
        return note
    session.add(new)
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError:
        note = (await session.execute(stmt)).scalar_one_or_none()
        if note is None:
            logger.error("%s note %d still not found after IntegrityError", kind, gitlab_note_id)
        return note
    return new


def _fill_note(
    note: Any,
    author_gitlab_id: Any,
    author_id: Any,
    author_username: Any,
    body: str,
    is_system: bool,
    obj: dict[str, Any],
) -> None:
    """What every note stores, MR or issue."""
    note.author_gitlab_id = author_gitlab_id
    note.author_id = author_id
    note.author_username = author_username
    note.body = body
    note.word_count = word_count(body)
    note.char_count = char_count(body)
    note.is_system = is_system
    note.created_at = _parse_dt(obj.get("created_at"))
    note.updated_at = _parse_dt(obj.get("updated_at"))


async def update_review_activity(
    session: AsyncSession,
    merge_request_id: Any,
    reviewer_id: Any,
) -> None:
    """Recompute the review activity aggregate for a reviewer on an MR."""
    # Get all non-system notes by this reviewer on this MR
    stmt = select(MRNote).where(
        MRNote.merge_request_id == merge_request_id,
        MRNote.author_id == reviewer_id,
        MRNote.is_system.is_(False),
    )
    result = await session.execute(stmt)
    notes = list(result.scalars().all())

    if not notes:
        return

    total_words = sum(n.word_count or 0 for n in notes)
    total_chars = sum(n.char_count or 0 for n in notes)
    first_note_at = min((n.created_at for n in notes if n.created_at), default=None)
    last_note_at = max((n.created_at for n in notes if n.created_at), default=None)
    meaningful = is_meaningful_comment(" ".join(n.body or "" for n in notes))

    # Upsert review activity
    ra_stmt = select(ReviewActivity).where(
        ReviewActivity.merge_request_id == merge_request_id,
        ReviewActivity.reviewer_id == reviewer_id,
    )
    ra_result = await session.execute(ra_stmt)
    ra = ra_result.scalar_one_or_none()

    if ra is None:
        ra = ReviewActivity(
            merge_request_id=merge_request_id,
            reviewer_id=reviewer_id,
        )
        session.add(ra)

    ra.note_count = len(notes)
    ra.total_words = total_words
    ra.total_chars = total_chars
    ra.first_note_at = first_note_at
    ra.last_note_at = last_note_at
    ra.is_meaningful = meaningful
    ra.recomputed_at = datetime.now(UTC)

    await session.flush()


def _parse_dt(val: str | None) -> datetime | None:
    from app.utils.time_utils import parse_gitlab_datetime

    return parse_gitlab_datetime(val)
