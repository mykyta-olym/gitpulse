"""A sync's background-job row from start to end: which attempt this run is,
cancelling, running, the metrics computed inline, completion, and failure.

Shared by the team sync and the project sync, which carried the same
bookkeeping line for line.
"""

import logging
import traceback
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.compliance.engine import backfill_compliance_history, compute_team_metrics
from app.db.session import async_session_ctx
from app.models.background_job import BackgroundJob
from app.services.events import SYNC_MAX_ATTEMPTS
from app.services.gitlab.client_types import is_gitlab_auth_error
from app.services.job_control import is_terminal_job_status
from app.workers.progress import publish_progress

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Attempt:
    """This run's attempt, from RQ's retry state, so the UI can show
    "Retrying (N/M)". get_current_job() works because a sync runs (via
    asyncio.run) in the worker thread holding the RQ job; outside a worker
    (e.g. unit tests) there is none: attempt 1, no retry."""

    rq_job: Any
    retries_left: int
    number: int

    @classmethod
    def current(cls) -> "Attempt":
        try:
            from rq import get_current_job

            rq_job = get_current_job()
        except Exception:
            rq_job = None
        left = getattr(rq_job, "retries_left", None) if rq_job is not None else None
        retries_left = left if isinstance(left, int) and left >= 0 else 0
        return cls(rq_job, retries_left, max(1, SYNC_MAX_ATTEMPTS - retries_left))

    @property
    def retrying(self) -> str:
        return f"Retrying ({self.number}/{SYNC_MAX_ATTEMPTS})…"


async def cancel(session: AsyncSession, job_uuid: uuid.UUID, reason: str) -> None:
    """End the job as cancelled, saying why - its team, project or course is
    gone or inactive."""
    bg_job = await session.get(BackgroundJob, job_uuid)
    if bg_job:
        bg_job.status = "cancelled"
        bg_job.result_summary = reason
        bg_job.completed_at = datetime.now(UTC)
        await session.commit()


async def start(
    session: AsyncSession,
    job_uuid: uuid.UUID,
    job_id: str,
    course_id: str | None,
    attempt: Attempt,
) -> tuple[bool, BackgroundJob | None]:
    """Mark the job running. False when it must not run: cancelled while it
    was queued (which is announced), or already finished."""
    bg_job = await session.get(BackgroundJob, job_uuid)
    if bg_job:
        if bg_job.status == "cancelled":
            publish_progress(
                job_id, "cancelled", "Sync cancelled.", course_id=course_id, extra={"progress": 100}
            )
            return False, bg_job
        if is_terminal_job_status(bg_job.status):
            return False, bg_job
        bg_job.status = "running"
        bg_job.started_at = datetime.now(UTC)
        if attempt.number > 1:
            # Read by the aggregate course views: the sync-status / SSE row
            # builder shows the active job's result_summary.
            bg_job.result_summary = attempt.retrying
        await session.commit()
    return True, bg_job


async def compute_metrics_inline(session: AsyncSession, team_id: str) -> bool:
    """The team's metrics, computed BEFORE the job reads completed so the page
    reload the completion triggers sees fresh snapshots; then the weekly
    history backfilled. False when the metrics failed."""
    try:
        logger.info("Computing metrics inline for team %s...", team_id)
        await compute_team_metrics(session, team_id)
        await session.commit()
        logger.info("Metrics computed for team %s", team_id)
    except Exception:
        logger.exception("Failed to compute metrics for team %s", team_id)
        await session.rollback()
        return False
    try:
        filled = await backfill_compliance_history(session, team_id)
        if filled:
            await session.commit()
            logger.info("Backfilled %d compliance week(s) for team %s", filled, team_id)
    except Exception:
        logger.warning(
            "Compliance backfill failed for team %s (metrics still saved)", team_id, exc_info=True
        )
        await session.rollback()
    return True


async def complete(
    session: AsyncSession, job_uuid: uuid.UUID, *, summary: str, duration_ms: int | None
) -> str:
    """Mark the job completed: "completed". "cancelled" when it was cancelled
    meanwhile (this run's pending writes are rolled back), "ended" when it
    ended some other way or its row is gone - both left as they are."""
    bg_job = await session.get(BackgroundJob, job_uuid)
    if not bg_job:
        return "ended"
    if bg_job.status == "cancelled":
        await session.rollback()
        return "cancelled"
    if is_terminal_job_status(bg_job.status):
        return "ended"
    bg_job.status = "completed"
    bg_job.completed_at = datetime.now(UTC)
    bg_job.duration_ms = duration_ms
    bg_job.result_summary = summary
    await session.commit()
    return "completed"


async def record_failure(
    job_uuid: uuid.UUID,
    job_id: str,
    exc: BaseException,
    attempt: Attempt,
    *,
    course_id: str | None,
) -> None:
    """The job row after the run raised.

    A GitLab 401/403 is permanent: RQ's retries are zeroed and the job fails
    at once, instead of burning every attempt on a dead token. Anything else
    keeps the row ACTIVE while RQ backs off - "Retrying (N/M)" rather than
    flapping running -> failed -> running - and fails on the last attempt.
    """
    is_auth = is_gitlab_auth_error(exc)
    retries_left = attempt.retries_left
    if is_auth and attempt.rq_job is not None:
        try:
            attempt.rq_job.retries_left = 0
        except Exception:
            logger.debug("Could not zero retries_left on RQ job", exc_info=True)
        retries_left = 0
    try:
        async with async_session_ctx() as session:
            bg_job = await session.get(BackgroundJob, job_uuid)
            if not bg_job:
                return
            if bg_job.status == "cancelled":
                publish_progress(
                    job_id,
                    "cancelled",
                    "Sync cancelled.",
                    course_id=course_id,
                    extra={"progress": 100},
                )
                return
            if is_terminal_job_status(bg_job.status):
                return
            if not is_auth and retries_left > 0:
                next_try = f"({attempt.number + 1}/{SYNC_MAX_ATTEMPTS})"
                bg_job.status = "running"
                bg_job.result_summary = f"Retrying {next_try}…"
                await session.commit()
                publish_progress(
                    job_id,
                    "running",
                    f"Retrying {next_try} after error…",
                    course_id=course_id,
                    extra={"attempt": attempt.number + 1, "max_attempts": SYNC_MAX_ATTEMPTS},
                )
                return
            bg_job.status = "failed"
            bg_job.completed_at = datetime.now(UTC)
            bg_job.error_message = (
                "GitLab API token invalid or expired (401/403) - sync "
                "blocked until a valid token is configured. Not retried."
                if is_auth
                else "".join(traceback.format_exception(exc))[-500:]
            )
            # No lingering "Retrying (...)" note from an earlier attempt.
            if bg_job.result_summary and bg_job.result_summary.startswith("Retrying"):
                bg_job.result_summary = None
            await session.commit()
            publish_progress(job_id, "failed", bg_job.error_message, course_id=course_id)
    except Exception:
        logger.exception("Failed to update job status")
