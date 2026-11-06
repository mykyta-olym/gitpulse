"""Shared cancellation helpers for background jobs."""

import asyncio
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from uuid import UUID

import structlog
from rq.command import send_stop_job_command
from rq.exceptions import NoSuchJobError
from rq.job import Job as RQJob
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import raise_service_unavailable
from app.models.background_job import BackgroundJob
from app.models.team import Team

logger = structlog.get_logger(__name__)

ACTIVE_JOB_STATUSES: tuple[str, ...] = ("enqueued", "started", "running")
TERMINAL_JOB_STATUSES: frozenset[str] = frozenset({"completed", "failed", "cancelled", "retried"})


def is_terminal_job_status(status: str | None) -> bool:
    """Return true when a job status must never be reconciled back to active."""
    return str(status or "").lower() in TERMINAL_JOB_STATUSES


def _duration_ms(started_at: datetime | None, completed_at: datetime) -> int | None:
    if started_at is None:
        return None
    return max(0, int((completed_at - started_at).total_seconds() * 1000))


def _cancel_rq_jobs_sync(rq_ids: Sequence[str]) -> None:

    from app.redis_pool import get_redis as _pool_get_redis

    conn = _pool_get_redis()
    for rq_id in rq_ids:
        try:
            rq_job = RQJob.fetch(rq_id, connection=conn)
            rq_status = rq_job.get_status(refresh=True)
            if rq_status in {"started", "running"}:
                send_stop_job_command(conn, rq_id)
            elif rq_status in {"queued", "deferred", "scheduled"}:
                rq_job.cancel()
        except NoSuchJobError:
            logger.debug(
                "rq_job_cancel_skipped",
                rq_job_id=rq_id,
                reason="job_missing",
            )


async def cancel_background_jobs(
    db: AsyncSession,
    jobs: Iterable[BackgroundJob],
    *,
    reason: str = "Cancelled by user",
) -> int:
    """Stop RQ jobs before marking their SQL journal entries cancelled."""
    jobs = [j for j in jobs if j.status in ACTIVE_JOB_STATUSES]
    await cancel_rq_job_ids(j.rq_job_id for j in jobs if j.rq_job_id)
    now = datetime.now(UTC)
    cancelled = 0

    for job in jobs:
        job.status = "cancelled"
        job.completed_at = job.completed_at or now
        job.duration_ms = job.duration_ms or (
            _duration_ms(job.started_at, job.completed_at) if job.completed_at else None
        )
        job.error_message = reason[:500]
        job.result_summary = None
        cancelled += 1

    if cancelled:
        await db.flush()

    return cancelled


async def cancel_rq_job_ids(rq_ids: Iterable[str]) -> int:
    """Request cancellation; preserve tracking when the queue is unavailable."""
    unique_ids = sorted({str(rq_id) for rq_id in rq_ids if rq_id})
    if not unique_ids:
        return 0
    try:
        await asyncio.to_thread(_cancel_rq_jobs_sync, unique_ids)
    except Exception:
        logger.warning("rq_cancel_failed", rq_job_ids=unique_ids, exc_info=True)
        raise_service_unavailable("Job cancellation is unavailable. Refresh and try again.")
    return len(unique_ids)


async def cancel_jobs_for_course(
    db: AsyncSession,
    course_id: UUID,
    *,
    job_types: Sequence[str] | None = None,
    reason: str = "Cancelled by user",
) -> int:
    """Cancel all active course-scoped jobs, including team-scoped jobs."""
    team_ids = list(await db.scalars(select(Team.id).where(Team.course_id == course_id)))
    scope_filters = [BackgroundJob.course_id == course_id]
    if team_ids:
        scope_filters.append(BackgroundJob.team_id.in_(team_ids))

    stmt = select(BackgroundJob).where(
        BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
        or_(*scope_filters),
    )
    if job_types:
        stmt = stmt.where(BackgroundJob.job_type.in_(tuple(job_types)))

    jobs = list(await db.scalars(stmt))
    return await cancel_background_jobs(db, jobs, reason=reason)
