"""Background worker job for LLM analysis of MRs."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from sqlalchemy import select

from app.config import get_settings
from app.db.session import async_session_ctx, dispose_engine, init_engine
from app.models.llm_log import LLMAnalysisLog
from app.models.merge_request import MergeRequest
from app.models.project import GitLabProject

logger = structlog.get_logger(__name__)


class LLMErrorType(StrEnum):
    """Classification of LLM errors for user-friendly messages."""

    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_NOT_FOUND = "model_not_found"
    INVALID_API_KEY = "invalid_api_key"
    RATE_LIMITED = "rate_limited"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"
    NO_MRS = "no_mrs"
    PROJECT_NOT_FOUND = "project_not_found"
    UNKNOWN = "unknown"


def classify_llm_error(exc: Exception) -> tuple[LLMErrorType, str]:
    """Classify an LLM exception into error type and user-friendly message."""
    exc_str = str(exc).lower()
    exc_type = type(exc).__name__

    # Google Gemini errors
    if "resource_exhausted" in exc_str or "quota" in exc_str:
        if "per_day" in exc_str or "daily" in exc_str:
            return (
                LLMErrorType.QUOTA_EXCEEDED,
                "Daily API quota exceeded. Please try again tomorrow or upgrade your API plan.",
            )
        return (
            LLMErrorType.RATE_LIMITED,
            "API rate limit exceeded. Please wait a few minutes and try again.",
        )

    if "not_found" in exc_str and "model" in exc_str:
        return (
            LLMErrorType.MODEL_NOT_FOUND,
            "The configured AI model is not available. Please check LLM_MODEL setting.",
        )

    if "invalid" in exc_str and ("api" in exc_str or "key" in exc_str or "credential" in exc_str):
        return (
            LLMErrorType.INVALID_API_KEY,
            "Invalid API key. Please check your LLM_API_KEY configuration.",
        )

    if "401" in exc_str or "unauthenticated" in exc_str or "unauthorized" in exc_str:
        return LLMErrorType.INVALID_API_KEY, "API authentication failed. Verify your API key."

    if "403" in exc_str or "permission" in exc_str or "forbidden" in exc_str:
        return LLMErrorType.INVALID_API_KEY, "API access denied. Check your API key permissions."

    # OpenAI / Groq specific errors - check quota BEFORE generic 429/rate-limit
    # because OpenAI insufficient_quota responses also contain "429".
    if "insufficient_quota" in exc_str or "billing" in exc_str:
        return LLMErrorType.QUOTA_EXCEEDED, "API quota exceeded. Please check your billing/plan."

    if "ratelimit" in exc_str or "rate_limit" in exc_str or "429" in exc_str:
        return LLMErrorType.RATE_LIMITED, "API rate limit exceeded. Please wait and try again."

    # Groq specific errors
    if "tokens_per_minute" in exc_str or "requests_per_minute" in exc_str:
        return (
            LLMErrorType.RATE_LIMITED,
            "Groq rate limit hit. Free tier has per-minute limits - wait and retry.",
        )

    if "tokens_per_day" in exc_str or "requests_per_day" in exc_str:
        return LLMErrorType.QUOTA_EXCEEDED, "Groq daily quota exceeded. Free tier resets daily."

    # Network errors
    if any(x in exc_str for x in ["connection", "timeout", "network", "unreachable", "dns"]):
        return (
            LLMErrorType.NETWORK_ERROR,
            "Network error connecting to AI service. Please try again later.",
        )

    if any(x in exc_type.lower() for x in ["connection", "timeout"]):
        return (
            LLMErrorType.NETWORK_ERROR,
            "Connection timeout. The AI service may be temporarily unavailable.",
        )

    # Parse errors
    if "json" in exc_str or "decode" in exc_str or "parse" in exc_str:
        return (
            LLMErrorType.PARSE_ERROR,
            f"AI returned an invalid response ({exc_type}). "
            f"The model may be overloaded - retry usually fixes this.",
        )

    # Server-side errors (OpenAI 500/502/503, etc.)
    _srv_err = ["500", "502", "503", "internal server error"]
    _srv_err += ["service unavailable", "bad gateway"]
    if any(x in exc_str for x in _srv_err):
        return (
            LLMErrorType.NETWORK_ERROR,
            "The AI service encountered a server error. Please try again in a few minutes.",
        )

    if any(
        x in exc_type.lower()
        for x in ["internalserver", "apierror", "serviceunavailable", "badgateway"]
    ):
        return (
            LLMErrorType.NETWORK_ERROR,
            "The AI service is temporarily unavailable. Please try again later.",
        )

    # Empty response errors
    _empty_kw = ["choices", "content", "response"]
    if "empty" in exc_str and any(k in exc_str for k in _empty_kw):
        return (
            LLMErrorType.PARSE_ERROR,
            "AI returned an empty response. Retry usually fixes this.",
        )

    # Validation errors (pydantic)
    if "validation" in exc_str or "validationerror" in exc_type.lower():
        return (
            LLMErrorType.PARSE_ERROR,
            "AI response did not match the expected format. Retry usually fixes this.",
        )

    return LLMErrorType.UNKNOWN, "An unexpected error occurred during analysis. Please try again."


def analyze_project_mrs(project_id: str | uuid.UUID) -> dict[str, Any]:
    """
    Analyze all recent open MRs in a project.
    Called as a background job via RQ.

    Returns:
        dict with 'analyzed', 'skipped', 'failed' counts
    """
    return asyncio.run(_analyze_project_mrs_async(project_id))


def analyze_single_mr(project_id: str | uuid.UUID, mr_iid: int) -> dict[str, Any]:
    """Analyze a single MR as a background job (RQ).

    Unlike :func:`analyze_project_mrs`, this targets ONE specific MR
    and always forces re-analysis (no cache check).
    """
    return asyncio.run(_analyze_single_mr_async(project_id, mr_iid))


async def _analyze_single_mr_async(project_id: str | uuid.UUID, mr_iid: int) -> dict[str, Any]:
    settings = get_settings()
    if not settings.llm_analysis_enabled:
        return {"analyzed": 0, "reason": "feature_disabled"}

    p_uuid = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(str(project_id))
    init_engine(str(settings.database_url))
    _pid = str(p_uuid)

    try:
        async with async_session_ctx() as session:
            project = await session.get(GitLabProject, p_uuid)
            if not project:
                logger.error("project_not_found", project_id=_pid)
                return {"analyzed": 0, "reason": "project_not_found"}

            # Check MR exists
            mr_stmt = select(MergeRequest).where(
                MergeRequest.project_id == p_uuid,
                MergeRequest.gitlab_iid == mr_iid,
            )
            mr_result = await session.execute(mr_stmt)
            mr = mr_result.scalar_one_or_none()
            if not mr:
                logger.error("mr_not_found", project_id=_pid, mr_iid=mr_iid)
                return {"analyzed": 0, "reason": "mr_not_found"}

            # Publish initial progress
            from app.workers.progress import publish_progress

            publish_progress(
                job_id=f"llm-{_pid}",
                status="running",
                message=f"Analyzing MR !{mr_iid}...",
                extra={
                    "channel": f"llm_analysis:{_pid}",
                    "progress": {
                        "analyzed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "total": 1,
                        "current_mr": mr_iid,
                    },
                    "percent": 0,
                },
                llm_project_id=_pid,
            )

            from app.services.llm.service import LLMService

            service = LLMService(settings)

            try:
                analysis_result = await service.analyze_mr(session, p_uuid, mr_iid)
                status = "completed" if analysis_result else "failed"
                msg = (
                    f"Analysis complete for MR !{mr_iid}"
                    if analysis_result
                    else f"Analysis returned no result for MR !{mr_iid}"
                )
            except Exception as exc:
                error_type, error_message = classify_llm_error(exc)
                logger.exception(
                    "single_mr_analysis_failed",
                    mr_iid=mr_iid,
                    error_type=error_type.value,
                )
                status = "failed"
                msg = error_message

                # Rollback any pending state before writing the error entry
                await session.rollback()

                # Store error entry
                error_log = LLMAnalysisLog(
                    project_id=p_uuid,
                    mr_iid=mr_iid,
                    target_type="error",
                    model_used=settings.llm_model,
                    structured_result={
                        "error_type": error_type.value,
                        "error_message": error_message,
                        "is_error": True,
                    },
                    risk_score=None,
                )
                session.add(error_log)
                await session.commit()

            # Publish completion
            publish_progress(
                job_id=f"llm-{_pid}",
                status=status,
                message=msg,
                extra={
                    "analyzed": 1 if status == "completed" else 0,
                    "failed": 0 if status == "completed" else 1,
                    "skipped": 0,
                    "total": 1,
                },
                llm_project_id=_pid,
            )

            # Clean up job_running entry
            from sqlalchemy import delete as sa_delete

            await session.execute(
                sa_delete(LLMAnalysisLog).where(
                    LLMAnalysisLog.project_id == p_uuid,
                    LLMAnalysisLog.target_type == "job_running",
                )
            )
            await session.commit()

            return {
                "analyzed": 1 if status == "completed" else 0,
                "failed": 0 if status == "completed" else 1,
                "mr_iid": mr_iid,
                "project_id": _pid,
            }
    finally:
        await dispose_engine()


def _update_job_progress(
    analyzed: int,
    failed: int,
    skipped: int,
    total: int,
    current_mr: int | None = None,
    *,
    project_id: str | None = None,
) -> None:
    """Update RQ job meta and publish to Redis pub/sub for SSE streaming."""
    progress_data = {
        "analyzed": analyzed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "current_mr": current_mr,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    rq_job_id: str | None = None
    try:
        from rq import get_current_job

        job = get_current_job()
        if job:
            rq_job_id = job.id
            job.meta["progress"] = progress_data
            job.save_meta()  # type: ignore[no-untyped-call]
    except Exception:  # noqa: S110 -- RQ progress meta is best-effort; SSE pipeline below provides redundant signal.
        pass  # Non-critical - progress display is best-effort

    # Publish to Redis pub/sub for SSE real-time streaming
    if project_id:
        from app.workers.progress import publish_progress

        pct = round((analyzed + failed + skipped) / total * 100) if total else 0
        msg = f"Analyzing MRs: {analyzed + failed + skipped}/{total}"
        if current_mr:
            msg += f" (MR !{current_mr})"
        publish_progress(
            job_id=rq_job_id or f"llm-{project_id}",
            status="running",
            message=msg,
            extra={
                "channel": f"llm_analysis:{project_id}",
                "progress": progress_data,
                "percent": pct,
            },
            llm_project_id=project_id,
        )


class _Tally:
    """The analysed, skipped and failed MRs of one project run, reported as
    they move."""

    def __init__(self, project_id: str, total: int) -> None:
        self.project_id = project_id
        self.total = total
        self.analyzed = 0
        self.skipped = 0
        self.failed = 0
        self.errors: list[dict[str, Any]] = []

    def report(self, current_mr: int | None = None) -> None:
        _update_job_progress(
            self.analyzed,
            self.failed,
            self.skipped,
            self.total,
            current_mr=current_mr,
            project_id=self.project_id,
        )


async def _project_course(session: Any, project: GitLabProject) -> Any:
    from app.models.course import Course
    from app.models.team import Team

    team = await session.get(Team, project.team_id)
    return await session.get(Course, team.course_id) if team else None


async def _recent_mr_iids(session: Any, p_uuid: uuid.UUID, course: Any, limit: int) -> list[int]:
    """The most recently updated MRs, at most ``limit`` (API rate limits), of
    the active semester only - this mirrors the dashboard read-path filter and
    spends no tokens on stale work from previous semesters."""
    from app.utils.semester import semester_floor_utc

    floor = semester_floor_utc(course.settings if course else None)
    where = [MergeRequest.project_id == p_uuid]
    if floor is not None:
        where.append(MergeRequest.created_at >= floor)
    mrs = (
        await session.execute(
            select(MergeRequest).where(*where).order_by(MergeRequest.updated_at.desc()).limit(limit)
        )
    ).scalars()
    return [mr.gitlab_iid for mr in mrs]


async def _recently_analyzed(
    session: Any, p_uuid: uuid.UUID, mr_iid: int, cache_hours: int
) -> bool:
    existing = (
        await session.execute(
            select(LLMAnalysisLog)
            .where(
                LLMAnalysisLog.project_id == p_uuid,
                LLMAnalysisLog.mr_iid == mr_iid,
            )
            .order_by(LLMAnalysisLog.analysis_timestamp.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return bool(
        existing and existing.analysis_timestamp > datetime.now(UTC) - timedelta(hours=cache_hours)
    )


async def _analyze_one(
    service: Any, p_uuid: uuid.UUID, mr_iid: int, tally: _Tally, cache_hours: int
) -> None:
    """One MR, unless analysed within the cache window, in a session of its
    own: a failure (and its rollback) cannot contaminate the connection the
    next MR uses (the MissingGreenlet fix)."""
    tally.report(mr_iid)
    try:
        async with async_session_ctx() as mr_session:
            if await _recently_analyzed(mr_session, p_uuid, mr_iid, cache_hours):
                logger.debug("skipping_recent_analysis", mr_iid=mr_iid)
                tally.skipped += 1
                tally.report(mr_iid)
                return

            analysis_result = await service.analyze_mr(mr_session, p_uuid, mr_iid)
            if analysis_result:
                tally.analyzed += 1
                logger.info(
                    "mr_analyzed",
                    mr_iid=mr_iid,
                    confidence=analysis_result.confidence_score,
                )
            else:
                tally.failed += 1
                logger.warning("analysis_returned_none", mr_iid=mr_iid)
            tally.report(mr_iid)
    except Exception as exc:
        tally.failed += 1
        error_type, error_message = classify_llm_error(exc)
        tally.errors.append(
            {
                "mr_iid": mr_iid,
                "error_type": error_type.value,
                "error_message": error_message,
                "exception": type(exc).__name__,
                "detail": str(exc)[:500],
            }
        )
        logger.exception(
            "analysis_failed",
            mr_iid=mr_iid,
            error_type=error_type.value,
            error=str(exc),
        )
        tally.report(mr_iid)


async def _store_failure_summary(p_uuid: uuid.UUID, model: str, tally: _Tally) -> None:
    """When every analysed MR failed: one error entry for display - the shared
    error, or "different errors"."""
    errors = tally.errors
    error_types = {e["error_type"] for e in errors}
    if len(error_types) == 1:
        rep_type = error_types.pop()
        rep_msg = errors[0]["error_message"]
    else:
        rep_type = "multiple_errors"
        rep_msg = f"{len(errors)} MRs failed with different errors"
    try:
        async with async_session_ctx() as err_session:
            err_session.add(
                LLMAnalysisLog(
                    project_id=p_uuid,
                    mr_iid=None,
                    target_type="error",
                    model_used=model,
                    structured_result={
                        "error_type": rep_type,
                        "error_message": rep_msg,
                        "is_error": True,
                        "failed_count": tally.failed,
                        "errors": errors,
                    },
                    risk_score=None,
                )
            )
    except Exception:
        logger.warning(
            "failed_to_save_error_entry",
            project_id=tally.project_id,
            exc_info=True,
        )


async def _analyze_project_mrs_async(project_id: str | uuid.UUID) -> dict[str, Any]:
    settings = get_settings()
    if not settings.llm_analysis_enabled:
        logger.warning("LLM feature disabled, skipping analysis")
        return {"analyzed": 0, "skipped": 0, "failed": 0, "reason": "feature_disabled"}

    # Handle both UUID objects and string UUIDs
    p_uuid = project_id if isinstance(project_id, uuid.UUID) else uuid.UUID(project_id)
    init_engine(str(settings.database_url))

    try:
        async with async_session_ctx() as session:
            project = await session.get(GitLabProject, p_uuid)
            if not project:
                logger.error("project_not_found", project_id=project_id)
                return {"analyzed": 0, "skipped": 0, "failed": 1, "reason": "project_not_found"}

            course = await _project_course(session, project)
            if course and not course.is_active:
                logger.info(
                    "Skipping LLM analysis for archived course (project=%s)",
                    project_id,
                )
                return {"analyzed": 0, "skipped": 0, "failed": 0, "reason": "course_archived"}

            mr_iids = await _recent_mr_iids(session, p_uuid, course, settings.llm_analysis_max_mrs)
            if not mr_iids:
                logger.info("no_mrs_found", project_id=project_id)
                # Store informational note
                session.add(
                    LLMAnalysisLog(
                        project_id=p_uuid,
                        mr_iid=None,
                        target_type="error",
                        model_used=settings.llm_model,
                        structured_result={
                            "error_type": LLMErrorType.NO_MRS.value,
                            "error_message": "No merge requests to analyze. Create some MRs first.",
                            "is_error": True,
                        },
                        risk_score=None,
                    )
                )
                await session.commit()
                return {"analyzed": 0, "skipped": 0, "failed": 0, "reason": "no_mrs"}

            from app.services.llm.service import LLMService

            service = LLMService(settings)
            _pid = str(p_uuid)
            tally = _Tally(_pid, len(mr_iids))
            tally.report()
            for mr_iid in mr_iids:
                await _analyze_one(
                    service, p_uuid, mr_iid, tally, settings.llm_analysis_cache_hours
                )

            # Publish final completion event via Redis pub/sub for SSE
            from app.workers.progress import publish_progress as _pub

            analyzed, skipped, failed = tally.analyzed, tally.skipped, tally.failed
            _pub(
                job_id=f"llm-{_pid}",
                status="completed" if analyzed > 0 or (failed == 0 and skipped > 0) else "failed",
                message=f"Analysis done: {analyzed} analyzed, {skipped} skipped, {failed} failed",
                extra={
                    "analyzed": analyzed,
                    "skipped": skipped,
                    "failed": failed,
                    "total": tally.total,
                },
                llm_project_id=_pid,
            )

            if failed > 0 and analyzed == 0 and tally.errors:
                await _store_failure_summary(p_uuid, settings.llm_model, tally)

            return {
                "analyzed": analyzed,
                "skipped": skipped,
                "failed": failed,
                "project_id": str(p_uuid),
                "errors": tally.errors or None,
            }
    finally:
        await dispose_engine()
