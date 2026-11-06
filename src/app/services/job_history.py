"""Terminal job cleanup shared by maintenance and permanent domain deletion."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import structlog
from redis.exceptions import WatchError
from rq.exceptions import NoSuchJobError
from rq.job import Job
from rq.registry import FailedJobRegistry
from rq.results import Result
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import raise_conflict, raise_service_unavailable
from app.models.background_job import BackgroundJob
from app.redis_pool import get_redis
from app.services.job_control import TERMINAL_JOB_STATUSES

logger = structlog.get_logger(__name__)
QUEUES = ("high", "default", "low")
_RQ_TERMINAL = {"finished", "failed", "canceled", "stopped"}


def _remove_rq_job(
    connection: Any,
    job_id: str,
    cutoff: datetime | None,
    registry: FailedJobRegistry | None = None,
) -> bool | None:
    """True: removed data; False: already absent; None: changed, active or too recent."""
    registries = [FailedJobRegistry(name, connection=connection) for name in QUEUES]
    result_key = Result.get_key(job_id)  # type: ignore[no-untyped-call]
    with connection.pipeline() as pipe:
        try:
            pipe.watch(Job.key_for(job_id), result_key, *(r.key for r in registries))
            if registry is not None and pipe.zscore(registry.key, job_id) is None:
                return None
            exists = bool(pipe.exists(Job.key_for(job_id), result_key)) or any(
                pipe.zscore(r.key, job_id) is not None for r in registries
            )
            try:
                job = Job.fetch(job_id, connection=connection)
            except NoSuchJobError:
                if registry is not None and cutoff is not None:
                    return None  # No activity time is known for an untracked orphan.
                pipe.multi()
            else:
                status = job.get_status(refresh=False)
                if status not in _RQ_TERMINAL:
                    return None
                if registry is not None and (status != "failed" or job.origin != registry.name):
                    return None
                activity = job.ended_at or job.last_heartbeat or job.created_at
                if cutoff is not None and activity.replace(tzinfo=UTC) >= cutoff:
                    return None
                pipe.multi()
                job.delete(pipeline=pipe, remove_from_queue=False)
            for retained_registry in registries:
                pipe.zrem(retained_registry.key, job_id)
            pipe.delete(result_key)
            pipe.execute()
            return exists
        except WatchError:
            return None  # A concurrent retry or completion wins over cleanup.


def _remove_rq_history(
    job_ids: set[str],
    cutoff: datetime | None,
    include_failures: bool,
    protected: set[str] | None = None,
) -> tuple[set[str], set[str]]:
    if not job_ids and not include_failures:
        return set(), set()
    connection = get_redis()
    deleted: set[str] = set()
    skipped: set[str] = set()
    for job_id in job_ids:
        result = _remove_rq_job(connection, job_id, cutoff)
        if result is None:
            skipped.add(job_id)
        elif result:
            deleted.add(job_id)
    if include_failures:
        for name in QUEUES:
            registry = FailedJobRegistry(name, connection=connection)
            for raw_id, _ in connection.zscan_iter(registry.key, count=100):  # type: ignore[attr-defined]
                job_id = raw_id.decode() if isinstance(raw_id, bytes) else raw_id
                if (
                    job_id not in skipped
                    and job_id not in (protected or set())
                    and _remove_rq_job(connection, job_id, cutoff, registry)
                ):
                    deleted.add(job_id)
    return deleted, skipped


async def delete_job_history(
    db: AsyncSession,
    *conditions: Any,
    cutoff: datetime | None = None,
    include_failures: bool = False,
    require_all: bool = False,
) -> dict[str, int]:
    """Remove Redis history before SQL rows; never report an active job as deleted.

    Redis and PostgreSQL cannot share a transaction. On Redis failure, SQL is
    untouched and retry is safe. SQL retains the journal if its commit fails.
    """
    jobs = list(
        (await db.scalars(select(BackgroundJob).where(*conditions).with_for_update())).all()
    )
    active = [j for j in jobs if j.status not in TERMINAL_JOB_STATUSES]
    if require_all and active:
        raise_conflict("Active jobs must finish before their history can be deleted.")
    terminal = [j for j in jobs if j.status in TERMINAL_JOB_STATUSES]
    rq_ids = {j.rq_job_id for j in terminal if j.rq_job_id}
    protected: set[str] = set()
    if include_failures:
        # SQL rows outside this cleanup's age/status filter remain authoritative.
        protected = {
            rq_id
            for rq_id in await db.scalars(
                select(BackgroundJob.rq_job_id).where(
                    BackgroundJob.rq_job_id.is_not(None),
                    BackgroundJob.id.not_in([j.id for j in terminal]),
                )
            )
            if rq_id is not None
        }
    try:
        # No thread deadline: a timed-out thread could still mutate Redis.
        removed, skipped = await asyncio.to_thread(
            _remove_rq_history, rq_ids, cutoff, include_failures, protected
        )
    except Exception:
        logger.exception("job_history_cleanup_failed")
        raise_service_unavailable("Job history cleanup is unavailable. Refresh and try again.")
    if require_all and skipped:
        raise_conflict("Some jobs are still active or changed. Refresh and try again.")
    eligible = [j for j in terminal if j.rq_job_id not in skipped]
    if eligible:
        await db.execute(
            delete(BackgroundJob).where(BackgroundJob.id.in_([j.id for j in eligible]))
        )
    return {
        "database_deleted": len(eligible),
        "redis_deleted": len(removed),
        "deleted": len(eligible) + len(removed - {j.rq_job_id for j in eligible}),
        "skipped": len(active) + len(terminal) - len(eligible),
    }
