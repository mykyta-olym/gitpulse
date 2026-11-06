"""Per-project GitLab sync job: the one project a teacher asked for, through
the same per-project sync the team sync runs for every project."""

import asyncio
import logging
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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

# Progress after each stage; commits run to the metrics at 95.
_STAGE_PROGRESS = {
    "issues": (20, "issues synced"),
    "merge_requests": (40, "merge requests synced"),
    "mr_notes": (55, "notes synced"),
    "pipelines": (75, "pipelines synced"),
}


@idempotent_job
def sync_single_project(
    project_id: str,
    job_id: str,
    course_id: str | None = None,
) -> None:
    """RQ job: sync GitLab data for ONE project (not the whole team).

    Performs only the per-project work (project members, issues, MRs, MR
    notes, pipelines, commits) for the given project. Project discovery remains
    team-scoped; member reconciliation here is additive/non-destructive.
    """
    asyncio.run(_sync_single_project_async(project_id, job_id, course_id=course_id))


async def _run(
    session: AsyncSession,
    project_uuid: uuid.UUID,
    job_uuid: uuid.UUID,
    job_id: str,
    course_id: str | None,
    attempt: job.Attempt,
) -> None:
    project = await session.get(GitLabProject, project_uuid)
    if not project:
        await asyncio.sleep(_SESSION_WARMUP_RETRY_DELAY_S)
        await session.invalidate()
        async with async_session_ctx() as retry_session:
            project = await retry_session.get(GitLabProject, project_uuid)
    if not project or project.gitlab_project_id is None:
        logger.warning("Project %s not found - aborting sync", project_uuid)
        await job.cancel(session, job_uuid, "Project not found")
        return
    team = await session.get(Team, project.team_id)
    if not project.is_active:
        logger.info("Project %s is unlinked - aborting project sync", project_uuid)
        await job.cancel(session, job_uuid, "Project unlinked - sync skipped")
        return
    if team and not team.is_active:
        logger.info("Team %s deactivated - aborting project sync", project.team_id)
        await job.cancel(session, job_uuid, "Team deactivated - sync skipped")
        return

    since: str | None = None
    if team:
        course_id = course_id or str(team.course_id)
        course = await session.get(Course, team.course_id)
        if course and not course.is_active:
            logger.info(
                "Skipping project sync for archived course %s (project %s)",
                course.id,
                project_uuid,
            )
            await job.cancel(session, job_uuid, "Course archived - sync skipped")
            return
        since = _semester_sync_since_iso(course)

    proceed, _ = await job.start(session, job_uuid, job_id, course_id, attempt)
    if not proceed:
        return

    t0 = time.monotonic()
    pid = int(project.gitlab_project_id)
    project_db_id = project.id
    team_id = project.team_id
    name = (
        project.gitlab_project_name
        or (project.gitlab_project_path or "").rsplit("/", 1)[-1]
        or str(pid)
    )

    def progress(message: str, pct: int) -> None:
        _publish_progress(
            job_id,
            "running",
            message,
            course_id=course_id,
            extra={"progress": pct, "project_name": name},
        )

    def on_stage(stage: str) -> None:
        if stage in _STAGE_PROGRESS:
            pct, what = _STAGE_PROGRESS[stage]
            progress(f"{name}: {what}", pct)

    students = await load_student_cache(session)
    progress(f"Syncing project {name}...", 5)
    counts = SyncCounts()
    settings = get_settings()
    async with GitLabClient(
        base_url=str(settings.gitlab_url), private_token=settings.gitlab_api_token
    ) as gl:
        gone = await deactivate_if_gone(session, gl, pid, project_db_id, team_id)
        if gone:
            await job.complete(session, job_uuid, summary=gone, duration_ms=None)
            return

        # The project's direct members, before authors and reviewers are
        # resolved from its issues, MRs and notes. Additive only: removals
        # stay with the team/course sync, which sees the whole roster.
        if team:
            try:
                from app.services.member_sync import sync_project_members_into_team

                result = await sync_project_members_into_team(
                    session, gl, team, project, source="project_sync"
                )
                await session.commit()
                if result.total_changes:
                    logger.info(
                        "Project sync updated %d team member(s) before data sync",
                        result.total_changes,
                    )
                students = await load_student_cache(session)
            except Exception:
                logger.exception("Failed syncing project members for project %s", pid)
                await session.rollback()

        await sync_project_data(
            session,
            gl,
            pid,
            project_db_id,
            since=since,
            students=students,
            counts=counts,
            on_stage=on_stage,
        )

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    summary = counts.summary("project timestamp and metrics refresh completed.")
    logger.info("Project sync complete for %s: %s in %dms", project_uuid, summary, elapsed_ms)

    progress("Computing metrics...", 95)
    if not await job.compute_metrics_inline(session, str(team_id)):
        # The metrics job as a fallback for a transient engine failure.
        try:
            from app.services.events import get_queue

            get_queue("low").enqueue(
                "app.workers.metrics_job.compute_metrics", str(team_id), job_timeout=300
            )
        except Exception:
            logger.debug("Could not enqueue post-project-sync metrics for team %s", team_id)

    state = await job.complete(session, job_uuid, summary=summary, duration_ms=elapsed_ms)
    if state == "cancelled":
        _publish_progress(
            job_id,
            "cancelled",
            "Sync cancelled.",
            course_id=course_id,
            extra={"progress": 100, "project_name": name},
        )
    if state != "completed":
        return
    try:
        await _invalidate_dashboard_cache_after_sync(
            session, team_id=team_id, course_id=course_id, project_id=project_db_id
        )
    except Exception:
        # Warned, as in the team sync: a silently stale Last Synced is
        # almost always a swallowed Redis/SCAN error here.
        logger.warning(
            "page_cache_invalidate_after_project_sync_failed",
            extra={
                "project_id": str(project_db_id),
                "team_id": str(team_id),
                "course_id": course_id,
            },
            exc_info=True,
        )
    _publish_progress(
        job_id,
        "completed",
        summary,
        course_id=course_id,
        extra={"progress": 100, "project_name": name, "project_done": True},
    )
    publish_dashboard_update("project", str(project_db_id), "sync_completed")
    if course_id:
        publish_dashboard_update(
            "course", course_id, "sync_completed", extra={"project_id": str(project_db_id)}
        )


async def _sync_single_project_async(
    project_id: str,
    job_id: str,
    *,
    course_id: str | None = None,
) -> None:
    try:
        job_uuid = uuid.UUID(job_id)
        project_uuid = uuid.UUID(project_id)
    except ValueError as e:
        logger.error("Invalid UUID provided to project sync job: %s", e)
        return
    attempt = job.Attempt.current()
    _publish_progress(
        job_id,
        "running",
        attempt.retrying if attempt.number > 1 else "Initialising worker...",
        course_id=course_id,
        extra={"progress": 0, "attempt": attempt.number, "max_attempts": SYNC_MAX_ATTEMPTS},
    )
    init_engine(str(get_settings().database_url))
    try:
        async with async_session_ctx() as session:
            await _run(session, project_uuid, job_uuid, job_id, course_id, attempt)
    except Exception as exc:
        logger.exception("Project sync failed for %s (attempt %d)", project_id, attempt.number)
        await job.record_failure(job_uuid, job_id, exc, attempt, course_id=course_id)
        raise
    finally:
        await dispose_engine()
