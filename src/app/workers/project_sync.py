"""One project's GitLab data brought up to date: issues and their notes, merge
requests, MR notes, pipelines, commits.

Shared by the team sync (every project of a group, one after another) and the
project sync (the one project a teacher asked for). The project sync used to
re-implement these stages, and drifted: it re-fetched everything on every run,
and it never recovered the commits of a merged MR whose branch was deleted or
stored an MR's own commit list - so the same project read differently after a
project sync than after a team sync.

Each stage commits on its own and survives its own failure: a project whose
pipelines fail to sync still gets its commits.
"""

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit import Commit
from app.models.issue import Issue
from app.models.issue_note import IssueNote
from app.models.merge_request import MergeRequest
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.student import Student
from app.services.gitlab.client import GitLabClient
from app.utils.text_analysis import char_count, word_count
from app.utils.time_utils import parse_gitlab_datetime
from app.workers.processors.commit_processor import process_commit, sync_project_commits
from app.workers.processors.issue_processor import process_issue_event
from app.workers.processors.mr_processor import process_mr_event
from app.workers.processors.note_processor import process_note_event
from app.workers.processors.pipeline_processor import process_pipeline_event
from app.workers.processors.student_resolver import resolve_student
from app.workers.sync_common import (
    _get_pipeline_concurrency,
    deactivate_orphaned_team_members,
    deactivate_project_and_reconcile,
    fetch_gitlab_intel_snapshot,
    gitlab_repo_is_empty,
    project_has_stored_commits,
)

logger = logging.getLogger(__name__)

StudentCache = dict[int, uuid.UUID | None]

# A pipeline in one of these is finished, and a finished pipeline does not
# change - so its detail and jobs are not re-fetched on the next sync.
_TERMINAL_PIPELINE = frozenset({"success", "failed", "canceled", "cancelled", "skipped"})


@dataclass
class SyncCounts:
    """What a sync brought in, for the job's summary."""

    issues: int = 0
    mrs: int = 0
    mr_notes: int = 0
    issue_notes: int = 0
    pipelines: int = 0
    commits: int = 0

    def summary(self, nothing_found: str) -> str:
        if not any(getattr(self, f.name) for f in fields(self)):
            return f"No GitLab records found in the configured course window; {nothing_found}"
        return (
            f"Refreshed GitLab data in the configured course window: "
            f"{self.issues} issues, {self.mrs} MRs, "
            f"{self.mr_notes} MR notes, {self.issue_notes} issue notes, "
            f"{self.pipelines} pipelines, {self.commits} commits."
        )


async def load_student_cache(session: AsyncSession) -> StudentCache:
    """GitLab user id -> student, so note authors resolve without a query each."""
    rows = await session.execute(
        select(Student.gitlab_user_id, Student.id).where(Student.gitlab_user_id.is_not(None))
    )
    return {int(gid): sid for gid, sid in rows.all() if gid is not None}


async def deactivate_if_gone(
    session: AsyncSession,
    gl: GitLabClient,
    pid: int,
    project_db_id: uuid.UUID,
    team_id: uuid.UUID,
) -> str | None:
    """None when the project can be synced. Otherwise it is gone from GitLab
    and has been deactivated - with its team's members, when it was the team's
    last active project - and the text says what happened.

    A project whose repository reads empty is gone when we already hold its
    commits (the repository was deleted) or when the repository does not exist
    at all (its branches 404). A fresh project nobody has pushed to yet also
    reads empty; it stays, so the team sees it while they start.
    """
    info = await gl.get_project(pid)
    if info is None:
        logger.warning(
            "Project %d returned 404 on GitLab - deactivating project %s", pid, project_db_id
        )
        try:
            project = (
                await session.execute(
                    select(GitLabProject).where(GitLabProject.id == project_db_id)
                )
            ).scalar_one_or_none()
            if project:
                project.is_active = False
                await session.commit()
            orphaned = await deactivate_orphaned_team_members(session, team_id)
            if orphaned:
                logger.info(
                    "Deactivated %d orphaned member(s) for team %s "
                    "after project %d was deleted on GitLab",
                    orphaned,
                    team_id,
                    pid,
                )
        except Exception:
            logger.exception("Failed to deactivate deleted project %s", project_db_id)
            await session.rollback()
        return "GitLab repository not found (404) - deactivated"

    if not gitlab_repo_is_empty(info):
        return None
    had_commits = await project_has_stored_commits(session, project_db_id)
    if not had_commits and await gl.repository_exists(pid):
        return None
    reason = (
        "repository deleted (empty, had prior commits)"
        if had_commits
        else "repository does not exist in GitLab"
    )
    logger.warning(
        "Project %d repository is gone (%s) - deactivating project %s", pid, reason, project_db_id
    )
    try:
        await deactivate_project_and_reconcile(
            session,
            project_db_id=project_db_id,
            team_id=team_id,
            gitlab_pid=pid,
            reason=reason,
        )
    except Exception:
        logger.exception("Failed to deactivate empty-repo project %s", project_db_id)
        await session.rollback()
    return "GitLab repository missing - deactivated"


@dataclass
class _Run:
    """One project's sync: where it reads from and writes to, and what it has
    learnt so far."""

    session: AsyncSession
    gl: GitLabClient
    pid: int
    project_db_id: uuid.UUID
    since: str | None  # the semester's start (ISO); None syncs the whole history
    students: StudentCache
    counts: SyncCounts
    mrs: list[dict[str, Any]] = field(default_factory=list)
    # Each MR's updated_at as stored BEFORE this sync overwrote it.
    mr_updated_before: dict[int, datetime | None] = field(default_factory=dict)

    def semaphore(self) -> asyncio.Semaphore:
        return asyncio.Semaphore(_get_pipeline_concurrency())


async def _updated_before(run: _Run, model: Any) -> dict[int, datetime | None]:
    """Each stored item's updated_at, by iid. GitLab bumps updated_at on any
    new note, so an item whose updated_at did not move has no new notes and
    no new diff or approvals."""
    rows = await run.session.execute(
        select(model.gitlab_iid, model.updated_at).where(model.project_id == run.project_db_id)
    )
    return {int(iid): upd for iid, upd in rows.all() if iid is not None}


def _unchanged(before: dict[int, datetime | None], iid: int, api_updated: Any) -> bool:
    stored = before.get(iid)
    return stored is not None and stored == parse_gitlab_datetime(api_updated)


# -- Issues -------------------------------------------------------------------


async def _store_issue_notes(
    run: _Run, issue_id: uuid.UUID, api_notes: list[dict[str, Any]]
) -> None:
    note_ids = [n.get("id") for n in api_notes if n.get("id")]
    existing: dict[int, IssueNote] = {}
    if note_ids:
        rows = await run.session.execute(
            select(IssueNote).where(IssueNote.gitlab_note_id.in_(note_ids))
        )
        existing = {n.gitlab_note_id: n for n in rows.scalars() if n.gitlab_note_id is not None}
    for data in api_notes:
        note_id = data.get("id")
        if not note_id:
            continue
        note = existing.get(note_id)
        if note is None:
            note = IssueNote(issue_id=issue_id, gitlab_note_id=note_id)
            run.session.add(note)
        author = data.get("author") or {}
        author_gitlab_id = author.get("id")
        author_username = author.get("username")
        note.author_gitlab_id = author_gitlab_id
        note.author_username = author_username
        note.author_id = run.students.get(int(author_gitlab_id)) if author_gitlab_id else None
        if note.author_id is None:
            # Not in the cache: resolve, falling back to the username.
            note.author_id = await resolve_student(run.session, author_gitlab_id, author_username)
        note.body = data.get("body")
        note.word_count = word_count(note.body or "")
        note.char_count = char_count(note.body or "")
        note.is_system = bool(data.get("system", False))
        note.created_at = parse_gitlab_datetime(data.get("created_at"))
        note.updated_at = parse_gitlab_datetime(data.get("updated_at"))
        run.counts.issue_notes += 1


async def _sync_issues(run: _Run) -> None:
    """Issues, and the notes of those that are new or changed."""
    api_issues = await run.gl.get_project_issues(run.pid, updated_after=run.since)
    before = await _updated_before(run, Issue)
    for data in api_issues:
        await process_issue_event(
            run.session,
            {"object_kind": "issue", "project": {"id": run.pid}, "object_attributes": data},
            run.pid,
        )
        run.counts.issues += 1
    await run.session.flush()

    iids = [d.get("iid") for d in api_issues if d.get("iid")]
    ids: dict[int, uuid.UUID] = {}
    if iids:
        rows = await run.session.execute(
            select(Issue.gitlab_iid, Issue.id).where(
                Issue.project_id == run.project_db_id, Issue.gitlab_iid.in_(iids)
            )
        )
        ids = dict(rows.tuples().all())
    targets = [
        (int(d["iid"]), ids[d["iid"]])
        for d in api_issues
        if d.get("iid") is not None
        and d["iid"] in ids
        and not _unchanged(before, int(d["iid"]), d.get("updated_at"))
    ]
    if len(targets) < len(ids):
        logger.info(
            "Project %d: skipping notes for %d/%d unchanged issues",
            run.pid,
            len(ids) - len(targets),
            len(ids),
        )
    if targets:
        sem = run.semaphore()

        async def fetch(iid: int) -> list[dict[str, Any]]:
            async with sem:
                return await run.gl.get_issue_notes(run.pid, iid)

        results = await asyncio.gather(*[fetch(iid) for iid, _ in targets], return_exceptions=True)
        for (iid, issue_id), api_notes in zip(targets, results, strict=True):
            # One failed fetch does not discard the batch.
            if isinstance(api_notes, BaseException):
                logger.warning(
                    "Issue notes fetch failed: project=%s issue=#%s: %s", run.pid, iid, api_notes
                )
                continue
            if api_notes:
                await _store_issue_notes(run, issue_id, api_notes)
    await run.session.commit()


# -- Merge requests and their notes -------------------------------------------


async def _sync_mrs(run: _Run) -> None:
    """Merge requests. The diff and approvals of an MR whose updated_at did not
    move are immutable, so their API enrichment - the dominant cost of this
    stage on a re-sync - is skipped."""
    run.mrs = await run.gl.get_project_merge_requests(run.pid, updated_after=run.since)
    # Taken before processing: process_mr_event overwrites updated_at.
    run.mr_updated_before = await _updated_before(run, MergeRequest)
    for data in run.mrs:
        iid = data.get("iid")
        await process_mr_event(
            run.session,
            {"object_kind": "merge_request", "project": {"id": run.pid}, "object_attributes": data},
            run.pid,
            skip_api_enrichment=(
                iid is not None
                and _unchanged(run.mr_updated_before, int(iid), data.get("updated_at"))
            ),
        )
        run.counts.mrs += 1
    await run.session.commit()


async def _sync_mr_notes(run: _Run) -> None:
    """The notes of the MRs that are new or changed, fetched concurrently."""
    targets = [
        m
        for m in run.mrs
        if m.get("iid")
        and not _unchanged(run.mr_updated_before, int(m["iid"]), m.get("updated_at"))
    ]
    if len(targets) < len(run.mrs):
        logger.info(
            "Project %d: skipping notes for %d/%d unchanged MRs",
            run.pid,
            len(run.mrs) - len(targets),
            len(run.mrs),
        )
    if not targets:
        return
    sem = run.semaphore()

    async def fetch(iid: int) -> list[dict[str, Any]]:
        async with sem:
            return await run.gl.get_mr_notes(run.pid, iid) or []

    results = await asyncio.gather(*[fetch(m["iid"]) for m in targets], return_exceptions=True)
    for mr, api_notes in zip(targets, results, strict=True):
        if isinstance(api_notes, BaseException):
            logger.warning(
                "MR notes fetch failed: project=%s mr=!%s: %s", run.pid, mr.get("iid"), api_notes
            )
            continue
        for data in api_notes:
            await process_note_event(
                run.session,
                {
                    "object_kind": "note",
                    "project": {"id": run.pid},
                    "object_attributes": data,
                    "merge_request": mr,
                },
                run.pid,
            )
            run.counts.mr_notes += 1
    await run.session.commit()


# -- Pipelines ----------------------------------------------------------------


async def _fetch_pipeline(
    gl: GitLabClient, pid: int, listed: dict[str, Any], sem: asyncio.Semaphore
) -> dict[str, Any] | None:
    """A pipeline's detail and jobs, as a pipeline event."""
    async with sem:
        pl_id = listed.get("id")
        if not pl_id:
            return None
        detail, jobs = await asyncio.gather(
            gl.get_pipeline(pid, pl_id), gl.get_pipeline_jobs(pid, pl_id)
        )
        return {
            "object_kind": "pipeline",
            "project": {"id": pid},
            "object_attributes": detail or listed,
            "builds": jobs or [],
        }


async def _sync_pipelines(run: _Run) -> None:
    """Pipelines: the detail and jobs of those that are new or still running.

    A pipeline stored in a terminal status is skipped when GitLab lists it
    terminal too (a retried one reads running again and is re-fetched) - the
    stage was the single biggest cost on CI-heavy fork repos, 7-15 s per
    project. The one exception: a finished pipeline that ran tests but has no
    stored coverage. GitLab computes coverage from the job logs and can fill
    it in AFTER the terminal webhook, and rows older than the coverage column
    never had it; re-fetching those once lets the % land (coverage is sticky
    in process_pipeline_event, so a still-blank one is cheap).
    """
    listed = await run.gl.get_project_pipelines(run.pid, updated_after=run.since)
    stored = await run.session.execute(
        select(
            Pipeline.gitlab_pipeline_id, Pipeline.status, Pipeline.coverage, Pipeline.has_test_job
        ).where(Pipeline.project_id == run.project_db_id)
    )
    finished = {
        int(gid)
        for gid, status, coverage, has_test in stored.all()
        if gid is not None
        and (status or "").lower() in _TERMINAL_PIPELINE
        and not (has_test and coverage is None)
    }
    to_fetch = [
        pl
        for pl in listed
        if not (pl.get("id") in finished and (pl.get("status") or "").lower() in _TERMINAL_PIPELINE)
    ]
    if len(to_fetch) < len(listed):
        logger.info(
            "Project %d: skipping %d/%d unchanged terminal pipelines",
            run.pid,
            len(listed) - len(to_fetch),
            len(listed),
        )
    sem = run.semaphore()
    payloads = await asyncio.gather(
        *[_fetch_pipeline(run.gl, run.pid, pl, sem) for pl in to_fetch], return_exceptions=True
    )
    for payload in payloads:
        if isinstance(payload, BaseException):
            logger.warning("Pipeline fetch failed for project %s: %s", run.pid, payload)
            continue
        if payload is None:
            continue
        await process_pipeline_event(run.session, payload, run.pid)
        run.counts.pipelines += 1
    await run.session.commit()


# -- Commits ------------------------------------------------------------------


async def _limited(sem: asyncio.Semaphore, call: Awaitable[Any]) -> Any:
    async with sem:
        return await call


async def _sync_commits(run: _Run) -> None:
    """The default branch's commits, each MR's source branch's, and those of a
    merged MR whose branch was deleted - from the MR itself."""
    project = (
        await run.session.execute(
            select(GitLabProject).where(GitLabProject.id == run.project_db_id)
        )
    ).scalar_one_or_none()
    if not project:
        return
    # Scoped to the semester when one is set, so imported template history is
    # skipped at the API.
    synced = await sync_project_commits(run.session, project, run.gl, since_date=run.since)

    # Student work lives on feature branches, which the default-branch fetch
    # misses - "0 commits" beside an MR with 4 changed files. Branches go one
    # at a time: they write to the one session, which is not concurrent-safe;
    # the costly per-commit detail fetch is already deduplicated against
    # stored SHAs inside sync_project_commits.
    per_branch: dict[str, int] = {}
    for mr in run.mrs:
        branch = (mr or {}).get("source_branch")
        if not branch or branch in per_branch or branch == project.default_branch:
            continue
        try:
            per_branch[branch] = await sync_project_commits(
                run.session, project, run.gl, ref=branch, since_date=run.since
            )
            synced += per_branch[branch]
        except Exception:
            per_branch.setdefault(branch, 0)
            logger.exception("Failed syncing branch commits for project %s ref=%s", run.pid, branch)
            await run.session.rollback()

    synced += await _recover_mr_commits(run, project, per_branch)
    run.counts.commits += synced
    logger.info("Synced %d commits for project %d", synced, run.pid)
    await run.session.commit()


async def _recover_mr_commits(run: _Run, project: GitLabProject, per_branch: dict[str, int]) -> int:
    """Each MR's own commit list, stored on the MR; the commits of those not
    yet stored; and the MRs whose branch turned out deleted.

    GitLab keeps an MR's commit list after its source branch is deleted on
    merge, when the branch fetch above returns nothing. The lists are fetched
    concurrently, and only the details of commits not already stored.
    """
    stored = set(
        (await run.session.execute(select(Commit.sha).where(Commit.project_id == project.id)))
        .scalars()
        .all()
    )
    by_iid = {int(m["iid"]): m for m in run.mrs if m and m.get("iid") is not None}
    # An incremental sync may never see an unchanged historical MR again.
    # Retry missing membership lists and commit details independently of updated_at.
    for iid, branch, shas in (
        await run.session.execute(
            select(
                MergeRequest.gitlab_iid, MergeRequest.source_branch, MergeRequest.commit_shas
            ).where(MergeRequest.project_id == project.id)
        )
    ).all():
        if iid is not None and (shas is None or any(sha not in stored for sha in shas)):
            by_iid.setdefault(int(iid), {"iid": int(iid), "source_branch": branch})
    mrs = list(by_iid.values())
    sem = run.semaphore()
    lists = await asyncio.gather(
        *[_limited(sem, run.gl.get_mr_commits(run.pid, int(m["iid"]))) for m in mrs],
        return_exceptions=True,
    )

    # What GitLab says each merge request contains. The student page lists
    # these instead of the whole source branch: a branch forked from a
    # template carries the template's history, which is how one MR showed 30
    # commits (23 of them the teacher's, from years before) where GitLab
    # showed 7.
    shas_by_iid: dict[int, list[str]] = {}
    seen: set[str] = set()
    missing: list[tuple[int, str | None, str]] = []  # (iid, source branch, sha)
    for mr, listed in zip(mrs, lists, strict=True):
        if isinstance(listed, BaseException):
            logger.warning(
                "Failed fetching MR commits for project %s MR %s: %r",
                run.pid,
                mr.get("iid"),
                listed,
            )
            continue
        iid = int(mr["iid"])
        shas_by_iid[iid] = []
        for c in listed or []:
            sha = c.get("id") or c.get("sha")
            if not sha:
                continue
            # Recorded BEFORE the cross-MR dedupe below, which exists to fetch
            # a commit's detail once; applied here it would drop a shared
            # commit from the SECOND merge request's list.
            shas_by_iid.setdefault(iid, []).append(str(sha))
            if sha in seen:
                continue
            seen.add(sha)
            if sha not in stored:
                missing.append((iid, mr.get("source_branch"), sha))

    # One statement per MR, and only for the MRs fetched: one whose fetch
    # failed keeps the list it had rather than being emptied.
    if shas_by_iid:
        for iid, shas in shas_by_iid.items():
            await run.session.execute(
                update(MergeRequest)
                .where(MergeRequest.project_id == project.id, MergeRequest.gitlab_iid == iid)
                .values(commit_shas=shas)
            )
        await run.session.commit()

    recovered: dict[int, int] = {}
    if missing:
        details = await asyncio.gather(
            *[_limited(sem, run.gl.get_commit(run.pid, sha)) for _, _, sha in missing],
            return_exceptions=True,
        )
        for (iid, branch, sha), detail in zip(missing, details, strict=True):
            if isinstance(detail, BaseException):
                logger.warning(
                    "Failed fetching commit detail %s for project %s: %r", sha, run.pid, detail
                )
                continue
            if not isinstance(detail, dict) or not detail:
                continue
            try:
                # Tagged with the source branch, so the attribution query
                # (project_id, ref) finds it after the branch is gone.
                await process_commit(run.session, detail, str(project.id), branch)
                recovered[iid] = recovered.get(iid, 0) + 1
            except Exception:
                logger.exception(
                    "Failed upserting recovered commit %s for project %s MR %s",
                    sha,
                    run.pid,
                    iid,
                )
                await run.session.rollback()

    # A merged MR whose commits came only from the MR endpoint, its branch
    # fetch having found none: the branch was deleted by hand after the
    # merge (force_remove does not cover that).
    for mr in mrs:
        iid = int(mr["iid"])
        branch = mr.get("source_branch")
        if not (
            recovered.get(iid, 0) > 0
            and mr.get("state") == "merged"
            and branch
            and per_branch.get(branch, 0) == 0
        ):
            continue
        try:
            row = (
                await run.session.execute(
                    select(MergeRequest).where(
                        MergeRequest.project_id == project.id, MergeRequest.gitlab_iid == iid
                    )
                )
            ).scalar_one_or_none()
            if row and not row.source_branch_deleted:
                row.source_branch_deleted = True
        except Exception:
            logger.exception(
                "Failed marking source_branch_deleted for project %s MR %s", run.pid, iid
            )
            await run.session.rollback()
    return sum(recovered.values())


# -- Last synced --------------------------------------------------------------


async def _mark_synced(run: _Run) -> None:
    """The project's last_synced_at, and its GitLab Intelligence snapshot
    (protected branches / contributors / repo stats), so the project page's
    panels render from stored data when GitLab is later unreachable. A None
    snapshot means those calls failed; the previous one is kept."""
    try:
        project = (
            await run.session.execute(
                select(GitLabProject).where(GitLabProject.id == run.project_db_id)
            )
        ).scalar_one_or_none()
        if project:
            project.last_synced_at = datetime.now(UTC)
            try:
                intel = await fetch_gitlab_intel_snapshot(run.gl, run.pid, project.default_branch)
                if intel:
                    project.gitlab_intel = intel
            except Exception:
                logger.exception("Failed fetching gitlab_intel for project %s", run.pid)
            await run.session.commit()
    except Exception:
        logger.exception("Failed updating last_synced_at for project %s", run.pid)
        await run.session.rollback()


_STAGES: tuple[tuple[str, str, Callable[[_Run], Awaitable[None]]], ...] = (
    ("issues", "issues", _sync_issues),
    ("merge_requests", "MRs", _sync_mrs),
    ("mr_notes", "notes", _sync_mr_notes),
    ("pipelines", "pipelines", _sync_pipelines),
    ("commits", "commits", _sync_commits),
)


async def sync_project_data(
    session: AsyncSession,
    gl: GitLabClient,
    pid: int,
    project_db_id: uuid.UUID,
    *,
    since: str | None,
    students: StudentCache,
    counts: SyncCounts,
    on_stage: Callable[[str], None] = lambda stage: None,
) -> None:
    """Sync the project's issues, MRs, MR notes, pipelines and commits, then
    mark it synced. ``counts`` is added to as records come in; ``on_stage`` is
    told each stage's name as it finishes, for progress."""
    run = _Run(session, gl, pid, project_db_id, since, students, counts)
    for stage, label, sync in _STAGES:
        try:
            await sync(run)
        except Exception:
            logger.exception("Failed syncing %s for project %s", label, pid)
            await session.rollback()
        on_stage(stage)
    await _mark_synced(run)
