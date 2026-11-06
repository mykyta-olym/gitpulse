"""Process GitLab merge request webhook events."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.compliance.patterns import resolve_patterns
from app.config import get_settings
from app.models.course_settings import CourseSettings
from app.models.issue import Issue
from app.models.merge_request import MergeRequest
from app.models.project import GitLabProject
from app.models.team import Team
from app.services.gitlab.client import GitLabClient
from app.utils.gitlab_patterns import (
    check_template_sections,
    count_test_files,
    primary_linked_issue_iid,
    validate_branch_name,
)
from app.utils.time_utils import parse_gitlab_datetime
from app.workers.processors._common import is_stale_update, replace_mr_diffs
from app.workers.processors.student_resolver import resolve_student

logger = logging.getLogger(__name__)


def _extract_assignee_reviewers(
    obj: dict[str, Any], payload: dict[str, Any]
) -> tuple[int | None, str | None, list[int]]:
    """Pull the explicit assignee + reviewer ids from an MR payload.

    A full API sync nests ``assignees``/``reviewers`` inside the MR detail
    (``object_attributes``); a live webhook puts them at the payload top level.
    We accept either so live updates aren't blank until the next full sync.
    Returns ``(assignee_gitlab_id, assignee_username, reviewer_gitlab_ids)``.
    """
    assignees = obj.get("assignees") or payload.get("assignees") or []
    assignee_info = (
        assignees[0] if assignees else (obj.get("assignee") or payload.get("assignee") or {})
    )
    if not isinstance(assignee_info, dict):
        assignee_info = {}
    assignee_gid = assignee_info.get("id")
    assignee_username = assignee_info.get("username")
    reviewers = obj.get("reviewers") or payload.get("reviewers") or []
    reviewer_gids = [int(r["id"]) for r in reviewers if isinstance(r, dict) and r.get("id")]
    return assignee_gid, assignee_username, reviewer_gids


def _enrichment_is_redundant(
    mr: MergeRequest | None, incoming_updated_at: "datetime | None"
) -> bool:
    """Whether the diff/approvals fetch can be skipped for this delivery.

    The bulk sync already skips it for an MR whose ``updated_at`` has not moved,
    because both are immutable while the MR is unchanged. The same holds for a
    webhook, and matters more there: GitLab re-delivers on failure, so every
    duplicate delivery otherwise costs two live API calls.

    ``changed_files`` is what the enrichment populates, so requiring it proves a
    previous fetch actually succeeded. Without that check, a delivery following
    a failed fetch (an expired token, say) would be permanently starved of
    enrichment, because its timestamp already matches what we stored.
    """
    if mr is None or incoming_updated_at is None:
        return False
    if mr.updated_at != incoming_updated_at:
        return False
    return bool(mr.changed_files)


async def process_mr_event(
    session: AsyncSession,
    payload: dict[str, Any],
    gitlab_project_id: int,
    gitlab_client: GitLabClient | None = None,
    skip_api_enrichment: bool = False,
) -> None:
    """Upsert a merge request and enrich via GitLab API.

    When ``skip_api_enrichment`` is set the expensive per-MR diff and
    approval API calls are skipped. Callers (the bulk team sync) pass this
    for MRs whose ``updated_at`` is unchanged since the last sync - the diff
    and approvals of an unchanged MR are immutable, so re-fetching them on
    every sync is pure waste and was the single biggest cost in the MR sync
    stage (~8 s/MR on diff-heavy fork repos).
    """
    obj = payload.get("object_attributes", {})
    if not obj:
        return

    # Find internal project
    project_stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
    project_result = await session.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    if not project:
        return

    gitlab_iid = obj.get("iid")
    gitlab_id = obj.get("id")
    if not gitlab_iid or not gitlab_id:
        return

    # Resolve author - try author object first (from API), then fallback to author_id
    author_info = obj.get("author") or {}
    author_gitlab_id = author_info.get("id") or obj.get("author_id")
    author_id = await resolve_student(session, author_gitlab_id, author_info.get("username"))

    # Resolve merged_by (if merge event)
    merged_by_gitlab_id = None
    merged_by_id = None
    if obj.get("action") == "merge" or obj.get("state") == "merged":
        # merged_by can be in user object or merged_by object
        merger_info = obj.get("merge_user") or obj.get("merged_by") or payload.get("user") or {}
        merged_by_gitlab_id = merger_info.get("id")
        merged_by_id = await resolve_student(
            session, merged_by_gitlab_id, merger_info.get("username")
        )

    # Upsert MR (use FOR UPDATE to prevent concurrent diff replace races)
    mr_stmt = (
        select(MergeRequest)
        .where(
            MergeRequest.project_id == project.id,
            MergeRequest.gitlab_iid == gitlab_iid,
        )
        .with_for_update()
    )
    mr_result = await session.execute(mr_stmt)
    mr = mr_result.scalar_one_or_none()

    # -- Guard against out-of-order / re-delivered MR events --
    # GitLab does not guarantee webhook ordering; a stale ``update`` (state=
    # opened) redelivered after the ``merge`` event would otherwise regress
    # mr.state and flip R10/R11 for the author. Skip the stale payload for an
    # MR we already hold newer state for. New MRs and full syncs (equal
    # updated_at) fall through and apply normally.
    incoming_updated_at = parse_gitlab_datetime(obj.get("updated_at"))
    if mr is not None and is_stale_update(mr.updated_at, incoming_updated_at):
        logger.info(
            "Skipping stale out-of-order MR webhook: project=%d iid=!%s "
            "incoming_updated_at=%s < stored=%s",
            gitlab_project_id,
            gitlab_iid,
            incoming_updated_at,
            mr.updated_at,
        )
        return

    # The bulk sync already skips the diff/approvals fetch for an MR whose
    # updated_at has not moved, because both are immutable while the MR is
    # unchanged. The same is true here, and it matters more: GitLab re-delivers
    # webhooks on failure, so a duplicate delivery otherwise costs two live API
    # calls each time. Only skip when a previous enrichment demonstrably
    # succeeded - changed_files is what it populates - so a delivery that
    # follows a failed fetch (an expired token, say) still gets its chance.
    if _enrichment_is_redundant(mr, incoming_updated_at):
        skip_api_enrichment = True

    if mr is None:
        mr = MergeRequest(
            project_id=project.id,
            gitlab_id=gitlab_id,
            gitlab_iid=gitlab_iid,
        )
        session.add(mr)

    mr.title = obj.get("title")
    mr.description = obj.get("description")
    mr.state = obj.get("state", "opened")
    mr.source_branch = obj.get("source_branch")
    mr.target_branch = obj.get("target_branch", "master")
    mr.author_gitlab_id = author_gitlab_id
    mr.author_id = author_id
    # Only overwrite a timestamp we actually parsed. Assigning unconditionally
    # meant an unparseable payload shape wiped the value a full sync had already
    # stored, and a NULL updated_at also switches off the stale-webhook guard
    # above, since it has nothing to compare an incoming delivery against.
    if (incoming_created_at := parse_gitlab_datetime(obj.get("created_at"))) is not None:
        mr.created_at = incoming_created_at
    if incoming_updated_at is not None:
        mr.updated_at = incoming_updated_at

    # Explicit GitLab assignee + reviewers (see _extract_assignee_reviewers:
    # full sync nests them in object_attributes, live webhooks put them at the
    # payload top level - accept both).
    _assignee_gid, _assignee_username, _reviewer_gids = _extract_assignee_reviewers(obj, payload)
    mr.assignee_gitlab_id = _assignee_gid
    mr.assignee_id = (
        await resolve_student(session, _assignee_gid, _assignee_username) if _assignee_gid else None
    )
    mr.reviewer_gitlab_ids = _reviewer_gids

    if merged_by_gitlab_id:
        mr.merged_by_gitlab_id = merged_by_gitlab_id
        mr.merged_by_id = merged_by_id
    if obj.get("state") == "merged":
        mr.merged_at = parse_gitlab_datetime(obj.get("merged_at") or obj.get("updated_at"))
    if obj.get("state") == "closed":
        mr.closed_at = parse_gitlab_datetime(obj.get("closed_at") or obj.get("updated_at"))

    # Detect branch deletion - GitLab sets force_remove_source_branch when
    # the project or user configured auto-delete on merge, or when GitLab
    # infers it from merge options. Present in both REST and webhook payloads.
    if obj.get("force_remove_source_branch") and mr.state == "merged":
        mr.source_branch_deleted = True

    await _link_issue(session, mr, project)
    test_patterns = await _apply_course_checks(session, mr, project)

    # -- Enrich via GitLab API: diff stats + test file detection --
    if not skip_api_enrichment:
        settings = get_settings()
        client = gitlab_client
        close_client = False
        if settings.gitlab_api_token and client is None:
            client = GitLabClient(
                base_url=settings.gitlab_url,
                private_token=settings.gitlab_api_token,
                timeout=settings.gitlab_api_timeout_seconds,
                max_retries=settings.gitlab_api_max_retries,
            )
            close_client = True
        if client is not None:
            try:
                await _enrich_from_api(
                    session, mr, client, gitlab_project_id, gitlab_iid, test_patterns
                )
            except Exception:
                logger.warning("GitLab API enrichment failed for MR !%d", gitlab_iid, exc_info=True)
            finally:
                if close_client:
                    await client.close()

    await session.flush()
    logger.debug(
        "MR upserted: project=%d iid=!%d state=%s branch_ok=%s linked=%s tests=%s",
        gitlab_project_id,
        gitlab_iid,
        mr.state,
        mr.branch_naming_ok,
        mr.has_issue_link,
        mr.has_test_changes,
    )


async def _link_issue(session: AsyncSession, mr: MergeRequest, project: GitLabProject) -> None:
    """The issue the MR closes: named in its description, or implied by the
    branch name ("issue-7-foo" -> #7)."""
    primary_iid = primary_linked_issue_iid(mr.description, mr.source_branch)
    mr.has_issue_link = bool(primary_iid)
    if primary_iid:
        mr.linked_issue_iid = primary_iid
        # Resolve to internal issue ID
        issue_stmt = select(Issue.id).where(
            Issue.project_id == project.id,
            Issue.gitlab_iid == primary_iid,
        )
        mr.linked_issue_id = (await session.execute(issue_stmt)).scalar_one_or_none()


async def _apply_course_checks(
    session: AsyncSession, mr: MergeRequest, project: GitLabProject
) -> Any:
    """Branch naming and template compliance on the course's patterns;
    returns the test-file patterns for the diff check."""
    team = (
        await session.execute(select(Team).where(Team.id == project.team_id))
    ).scalar_one_or_none()
    cs = None
    if team:
        cs_stmt = select(CourseSettings).where(CourseSettings.course_id == team.course_id)
        cs = (await session.execute(cs_stmt)).scalar_one_or_none()
    patterns = resolve_patterns(cs)
    mr.branch_naming_ok = (
        validate_branch_name(mr.source_branch or "", patterns.branch_pattern)
        if patterns.branch_pattern
        else True
    )
    compliant, _ = check_template_sections(mr.description or "", patterns.required_sections)
    mr.template_compliant = compliant
    return patterns.test_file_patterns


async def _enrich_from_api(
    session: AsyncSession,
    mr: MergeRequest,
    client: GitLabClient,
    gitlab_project_id: int,
    gitlab_iid: int,
    test_patterns: Any,
) -> None:
    """The MR's changed files, diff stats, per-file diffs and approvals."""
    changes, approvals = await asyncio.gather(
        client.get_mr_changes(gitlab_project_id, gitlab_iid),
        client.get_mr_approvals(gitlab_project_id, gitlab_iid),
    )
    if changes:
        changes_list = changes.get("changes", [])
        changed_files = [c.get("new_path", "") for c in changes_list]
        normalized_files = [path for path in changed_files if path]
        mr.changed_files = normalized_files[:200]
        mr.files_changed = len(normalized_files)
        mr.has_test_changes = count_test_files(normalized_files, test_patterns) > 0

        # Diff stats
        diff_stats = changes.get("diff_stats", {})
        mr.lines_added = diff_stats.get("additions")
        mr.lines_removed = diff_stats.get("deletions")
        if changes_list:
            await replace_mr_diffs(session, mr.id, changes_list)

    if approvals:
        _approved = approvals.get("approved_by", []) or []
        mr.approvals_count = len(_approved)
        mr.approvals_required = approvals.get("approvals_required", 0)
        mr.approved_by_gitlab_ids = [
            int(a["user"]["id"])
            for a in _approved
            if isinstance(a, dict) and isinstance(a.get("user"), dict) and a["user"].get("id")
        ]
