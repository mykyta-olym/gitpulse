"""Shared helpers and constants for sync/run-checks endpoints.

Job-lock, active-job lookup, freshness, worker-availability and GitLab
reachability helpers extracted from sync.py so the route handlers and the
SSE stream module can share a single source of truth.
"""

import asyncio
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from rq import Worker
from rq.exceptions import NoSuchJobError
from sqlalchemy import Select, func, select

from app.config import get_settings
from app.dependencies import DbSession
from app.models.background_job import BackgroundJob
from app.redis_pool import get_redis as _pool_get_redis
from app.services.job_control import TERMINAL_JOB_STATUSES

logger = structlog.get_logger(__name__)


# Freshness window for sync: skip re-syncing a team whose last successful
# sync completed within this window (unless the caller passes ?force=true).
# Prevents thrashing the GitLab API when Sync All is pressed repeatedly or
# across multiple teachers viewing the same course.
SYNC_FRESHNESS_TTL = timedelta(minutes=5)
ACTIVE_SYNC_STATUSES = ("enqueued", "started", "running")
ACTIVE_RUN_CHECK_STATUSES = ("enqueued", "started", "running")
RUN_CHECKS_ACTIVE_WINDOW = timedelta(minutes=10)

# Statuses + window used to reconstruct "what the sync did recently" (both
# in-flight and terminal) for the /sync/active reconciler and the SSE stream.
RECENT_SYNC_JOB_STATUSES = (
    "enqueued",
    "started",
    "running",
    "failed",
    "completed",
    "cancelled",
)
RECENT_SYNC_JOBS_WINDOW = timedelta(hours=2)


def recent_sync_jobs_stmt(team_ids: Sequence[uuid.UUID]) -> Select[Any]:
    """SELECT recent sync BackgroundJobs across a set of teams (newest first).

    The /sync/active reconciler (sync.py) and the SSE sync stream
    (sync_stream.py) both rebuilt current sync state from the last 2 h of sync
    jobs with an identical query - only the columns each consumed differed. This
    is the single source of truth for that query (status list + window);
    it selects the superset of columns and callers unpack what they use.
    """
    cutoff = datetime.now(UTC) - RECENT_SYNC_JOBS_WINDOW
    return (
        select(
            BackgroundJob.team_id,
            BackgroundJob.project_id,
            BackgroundJob.status,
            BackgroundJob.completed_at,
            BackgroundJob.enqueued_at,
            BackgroundJob.result_summary,
        )
        .where(
            BackgroundJob.job_type == "sync",
            BackgroundJob.team_id.in_(team_ids),
            BackgroundJob.status.in_(RECENT_SYNC_JOB_STATUSES),
            BackgroundJob.enqueued_at >= cutoff,
        )
        .order_by(BackgroundJob.enqueued_at.desc())
    )


async def _recently_synced_team_ids(
    db: DbSession, team_ids: list[uuid.UUID], ttl: timedelta = SYNC_FRESHNESS_TTL
) -> set[uuid.UUID]:
    """Return the subset of ``team_ids`` whose latest completed sync is within ``ttl``.

    Used to short-circuit ``/sync-all`` and single-team sync calls so we do not
    hammer GitLab when data is already fresh.  Uses the last ``BackgroundJob``
    row with ``status = 'completed'`` and ``job_type = 'sync'``.
    """
    if not team_ids:
        return set()
    cutoff = datetime.now(UTC) - ttl
    stmt = (
        select(BackgroundJob.team_id, func.max(BackgroundJob.completed_at).label("last"))
        .where(
            BackgroundJob.job_type == "sync",
            BackgroundJob.project_id.is_(None),
            BackgroundJob.status == "completed",
            BackgroundJob.team_id.in_(team_ids),
            BackgroundJob.completed_at.is_not(None),
        )
        .group_by(BackgroundJob.team_id)
    )
    rows = (await db.execute(stmt)).all()
    return {tid for tid, last in rows if last is not None and last >= cutoff}


async def _reconcile_stale_jobs(db: DbSession, team_ids: list[uuid.UUID]) -> int:
    """Reconcile DB BackgroundJob records with actual RQ job status.

    Handles two categories:
    1. Jobs WITH an rq_job_id - check actual RQ status and reconcile.
    2. Orphan jobs WITHOUT an rq_job_id - these were created but never
       successfully enqueued (Redis failure, crash, etc.).  They block
       future syncs forever because the "already running" check sees them.
       Mark them failed after a short grace period.

    Returns the number of records fixed.
    """
    if not team_ids:
        return 0

    stale_stmt = (
        select(BackgroundJob)
        .where(
            BackgroundJob.job_type == "sync",
            BackgroundJob.team_id.in_(team_ids),
            BackgroundJob.status.in_(ACTIVE_SYNC_STATUSES),
        )
        .order_by(BackgroundJob.enqueued_at.desc())
    )
    result = await db.execute(stale_stmt)
    jobs = list(result.scalars().all())
    if not jobs:
        return 0

    fixed = 0
    now = datetime.now(UTC)

    # -- Phase 1: orphan jobs (no rq_job_id) --
    # These were created in the DB but never made it to Redis.
    # After 2 minutes they are certainly not going to start.
    orphan_grace = timedelta(minutes=2)
    for bg_job in jobs:
        if bg_job.rq_job_id is not None:
            continue
        age = now - bg_job.enqueued_at if bg_job.enqueued_at else timedelta(hours=1)
        if age > orphan_grace:
            bg_job.status = "failed"
            bg_job.completed_at = now
            bg_job.error_message = (
                bg_job.error_message
                or "Orphan job - never enqueued to Redis. Cleared automatically."
            )
            fixed += 1
            logger.info(
                "reconciled_orphan_job",
                job_id=str(bg_job.id),
                team_id=str(bg_job.team_id),
                age_s=int(age.total_seconds()),
            )

    # -- Phase 2: jobs with rq_job_id - check actual RQ status --
    rq_jobs = [j for j in jobs if j.rq_job_id is not None and j.status not in TERMINAL_JOB_STATUSES]
    if rq_jobs:
        try:
            get_settings()

            def _reconcile_rq_sync(rq_jobs_data: list[str]) -> list[tuple[str, Any]]:
                conn = _pool_get_redis()
                from rq.job import Job as RQJob

                # Collect live worker names once for orphan detection
                live_workers: set[str] = set()
                try:
                    from rq import Worker as RQWorker

                    for w in RQWorker.all(connection=conn):
                        live_workers.add(w.name)
                except Exception:  # noqa: S110 -- liveness check is optional; absence falls through to other heuristics.
                    pass  # if we can't list workers, skip liveness check

                results: list[tuple[str, Any]] = []
                for rq_id in rq_jobs_data:
                    try:
                        rq_job = RQJob.fetch(rq_id, connection=conn)
                        rq_status: Any = rq_job.get_status(refresh=True)
                        # If "started" but the executing worker is gone, treat as failed
                        if rq_status == "started" and live_workers:
                            origin_worker = getattr(rq_job, "worker_name", None)
                            if origin_worker and origin_worker not in live_workers:
                                rq_status = "worker_dead"
                        results.append((rq_id, rq_status))
                    except NoSuchJobError:
                        results.append((rq_id, None))
                    except Exception:
                        logger.warning("Failed to fetch RQ job %s", rq_id, exc_info=True)
                return results

            rq_ids = [j.rq_job_id for j in rq_jobs if j.rq_job_id]
            rq_results = await asyncio.to_thread(_reconcile_rq_sync, rq_ids)
            rq_status_map = dict(rq_results)

            for bg_job in rq_jobs:
                rq_id = bg_job.rq_job_id
                if rq_id is None or rq_id not in rq_status_map:
                    continue
                rq_status = rq_status_map.get(rq_id)
                if rq_status is None:
                    # RQ job gone (expired/cleaned)
                    age = now - bg_job.enqueued_at if bg_job.enqueued_at else timedelta(0)
                    if age > timedelta(minutes=3):
                        bg_job.status = "failed"
                        bg_job.completed_at = now
                        bg_job.error_message = "Job history is missing. Run the sync again."
                        fixed += 1
                    continue

                if rq_status == "finished" and bg_job.status != "completed":
                    bg_job.status = "completed"
                    bg_job.completed_at = bg_job.completed_at or now
                    bg_job.result_summary = bg_job.result_summary or "Job finished (reconciled)."
                    fixed += 1
                elif (
                    rq_status in ("canceled", "cancelled", "stopped")
                    and bg_job.status != "cancelled"
                ):
                    bg_job.status = "cancelled"
                    bg_job.completed_at = bg_job.completed_at or now
                    bg_job.error_message = bg_job.error_message or "Job cancelled."
                    fixed += 1
                elif (
                    rq_status in ("failed", "worker_dead")
                    and bg_job.status not in TERMINAL_JOB_STATUSES
                ):
                    bg_job.status = "failed"
                    bg_job.completed_at = now
                    bg_job.error_message = bg_job.error_message or (
                        "Worker died - job interrupted."
                        if rq_status == "worker_dead"
                        else "RQ job failed."
                    )
                    fixed += 1
                elif rq_status == "started" and bg_job.status == "enqueued":
                    bg_job.status = "running"
                    bg_job.started_at = bg_job.started_at or now
                    fixed += 1

        except Exception:
            logger.debug("reconcile_stale_jobs_failed", exc_info=True)

    if fixed:
        await db.flush()
        logger.info("reconciled_stale_jobs", count=fixed)

    return fixed


def _advisory_lock_key(entity_id: uuid.UUID) -> int:
    """Map a UUID into PostgreSQL's signed 32-bit advisory-lock key space."""
    return int(entity_id.int % (2**31))


async def _lock_team_job_scope(db: DbSession, team_id: uuid.UUID) -> None:
    """Serialize sync/checks enqueues for the same group."""
    await db.execute(select(func.pg_advisory_xact_lock(_advisory_lock_key(team_id))))


async def _get_active_run_checks_job(
    db: DbSession,
    team_id: uuid.UUID,
) -> BackgroundJob | None:
    cutoff = datetime.now(UTC) - RUN_CHECKS_ACTIVE_WINDOW
    stmt = (
        select(BackgroundJob)
        .where(
            BackgroundJob.team_id == team_id,
            BackgroundJob.job_type == "run_checks",
            BackgroundJob.status.in_(ACTIVE_RUN_CHECK_STATUSES),
            BackgroundJob.enqueued_at > cutoff,
        )
        .order_by(BackgroundJob.enqueued_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _get_active_sync_job(
    db: DbSession,
    team_id: uuid.UUID,
    *,
    include_project_syncs: bool = True,
) -> BackgroundJob | None:
    conditions = [
        BackgroundJob.team_id == team_id,
        BackgroundJob.job_type == "sync",
        BackgroundJob.status.in_(ACTIVE_SYNC_STATUSES),
    ]
    if not include_project_syncs:
        conditions.append(BackgroundJob.project_id.is_(None))
    stmt = (
        select(BackgroundJob).where(*conditions).order_by(BackgroundJob.enqueued_at.desc()).limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def _active_run_checks_team_ids(
    db: DbSession,
    team_ids: list[uuid.UUID],
) -> set[uuid.UUID]:
    if not team_ids:
        return set()
    cutoff = datetime.now(UTC) - RUN_CHECKS_ACTIVE_WINDOW
    rows = (
        await db.execute(
            select(BackgroundJob.team_id).where(
                BackgroundJob.team_id.in_(team_ids),
                BackgroundJob.job_type == "run_checks",
                BackgroundJob.status.in_(ACTIVE_RUN_CHECK_STATUSES),
                BackgroundJob.enqueued_at > cutoff,
            )
        )
    ).all()
    return {team_id for (team_id,) in rows if team_id is not None}


async def _active_sync_team_ids(
    db: DbSession,
    team_ids: list[uuid.UUID],
) -> set[uuid.UUID]:
    if not team_ids:
        return set()
    rows = (
        await db.execute(
            select(BackgroundJob.team_id).where(
                BackgroundJob.team_id.in_(team_ids),
                BackgroundJob.job_type == "sync",
                BackgroundJob.status.in_(ACTIVE_SYNC_STATUSES),
            )
        )
    ).all()
    return {team_id for (team_id,) in rows if team_id is not None}


def _has_active_rq_workers_sync() -> bool:
    try:
        conn = _pool_get_redis()
        workers = Worker.all(connection=conn)
        now = datetime.now(UTC)
        # RQ workers heartbeat every ~worker_ttl/2.5 ≈ 168 s (default
        # worker_ttl = 420 s).  The freshness window must exceed the
        # heartbeat interval; otherwise all workers appear "stale" in
        # between heartbeat cycles.  Use RQ's own TTL as the threshold.
        freshness_window = timedelta(seconds=420)
        for worker in workers:
            if worker.state not in {"idle", "busy"}:
                continue
            heartbeat = worker.last_heartbeat
            if heartbeat is None:
                continue
            if heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=UTC)
            if now - heartbeat <= freshness_window:
                return True
        return False
    except Exception:
        logger.exception("failed_to_check_workers")
        return False


async def _has_active_rq_workers() -> bool:
    return await asyncio.to_thread(_has_active_rq_workers_sync)


async def require_gitlab_ready() -> None:
    """Block a GitLab-dependent action unless the token is currently usable.

    Consults the shared, cached token-health flag (so a 401 seen anywhere in
    the app short-circuits every entrypoint without each re-probing GitLab) and
    raises a 503 the UI surfaces verbatim:

      - ``unauthorized`` -> explicit "token invalid" wording so the teacher
        rotates the token instead of retrying;
      - ``unreachable``  -> generic connectivity wording.

    Shared by sync, project-sync, sync-all and the GitLab import entrypoints so
    no doomed job is ever enqueued against a dead token.
    """
    from app.api.errors import raise_service_unavailable
    from app.services.gitlab import token_health as gitlab_token_health

    st = await gitlab_token_health.status()
    if st == "unauthorized":
        raise_service_unavailable(
            "GitLab API token is invalid or expired (401 Unauthorized). Sync, "
            "import and other GitLab actions are blocked until a valid token is "
            "configured. Please update the GitLab API token, then retry."
        )
    if st != "ok":
        raise_service_unavailable(
            "GitLab server is currently unreachable. GitLab actions cannot start "
            "- please retry once connectivity is restored."
        )
