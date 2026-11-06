"""LLM analysis routes for projects (split from projects.py)."""

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
from rq.job import Job
from sqlalchemy import delete, select

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
from app.schemas.dashboard import LLMProjectAnalysisStatusResponse
from app.services.job_control import cancel_rq_job_ids

router = APIRouter()


@router.post("/projects/{project_id}/llm-analyze")
async def project_llm_analyze(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Trigger LLM analysis for a specific project - redirects to team endpoint."""
    project = await db.get(GitLabProject, project_id)
    if not project:
        return _not_found_response(request, "Project")

    team = await db.get(Team, project.team_id)
    if not team or not await _can_manage_team(team, _auth, db):
        return _not_found_response(request, "Project", message="Access denied.")

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

    # Clear old error and job entries before starting new analysis
    from app.models.llm_log import LLMAnalysisLog

    delete_old_stmt = delete(LLMAnalysisLog).where(
        LLMAnalysisLog.project_id == project_id,
        LLMAnalysisLog.target_type.in_(["error", "job_running", "job_cancelled"]),
    )
    await db.execute(delete_old_stmt)

    # Enqueue background job for this project
    from app.services.events import get_queue

    q = get_queue("high")
    job = q.enqueue(
        "app.workers.llm_job.analyze_project_mrs",
        str(project.id),
        job_timeout=settings.rq_default_timeout * 2,
    )

    # Store job tracking entry - single commit with delete + insert
    job_entry = LLMAnalysisLog(
        project_id=project_id,
        target_type="job_running",
        model_used=settings.llm_model,
        structured_result={"job_id": job.id, "started_at": datetime.now(UTC).isoformat()},
    )
    db.add(job_entry)
    await db.commit()

    logger.info(
        "llm_analysis_enqueued_project",
        project_id=str(project_id),
        team_id=str(team.id),
        job_id=job.id,
    )

    return Response(
        status_code=303,
        headers={"Location": f"/dashboard/projects/{project_id}?analysis_started=1"},
    )


@router.post("/projects/{project_id}/llm-analyze-mr/{mr_iid}")
async def project_llm_analyze_single_mr(
    project_id: uuid.UUID,
    mr_iid: int,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Enqueue background analysis for a single MR (SSE-compatible)."""
    project = await db.get(GitLabProject, project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)

    team = await db.get(Team, project.team_id)
    if not team or not await _can_manage_team(team, _auth, db):
        return JSONResponse({"error": "Access denied"}, status_code=403)

    settings = get_settings()
    if not settings.llm_analysis_enabled:
        return JSONResponse({"error": "LLM feature disabled"}, status_code=400)

    # An archived course is read-only: never spend LLM budget on it.
    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    # Clear old error and job entries for this specific MR
    from app.models.llm_log import LLMAnalysisLog

    del_stmt = delete(LLMAnalysisLog).where(
        LLMAnalysisLog.project_id == project_id,
        LLMAnalysisLog.mr_iid == mr_iid,
        LLMAnalysisLog.target_type.in_(["error", "job_running", "job_cancelled"]),
    )
    await db.execute(del_stmt)

    # Enqueue background job
    from app.services.events import get_queue

    q = get_queue("high")
    job = q.enqueue(
        "app.workers.llm_job.analyze_single_mr",
        str(project.id),
        mr_iid,
        job_timeout=settings.rq_default_timeout,
    )

    # Store job tracking entry - single commit with delete + insert
    job_entry = LLMAnalysisLog(
        project_id=project_id,
        target_type="job_running",
        model_used=settings.llm_model,
        structured_result={"job_id": job.id, "started_at": datetime.now(UTC).isoformat()},
    )
    db.add(job_entry)
    await db.commit()

    logger.info(
        "single_mr_analysis_enqueued",
        project_id=str(project_id),
        mr_iid=mr_iid,
        job_id=job.id,
    )

    return JSONResponse({"status": "started", "mr_iid": mr_iid, "job_id": job.id})


async def _poll_llm_analysis_status(
    project_id: uuid.UUID,
    session: Any,
) -> dict[str, Any]:
    """Build LLM analysis status snapshot from DB + RQ.

    Shared by the REST polling endpoint and the SSE reconciliation loop.
    Returns a plain dict; callers convert to the appropriate response type.
    """
    from app.models.llm_log import LLMAnalysisLog

    # Check for recently completed/failed jobs first (prevents race
    # between REST and SSE callers that used to delete the entry).
    done_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project_id,
            LLMAnalysisLog.target_type.in_(("job_completed", "job_failed", "job_cancelled")),
        )
        .order_by(LLMAnalysisLog.analysis_timestamp.desc())
        .limit(1)
    )
    done_result = await session.execute(done_stmt)
    done_entry = done_result.scalar_one_or_none()
    if done_entry:
        age = datetime.now(UTC) - done_entry.analysis_timestamp.replace(tzinfo=UTC)
        if age < timedelta(minutes=5):
            if done_entry.target_type == "job_completed":
                return {"status": "completed", "message": "Analysis complete!", "reload": True}
            if done_entry.target_type == "job_cancelled":
                return {"status": "cancelled", "message": "Analysis cancelled.", "reload": True}
            _sr = done_entry.structured_result or {}
            err = _sr.get("error", "Analysis failed")
            return {
                "status": "failed",
                "message": err,
                "error_type": _sr.get("error_type", "unknown"),
                "raw_error": _sr.get("error_message", err),
                "reload": True,
            }
        # Stale - clean up
        await session.delete(done_entry)
        await session.commit()

    job_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project_id,
            LLMAnalysisLog.target_type == "job_running",
        )
        .limit(1)
    )
    job_result = await session.execute(job_stmt)
    job_entry = job_result.scalar_one_or_none()

    if not job_entry:
        return {"status": "none", "message": "No analysis running"}

    job_age = datetime.now(UTC) - job_entry.analysis_timestamp.replace(tzinfo=UTC)
    if job_age > timedelta(minutes=20):
        await session.delete(job_entry)
        await session.commit()
        return {"status": "failed", "message": "Analysis timed out.", "reload": True}

    rq_job_id = job_entry.structured_result.get("job_id")
    if rq_job_id:
        conn = None
        try:
            conn = _get_redis()
            rq_job = Job.fetch(rq_job_id, connection=conn)
            rq_status = rq_job.get_status(refresh=True)
            if rq_status in {"canceled", "cancelled", "stopped"}:
                job_entry.target_type = "job_cancelled"
                job_entry.structured_result = {
                    **(job_entry.structured_result or {}),
                    "error": "Analysis cancelled.",
                    "error_type": "cancelled",
                    "error_message": "Analysis cancelled.",
                }
                await session.commit()
                return {"status": "cancelled", "message": "Analysis cancelled.", "reload": True}
            if rq_job.is_finished:
                job_entry.target_type = "job_completed"
                await session.commit()
                return {"status": "completed", "message": "Analysis complete!", "reload": True}
            if rq_job.is_failed:
                # Extract clean error message from traceback
                raw_exc = str(rq_job.exc_info) if rq_job.exc_info else ""
                # Get just the last line of the traceback (the actual exception)
                exc_lines = [ln.strip() for ln in raw_exc.strip().splitlines() if ln.strip()]
                err_msg = exc_lines[-1][:200] if exc_lines else "Unknown error"
                # Classify the error for user-friendly display
                from app.workers.llm_job import LLMErrorType, classify_llm_error

                try:
                    _err_type, _err_msg = classify_llm_error(Exception(err_msg))
                except Exception:
                    _err_type = LLMErrorType.UNKNOWN
                    _err_msg = "An unexpected error occurred during analysis."
                job_entry.target_type = "job_failed"
                job_entry.structured_result = {
                    **(job_entry.structured_result or {}),
                    "error": _err_msg,
                    "error_type": _err_type.value,
                    "error_message": _err_msg,
                    "is_error": True,
                }
                await session.commit()
                return {
                    "status": "failed",
                    "message": _err_msg,
                    "error_type": _err_type.value,
                    "raw_error": err_msg,
                    "reload": True,
                }
            progress = rq_job.meta.get("progress", {})
            total = progress.get("total", 0)
            analyzed = progress.get("analyzed", 0)
            failed_count = progress.get("failed", 0)
            skipped = progress.get("skipped", 0)
            current_mr = progress.get("current_mr")
            done = analyzed + failed_count + skipped
            pct = int((done / total) * 100) if total else 0
            msg = f"Analyzing MR !{current_mr}..." if current_mr else "Analyzing merge requests..."
            return {
                "status": "running",
                "message": msg,
                "analyzed": analyzed,
                "failed": failed_count,
                "skipped": skipped,
                "total": total,
                "progress": pct,
                "current_mr": current_mr,
            }
        except Exception:
            logger.debug("analysis_status_poll_failed")
        finally:
            if conn is not None:
                with suppress(Exception):
                    conn.close()

    return {"status": "running", "message": "Analysis in progress..."}


@router.post("/projects/{project_id}/llm-analysis-cancel")
async def cancel_project_llm_analysis(
    project_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
) -> Response:
    """Cancel the active project LLM analysis RQ job(s)."""
    from app.models.llm_log import LLMAnalysisLog

    project = await db.get(GitLabProject, project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    team = await db.get(Team, project.team_id)
    if not team or not await _can_manage_team(team, _auth, db):
        return JSONResponse({"error": "Project not found"}, status_code=404)

    running_stmt = (
        select(LLMAnalysisLog)
        .where(
            LLMAnalysisLog.project_id == project_id,
            LLMAnalysisLog.target_type == "job_running",
        )
        .order_by(LLMAnalysisLog.analysis_timestamp.desc())
    )
    entries = list((await db.execute(running_stmt)).scalars().all())
    rq_ids = [
        str((entry.structured_result or {}).get("job_id"))
        for entry in entries
        if (entry.structured_result or {}).get("job_id")
    ]
    cancelled = await cancel_rq_job_ids(rq_ids)
    now = datetime.now(UTC)
    for entry in entries:
        entry.target_type = "job_cancelled"
        entry.analysis_timestamp = now
        entry.structured_result = {
            **(entry.structured_result or {}),
            "error": "Analysis cancelled.",
            "error_type": "cancelled",
            "error_message": "Analysis cancelled.",
        }
    await db.commit()
    return JSONResponse(
        {
            "status": "cancelled" if entries else "idle",
            "cancelled": cancelled,
            "message": "Analysis cancelled." if entries else "No active analysis to cancel.",
        }
    )


@router.get(
    "/projects/{project_id}/llm-analysis-status",
    response_model=LLMProjectAnalysisStatusResponse,
)
async def project_llm_analysis_status(
    project_id: uuid.UUID,
    _auth: TeacherAuth,
    db: DbSession,
) -> LLMProjectAnalysisStatusResponse | Response:
    """Check status of LLM analysis job for a project."""
    from app.models.llm_log import LLMAnalysisLog

    settings = get_settings()
    if not settings.llm_analysis_enabled:
        return LLMProjectAnalysisStatusResponse(status="none", message="AI analysis is disabled")

    # Verify access to this project's team
    project = await db.get(GitLabProject, project_id)
    if not project:
        return JSONResponse({"error": "Project not found"}, status_code=404)
    team_stmt = select(Team).where(Team.id == project.team_id)
    team_result = await db.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    if not team or not await _can_view_team(team, _auth, db):
        return JSONResponse({"error": "Project not found"}, status_code=404)

    result = await _poll_llm_analysis_status(project_id, db)

    # Check for recent error if no job is active
    if result["status"] == "none":
        error_stmt = (
            select(LLMAnalysisLog)
            .where(
                LLMAnalysisLog.project_id == project_id,
                LLMAnalysisLog.target_type == "error",
                LLMAnalysisLog.analysis_timestamp > datetime.now(UTC) - timedelta(hours=2),
            )
            .order_by(LLMAnalysisLog.analysis_timestamp.desc())
            .limit(1)
        )
        error_result = await db.execute(error_stmt)
        error_entry = error_result.scalar_one_or_none()
        if error_entry:
            result = {
                "status": "failed",
                "message": error_entry.structured_result.get("error_message", "Analysis failed"),
            }

    return LLMProjectAnalysisStatusResponse(**result)


# -- SSE stream for project LLM analysis --


@router.get("/projects/{project_id}/llm-analysis-stream", name="project_llm_analysis_stream")
async def project_llm_analysis_stream(
    project_id: uuid.UUID,
    request: Request,
    _auth: TeacherAuth,
) -> Response:
    """Stream project LLM analysis status via Server-Sent Events.

    Subscribes to Redis ``llm_analysis:{project_id}`` channel for real-time
    progress updates from the worker.  Falls back to periodic DB/RQ polling
    every 2s to reconcile status.

    Events:
      - ``data`` with JSON status payload (status, message, progress, etc.)
      - Named ``complete`` event when analysis finishes (success or failure)
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

    # -- Initial DB lookup in a cancellation-safe session --
    async with async_session_ctx() as db:
        project = await db.get(GitLabProject, project_id)
        if not project:
            return JSONResponse({"error": "Project not found"}, status_code=404)

        team = await db.get(Team, project.team_id)
        if not team or not await _can_view_team(team, _auth, db):
            return JSONResponse({"error": "Project not found"}, status_code=404)

    pid = str(project_id)

    async def _redis_llm_listener(
        p_id: str,
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        """Listen to Redis pub/sub for LLM analysis updates."""
        from app.api.dashboard._helpers import _redis_channel_listener

        await _redis_channel_listener(f"llm_analysis:{p_id}", queue)

    async def _event_generator() -> AsyncGenerator[str, None]:
        redis_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=200)
        redis_task: asyncio.Task[None] | None = None

        try:
            redis_task = asyncio.create_task(_redis_llm_listener(pid, redis_queue))
        except Exception:
            logger.warning("llm_redis_listener_start_failed", project_id=pid, exc_info=True)

        poll_interval = 2
        heartbeat_counter = 0
        prev_hash = ""

        try:
            while True:
                if await request.is_disconnected():
                    break

                # Drain Redis pub/sub messages (real-time from worker)
                while not redis_queue.empty():
                    try:
                        data = redis_queue.get_nowait()
                        yield f"data: {json.dumps(data, default=str)}\n\n"
                        status_val = str(data.get("status", "")).lower()
                        if status_val in ("completed", "failed", "cancelled"):
                            yield f"event: complete\ndata: {json.dumps(data, default=str)}\n\n"
                            return
                    except asyncio.QueueEmpty:
                        break

                # Periodic DB/RQ poll for status reconciliation
                async with async_session_ctx() as session:
                    try:
                        snapshot = await _poll_llm_analysis_status(project_id, session)
                    except Exception:
                        logger.warning(
                            "llm_poll_status_failed",
                            project_id=str(project_id),
                            exc_info=True,
                        )
                        snapshot = None

                    if snapshot is not None:
                        snap_hash = json.dumps(snapshot, sort_keys=True, default=str)
                        if snap_hash != prev_hash:
                            prev_hash = snap_hash
                            yield f"data: {json.dumps(snapshot, default=str)}\n\n"
                            status_val = str(snapshot.get("status", "")).lower()
                            if status_val in ("completed", "failed", "cancelled", "none"):
                                if status_val != "none":
                                    evt = json.dumps(snapshot, default=str)
                                    yield f"event: complete\ndata: {evt}\n\n"
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


@router.post("/projects/{project_id}/dismiss-llm-error", name="dismiss_llm_error")
async def dismiss_llm_error(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    """Dismiss LLM analysis error for a project."""
    from app.models.llm_log import LLMAnalysisLog

    # Verify project exists and user has access
    project = await db.get(GitLabProject, project_id)
    if not project:
        return _not_found_response(request, "Project")

    team = await db.get(Team, project.team_id)
    if not team or not await _can_view_team(team, _auth, db):
        return _not_found_response(request, "Project")

    # Delete error and stale terminal entries for this project
    delete_stmt = delete(LLMAnalysisLog).where(
        LLMAnalysisLog.project_id == project_id,
        LLMAnalysisLog.target_type.in_(("error", "job_completed", "job_failed", "job_cancelled")),
    )
    await db.execute(delete_stmt)
    await db.commit()

    logger.info("llm_error_dismissed", project_id=str(project_id))

    return Response(
        status_code=303,
        headers={"Location": f"/dashboard/projects/{project_id}"},
    )
