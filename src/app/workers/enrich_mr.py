"""Job 3: enrich_mr - re-fetch MR data from GitLab API and update DB.

Fetches the full MR state (diff stats, approvals, notes count, pipeline
status) from the GitLab API.  This is the heavyweight enrichment job -
it makes 3-4 API calls per MR (MR detail, changes, approvals, notes).

Idempotency
-----------
Pure UPSERT on ``(project_id, gitlab_iid)``.  Approval and note data is
merged, not appended - safe to run multiple times.

Compliance data enriched
------------------------
- ``branch_naming_ok``   - validated against course settings pattern
- ``template_compliant`` - MR description checked for required sections
- ``has_test_changes``   - diff files matched against test file patterns
- ``has_issue_link``     - closing references extracted from description
- Approvals upserted into ``mr_approvals``
- Review activities aggregated into ``review_activities``
"""

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import select

from app.compliance.patterns import resolve_patterns
from app.services.gitlab.token_health import gitlab_token_guarded
from app.utils.time_utils import parse_gitlab_datetime
from app.workers.enrich_common import before_semester, course_of, student_id
from app.workers.idempotency import idempotent_job
from app.workers.processors._common import replace_mr_diffs

logger = logging.getLogger(__name__)


@gitlab_token_guarded
@idempotent_job
def enrich_mr(project_gitlab_id: int, mr_iid: int) -> None:
    """RQ job: enrich a single merge request from GitLab API."""

    from app.observability.metrics import ENRICHMENT_DURATION, ENRICHMENT_TOTAL

    t0 = time.monotonic()
    try:
        asyncio.run(_enrich_async(project_gitlab_id, mr_iid))
        ENRICHMENT_TOTAL.labels(entity_type="mr", status="ok").inc()
    except Exception:
        ENRICHMENT_TOTAL.labels(entity_type="mr", status="error").inc()
        raise
    finally:
        ENRICHMENT_DURATION.labels(entity_type="mr").observe(time.monotonic() - t0)


async def _enrich_async(project_gitlab_id: int, mr_iid: int) -> None:
    from app.models.merge_request import MergeRequest
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
                "Project gitlab_id=%s not registered - skip",
                project_gitlab_id,
            )
            return
        course = await course_of(session, project)
        if course and not course.is_active:
            logger.info(
                "Skipping MR enrichment for archived course (project=%s)",
                project_gitlab_id,
            )
            return
        course_settings = course.settings if course else None

        async with GitLabClient(
            base_url=str(settings.gitlab_url),
            private_token=settings.gitlab_api_token,
        ) as gl:
            api_mr = await gl.get_merge_request(project_gitlab_id, mr_iid)
            if api_mr is None:
                logger.warning("MR %s!%s not found via API", project_gitlab_id, mr_iid)
                return
            changes = await gl.get_mr_changes(project_gitlab_id, mr_iid)
            approvals_data = await gl.get_mr_approvals(project_gitlab_id, mr_iid)
            notes_data = await gl.get_mr_notes(project_gitlab_id, mr_iid)

        if before_semester(
            api_mr.get("created_at"), course_settings, "MR", project_gitlab_id, mr_iid
        ):
            return

        change_items: list[dict[str, Any]] = []
        if isinstance(changes, dict):
            change_items = list(changes.get("changes", []) or [])
        approved_by = approvals_data.get("approved_by", []) if approvals_data else []
        mr_data = await _mr_fields(
            session, api_mr, changes, change_items, approvals_data, course_settings
        )

        mr = (
            await session.execute(
                select(MergeRequest).where(
                    MergeRequest.project_id == project.id,
                    MergeRequest.gitlab_iid == mr_iid,
                )
            )
        ).scalar_one_or_none()
        if mr is None:
            mr = MergeRequest(project_id=project.id, gitlab_iid=mr_iid, **mr_data)
            session.add(mr)
        else:
            for k, v in mr_data.items():
                setattr(mr, k, v)
        await session.flush()

        # The linked issue's row (FK), so R11 checks the actual ticket's state
        # rather than guessing from issues_assigned.
        if mr_data["linked_issue_iid"] is not None:
            from app.models.issue import Issue

            mr.linked_issue_id = (
                await session.execute(
                    select(Issue.id).where(
                        Issue.project_id == project.id,
                        Issue.gitlab_iid == mr_data["linked_issue_iid"],
                    )
                )
            ).scalar_one_or_none()

        if change_items:
            await replace_mr_diffs(session, mr.id, change_items)
        for entry in approved_by:
            user = entry.get("user", entry)
            await _add_approval(
                session, mr, user.get("id"), parse_gitlab_datetime(entry.get("approved_at"))
            )
        for approver_gl_id, approved_at in _approvals_in_system_notes(notes_data).items():
            await _add_approval(session, mr, approver_gl_id, approved_at)
        await _ingest_notes(session, mr, notes_data)

        await session.commit()
        logger.info(
            "Enriched MR %s!%s - %d approvals, %d notes ingested",
            project_gitlab_id,
            mr_iid,
            len(approved_by),
            len(notes_data or []),
        )


async def _mr_fields(
    session: Any,
    api_mr: dict[str, Any],
    changes: Any,
    change_items: list[dict[str, Any]],
    approvals_data: Any,
    course_settings: Any,
) -> dict[str, Any]:
    """The MR's stored fields from the API, the compliance verdicts included."""
    from app.utils.gitlab_patterns import (
        check_template_sections,
        count_test_files,
        primary_linked_issue_iid,
        validate_branch_name,
    )

    source_branch = api_mr.get("source_branch", "")
    description = api_mr.get("description") or ""
    patterns = resolve_patterns(course_settings)
    branch_ok = (
        validate_branch_name(source_branch, patterns.branch_pattern)
        if patterns.branch_pattern
        else True
    )
    template_ok, _ = check_template_sections(description, patterns.required_sections)
    linked_issue = primary_linked_issue_iid(description, source_branch)
    changed_files = [c.get("new_path", "") for c in change_items if isinstance(c, dict)]
    normalized_files = [path for path in changed_files if path]
    diff_stats = (changes.get("diff_stats") or {}) if isinstance(changes, dict) else None
    merged_by_raw = api_mr.get("merged_by") or api_mr.get("merge_user") or {}
    approved_by = approvals_data.get("approved_by", []) if approvals_data else []
    return {
        "gitlab_id": api_mr["id"],
        "title": api_mr.get("title", ""),
        "description": description,
        "state": api_mr.get("state", "opened"),
        "source_branch": source_branch,
        "target_branch": api_mr.get("target_branch", ""),
        "author_gitlab_id": (api_mr.get("author") or {}).get("id"),
        "author_id": await student_id(session, api_mr.get("author", {}).get("id")),
        "merged_by_gitlab_id": merged_by_raw.get("id"),
        "merged_by_id": await student_id(session, merged_by_raw.get("id")),
        "branch_naming_ok": branch_ok,
        "template_compliant": template_ok,
        "has_test_changes": count_test_files(normalized_files, patterns.test_file_patterns) > 0,
        "has_issue_link": linked_issue is not None,
        "linked_issue_iid": linked_issue,
        "changed_files": normalized_files[:200],
        "lines_added": diff_stats.get("additions") if diff_stats is not None else None,
        "lines_removed": diff_stats.get("deletions") if diff_stats is not None else None,
        "files_changed": len(change_items),
        "approvals_count": len(approved_by),
        "approvals_required": approvals_data.get("approvals_required", 0) if approvals_data else 0,
        "created_at": parse_gitlab_datetime(api_mr.get("created_at")),
        "merged_at": parse_gitlab_datetime(api_mr.get("merged_at")),
        "closed_at": parse_gitlab_datetime(api_mr.get("closed_at")),
    }


async def _add_approval(session: Any, mr: Any, approver_gl_id: Any, approved_at: Any) -> None:
    """An MRApproval row for this approver, unless the MR already has one."""
    from app.models.mr_approval import MRApproval

    if not approver_gl_id:
        return
    existing = await session.execute(
        select(MRApproval).where(
            MRApproval.merge_request_id == mr.id,
            MRApproval.approver_gitlab_id == approver_gl_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return
    session.add(
        MRApproval(
            merge_request_id=mr.id,
            approver_gitlab_id=approver_gl_id,
            approver_id=await student_id(session, approver_gl_id),
            approved_at=approved_at,
        )
    )


def _approvals_in_system_notes(notes_data: Any) -> dict[Any, Any]:
    """Approvers by their system notes, with when they approved.

    GitLab CE writes the Approve button as a system note - "approved this
    merge request" ("approved this MR" on older versions) by the approver -
    and its /approvals endpoint may not show it without the licensed
    feature. A later "unapproved" takes the approval back.
    """
    approve_bodies = ("approved this merge request", "approved this mr")
    unapprove_bodies = ("unapproved this merge request", "unapproved this mr")
    actions: dict[Any, tuple[Any, bool]] = {}
    for note_data in notes_data or []:
        if not note_data.get("system"):
            continue
        body_l = (note_data.get("body") or "").strip().lower()
        approver_gl = (note_data.get("author") or {}).get("id")
        if not approver_gl:
            continue
        ts = parse_gitlab_datetime(note_data.get("created_at"))
        if any(body_l == b or body_l.startswith(b) for b in approve_bodies):
            actions[approver_gl] = (ts, True)
        elif any(body_l == b or body_l.startswith(b) for b in unapprove_bodies):
            actions[approver_gl] = (ts, False)
    return {gl_id: ts for gl_id, (ts, approved) in actions.items() if approved}


async def _ingest_notes(session: Any, mr: Any, notes_data: Any) -> None:
    """The MR's discussion notes not stored yet - and the ReviewActivity of
    every reviewer among them, which R06/R07 read: a review note that reached
    the database through enrichment (a missed or late note webhook, a bulk
    back-fill) created an MRNote but no ReviewActivity, so R07 under-credited
    the reviewer. Mirrors the note webhook path."""
    from app.models.mr_note import MRNote
    from app.utils.gitlab_patterns import extract_commit_refs
    from app.utils.text_analysis import char_count, word_count

    reviewers: set[Any] = set()
    for note_data in notes_data or []:
        if note_data.get("system"):
            continue  # approval system notes are read above
        note_gl_id = note_data.get("id")
        if not note_gl_id:
            continue
        existing = await session.execute(select(MRNote).where(MRNote.gitlab_note_id == note_gl_id))
        if existing.scalar_one_or_none() is not None:
            continue
        body = note_data.get("body") or ""
        author_info = note_data.get("author", {}) or {}
        author_gl = author_info.get("id")
        note_student_id = await student_id(session, author_gl)
        commit_refs = extract_commit_refs(body)
        session.add(
            MRNote(
                merge_request_id=mr.id,
                gitlab_note_id=note_gl_id,
                author_gitlab_id=author_gl,
                author_id=note_student_id,
                author_username=author_info.get("username"),
                body=body,
                word_count=word_count(body),
                char_count=char_count(body),
                is_system=False,
                is_resolvable=note_data.get("resolvable", False),
                is_resolved=note_data.get("resolved"),
                contains_commit_ref=len(commit_refs) > 0,
                commit_refs=commit_refs,
                discussion_id=note_data.get("discussion_id"),
                created_at=parse_gitlab_datetime(note_data.get("created_at")),
                updated_at=parse_gitlab_datetime(note_data.get("updated_at")),
            )
        )
        # A note by someone other than the MR author is a review.
        if note_student_id is not None and note_student_id != mr.author_id:
            reviewers.add(note_student_id)
    if reviewers:
        from app.workers.processors.note_processor import update_review_activity

        for reviewer_id in reviewers:
            await update_review_activity(session, mr.id, reviewer_id)
