"""Server-Sent Events endpoint for real-time job progress tracking.

Allows the frontend to subscribe to job status updates via SSE,
so long-running processes (sync, report generation, LLM analysis)
continue to push progress even if the user navigates between pages.

Cross-process communication:
    Workers publish progress to Redis pub/sub channel ``job_progress:{job_id}``.
    This SSE endpoint subscribes to that channel and bridges updates to clients.
    Falls back to periodic DB polling if Redis pub/sub is unavailable.

Usage (frontend):
    const es = new EventSource('/api/v1/jobs/{job_id}/stream');
    es.onmessage = (e) => {
        const data = JSON.parse(e.data);
        // data.status, data.result_summary, ...
    };
    es.addEventListener('complete', (e) => es.close());
    es.addEventListener('error', (e) => es.close());
"""

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Request
from fastapi.responses import StreamingResponse
from rq.job import Job as RqJob
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import raise_forbidden, raise_not_found
from app.db.session import async_session_ctx
from app.dependencies import (
    ApiAuth,
    ApiTeacherAuth,
    DbSession,
    _extract_bearer_token,
    _validate_session,
)
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team
from app.schemas.jobs import JobCancelRequest, JobCancelResponse, JobPollingStatus
from app.services.job_control import (
    ACTIVE_JOB_STATUSES,
    TERMINAL_JOB_STATUSES,
    cancel_background_jobs,
    cancel_jobs_for_course,
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def _load_sse_user(
    request: Request,
    db: AsyncSession,
) -> Any:
    """Resolve the current User from the session cookie.

    SSE endpoints use ``ApiTeacherAuth`` which validates the session but
    only returns the auth method string.  This helper re-reads the session
    to extract the username and loads the corresponding ``User`` row.

    Returns ``None`` when the user cannot be resolved (bearer-only auth
    without a session, user deleted, etc.).
    """
    from app.config import get_settings
    from app.models.user import User
    from app.security.session_auth import get_current_session

    settings = get_settings()
    session_data = get_current_session(
        request,
        settings.secret_key,
        max_age=settings.session_max_age_seconds,
        app_base_url=settings.app_base_url,
        session_absolute_max_age=settings.session_absolute_max_age_seconds,
    )
    if not session_data:
        return None
    username = session_data.get("user")
    if not username:
        return None
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


def _fetch_rq_status_sync(rq_id: str) -> Any:
    """Fetch the current RQ job status (runs in thread)."""

    from app.redis_pool import get_redis as _pool_get_redis

    conn = _pool_get_redis()
    rq_job = RqJob.fetch(rq_id, connection=conn)
    return rq_job.get_status(refresh=True)


async def _reconcile_rq_status(job: BackgroundJob, db: Any) -> None:
    """Reconcile BackgroundJob DB status with actual RQ job status.

    Used by both the polling endpoint and SSE heartbeat to detect
    completion for jobs whose workers don't update the DB record.
    """
    if not job.rq_job_id or job.status in TERMINAL_JOB_STATUSES:
        return
    try:
        rq_status = await asyncio.to_thread(_fetch_rq_status_sync, job.rq_job_id)
        now = datetime.now(UTC)

        if rq_status == "started" and job.status == "enqueued":
            job.status = "running"
            if job.started_at is None:
                job.started_at = now
            await db.flush()
        elif rq_status in {"canceled", "cancelled"} and job.status != "cancelled":
            job.status = "cancelled"
            job.completed_at = now
            if not job.error_message:
                job.error_message = "Job cancelled."
            await db.flush()
        elif rq_status == "failed" and job.status not in TERMINAL_JOB_STATUSES:
            job.status = "failed"
            job.completed_at = now
            if not job.error_message:
                job.error_message = "RQ job failed before completion."
            await db.flush()
        elif rq_status == "finished" and job.status not in TERMINAL_JOB_STATUSES:
            job.status = "completed"
            if job.started_at is None:
                job.started_at = now
            if job.completed_at is None:
                job.completed_at = now
            if not job.result_summary:
                job.result_summary = "Job finished."
            await db.flush()
    except Exception:
        logger.debug("job_status_reconcile_skipped job_id=%s", str(job.id), exc_info=True)


async def _can_view_job(request: Request, job: BackgroundJob, db: AsyncSession) -> bool:
    """Authorize a reader for a job's status / progress.

    ``ApiAuth`` only *authenticates*; without this, any logged-in user could
    poll or stream ANY job by its (random UUID) id and read another course's
    process status and error messages. Rules:

      * Bearer-token client -> privileged API (shared teacher token, or a
        per-user token already role-checked at auth) -> allowed.
      * Session admin -> allowed (manages every process).
      * Session non-admin -> only jobs belonging to a course they can view.
      * Jobs with no resolvable course -> admin / token only.
    """
    if _extract_bearer_token(request) is not None:
        return True

    from app.config import get_settings

    session_data = _validate_session(request, get_settings())
    if not session_data:
        return False
    if session_data.get("role") == "admin":
        return True

    course_id = job.course_id
    if course_id is None and job.team_id is not None:
        team = await db.get(Team, job.team_id)
        course_id = team.course_id if team else None
    if course_id is None and job.project_id is not None:
        project = await db.get(GitLabProject, job.project_id)
        if project is not None:
            team = await db.get(Team, project.team_id)
            course_id = team.course_id if team else None
    if course_id is None:
        return False

    from app.api.dashboard._access import _can_view_course

    course = await db.get(Course, course_id)
    return bool(course and await _can_view_course(course, session_data, db))


async def _can_manage_job(request: Request, job: BackgroundJob, db: AsyncSession) -> bool:
    """Authorize cancellation for a background job."""
    if _extract_bearer_token(request) is not None:
        return True

    from app.config import get_settings

    session_data = _validate_session(request, get_settings())
    if not session_data:
        return False
    if session_data.get("role") == "admin":
        return True

    from app.api.dashboard._access import can_manage_via_request

    if job.course_id is not None:
        course = await db.get(Course, job.course_id)
        return bool(course and await can_manage_via_request(request, db, course=course))
    if job.team_id is not None:
        team = await db.get(Team, job.team_id)
        return bool(team and await can_manage_via_request(request, db, team=team))
    if job.project_id is not None:
        project = await db.get(GitLabProject, job.project_id)
        return bool(project and await can_manage_via_request(request, db, project=project))
    return False


async def _can_view_dashboard_stream(
    request: Request,
    db: AsyncSession,
    *,
    team_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
) -> bool:
    """Authorize a real-time dashboard stream subscriber (same model as
    ``_can_view_job``). Without this, any logged-in user could subscribe to ANY
    team's / course's ``dashboard:*`` channel and watch another group's activity
    notifications in real time. Bearer-token clients and admins are allowed;
    a session user must be able to view the team (or course) being subscribed to.
    """
    if _extract_bearer_token(request) is not None:
        return True

    from app.config import get_settings

    session_data = _validate_session(request, get_settings())
    if not session_data:
        return False
    if session_data.get("role") == "admin":
        return True

    from app.api.dashboard._access import _can_view_course, _can_view_team

    if team_id is not None:
        team = await db.get(Team, team_id)
        return bool(team and await _can_view_team(team, session_data, db))
    if course_id is not None:
        course = await db.get(Course, course_id)
        return bool(course and await _can_view_course(course, session_data, db))
    return False


@router.get("/jobs/{job_id}", name="get_job_status_sse", response_model=JobPollingStatus)
async def get_job_status(
    job_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiAuth,
) -> JobPollingStatus:
    """Get current job status (used by polling fallback when SSE unavailable).

    Reconciles DB status with actual RQ job status when the job has
    an associated rq_job_id, so stale 'enqueued' states are corrected.
    """
    job = await db.get(BackgroundJob, job_id)
    if not job:
        raise_not_found("Job not found")
    if not await _can_view_job(request, job, db):
        # 404, not 403 - never confirm a foreign job's existence.
        raise_not_found("Job not found")

    # Reconcile DB status with actual RQ job status when possible.
    await _reconcile_rq_status(job, db)

    return JobPollingStatus(
        job_id=job_id,
        status=job.status,
        job_type=job.job_type,
        result_summary=job.result_summary,
        error_message=job.error_message,
        enqueued_at=job.enqueued_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_job(
    job_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
    payload: JobCancelRequest | None = Body(default=None),
) -> JobCancelResponse:
    """Cancel one active background job."""
    job = await db.get(BackgroundJob, job_id)
    if not job:
        raise_not_found("Job not found")
    if not await _can_manage_job(request, job, db):
        raise_not_found("Job not found")

    if job.status not in ACTIVE_JOB_STATUSES:
        return JobCancelResponse(
            job_id=job.id,
            status=job.status,
            cancelled=0,
            message="Job already finished.",
        )

    reason = (payload.reason if payload else "Cancelled by user").strip() or "Cancelled by user"
    cancelled = await cancel_background_jobs(db, [job], reason=reason)
    await db.commit()
    return JobCancelResponse(
        job_id=job.id,
        status=job.status,
        cancelled=cancelled,
        message="Process cancelled." if cancelled else "Job already finished.",
    )


@router.post("/courses/{course_id}/jobs/cancel", response_model=JobCancelResponse)
async def cancel_course_jobs(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
    payload: JobCancelRequest | None = Body(default=None),
) -> JobCancelResponse:
    """Cancel active course-scoped jobs, optionally filtered by job type."""
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")

    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, course=course):
        raise_forbidden("Not allowed to cancel jobs for this course")

    request_payload = payload or JobCancelRequest()
    reason = request_payload.reason.strip() or "Cancelled by user"
    job_types = request_payload.job_types or None
    cancelled = await cancel_jobs_for_course(db, course_id, job_types=job_types, reason=reason)
    await db.commit()

    return JobCancelResponse(
        job_id=None,
        status="cancelled" if cancelled else "idle",
        cancelled=cancelled,
        message=(
            f"Cancelled {cancelled} process{'es' if cancelled != 1 else ''}."
            if cancelled
            else "No active process to cancel."
        ),
    )


@router.get("/jobs/{job_id}/stream", name="stream_job_progress_sse")
async def stream_job_progress(
    job_id: uuid.UUID,
    request: Request,
    _auth: ApiAuth,
) -> StreamingResponse:
    """Stream job progress via Server-Sent Events.

    The stream emits:
      - ``data`` events with JSON payload containing job status
      - ``complete`` event when the job finishes (success or failure)
      - Heartbeat comments every 15s to keep the connection alive

    The client should close the EventSource on ``complete`` or ``error``.

    Note: avoids ``db: DbSession`` to prevent connection-pool leaks
    when Starlette's middleware cancel scope terminates the DI session
    during streaming.
    """
    async with async_session_ctx() as _init_session:
        job = await _init_session.get(BackgroundJob, job_id)
        if not job:
            raise_not_found("Job not found")
        if not await _can_view_job(request, job, _init_session):
            # 404, not 403 - never confirm a foreign job's existence.
            raise_not_found("Job not found")

        # Capture initial state before the session closes
        initial_status = job.status
        initial_data: dict[str, object] = {
            "job_id": str(job_id),
            "status": job.status,
            "job_type": job.job_type,
            "result_summary": job.result_summary,
            "error_message": job.error_message,
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    job_id_str = str(job_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        from app.config import get_settings

        settings = get_settings()
        redis_listener: asyncio.Task[None] | None = None
        update_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=100)

        # Start Redis pub/sub listener in background
        try:
            redis_listener = asyncio.create_task(_redis_pubsub_listener(job_id_str, update_queue))
        except Exception:
            logger.warning("Redis pub/sub listener not available for SSE", exc_info=True)

        try:
            # Send initial state
            yield _format_sse(initial_data)

            # If already completed, send complete event and close
            if initial_status in TERMINAL_JOB_STATUSES:
                final_payload: dict[str, object] = {"status": initial_status}
                if initial_data.get("error_message"):
                    final_payload["error_message"] = initial_data["error_message"]
                if initial_data.get("result_summary"):
                    final_payload["result_summary"] = initial_data["result_summary"]
                yield _format_sse_event("complete", final_payload)
                return

            # Poll for updates via Redis pub/sub queue + DB fallback
            poll_interval = settings.sse_poll_interval_seconds
            heartbeat_interval = settings.sse_heartbeat_interval_seconds
            heartbeat_counter = 0

            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Drain all pending Redis pub/sub messages
                while not update_queue.empty():
                    try:
                        data = update_queue.get_nowait()
                        yield _format_sse(data)
                        status_val = data.get("status", "")
                        if status_val in TERMINAL_JOB_STATUSES:
                            complete_payload: dict[str, object] = {"status": status_val}
                            if data.get("result_summary"):
                                complete_payload["result_summary"] = data["result_summary"]
                            if data.get("error_message"):
                                complete_payload["error_message"] = data["error_message"]
                            yield _format_sse_event("complete", complete_payload)
                            return
                    except asyncio.QueueEmpty:
                        break

                # Periodic DB poll for status reconciliation
                heartbeat_counter += poll_interval
                if heartbeat_counter >= heartbeat_interval:
                    heartbeat_counter = 0
                    yield ": heartbeat\n\n"

                    # Refresh job status from DB + reconcile with RQ
                    try:
                        async with async_session_ctx() as fresh_session:
                            fresh_job = await fresh_session.get(BackgroundJob, job_id)
                            if fresh_job:
                                # Reconcile with RQ so sweep jobs that
                                # don't update the DB record are detected
                                await _reconcile_rq_status(fresh_job, fresh_session)
                                await fresh_session.commit()
                                if fresh_job.status in TERMINAL_JOB_STATUSES:
                                    yield _format_sse(
                                        {
                                            "job_id": job_id_str,
                                            "status": fresh_job.status,
                                            "result_summary": fresh_job.result_summary,
                                            "error_message": fresh_job.error_message,
                                            "completed_at": (
                                                fresh_job.completed_at.isoformat()
                                                if fresh_job.completed_at
                                                else None
                                            ),
                                        }
                                    )
                                    yield _format_sse_event(
                                        "complete",
                                        {
                                            "status": fresh_job.status,
                                            "result_summary": fresh_job.result_summary,
                                            "error_message": fresh_job.error_message,
                                        },
                                    )
                                    return
                    except Exception:
                        logger.warning("sse_db_poll_error", exc_info=True)

                await asyncio.sleep(poll_interval)

        finally:
            if redis_listener and not redis_listener.done():
                redis_listener.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await redis_listener

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Encoding": "identity",
        },
    )


async def _redis_pubsub_listener(
    job_id: str,
    queue: asyncio.Queue[dict[str, object]],
) -> None:
    """Listen to Redis pub/sub channel for job progress updates."""
    from app.api.dashboard._helpers import _redis_channel_listener

    await _redis_channel_listener(f"job_progress:{job_id}", queue)


async def _redis_dashboard_listener(
    channel: str,
    queue: asyncio.Queue[dict[str, object]],
) -> None:
    """Listen to a Redis pub/sub dashboard channel."""
    from app.api.dashboard._helpers import _redis_channel_listener

    await _redis_channel_listener(channel, queue)


# -- Dashboard SSE streams --


@router.get("/teams/{team_id}/stream", name="stream_team_dashboard")
async def stream_team_dashboard(
    team_id: uuid.UUID,
    request: Request,
    _auth: ApiAuth,
) -> StreamingResponse:
    """SSE stream for real-time team dashboard updates.

    Subscribes to ``dashboard:team:{team_id}`` Redis pub/sub channel.
    When webhooks are processed or metrics recomputed, a notification is
    pushed so the frontend can fetch fresh data from the live-data endpoint.

    Events emitted:
      - ``update`` with JSON payload ``{"event": "...", ...}``
      - Heartbeat comments every 15 s
    """
    async with async_session_ctx() as _authz_session:
        if not await _can_view_dashboard_stream(request, _authz_session, team_id=team_id):
            # 404, not 403 - never confirm a foreign group's existence.
            raise_not_found("Group not found")

    async def _event_generator() -> AsyncGenerator[str, None]:
        redis_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=200)
        redis_task: asyncio.Task[None] | None = None

        try:
            channel = f"dashboard:team:{team_id}"
            redis_task = asyncio.create_task(_redis_dashboard_listener(channel, redis_queue))
        except Exception:
            logger.warning("Redis pub/sub for team dashboard stream unavailable", exc_info=True)

        heartbeat_counter = 0
        poll_interval = 2

        try:
            # Initial connection acknowledgement
            yield _format_sse_event("connected", {"team_id": str(team_id)})

            while True:
                if await request.is_disconnected():
                    break

                # Drain all pending notifications
                while not redis_queue.empty():
                    try:
                        data = redis_queue.get_nowait()
                        yield _format_sse_event("update", data)
                    except asyncio.QueueEmpty:
                        break

                # Heartbeat
                heartbeat_counter += poll_interval
                if heartbeat_counter >= 15:
                    heartbeat_counter = 0
                    yield ": heartbeat\n\n"

                await asyncio.sleep(poll_interval)
        finally:
            if redis_task and not redis_task.done():
                redis_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await redis_task

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


@router.get("/courses/{course_id}/stream", name="stream_course_dashboard")
async def stream_course_dashboard(
    course_id: uuid.UUID,
    request: Request,
    _auth: ApiAuth,
) -> StreamingResponse:
    """SSE stream for real-time course dashboard updates.

    Subscribes to ``dashboard:course:{course_id}`` Redis pub/sub channel.
    Pushes ``update`` events when team metrics change, members are modified,
    or webhooks trigger data changes for any team in the course.
    """
    async with async_session_ctx() as _authz_session:
        if not await _can_view_dashboard_stream(request, _authz_session, course_id=course_id):
            # 404, not 403 - never confirm a foreign course's existence.
            raise_not_found("Course not found")

    async def _event_generator() -> AsyncGenerator[str, None]:
        redis_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=200)
        redis_task: asyncio.Task[None] | None = None

        try:
            channel = f"dashboard:course:{course_id}"
            redis_task = asyncio.create_task(_redis_dashboard_listener(channel, redis_queue))
        except Exception:
            logger.warning("Redis pub/sub for course dashboard stream unavailable", exc_info=True)

        heartbeat_counter = 0
        poll_interval = 2

        try:
            yield _format_sse_event("connected", {"course_id": str(course_id)})

            while True:
                if await request.is_disconnected():
                    break

                while not redis_queue.empty():
                    try:
                        data = redis_queue.get_nowait()
                        yield _format_sse_event("update", data)
                    except asyncio.QueueEmpty:
                        break

                heartbeat_counter += poll_interval
                if heartbeat_counter >= 15:
                    heartbeat_counter = 0
                    yield ": heartbeat\n\n"

                await asyncio.sleep(poll_interval)
        finally:
            if redis_task and not redis_task.done():
                redis_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await redis_task

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


def _format_sse(data: dict[str, object]) -> str:
    """Format a dict as an SSE data event."""
    return f"data: {json.dumps(data, default=str)}\n\n"


def _format_sse_event(event: str, data: dict[str, object]) -> str:
    """Format a named SSE event."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


# -- Global dashboard SSE stream --


@router.get("/dashboard/stream", name="stream_dashboard_global")
async def stream_dashboard_global(
    request: Request,
    _auth: ApiAuth,
) -> StreamingResponse:
    """SSE stream for the dashboard home page.

    Subscribes to the ``dashboard:global`` Redis pub/sub channel.
    When any team or course data changes, a notification is pushed so
    the frontend can fetch fresh stats from ``/dashboard/stats``.
    """

    async def _event_generator() -> AsyncGenerator[str, None]:
        redis_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=200)
        redis_task: asyncio.Task[None] | None = None

        try:
            redis_task = asyncio.create_task(
                _redis_dashboard_listener("dashboard:global", redis_queue),
            )
        except Exception:
            logger.warning("Redis pub/sub for global dashboard stream unavailable", exc_info=True)

        heartbeat_counter = 0
        poll_interval = 2

        try:
            yield _format_sse_event("connected", {"status": "ok"})

            while True:
                if await request.is_disconnected():
                    break

                while not redis_queue.empty():
                    try:
                        data = redis_queue.get_nowait()
                        yield _format_sse_event("update", data)
                    except asyncio.QueueEmpty:
                        break

                heartbeat_counter += poll_interval
                if heartbeat_counter >= 15:
                    heartbeat_counter = 0
                    yield ": heartbeat\n\n"

                await asyncio.sleep(poll_interval)
        finally:
            if redis_task and not redis_task.done():
                redis_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await redis_task

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


# -- Support ticket SSE stream --


@router.get("/support/tickets/{ticket_id}/stream", name="stream_ticket_updates")
async def stream_ticket_updates(
    ticket_id: int,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> StreamingResponse:
    """SSE stream for real-time support ticket updates.

    Subscribes to ``support:ticket:{ticket_id}`` Redis pub/sub channel.
    Pushes events when comments are added or ticket fields change.

    Events emitted:
      - ``comment`` - new comment added
      - ``update`` - ticket field changed (status, priority, etc.)
      - Heartbeat comments every 15 s
    """
    # Validate ticket exists and user is course staff
    from app.models.course import Course
    from app.models.support_ticket import SupportTicket
    from app.security.course_roles import is_course_staff

    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise_not_found("Ticket not found")
    course = await db.get(Course, ticket.course_id)
    if not course:
        raise_not_found("Course not found")
    # Resolve user from session for course staff check
    user = await _load_sse_user(request, db)
    if user is None or not await is_course_staff(db, course, user):
        raise_forbidden("Not a teacher for this course")

    async def _event_generator() -> AsyncGenerator[str, None]:
        redis_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=200)
        redis_task: asyncio.Task[None] | None = None

        try:
            channel = f"support:ticket:{ticket_id}"
            redis_task = asyncio.create_task(
                _redis_dashboard_listener(channel, redis_queue),
            )
        except Exception:
            logger.warning("Redis pub/sub for ticket SSE unavailable", exc_info=True)

        heartbeat_counter = 0
        poll_interval = 2

        try:
            yield _format_sse_event("connected", {"ticket_id": ticket_id})

            while True:
                if await request.is_disconnected():
                    break

                while not redis_queue.empty():
                    try:
                        data = redis_queue.get_nowait()
                        event_type = data.pop("_event", "update")
                        yield _format_sse_event(str(event_type), data)
                    except asyncio.QueueEmpty:
                        break

                heartbeat_counter += poll_interval
                if heartbeat_counter >= 15:
                    heartbeat_counter = 0
                    yield ": heartbeat\n\n"

                await asyncio.sleep(poll_interval)
        finally:
            if redis_task and not redis_task.done():
                redis_task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await redis_task

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )
