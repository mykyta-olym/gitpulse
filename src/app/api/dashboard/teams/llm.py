"""LLM teamwork-analysis routes (trigger, status, SSE stream) for teams."""

import asyncio
import contextlib
import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job
from sqlalchemy import select

from app.api.dashboard._access import _can_manage_team, _can_view_team
from app.api.dashboard._helpers import (
    _feature_disabled_response,
    _get_redis,
    _not_found_response,
    logger,
)
from app.config import get_settings
from app.dependencies import CSRFCheck, DbSession, RateLimitDep, TeacherAuth
from app.models.project import GitLabProject
from app.models.team import Team
from app.redis_pool import get_redis as _pool_get_redis
from app.schemas.dashboard import LLMTeamAnalysisStatusResponse
from app.services.job_control import cancel_rq_job_ids

router = APIRouter()


# -- LLM Analysis --


def _fresh_cancelled_marker(request: Request, team_id: uuid.UUID) -> dict[str, Any] | None:
    """Return a recent team-analysis cancellation marker, clearing stale ones."""
    try:
        markers = request.session.get("llm_analysis_cancelled", {})
        marker = markers.get(str(team_id))
    except Exception:
        return None
    if not isinstance(marker, dict):
        return None
    try:
        cancelled_at = datetime.fromisoformat(str(marker.get("cancelled_at", "")))
    except Exception:
        cancelled_at = datetime.now(UTC)
    if cancelled_at.tzinfo is None:
        cancelled_at = cancelled_at.replace(tzinfo=UTC)
    if datetime.now(UTC) - cancelled_at <= timedelta(minutes=5):
        return marker
    with suppress(Exception):
        request.session["llm_analysis_cancelled"].pop(str(team_id), None)
    return None


@router.post("/teams/{team_id}/llm-analyze")
async def trigger_llm_analysis(
    team_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Trigger LLM analysis for the team's latest MRs."""
    # Access control
    team = await db.get(Team, team_id)
    if not team or not await _can_manage_team(team, _auth, db):
        return _not_found_response(request, "Group", message="Access denied.")

    settings = get_settings()
    if not settings.llm_analysis_enabled:
        return _feature_disabled_response(
            request,
            "AI Teamwork Analysis",
            "The LLM-powered analysis feature is currently disabled for this environment.",
            "FEATURE_LLM_SUGGESTIONS=true",
        )

    # An archived course is read-only: never spend LLM budget on it.
    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    # Get team's projects
    p_stmt = select(GitLabProject).where(GitLabProject.team_id == team_id)
    p_result = await db.execute(p_stmt)
    projects = list(p_result.scalars().all())

    if not projects:
        return _feature_disabled_response(
            request,
            "AI Teamwork Analysis",
            "This team has no GitLab projects linked yet. "
            "Link a project first to enable AI analysis.",
            None,
        )

    # Enqueue background job for each project's MRs
    conn = _pool_get_redis()
    q = Queue("high", connection=conn)

    job_ids = []
    for project in projects:
        job = q.enqueue(
            "app.workers.llm_job.analyze_project_mrs",
            str(project.id),
            job_timeout=settings.rq_default_timeout * 2,  # LLM calls can be slow
        )
        job_ids.append(job.id)

    # Store job IDs in session for tracking (best-effort; no-op if session
    # middleware is not available - job status falls back to direct Redis checks)
    try:
        if "llm_analysis_jobs" not in request.session:
            request.session["llm_analysis_jobs"] = {}
        request.session["llm_analysis_jobs"][str(team_id)] = {
            "job_ids": job_ids,
            "total": len(job_ids),
            "started_at": datetime.now(UTC).isoformat(),
        }
        if "llm_analysis_cancelled" in request.session:
            request.session["llm_analysis_cancelled"].pop(str(team_id), None)
    except Exception:
        logger.debug("session write unavailable for llm_analysis_jobs")

    logger.info(
        "llm_analysis_enqueued",
        team_id=str(team_id),
        project_count=len(projects),
        job_ids=job_ids,
    )

    return Response(
        status_code=303,
        headers={"Location": f"/dashboard/teams/{team_id}?analysis_started=1"},
    )


def _team_jobs(request: Request, team_id: uuid.UUID) -> dict[str, Any] | None:
    """The team's analysis jobs this session tracks."""
    try:
        jobs: dict[str, Any] | None = request.session.get("llm_analysis_jobs", {}).get(str(team_id))
    except Exception:
        return None
    return jobs


def _jobs_status(
    request: Request, team_id: uuid.UUID, session_jobs: dict[str, Any] | None
) -> tuple[dict[str, Any], bool]:
    """Report observed outcomes; an unavailable queue never means success."""
    cancelled = _fresh_cancelled_marker(request, team_id)
    if cancelled:
        return {
            "status": "cancelled",
            "message": cancelled.get("message", "Analysis cancelled."),
            "completed": 0,
            "failed": 0,
            "running": 0,
            "total": cancelled.get("total", 0),
            "progress": 100,
        }, False
    if not session_jobs:
        return {"status": "none", "message": "No analysis jobs found"}, False

    job_ids = session_jobs.get("job_ids", [])
    total = len(job_ids)
    if not job_ids:
        return {"status": "none", "message": "No jobs to track"}, False

    try:
        conn = _get_redis()
    except Exception:
        return {
            "status": "running",
            "message": "Status unavailable (queue offline)",
            "completed": 0,
            "failed": 0,
            "running": total,
            "total": total,
        }, False

    completed = 0
    failed = 0
    cancelled_count = 0
    running = 0
    unavailable = False
    expired = 0
    try:
        for job_id in job_ids:
            try:
                job = Job.fetch(job_id, connection=conn)
                job_status = job.get_status(refresh=True)
                if job_status in {"canceled", "cancelled", "stopped"}:
                    cancelled_count += 1
                elif job.is_finished:
                    completed += 1
                elif job.is_failed:
                    failed += 1
                else:
                    running += 1
            except NoSuchJobError:
                failed += 1
                expired += 1
            except Exception:
                running += 1
                unavailable = True
    finally:
        with suppress(Exception):
            conn.close()

    if completed + failed + cancelled_count == total:
        if cancelled_count:
            return {
                "status": "cancelled",
                "message": (
                    f"Analysis cancelled: {cancelled_count} cancelled, {completed} completed"
                ),
                "completed": completed,
                "failed": failed,
                "running": 0,
                "total": total,
                "progress": 100,
            }, True
        return {
            "status": "failed" if failed else "completed",
            "message": (
                "Analysis history expired. Run the analysis again."
                if expired
                else f"Analysis complete: {completed} succeeded, {failed} failed"
            ),
            "completed": completed,
            "failed": failed,
            "total": total,
        }, True

    return {
        "status": "running",
        "message": (
            "Status unavailable (queue offline)"
            if unavailable
            else f"Analyzing... {completed}/{total} projects done"
        ),
        "completed": completed,
        "failed": failed,
        "running": running,
        "total": total,
        "progress": int((completed / total) * 100) if total > 0 else 0,
    }, False


@router.get(
    "/teams/{team_id}/llm-analysis-status",
    response_model=LLMTeamAnalysisStatusResponse,
)
async def llm_analysis_status(
    team_id: uuid.UUID,
    request: Request,
    _auth: TeacherAuth,
) -> LLMTeamAnalysisStatusResponse:
    """Check status of LLM analysis jobs for a team."""
    settings = get_settings()
    if not settings.llm_analysis_enabled:
        return LLMTeamAnalysisStatusResponse(status="none", message="AI analysis is disabled")

    status, done = _jobs_status(request, team_id, _team_jobs(request, team_id))
    if done:
        # All jobs done, clear from session
        try:
            if (
                "llm_analysis_jobs" in request.session
                and str(team_id) in request.session["llm_analysis_jobs"]
            ):
                del request.session["llm_analysis_jobs"][str(team_id)]
        except Exception:
            logger.debug("session clear unavailable for llm_analysis_jobs")
    return LLMTeamAnalysisStatusResponse(**status)


@router.post("/teams/{team_id}/llm-analysis-cancel")
async def cancel_team_llm_analysis(
    team_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
) -> Response:
    """Cancel active team LLM analysis RQ job(s) tracked in the user session."""
    team = await db.get(Team, team_id)
    if not team or not await _can_manage_team(team, _auth, db):
        return JSONResponse({"error": "Group not found"}, status_code=404)

    session_jobs = _team_jobs(request, team_id)
    job_ids = list((session_jobs or {}).get("job_ids", []) or [])
    cancelled = await cancel_rq_job_ids(job_ids)
    try:
        if "llm_analysis_jobs" in request.session:
            request.session["llm_analysis_jobs"].pop(str(team_id), None)
        if "llm_analysis_cancelled" not in request.session:
            request.session["llm_analysis_cancelled"] = {}
        request.session["llm_analysis_cancelled"][str(team_id)] = {
            "message": "Analysis cancelled.",
            "total": (session_jobs or {}).get("total", cancelled),
            "cancelled_at": datetime.now(UTC).isoformat(),
        }
    except Exception:
        logger.debug("session write unavailable for llm_analysis_cancelled")

    return JSONResponse(
        {
            "status": "cancelled" if job_ids else "idle",
            "cancelled": cancelled,
            "message": "Analysis cancelled." if job_ids else "No active analysis to cancel.",
        }
    )


# -- SSE stream for team LLM analysis --


@router.get("/teams/{team_id}/llm-analysis-stream", name="team_llm_analysis_stream")
async def team_llm_analysis_stream(
    team_id: uuid.UUID,
    request: Request,
    _auth: TeacherAuth,
) -> Response:
    """Stream team LLM analysis status via Server-Sent Events.

    Subscribes to Redis ``llm_analysis:{project_id}`` channels for all team
    projects.  Polls session/RQ every 2s for status reconciliation.

    Events:
      - ``data`` with JSON status (status, message, completed, total, etc.)
      - Named ``complete`` event when all project analyses finish
      - Heartbeat comments every 15s

    NOTE: Uses ``async_session_ctx()`` instead of DI ``DbSession`` because
    SSE streaming responses outlive the ASGI request scope.  When the
    client disconnects, Starlette's cancel scope fires ``CancelledError``
    which races with the DI async-generator cleanup, leaking the asyncpg
    connection back to the pool.  ``async_session_ctx()`` shields
    rollback/close from cancellation via ``anyio.CancelScope(shield=True)``.
    """

    from app.db.session import async_session_ctx

    settings = get_settings()
    if not settings.llm_analysis_enabled:
        return JSONResponse({"error": "AI analysis is disabled"}, status_code=404)

    # -- Initial DB lookups in a cancellation-safe session --
    async with async_session_ctx() as db:
        team = await db.get(Team, team_id)
        if not team:
            return JSONResponse({"error": "Group not found"}, status_code=404)

        if not await _can_view_team(team, _auth, db):
            return JSONResponse({"error": "Group not found"}, status_code=404)

        p_stmt = select(GitLabProject.id).where(GitLabProject.team_id == team_id)
        p_result = await db.execute(p_stmt)
        project_ids = [str(pid) for pid in p_result.scalars().all()]

    return StreamingResponse(
        _status_events(request, team_id, _team_jobs(request, team_id), project_ids),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


async def _status_events(
    request: Request,
    team_id: uuid.UUID,
    session_jobs: dict[str, Any] | None,
    project_ids: list[str],
) -> AsyncGenerator[str, None]:
    """The workers' own progress messages as they arrive, and the polled team
    status whenever it changes, until the analysis is over."""
    from app.api.dashboard._helpers import _redis_channel_listener

    redis_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=200)
    redis_task: asyncio.Task[None] | None = None

    if project_ids:
        try:
            redis_task = asyncio.create_task(
                _redis_channel_listener([f"llm_analysis:{pid}" for pid in project_ids], redis_queue)
            )
        except Exception:
            logger.warning("team_llm_redis_listener_start_failed", exc_info=True)

    poll_interval = 2
    heartbeat_counter = 0
    prev_hash = ""

    try:
        while True:
            if await request.is_disconnected():
                break

            # Drain Redis pub/sub messages (real-time from workers)
            while not redis_queue.empty():
                try:
                    data = redis_queue.get_nowait()
                    yield f"data: {json.dumps(data, default=str)}\n\n"
                except asyncio.QueueEmpty:
                    break

            # Poll session/RQ for aggregated status
            snapshot, _done = _jobs_status(request, team_id, session_jobs)
            snap_hash = json.dumps(snapshot, sort_keys=True, default=str)

            if snap_hash != prev_hash:
                prev_hash = snap_hash
                yield f"data: {json.dumps(snapshot, default=str)}\n\n"
                status_val = str(snapshot.get("status", "")).lower()
                if status_val in ("completed", "failed", "cancelled", "none"):
                    if status_val != "none":
                        yield f"event: complete\ndata: {json.dumps(snapshot, default=str)}\n\n"
                    return

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
