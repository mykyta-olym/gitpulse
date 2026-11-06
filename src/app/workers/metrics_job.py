"""Job 4: compute_metrics - recompute compliance metrics for one team.

This is the core grading job.  It loads all team data (issues, MRs, notes,
approvals, reviews, pipelines, commits) and evaluates 13 compliance checks per
student based on the course requirements (ZSI, DevOps, etc.).  The authoritative
definitions live in ``app.compliance`` (``engine_checks`` + ``types``):

    R01  Issue Assigned      R08  Response Quality
    R02  Branch Naming       R09  Approval Received
    R03  Test Changes        R10  Merged by Author
    R04  MR-Issue Link       R11  Closure State
    R05  MR Template         R12  Pipeline Health
    R06  Review Received     R13  Commit Quality
    R07  Review Duty (given)

Idempotency
-----------
Pure function of current DB state -> MetricSnapshot.  The compliance engine
reads the latest data and writes a new snapshot row.  Re-running produces
an identical snapshot (deduplicated by ``(team_id, student_id, computed_at)``
truncated to the nearest minute via DB unique constraint).

Scheduling
----------
- Triggered after sync_job completes for a team.
- Scheduled periodically (every 30 min) for all active teams.
- Manually triggered via ``POST /api/v1/teams/{id}/sync``.
"""

import asyncio
import logging
import time
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.observability.metrics import METRICS_COMPUTE_DURATION, METRICS_COMPUTE_TOTAL
from app.workers.idempotency import idempotent_job

logger = logging.getLogger(__name__)


@idempotent_job
def compute_metrics(team_id: str) -> None:
    """RQ job: recompute all compliance metrics for a team."""
    asyncio.run(_compute_async(team_id))


@idempotent_job
def compute_metrics_selective(
    team_id: str,
    job_id: str | None = None,
    check_codes: list[str] | None = None,
) -> None:
    """RQ job: recompute metrics for selected checks (or all if *check_codes* is empty/None).

    Parameters
    ----------
    job_id:
        Optional ``BackgroundJob.id`` - used to mark the DB record as
        completed / failed when the job finishes.
    check_codes:
        Specific check codes to evaluate (e.g. ``["R01", "R03"]``).
        ``None`` or ``[]`` -> evaluate all enabled checks (ignoring weekly
        deadlines).
    """
    codes = set(check_codes) if check_codes else None
    asyncio.run(_compute_async(team_id, force_all_checks=True, job_id=job_id, check_codes=codes))


def _job_uuid(job_id: str | uuid.UUID) -> uuid.UUID:
    return uuid.UUID(job_id) if isinstance(job_id, str) else job_id


async def _close_job(
    session: Any, job_id: str | uuid.UUID, summary: str, *, duration_ms: int | None = None
) -> bool:
    """Mark the job completed with ``summary`` unless it already ended."""
    from app.models.background_job import BackgroundJob
    from app.services.job_control import is_terminal_job_status

    bg_job = await session.get(BackgroundJob, _job_uuid(job_id))
    if not bg_job or is_terminal_job_status(bg_job.status):
        return False
    bg_job.status = "completed"
    bg_job.completed_at = datetime.now(UTC)
    if duration_ms is not None:
        bg_job.duration_ms = duration_ms
    bg_job.result_summary = summary
    await session.commit()
    return True


async def _archived_reason(session: Any, team_id: str | uuid.UUID) -> str | None:
    """Why the metrics of this group are not computed: it or its course is archived."""
    from app.models.course import Course
    from app.models.team import Team

    team = await session.get(Team, _job_uuid(team_id))
    if not team:
        return None
    if not team.is_active:
        return "group"
    course = await session.get(Course, team.course_id)
    if course and not course.is_active:
        return "course"
    return None


async def _announce_metrics(session: Any, team_id: str, job_id: str | None) -> None:
    """Drop the group's cached pages and tell the analytics and dashboard
    streams - optional: the metrics are already written."""
    try:
        from app.models.team import Team as _Team

        _tid = _job_uuid(team_id)
        _team = await session.get(_Team, _tid)
        if not (_team and _team.course_id):
            return
        # Page-fragment cache invalidation: drop the cached team / course /
        # analytics / per-student HTML so the next dashboard request renders
        # the freshly computed metrics instead of serving 60 s-old data.
        try:
            from app.models.team_member import TeamMember
            from app.services.page_cache import invalidate_cascade

            _mem_stmt = select(TeamMember.student_id).where(
                TeamMember.team_id == _tid,
                TeamMember.left_at.is_(None),
            )
            _student_ids = [
                sid for (sid,) in (await session.execute(_mem_stmt)).all() if sid is not None
            ]
            invalidate_cascade(team_id=_tid, course_id=_team.course_id, student_ids=_student_ids)
        except Exception:  # noqa: S110 -- best-effort cache purge; TTL self-heals.
            pass

        # Notify analytics + dashboard SSE streams after cache invalidation
        # so receivers reload fresh SSR snapshots.
        from app.workers.progress import publish_dashboard_update
        from app.workers.progress import publish_progress as _pub

        _pub(
            job_id or f"metrics-{team_id}",
            "updated",
            "Compliance metrics updated",
            analytics_course_id=str(_team.course_id),
            extra={"team_id": str(team_id), "event": "metrics_updated"},
        )
        publish_dashboard_update("team", str(team_id), "metrics_computed")
        publish_dashboard_update(
            "course",
            str(_team.course_id),
            "metrics_computed",
            extra={"team_id": str(team_id)},
        )
    except Exception:  # noqa: S110 -- analytics SSE broadcast is optional; metric write already succeeded.
        pass  # analytics SSE is optional


async def _fail_job(job_id: str, exc: Exception, t0: float) -> None:
    """Mark the job failed in the DB and on the progress channel, so the SSE
    polling and the live stream both see it."""
    from app.db.session import async_session_ctx
    from app.services.job_control import is_terminal_job_status

    try:
        async with async_session_ctx() as err_session:
            from app.models.background_job import BackgroundJob as BgJob

            err_job = await err_session.get(BgJob, _job_uuid(job_id))
            if err_job and not is_terminal_job_status(err_job.status):
                err_job.status = "failed"
                err_job.completed_at = datetime.now(UTC)
                err_job.duration_ms = int((time.monotonic() - t0) * 1000)
                err_job.error_message = str(exc)[:2000]
                await err_session.commit()
    except Exception:
        logger.debug("Failed to mark BackgroundJob %s as failed in DB", job_id)
    try:
        from app.workers.progress import publish_progress as _pp

        _pp(job_id, "failed", str(exc), extra={"error_message": str(exc)})
    except Exception:  # noqa: S110 -- SSE progress publish is best-effort inside the error path.
        pass  # SSE progress is best-effort - never break the error path


def _summary(check_codes: set[str] | None, force_all_checks: bool) -> str:
    if check_codes:
        return f"Selected checks completed ({', '.join(sorted(check_codes))})."
    if force_all_checks:
        return "All checks evaluated (weekly deadlines bypassed)."
    return "Metrics recomputed."


async def _compute_async(
    team_id: str,
    *,
    force_all_checks: bool = False,
    job_id: str | None = None,
    student_ids: set[str] | None = None,
    check_codes: set[str] | None = None,
) -> None:
    from app.compliance.engine import compute_team_metrics
    from app.config import get_settings
    from app.db.session import async_session_ctx, dispose_engine, init_engine
    from app.observability.tracing import get_tracer
    from app.services.job_control import is_terminal_job_status
    from app.workers.progress import publish_progress

    settings = get_settings()
    init_engine(str(settings.database_url))

    tracer = get_tracer()
    span_ctx = None
    if tracer:
        span_ctx = tracer.start_as_current_span(
            "compute_metrics", attributes={"app.team_id": team_id}
        )
        span_ctx.__enter__()

    # Convert string UUIDs to proper UUID objects for the engine
    student_uuid_set: set[uuid.UUID] | None = None
    if student_ids:
        student_uuid_set = {uuid.UUID(sid) if isinstance(sid, str) else sid for sid in student_ids}

    t0 = time.monotonic()
    try:
        if job_id:
            publish_progress(
                job_id,
                "running",
                "Starting checks evaluation…",
                extra={"progress": 0},
            )

        async with async_session_ctx() as session:
            if job_id:
                from app.models.background_job import BackgroundJob

                bg_job = await session.get(BackgroundJob, _job_uuid(job_id))
                if bg_job and bg_job.status == "cancelled":
                    publish_progress(
                        job_id,
                        "cancelled",
                        "Checks cancelled.",
                        extra={"progress": 100},
                    )
                    return
                if bg_job and not is_terminal_job_status(bg_job.status):
                    bg_job.status = "running"
                    bg_job.started_at = datetime.now(UTC)
                    await session.commit()

            archived = await _archived_reason(session, team_id)
            if archived:
                logger.info(
                    "Skipping metrics computation for archived %s (team=%s)",
                    archived,
                    team_id,
                )
                if job_id:
                    summary = f"Skipped - {archived} is archived"
                    publish_progress(job_id, "completed", summary)
                    await _close_job(session, job_id, summary)
                return

            if job_id:
                codes_label = ", ".join(sorted(check_codes)) if check_codes else "all"
                publish_progress(
                    job_id,
                    "running",
                    f"Evaluating checks ({codes_label})…",
                    extra={"progress": 20},
                )

            await compute_team_metrics(
                session,
                team_id,
                force_all_checks=force_all_checks,
                student_ids=student_uuid_set,
                check_codes=check_codes,
            )
            if job_id:
                bg_job = await session.get(BackgroundJob, _job_uuid(job_id))
                if bg_job and bg_job.status == "cancelled":
                    await session.rollback()
                    publish_progress(
                        job_id,
                        "cancelled",
                        "Checks cancelled.",
                        extra={"progress": 100},
                    )
                    return
            await session.commit()
            await _announce_metrics(session, team_id, job_id)

            if job_id:
                publish_progress(job_id, "running", "Saving results...", extra={"progress": 90})
                summary = _summary(check_codes, force_all_checks)
                duration = int((time.monotonic() - t0) * 1000)
                if await _close_job(session, job_id, summary, duration_ms=duration):
                    publish_progress(
                        job_id,
                        "completed",
                        summary,
                        extra={"result_summary": summary, "progress": 100},
                    )

            METRICS_COMPUTE_DURATION.observe(time.monotonic() - t0)
            METRICS_COMPUTE_TOTAL.labels(status="ok").inc()
            label = " (force_all_checks)" if force_all_checks else ""
            logger.info("Metrics recomputed for team %s%s", team_id, label)
    except Exception as exc:
        logger.exception("Failed to compute metrics for team %s: %s", team_id, exc)
        METRICS_COMPUTE_TOTAL.labels(status="error").inc()
        if job_id:
            await _fail_job(job_id, exc, t0)
        raise
    finally:
        if span_ctx:
            with suppress(Exception):
                span_ctx.__exit__(None, None, None)
        await dispose_engine()
