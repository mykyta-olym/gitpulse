"""Process git commits - store and link to students."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.commit import Commit
from app.models.project import GitLabProject
from app.models.student import Student
from app.utils.time_utils import parse_gitlab_datetime

logger = logging.getLogger(__name__)


async def process_commit(
    session: AsyncSession,
    commit_data: dict[str, Any],
    project_id_uuid: str,
    ref: str | None = None,
) -> Commit | None:
    """Process a single commit and store it.

    Args:
        session: Database session
        commit_data: Commit data from GitLab API or webhook
        project_id_uuid: UUID of the GitLabProject
        ref: Branch/ref name if known

    Returns:
        The created or updated Commit, or None on error
    """
    sha = commit_data.get("id") or commit_data.get("sha")
    if not sha:
        logger.warning("Commit missing sha/id: %s", commit_data)
        return None

    # Extract commit info
    title = commit_data.get("title") or ""
    message = commit_data.get("message") or title

    # Parse title from message if not provided
    if not title and message:
        title = message.split("\n")[0][:500]

    # Author info
    author_name = commit_data.get("author_name")
    author_email = commit_data.get("author_email")

    # GitLab API sometimes provides author as nested object
    if not author_name and "author" in commit_data:
        author = commit_data["author"]
        if isinstance(author, dict):
            author_name = author.get("name")
            author_email = author.get("email")

    # Stats. GitLab's commit `stats` payload exposes additions / deletions
    # and `total` (= additions + deletions LINES). It does NOT include the
    # number of files touched - that requires a separate /diff call which
    # would be too expensive per-commit during a sweep. Leave
    # `files_changed` at 0 (unknown) rather than misreporting line totals
    # as a file count.
    stats = commit_data.get("stats", {})
    additions = stats.get("additions", 0) if stats else 0
    deletions = stats.get("deletions", 0) if stats else 0
    files_changed = 0

    # Parent SHAs
    parent_ids = commit_data.get("parent_ids", [])

    # Timestamp. Route through the shared parse_gitlab_datetime so commit
    # timestamps are always tz-aware (naive -> UTC), consistent with every
    # other entity and with the tz-aware committed_at column / the compliance
    # engine's tz-aware semester-window comparison. Using datetime.fromisoformat
    # directly here left offset-less timestamps naive.
    committed_at = None
    ts_val = (
        commit_data.get("committed_date")
        or commit_data.get("created_at")
        or commit_data.get("timestamp")
    )
    if isinstance(ts_val, datetime):
        committed_at = ts_val if ts_val.tzinfo else ts_val.replace(tzinfo=UTC)
    elif ts_val:
        committed_at = parse_gitlab_datetime(str(ts_val))

    # Try to match author to student
    author_id = None
    author_gitlab_id = None
    if author_email or author_name:
        author_id, author_gitlab_id = await _match_author_to_student(
            session, project_id_uuid, author_email, author_name
        )

    # Upsert commit
    stmt = (
        insert(Commit)
        .values(
            project_id=project_id_uuid,
            sha=sha,
            short_sha=sha[:8],
            author_name=author_name,
            author_email=author_email,
            author_gitlab_id=author_gitlab_id,
            author_id=author_id,
            title=title[:500] if title else None,
            message=message,
            files_changed=files_changed,
            additions=additions,
            deletions=deletions,
            parent_shas=parent_ids,
            ref=ref,
            committed_at=committed_at,
        )
        .on_conflict_do_update(
            index_elements=["project_id", "sha"],
            set_={
                "author_name": author_name,
                "author_email": author_email,
                "author_gitlab_id": author_gitlab_id,
                "author_id": author_id,
                "title": title[:500] if title else None,
                "message": message,
                "files_changed": files_changed,
                "additions": additions,
                "deletions": deletions,
                "parent_shas": parent_ids,
                "ref": ref,
                "committed_at": committed_at,
            },
        )
        .returning(Commit)
    )

    result = await session.execute(stmt)
    commit = result.scalar_one_or_none()

    if commit:
        logger.debug(
            "Processed commit %s by %s (%s) in project %s",
            sha[:8],
            author_name,
            author_email,
            project_id_uuid,
        )

    return commit


async def _match_author_to_student(
    session: AsyncSession,
    project_id_uuid: str,
    email: str | None,
    name: str | None,
) -> tuple[str | None, int | None]:
    """Try to match commit author to a student.

    Matching strategy:
    1. Match by email (exact, case-insensitive)
    2. Match by GitLab username in email (user@gitlab.com patterns)
    3. Match by name similarity (last resort)

    Returns:
        Tuple of (student_id UUID string, gitlab_user_id) or (None, None)
    """

    from app.models.team_member import TeamMember

    # Get project's team to limit student search
    project_stmt = select(GitLabProject.team_id).where(GitLabProject.id == project_id_uuid)
    result = await session.execute(project_stmt)
    team_id = result.scalar_one_or_none()

    if not team_id:
        return None, None

    # Base query for students in this team (join through TeamMember)
    team_student_ids = select(TeamMember.student_id).where(TeamMember.team_id == team_id)
    base_stmt = select(Student).where(Student.id.in_(team_student_ids))

    # Strategy 1: Match by email
    if email:
        email_lower = email.lower()
        stmt = base_stmt.where(func.lower(Student.email) == email_lower)
        result = await session.execute(stmt)
        matched_student = cast("Student | None", result.scalars().first())
        if matched_student:
            return str(matched_student.id), matched_student.gitlab_user_id

    # Strategy 2: Match by gitlab_username
    # GitLab noreply emails come in two formats:
    #   username@users.noreply.gitlab.com
    #   12345678+username@users.noreply.gitlab.com  (with numeric prefix)
    # Strip the leading "<digits>+" prefix so both formats resolve correctly.
    if email:
        local_part = email.split("@")[0].lower()
        if "+" in local_part:
            local_part = local_part.split("+", 1)[-1]
        potential_username = local_part
        stmt = base_stmt.where(func.lower(Student.gitlab_username) == potential_username)
        result = await session.execute(stmt)
        matched_student = cast("Student | None", result.scalars().first())
        if matched_student:
            return str(matched_student.id), matched_student.gitlab_user_id

    # Strategy 3: Match by name (fuzzy - be careful)
    # Only do exact name match to avoid false positives
    if name:
        stmt = base_stmt.where(func.lower(Student.full_name) == name.lower())
        result = await session.execute(stmt)
        matched_student = cast("Student | None", result.scalars().first())
        if matched_student:
            return str(matched_student.id), matched_student.gitlab_user_id

    return None, None


async def sync_project_commits(
    session: AsyncSession,
    project: GitLabProject,
    gitlab_client: Any,
    since_date: str | None = None,
    ref: str | None = None,
) -> int:
    """Sync all commits for a project from GitLab.

    Args:
        session: Database session
        project: GitLabProject model instance
        gitlab_client: GitLab API client
        since_date: ISO 8601 date to fetch commits from (optional)
        ref: Branch name (optional, defaults to default branch)

    Returns:
        Number of commits synced
    """
    logger.info(
        "Syncing commits for project %s (gitlab_id=%d) since=%s ref=%s",
        project.gitlab_project_path,
        project.gitlab_project_id,
        since_date,
        ref,
    )

    # Fetch commits from GitLab
    commits = await gitlab_client.get_commits(
        project_id=project.gitlab_project_id,
        ref_name=ref or project.default_branch,
        since=since_date,
        per_page=100,
        all_pages=True,
    )

    if not commits:
        logger.info("No commits found for project %d", project.gitlab_project_id)
        return 0

    logger.info("Fetched %d commits from GitLab", len(commits))

    # Skip detail-fetch for commits we already have in DB - this is the
    # single biggest incremental-sync win. The GitLab list endpoint returns
    # title/author/timestamp; only the /commits/:sha endpoint returns
    # additions/deletions stats. For commits already stored we already
    # have those stats from the previous sync, so re-fetching them is
    # pure waste (and the dominant source of GitLab API timeouts during
    # large sweeps).
    shas = [c.get("id") for c in commits if c.get("id")]
    existing_shas: set[str] = set()
    if shas:
        existing_stmt = select(Commit.sha).where(
            Commit.project_id == project.id,
            Commit.sha.in_(shas),
        )
        existing_res = await session.execute(existing_stmt)
        existing_shas = {row[0] for row in existing_res.all()}

    new_shas = [s for s in shas if s not in existing_shas]
    if existing_shas:
        logger.info(
            "Skipping %d commits already in DB; fetching %d new",
            len(existing_shas),
            len(new_shas),
        )

    if not new_shas:
        return 0

    # Fetch detailed stats concurrently (semaphore limits parallel API calls)
    concurrency = get_settings().sync_pipeline_concurrency or 5
    sem = asyncio.Semaphore(concurrency)

    async def _fetch_detail(sha: str) -> dict[str, Any] | None:
        async with sem:
            return cast(
                "dict[str, Any] | None",
                await gitlab_client.get_commit(project.gitlab_project_id, sha),
            )

    detailed_list = await asyncio.gather(
        *[_fetch_detail(s) for s in new_shas], return_exceptions=True
    )

    total_processed = 0
    for commit_detailed in detailed_list:
        if isinstance(commit_detailed, BaseException):
            logger.warning(
                "Commit detail fetch failed for project %s: %s",
                project.gitlab_project_path,
                commit_detailed,
            )
            continue
        if not commit_detailed:
            continue
        commit_obj = await process_commit(
            session, commit_detailed, str(project.id), ref or project.default_branch
        )
        if commit_obj:
            total_processed += 1

    await session.commit()
    logger.info("Synced %d commits for project %s", total_processed, project.gitlab_project_path)
    return total_processed
