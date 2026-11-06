"""Full GitLab API sync for a team - backfill all issues, MRs, notes, pipelines.

After sync completes, automatically enqueues ``compute_metrics`` for the team
so that compliance scores reflect the latest data.

Idempotency
-----------
Every entity is upserted via unique business keys.  Running sync twice
produces the same DB state.  The BackgroundJob row tracks status so the
teacher can see progress.
"""

import asyncio
import logging
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.session import async_session_ctx, dispose_engine, init_engine
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team
from app.services.events import SYNC_MAX_ATTEMPTS
from app.services.gitlab.client import GitLabClient
from app.workers import sync_lifecycle as job
from app.workers.idempotency import idempotent_job
from app.workers.progress import publish_dashboard_update
from app.workers.progress import publish_progress as _publish_progress
from app.workers.project_sync import (
    SyncCounts,
    deactivate_if_gone,
    load_student_cache,
    sync_project_data,
)
from app.workers.sync_cache import _invalidate_dashboard_cache_after_sync
from app.workers.sync_common import _SESSION_WARMUP_RETRY_DELAY_S, _semester_sync_since_iso

logger = logging.getLogger(__name__)

# Per project: issues, MRs, MR notes, pipelines, commits, finalize.
_STEPS_PER_PROJECT = 6
_STAGE_DONE = {
    "issues": (1, "issues synced"),
    "merge_requests": (2, "merge requests synced"),
    "mr_notes": (3, "notes synced"),
    "pipelines": (4, "pipelines synced"),
    "commits": (5, "commits synced"),
}


@idempotent_job
def full_sync(team_id: str, job_id: str, course_id: str | None = None) -> None:
    """RQ job: sync all GitLab data for a team, then recompute metrics."""
    asyncio.run(_sync_async(team_id, job_id, course_id=course_id))


def _gitlab(**kwargs: Any) -> GitLabClient:
    settings = get_settings()
    return GitLabClient(
        base_url=str(settings.gitlab_url), private_token=settings.gitlab_api_token, **kwargs
    )


class _TeamSync:
    def __init__(self, team_id: str, job_id: str, course_id: str | None) -> None:
        self.team_id = team_id
        self.job_id = job_id
        self.team_uuid = uuid.UUID(team_id)
        self.job_uuid = uuid.UUID(job_id)
        # The caller's course id carries the early progress to the course's
        # stream; replaced by the team's own once it is loaded.
        self.course_id = course_id
        self.since: str | None = None
        self.counts = SyncCounts()
        self.t0 = time.monotonic()

    def progress(self, message: str, **extra: Any) -> None:
        _publish_progress(self.job_id, "running", message, course_id=self.course_id, extra=extra)

    async def run(self, session: AsyncSession, attempt: job.Attempt) -> None:
        self.progress("Loading team data...", progress=2)
        team = await session.get(Team, self.team_uuid)
        if not team:
            # Once more after a short delay - the pool may not be warm on the
            # very first job after engine init.
            logger.info(
                "Team %s not found on first attempt - retrying after %ss",
                self.team_id,
                _SESSION_WARMUP_RETRY_DELAY_S,
            )
            await asyncio.sleep(_SESSION_WARMUP_RETRY_DELAY_S)
            await session.invalidate()
            async with async_session_ctx() as retry_session:
                team = await retry_session.get(Team, self.team_uuid)
        if not team:
            logger.warning("Team %s not found (deleted?) - aborting sync", self.team_id)
            await job.cancel(session, self.job_uuid, "Team not found - possibly deleted")
            return
        if not team.is_active:
            logger.info("Team %s is deactivated - aborting sync", self.team_id)
            await job.cancel(session, self.job_uuid, "Team deactivated - sync skipped")
            return

        self.course_id = str(team.course_id)
        course = await session.get(Course, team.course_id)
        if course and not course.is_active:
            logger.info("Skipping sync for archived course %s (team %s)", course.id, self.team_id)
            await job.cancel(session, self.job_uuid, "Course archived - sync skipped")
            return
        # Every fetch is scoped to the semester when one is set: without it a
        # sync ingested imported template history (2021/2022 commits in a 2026
        # course), bloating storage, slowing the run and polluting the weekly
        # metrics before any view could hide it.
        self.since = _semester_sync_since_iso(course)
        if self.since is not None:
            logger.info(
                "Sync window for team %s scoped to semester start %s", self.team_id, self.since
            )

        proceed, bg_job = await job.start(
            session, self.job_uuid, self.job_id, self.course_id, attempt
        )
        if not proceed:
            return
        if bg_job:
            self.progress(
                attempt.retrying if attempt.number > 1 else "Starting sync...",
                progress=0,
                attempt=attempt.number,
                max_attempts=SYNC_MAX_ATTEMPTS,
            )

        await self._discover_projects(session)
        await self._sync_members(session)

        # Only ACTIVE projects: an inactive one was unlinked by a teacher or
        # deactivated when its repository was deleted, and syncing it would
        # flip it back on and defeat the Unlink.
        projects = [
            p
            for p in (
                await session.execute(
                    select(GitLabProject).where(
                        GitLabProject.team_id == self.team_uuid, GitLabProject.is_active.is_(True)
                    )
                )
            ).scalars()
            if p.gitlab_project_id is not None
        ]
        if not projects:
            logger.warning("Team %s has no registered projects", self.team_id)
            if bg_job:
                await job.complete(
                    session, self.job_uuid, summary="No projects to sync", duration_ms=None
                )
            return

        if not await self._sync_projects(session, projects, bg_job is not None):
            return
        await self._finish(session, len(projects))

    async def _discover_projects(self, session: AsyncSession) -> None:
        """Projects added to the group mid-semester. The sync used to process
        only the projects registered at import, silently skipping new ones."""
        try:
            team = await session.get(Team, self.team_uuid)
            if not team or not team.gitlab_group_id:
                return
            known = {
                int(gid)
                for (gid,) in (
                    await session.execute(
                        select(GitLabProject.gitlab_project_id).where(
                            GitLabProject.team_id == self.team_uuid,
                            GitLabProject.gitlab_project_id.is_not(None),
                        )
                    )
                ).all()
            }
            # One team per project: the team's "group" id is its project's id.
            if team.gitlab_group_id in known:
                return
            self.progress("Checking for new projects...", progress=3)
            async with _gitlab() as gl:
                listed = await gl.get_group_projects(
                    int(team.gitlab_group_id), include_subgroups=True, include_archived=False
                )

            from app.security.webhook_auth import (
                compute_webhook_lookup_key,
                generate_webhook_secret,
                hash_webhook_secret,
            )

            added = 0
            for data in listed:
                gid = data.get("id")
                if not gid or int(gid) in known:
                    continue
                taken = (
                    await session.execute(
                        select(GitLabProject.id)
                        .where(GitLabProject.gitlab_project_id == int(gid))
                        .limit(1)
                    )
                ).scalar_one_or_none()
                if taken is not None:
                    continue  # another team's project - not ours to take
                path = data.get("path_with_namespace") or data.get("path") or ""
                secret = generate_webhook_secret()
                session.add(
                    GitLabProject(
                        team_id=self.team_uuid,
                        gitlab_project_id=int(gid),
                        gitlab_project_path=str(path),
                        gitlab_project_name=str(
                            data.get("name") or (path.split("/")[-1] if path else "?")
                        ),
                        default_branch=str(data.get("default_branch") or "main"),
                        webhook_secret_hash=hash_webhook_secret(secret),
                        webhook_secret_lookup=compute_webhook_lookup_key(secret),
                        is_active=True,
                    )
                )
                added += 1
                known.add(int(gid))
            if added:
                await session.commit()
                logger.info("Discovered %d new project(s) for team %s", added, self.team_id)
                self.progress(f"Discovered {added} new project(s), syncing data...", progress=4)
        except Exception:
            logger.exception(
                "Project discovery failed for team %s - continuing with known projects",
                self.team_id,
            )
            await session.rollback()

    async def _sync_members(self, session: AsyncSession) -> None:
        """The group's members, so the Group Members table is filled on a
        manual sync too; then the students' e-mails, which the Members API
        hides from a non-admin token ("PRIVATE") - from User rows first, then
        the API."""
        from app.services.gitlab_import.email_enrichment import (
            _enrich_student_emails,
            _enrich_student_emails_arena,
            _enrich_student_emails_fast,
            _enrich_user_emails_arena,
            _enrich_user_emails_from_students,
        )
        from app.services.member_sync import sync_team_members

        try:
            self.progress("Syncing group members…", progress=5)
            team = (
                await session.execute(
                    select(Team)
                    .where(Team.id == self.team_uuid)
                    .options(selectinload(Team.members), selectinload(Team.projects))
                )
            ).scalar_one_or_none()
            if not team:
                return
            async with _gitlab(timeout=15, max_retries=1) as gl:
                result = await sync_team_members(session, gl, team, source="full_sync")
            await session.commit()
            logger.info(
                "Member sync for team %s: +%d -%d ~%d reactivated=%d",
                self.team_id,
                result.members_added,
                result.members_removed,
                result.roles_changed,
                result.members_reactivated,
            )
            try:
                await _enrich_user_emails_from_students(session)
                await _enrich_student_emails_fast(session)
                await _enrich_student_emails_arena(session)
                await _enrich_user_emails_arena(session)
                async with _gitlab(timeout=15, max_retries=1) as gl:
                    await _enrich_student_emails(session, gl)
                await session.commit()
            except Exception:
                logger.warning(
                    "Email enrichment failed for team %s - continuing", self.team_id, exc_info=True
                )
                await session.rollback()
        except Exception:
            logger.warning(
                "Member sync failed for team %s - continuing with data sync",
                self.team_id,
                exc_info=True,
            )
            await session.rollback()

    async def _sync_projects(
        self, session: AsyncSession, projects: list[GitLabProject], has_job: bool
    ) -> bool:
        """Every project in turn. False when the team was deactivated midway
        (the job is then cancelled)."""
        refs = [
            (
                int(p.gitlab_project_id),
                p.id,
                p.gitlab_project_name
                or (p.gitlab_project_path or "").rsplit("/", 1)[-1]
                or str(p.gitlab_project_id),
            )
            for p in projects
        ]
        students = await load_student_cache(session)
        total = len(refs)
        async with _gitlab() as gl:
            for idx, (pid, project_db_id, name) in enumerate(refs, 1):
                proj_t0 = time.monotonic()
                base = (idx - 1) * _STEPS_PER_PROJECT

                def pct(sub: int, *, _base: int = base) -> int:
                    return min(99, round((_base + sub) / (total * _STEPS_PER_PROJECT) * 100))

                self.progress(
                    f"Syncing project {idx}/{total}...",
                    synced_projects=idx - 1,
                    total_projects=total,
                    progress=pct(0),
                )
                team = await session.get(Team, self.team_uuid)
                if not team or not team.is_active:
                    logger.info("Team %s deactivated mid-sync - stopping", self.team_id)
                    if has_job:
                        await job.cancel(session, self.job_uuid, "Team deactivated during sync")
                    return False
                if await deactivate_if_gone(session, gl, pid, project_db_id, self.team_uuid):
                    continue

                # Per-stage timings, so a slow project (a fork carrying the
                # template's whole history) is pinned to its slow stage.
                stage_ms: dict[str, int] = {}
                lap = [time.monotonic()]

                def on_stage(
                    stage: str,
                    *,
                    _idx: int = idx,
                    _pct: Any = pct,
                    _ms: dict[str, int] = stage_ms,
                    _lap: list[float] = lap,
                ) -> None:
                    now = time.monotonic()
                    _ms[stage] = int((now - _lap[0]) * 1000)
                    _lap[0] = now
                    sub, what = _STAGE_DONE[stage]
                    self.progress(
                        f"Project {_idx}/{total}: {what}",
                        progress=_pct(sub),
                        synced_projects=_idx - 1,
                        total_projects=total,
                    )

                await sync_project_data(
                    session,
                    gl,
                    pid,
                    project_db_id,
                    since=self.since,
                    students=students,
                    counts=self.counts,
                    on_stage=on_stage,
                )
                logger.info(
                    "Project %d (%d/%d) synced in %dms",
                    pid,
                    idx,
                    total,
                    int((time.monotonic() - proj_t0) * 1000),
                )
                logger.info(
                    "Project %d stage timings (ms): %s",
                    pid,
                    ", ".join(f"{k}={v}" for k, v in stage_ms.items()),
                )
                self.progress(
                    f"Synced {idx}/{total} projects",
                    synced_projects=idx,
                    total_projects=total,
                    progress=pct(_STEPS_PER_PROJECT),
                    project_name=name,
                    project_done=True,
                )
        return True

    async def _finish(self, session: AsyncSession, total: int) -> None:
        summary = self.counts.summary("team metrics and cache refresh completed.")
        c = self.counts
        logger.info(
            "Sync complete for team %s: %d issues, %d MRs, %d MR notes, "
            "%d issue notes, %d pipelines in %dms",
            self.team_id,
            c.issues,
            c.mrs,
            c.mr_notes,
            c.issue_notes,
            c.pipelines,
            int((time.monotonic() - self.t0) * 1000),
        )
        done = {"synced_projects": total, "total_projects": total}
        self.progress("Computing metrics…", progress=99, **done)
        await job.compute_metrics_inline(session, self.team_id)

        state = await job.complete(
            session,
            self.job_uuid,
            summary=summary,
            duration_ms=int((time.monotonic() - self.t0) * 1000),
        )
        if state == "cancelled":
            _publish_progress(
                self.job_id,
                "cancelled",
                "Sync cancelled.",
                course_id=self.course_id,
                extra={"progress": 100},
            )
        if state != "completed":
            return
        try:
            await _invalidate_dashboard_cache_after_sync(
                session, team_id=self.team_uuid, course_id=self.course_id
            )
        except Exception:
            # A stale Last Synced after a successful sync is almost always
            # this swallowing a Redis hiccup: warned, not re-raised.
            logger.warning(
                "page_cache_invalidate_after_full_sync_failed",
                extra={"team_id": self.team_id, "course_id": self.course_id},
                exc_info=True,
            )
        _publish_progress(
            self.job_id,
            "completed",
            summary,
            course_id=self.course_id,
            extra={"progress": 100, **done},
        )
        publish_dashboard_update("team", self.team_id, "sync_completed")
        if self.course_id:
            publish_dashboard_update(
                "course", self.course_id, "sync_completed", extra={"team_id": self.team_id}
            )
        # The team's compliance snapshot, now that its data moved.
        try:
            from app.services.events import get_queue

            get_queue("low").enqueue(
                "app.workers.sweep.compliance_snapshot_for_team", self.team_id, job_timeout=300
            )
        except Exception:
            logger.debug(
                "Could not enqueue the post-sync compliance snapshot for team %s", self.team_id
            )


async def _sync_async(team_id: str, job_id: str, *, course_id: str | None = None) -> None:
    try:
        sync = _TeamSync(team_id, job_id, course_id)
    except ValueError as e:
        logger.error("Invalid UUID provided to sync job: %s", e)
        return
    attempt = job.Attempt.current()
    # Before the potentially slow engine init / DB connect, so the UI shows
    # activity at once.
    sync.progress("Initialising worker...", progress=0)
    init_engine(str(get_settings().database_url))
    try:
        async with async_session_ctx() as session:
            await sync.run(session, attempt)
    except Exception as exc:
        logger.exception("Sync failed for team %s (attempt %d)", team_id, attempt.number)
        await job.record_failure(sync.job_uuid, job_id, exc, attempt, course_id=sync.course_id)
        raise
    finally:
        await dispose_engine()
