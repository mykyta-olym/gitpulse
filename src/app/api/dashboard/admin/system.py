"""Admin system health, monitoring, background jobs and deployment configuration."""

import asyncio
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func as sa_func
from sqlalchemy import select

from app.api.dashboard._helpers import (
    _csrf_token,
    _role_context,
    _templates,
    logger,
)
from app.api.health import _format_uptime, get_health_report
from app.config import get_settings
from app.dependencies import AdminAuth, CSRFCheck, DbSession, RateLimitDep
from app.i18n import resolve_locale, translate_text
from app.i18n.job_messages import METADATA
from app.i18n.job_messages import label as job_label
from app.i18n.job_messages import message as job_message
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.team import Team
from app.observability import insights, job_diagnostics
from app.redis_pool import get_redis as _pool_get_redis
from app.schemas.health import ComponentHealth, HealthResponse
from app.services.job_history import delete_job_history
from app.template_helpers import local_time

router = APIRouter()


_TERMINAL_JOB_STATUSES = ("completed", "failed", "cancelled")

_COMPONENT_META: dict[str, tuple[str, str]] = {
    "database": ("Database", "database"),
    "redis": ("Redis", "server"),
    "session_store": ("Sessions", "key"),
    "gitlab": ("GitLab", "gitlab"),
    "smtp": ("Email", "mail"),
}
_COMPONENT_ORDER = ("database", "redis", "session_store", "gitlab", "smtp")


def _format_latency(ms: float | None) -> str:
    if ms is None:
        return "-"
    if ms < 1:
        return "< 1 ms"
    if ms < 1000:
        return f"{ms:.1f} ms"
    return f"{ms / 1000:.2f} s"


def _health_signature(report: HealthResponse) -> str:
    parts = [
        f"{name}:{comp.status}:{comp.error or ''}"
        for name, comp in sorted(report.components.items())
    ]
    return f"{report.status}|{'|'.join(parts)}"


def _component_details_text(
    name: str,
    comp: ComponentHealth,
    t: Any,
) -> str:
    details = comp.details or {}
    if name == "database" and details:
        size = details.get("pool_size")
        if size is not None:
            active = details.get("pool_active", 0)
            idle = details.get("pool_idle", 0)
            overflow = details.get("pool_overflow", 0)
            return (
                f"{t('Pool')}: {size} "
                f"({active} {t('active')}, {idle} {t('idle')}, {overflow} {t('overflow')})"
            )
    if name == "redis" and details:
        parts: list[str] = []
        if details.get("redis_version"):
            parts.append(f"Redis {details['redis_version']}")
        if details.get("connected_clients") is not None:
            parts.append(f"{details['connected_clients']} {t('clients')}")
        if details.get("used_memory_human"):
            parts.append(f"{details['used_memory_human']} {t('memory')}")
        if parts:
            return ", ".join(parts)
    if name in {"session_store", "sessions"}:
        if details.get("note"):
            note = str(t(str(details["note"])))
            return f"Redis ({note})" if details.get("backend") == "redis" else note
        if comp.status == "ok" and not details and not comp.error:
            return str(t("Server-side session read/write verified"))
    if name == "gitlab" and details.get("gitlab_version"):
        return f"GitLab {details['gitlab_version']}"
    if name in {"smtp", "email"} and details.get("endpoint"):
        return str(details["endpoint"])
    fallback = [
        f"{key.replace('_', ' ')}: {val}"
        for key, val in details.items()
        if val is not None and val != ""
    ]
    return ", ".join(fallback)


def _health_context(request: Request, report: HealthResponse) -> dict[str, Any]:
    """Prepare the server-rendered System Health KPI and component table context."""
    locale = resolve_locale(request)

    def t(value: str) -> str:
        return translate_text(locale, value)

    status = str(report.status)
    # Readiness concerns core services; this card summarizes every displayed check.
    if status == "ok" and any(str(c.status) != "ok" for c in report.components.values()):
        status = "degraded"
    overall_map: dict[str, tuple[str, str, str]] = {
        "ok": (t("All systems operational"), "check-circle", "success"),
        "degraded": (t("Some components are degraded"), "alert-triangle", "warning"),
        "down": (t("System is unavailable"), "x-circle", "danger"),
    }
    status_summary, status_icon, status_state = overall_map.get(
        status,
        (status, "alert-triangle", "warning"),
    )
    comp_status_map: dict[str, tuple[str, str]] = {
        "ok": (t("Operational"), "success"),
        "degraded": (t("Degraded"), "warning"),
        "error": (t("Down"), "danger"),
    }

    ordered_keys = [k for k in _COMPONENT_ORDER if k in report.components] + [
        k for k in report.components if k not in _COMPONENT_ORDER
    ]
    components: list[dict[str, Any]] = []
    for key in ordered_keys:
        comp = report.components[key]
        raw_label, icon_name = _COMPONENT_META.get(
            key, (key.replace("_", " ").capitalize(), "server")
        )
        c_label, c_variant = comp_status_map.get(str(comp.status), (str(comp.status), "danger"))
        components.append(
            {
                "key": key,
                "label": t(raw_label),
                "icon": icon_name,
                "status_label": c_label,
                "badge_variant": c_variant,
                "latency_label": _format_latency(comp.latency_ms),
                "details_text": _component_details_text(key, comp, t),
                "error": t(comp.error) if comp.error else "",
            }
        )

    ok_count = sum(1 for c in report.components.values() if str(c.status) == "ok")
    total_count = len(report.components)
    healthy_ratio = f"{ok_count} / {total_count}" if total_count else "0 / 0"
    status_desc = (
        f"{status_summary} ({report.checks_duration_ms:.1f} ms)"
        if report.checks_duration_ms and report.checks_duration_ms > 0
        else status_summary
    )
    env_label = f"{t('Environment')}: {report.environment}" if report.environment else ""
    return {
        "status": status,
        "healthy_ratio": healthy_ratio,
        "status_desc": status_desc,
        "status_icon": status_icon,
        "status_state": status_state,
        "uptime_human": report.uptime_human or _format_uptime(report.uptime_seconds),
        "environment_label": env_label,
        "version": report.version,
        "python_label": f"Python {sys.version.split()[0]}",
        "timestamp": report.timestamp,
        "signature": _health_signature(report),
        "components": components,
    }


def _queue_status_text(request: Request, snapshot: dict[str, Any] | None) -> str:
    """Format the live RQ queue summary identically to 10-stats.js."""
    locale = resolve_locale(request)

    def t(value: str) -> str:
        return translate_text(locale, value)

    if snapshot is None:
        return t("Queue status is temporarily unavailable.")
    queues = snapshot.get("queues") or {}
    summary = ", ".join(f"{name}: {queues.get(name, 0)}" for name in ("high", "default", "low"))
    workers = snapshot.get("workers")
    workers_text = workers if workers is not None else "-"
    base = f"{t('Queued jobs')}: {summary}. {t('Workers online')}: {workers_text}."
    if workers == 0:
        return f"{base} {t('No active workers; queued jobs will wait.')}"
    return base


def _jobs_table_context(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
    """Prepare one presentation for the initial table and every later response."""
    locale = resolve_locale(request)

    def t(value: str) -> str:
        return translate_text(locale, value)

    rows = []
    for job in payload["jobs"]:
        row = dict(job)
        diagnostic = row.get("diagnostic", {})
        row["type_label"] = (
            t(
                {"project": "Project sync", "course": "Course sync", "group": "Group sync"}.get(
                    row.get("scope") or "", "GitLab sync"
                )
            )
            if row["job_type"] == "sync"
            else job_label(row["job_type"], t)
        )
        row["description"] = t(METADATA["descriptions"].get(row["job_type"], ""))
        row["message"] = job_message(row.get("error_message") or row.get("result_summary") or "", t)
        row["status_variant"] = {
            "completed": "success",
            "running": "info",
            "started": "info",
            "failed": "danger",
            "enqueued": "muted",
            "cancelled": "warning",
        }.get(row["status"], "muted")
        row["active"] = row["status"] not in _TERMINAL_JOB_STATUSES
        row["times"] = {
            key: datetime.fromisoformat(row[key]) if row.get(key) else None
            for key in ("enqueued_at", "started_at", "completed_at", "last_activity")
        }
        cause_text = t(diagnostic.get("cause", "")) if diagnostic.get("cause") else ""
        row["facts"] = [
            {
                "label": t("Enqueued"),
                "html": local_time(row["times"]["enqueued_at"])
                if row["times"]["enqueued_at"] and not row.get("read_only")
                else "",
            },
            {
                "label": t("Started"),
                "html": local_time(row["times"]["started_at"])
                if row["times"]["started_at"]
                else "",
            },
            {
                "label": t("Completed"),
                "html": local_time(row["times"]["completed_at"])
                if row["times"]["completed_at"]
                else "",
            },
            {"label": "RQ ID", "text": row.get("rq_job_id") or ""},
            {
                "label": t("Result / Error"),
                "text": row["message"]
                if len(row["message"]) > 180 or "\n" in row["message"]
                else "",
            },
            {
                "label": t("Cause"),
                "text": cause_text if cause_text != row["message"] else "",
            },
            {"label": t("Details"), "text": t(diagnostic.get("hint", ""))},
            {"label": t("Diagnostic reference"), "text": diagnostic.get("reference", "")},
        ]
        row["facts"] = [fact for fact in row["facts"] if fact.get("html") or fact.get("text")]
        rows.append(row)
    return {
        "jobs": rows,
        "failure_history": payload["failure_history"],
        "job_type_options": [(key, job_label(key, t)) for key in payload["job_types"]],
        "selectable_jobs": any(not row.get("read_only") and not row["active"] for row in rows),
    }


def _job_op_row(
    j: BackgroundJob,
    team_names: dict[uuid.UUID, str],
    course_names: dict[uuid.UUID, str],
) -> dict[str, Any]:
    """Serialize a BackgroundJob to the Job History row shape."""
    last_ts = j.completed_at or j.started_at or j.enqueued_at
    return {
        "id": str(j.id),
        "job_type": j.job_type,
        "rq_job_id": j.rq_job_id,
        "status": j.status,
        "team_id": str(j.team_id) if j.team_id else None,
        "team_name": team_names.get(j.team_id) if j.team_id else None,
        "course_id": str(j.course_id) if j.course_id else None,
        "course_name": course_names.get(j.course_id) if j.course_id else None,
        "project_id": str(j.project_id) if j.project_id else None,
        "scope": _background_job_scope(j),
        "result_summary": (j.result_summary or "")[:500],
        "enqueued_at": j.enqueued_at.isoformat() if j.enqueued_at else None,
        "last_activity": last_ts.isoformat() if last_ts else None,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        "duration_ms": j.duration_ms,
        "error_message": (j.error_message or "")[:500],
    }


def _background_job_scope(job: BackgroundJob) -> str | None:
    """Return the user-visible scope for a sync job."""
    if job.job_type != "sync":
        return None
    if job.project_id:
        return "project"
    if job.course_id:
        return "course"
    if job.team_id:
        return "group"
    return None


@router.get("/admin/system", response_class=HTMLResponse)
async def admin_system_page(request: Request, db: DbSession, auth: AdminAuth) -> Response:
    """Admin page showing feature flags, LLM config and runtime info."""
    settings = get_settings()

    # Build feature-flag list from settings
    feature_flags = []
    for field_name in sorted(dir(settings)):
        if field_name.startswith("feature_"):
            # Read from the CLASS: instance access to `model_fields` is
            # deprecated in Pydantic 2.11 and removed in V3, where this line
            # would start raising and take the whole admin page with it.
            field_info = type(settings).model_fields.get(field_name)
            description = field_info.description if field_info else ""
            enabled = (
                settings.llm_analysis_enabled
                if field_name == "feature_llm_suggestions"
                else getattr(settings, field_name, False)
            )
            feature_flags.append(
                {
                    "key": field_name,
                    "enabled": enabled,
                    "description": description,
                },
            )

    # LLM config (safe subset - no raw key)
    api_key_hint = settings.llm_api_key[-4:] if len(settings.llm_api_key) >= 4 else ""
    llm_config = {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "max_tokens": settings.llm_max_tokens,
        "debug": settings.llm_debug_mode,
        "api_key_hint": api_key_hint,
        "enabled": settings.llm_analysis_enabled,
    }

    runtime = {
        "python_version": sys.version.split()[0],
        "debug": settings.debug,
        "base_url": settings.app_base_url,
    }

    async def _safe_queue_snapshot() -> dict[str, Any] | None:
        try:
            return await asyncio.wait_for(asyncio.to_thread(_queue_snapshot), timeout=2)
        except Exception:
            logger.debug("initial_queue_status_unavailable", exc_info=True)
            return None

    # Render all sections on the first frame with the same partials used for refresh.
    health_report, failures, monitoring, queue_snap = await asyncio.gather(
        get_health_report(force=False),
        job_diagnostics.snapshot(),
        insights.snapshot(),
        _safe_queue_snapshot(),
    )
    page_size = auth.get("default_page_size", "50")
    page_size = page_size if page_size in ("25", "50", "100", "all") else "50"
    jobs_first_page = await build_jobs_payload(
        db, None, None, 500 if page_size == "all" else int(page_size), 0, failures=failures
    )
    return _templates(request).TemplateResponse(
        request,
        "admin_system.html",
        {
            "request": request,
            "health": _health_context(request, health_report),
            "queue_status_text": _queue_status_text(request, queue_snap),
            "queue_workers_zero": bool(queue_snap and queue_snap.get("workers") == 0),
            "feature_flags": feature_flags,
            "llm_config": llm_config,
            "runtime": runtime,
            "jobs_first_page_json": jobs_first_page,
            "jobs_page_size": "all" if page_size == "all" else int(page_size),
            **_jobs_table_context(request, jobs_first_page),
            "monitoring_enabled": settings.monitoring_enabled,
            "monitoring": monitoring,
            "series": insights.series_rows(monitoring),
            "csrf_token": _csrf_token(auth),
            **_role_context(auth),
        },
        headers={"Cache-Control": "no-store"},
    )


@router.get("/api/v1/admin/system/health", response_class=HTMLResponse)
async def admin_system_health(request: Request, _auth: AdminAuth) -> Response:
    """Refresh the System Health section with the same partial as the initial page."""
    fresh = request.query_params.get("fresh") == "1"
    report = await get_health_report(force=fresh)
    health_ctx = _health_context(request, report)
    return _templates(request).TemplateResponse(
        request,
        "partials/admin/_system_health.html",
        {"health": health_ctx},
        headers={
            "Cache-Control": "no-store",
            "X-Health-Status": health_ctx["status"],
        },
    )


@router.get("/api/v1/admin/system/monitoring", response_class=HTMLResponse)
async def admin_system_monitoring(request: Request, _auth: AdminAuth) -> Response:
    """Refresh the monitoring section with the same template as the initial page."""
    fresh = request.query_params.get("fresh") == "1"
    monitoring = await insights.snapshot(force=fresh)
    return _templates(request).TemplateResponse(
        request,
        "partials/admin/_system_monitoring.html",
        {
            "monitoring": monitoring,
            "series": insights.series_rows(monitoring),
            "monitoring_enabled": get_settings().monitoring_enabled,
        },
        status_code=503 if monitoring.configured and not monitoring.reachable else 200,
        headers={"Cache-Control": "no-store"},
    )


def _queue_snapshot() -> dict[str, Any]:
    """Read the actual RQ queues and live workers, outside the event loop."""
    from rq import Queue
    from rq.worker import Worker

    connection = _pool_get_redis()
    return {
        "queues": {
            name: len(Queue(name, connection=connection)) for name in ("high", "default", "low")
        },
        "workers": len(Worker.all(connection=connection)),
    }


@router.get("/api/v1/admin/system/stats", response_class=JSONResponse)
async def admin_system_stats(_auth: AdminAuth) -> Response:
    """Queue depths and live worker count; domain totals belong to their pages."""
    try:
        snapshot = await asyncio.wait_for(asyncio.to_thread(_queue_snapshot), timeout=3)
    except Exception:
        logger.warning("RQ status unavailable", exc_info=True)
        return JSONResponse(
            {"status": "unavailable", "queues": {}, "workers": None}, status_code=503
        )
    return JSONResponse({"status": "ok", **snapshot})


@router.get("/api/v1/admin/system/llm-status", response_class=JSONResponse)
async def admin_llm_status(_auth: AdminAuth) -> Response:
    """Check LLM provider status: key validity, model availability, balance (if supported)."""
    settings = get_settings()

    if not settings.llm_analysis_enabled:
        return JSONResponse({"status": "disabled", "message": "LLM feature is disabled"})

    if not settings.llm_api_key:
        return JSONResponse({"status": "error", "message": "API key is not set"})

    provider = settings.llm_provider
    result: dict[str, object] = {"status": "ok", "provider": provider, "model": settings.llm_model}

    try:
        if provider in ("openai", "azure", "groq"):
            import openai

            default_base = "https://api.groq.com/openai/v1" if provider == "groq" else None
            client = openai.AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_api_base_url or default_base,
            )
            try:
                models = await client.models.list()
                model_ids = [m.id for m in models.data[:50]]
                result["available_models"] = len(models.data)
                result["model_available"] = settings.llm_model in model_ids
            finally:
                await client.close()

        elif provider == "gemini":
            from google import genai

            genai.Client(api_key=settings.llm_api_key)  # validates key
            result["model_available"] = True  # Gemini doesn't expose a list_models easily

        result["message"] = "API key is valid"
    except Exception as exc:
        err_str = str(exc)
        if "401" in err_str or "invalid" in err_str.lower() or "auth" in err_str.lower():
            result["status"] = "error"
            result["message"] = "Invalid API key"
        elif "429" in err_str or "rate" in err_str.lower() or "quota" in err_str.lower():
            result["status"] = "warning"
            result["message"] = "Rate limited or quota exceeded"
        else:
            result["status"] = "error"
            result["message"] = f"Connection error: {err_str[:200]}"

    return JSONResponse(result)


async def build_jobs_payload(
    db: Any,
    status_filter: str | None,
    type_filter: str | None,
    limit: int,
    offset: int,
    *,
    failures: job_diagnostics.FailureLog | None = None,
) -> dict[str, Any]:
    """Page tracked jobs and bounded RQ failures, once per execution.

    Skip at most the bounded RQ row count fewer SQL rows, merge that window,
    then slice. Deep pages stay bounded instead of reading the entire SQL log.
    RQ-only records are read-only and are excluded from SQL deletion controls.
    """
    failure_rows = {row["id"]: row for row in failures.rows} if failures else {}
    tracked = (
        set(
            (
                await db.execute(
                    select(BackgroundJob.rq_job_id).where(BackgroundJob.rq_job_id.in_(failure_rows))
                )
            ).scalars()
        )
        if failure_rows
        else set()
    )
    retained = [
        {
            "id": "rq-" + row["id"],
            "rq_job_id": row["id"],
            "job_type": row["function"].rsplit(".", 1)[-1],
            "status": "failed",
            "enqueued_at": row["observed_at"].isoformat() if row["observed_at"] else None,
            "duration_ms": None,
            "error_message": row["cause"],
            "read_only": True,
            "diagnostic": row,
        }
        for row in failure_rows.values()
        if row["id"] not in tracked
        and (not status_filter or status_filter == "failed")
        and (not type_filter or type_filter == row["function"].rsplit(".", 1)[-1])
    ]
    db_offset = max(0, offset - len(retained))
    conditions = []
    if status_filter:
        conditions.append(BackgroundJob.status == status_filter)
    if type_filter:
        conditions.append(BackgroundJob.job_type == type_filter)
    total = (
        await db.execute(select(sa_func.count(BackgroundJob.id)).where(*conditions))
    ).scalar() or 0
    jobs = list(
        (
            await db.execute(
                select(BackgroundJob)
                .where(*conditions)
                .order_by(
                    sa_func.coalesce(
                        BackgroundJob.completed_at,
                        BackgroundJob.started_at,
                        BackgroundJob.enqueued_at,
                    ).desc(),
                    BackgroundJob.id.desc(),
                )
                .offset(db_offset)
                .limit(limit + len(retained))
            )
        )
        .scalars()
        .all()
    )

    team_ids = {job.team_id for job in jobs if job.team_id}
    team_names = (
        dict((await db.execute(select(Team.id, Team.name).where(Team.id.in_(team_ids)))).all())
        if team_ids
        else {}
    )
    course_ids = {job.course_id for job in jobs if job.course_id}
    course_names = {}
    if course_ids:
        course_rows = (
            await db.execute(
                select(Course.id, Course.code, Course.name).where(Course.id.in_(course_ids))
            )
        ).all()
        course_names = {row[0]: f"{row[1]} - {row[2]}" if row[1] else row[2] for row in course_rows}
    job_types = (
        (
            await db.execute(
                select(BackgroundJob.job_type).distinct().order_by(BackgroundJob.job_type)
            )
        )
        .scalars()
        .all()
    )
    rows = [_job_op_row(job, team_names, course_names) for job in jobs]
    for row in rows:
        if row["rq_job_id"] in failure_rows:
            row["diagnostic"] = failure_rows[row["rq_job_id"]]
    rows += retained

    def chronological(row: dict[str, Any]) -> tuple[datetime, str]:
        raw = row.get("last_activity") or row["enqueued_at"]
        stamp = datetime.fromisoformat(raw) if raw else datetime.min.replace(tzinfo=UTC)
        return stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp, row["id"]

    rows.sort(key=chronological, reverse=True)
    # Datetimes belong only to the diagnostic reader; API rows carry ISO stamps.
    for row in rows:
        if "diagnostic" in row:
            row["diagnostic"] = {k: v for k, v in row["diagnostic"].items() if k != "observed_at"}
    return {
        "jobs": rows[offset - db_offset : offset - db_offset + limit],
        "job_types": sorted(
            set(job_types)
            | {
                row["function"].rsplit(".", 1)[-1]
                for row in failure_rows.values()
                if row["id"] not in tracked
            }
        ),
        "total": total + len(retained),
        "failure_history": {
            "available": failures.available,
            "total": failures.total,
            "limit": job_diagnostics.LIMIT,
        }
        if failures
        else None,
    }


@router.get("/api/v1/admin/system/jobs", response_class=JSONResponse)
async def admin_system_jobs(
    db: DbSession,
    _auth: AdminAuth,
    request: Request,
) -> Response:
    """Return the operations log page as JSON (see build_jobs_payload)."""
    params = request.query_params
    try:
        limit = min(max(int(params.get("limit", "100")), 1), 500)
    except (ValueError, TypeError):
        limit = 100
    try:
        offset = max(int(params.get("offset", "0")), 0)
    except (ValueError, TypeError):
        offset = 0
    payload = await build_jobs_payload(
        db,
        params.get("status"),
        params.get("type"),
        limit,
        offset,
        failures=await job_diagnostics.snapshot(),
    )
    context = _jobs_table_context(request, payload)
    templates = _templates(request)
    payload["rows_html"] = bytes(
        templates.TemplateResponse(request, "partials/admin/_system_job_rows.html", context).body
    ).decode()
    payload["history_html"] = bytes(
        templates.TemplateResponse(
            request, "partials/admin/_system_failure_info.html", context
        ).body
    ).decode()
    return JSONResponse(payload)


@router.post("/api/v1/admin/system/jobs/purge", response_class=JSONResponse)
async def admin_purge_jobs(
    request: Request,
    db: DbSession,
    _auth: AdminAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Remove terminal SQL jobs and retained RQ failures; preserve the audit."""
    body = await request.json()
    try:
        hours = int(body.get("hours", 24))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="hours must be an integer") from exc
    if not 1 <= hours <= 87600:
        raise HTTPException(status_code=400, detail="hours must be between 1 and 87600")
    status_filter = body.get("status", "both")
    if status_filter not in (*_TERMINAL_JOB_STATUSES, "both"):
        raise HTTPException(status_code=400, detail="only terminal jobs can be purged")
    # Cached older clients sent "both"; it now means background jobs only.
    if body.get("scope", "jobs") not in ("jobs", "both"):
        raise HTTPException(status_code=400, detail="only background jobs can be purged here")
    cutoff = datetime.now(UTC) - timedelta(hours=hours) if hours < 87600 else None
    conditions: list[Any] = [BackgroundJob.status.in_(_TERMINAL_JOB_STATUSES)]
    if status_filter != "both":
        conditions.append(BackgroundJob.status == status_filter)
    if cutoff is not None:
        conditions.append(
            sa_func.coalesce(
                BackgroundJob.completed_at, BackgroundJob.started_at, BackgroundJob.enqueued_at
            )
            < cutoff
        )
    counts = await delete_job_history(
        db, *conditions, cutoff=cutoff, include_failures=status_filter in ("both", "failed")
    )
    await db.commit()
    return JSONResponse({"status": "purged", **counts, "hours": hours, "scope": "jobs"})


@router.post("/api/v1/admin/system/jobs/delete", response_class=JSONResponse)
async def admin_delete_jobs(
    request: Request,
    db: DbSession,
    _auth: AdminAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> Response:
    """Delete selected terminal jobs; never delete active jobs or audit entries."""
    body = await request.json()
    ids = body.get("ids")
    if not isinstance(ids, list) or not ids or len(ids) > 1000:
        raise HTTPException(status_code=400, detail="ids must contain 1 to 1000 job UUIDs")
    try:
        job_ids = [uuid.UUID(str(value)) for value in ids]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ids must be background job UUIDs") from exc
    counts = await delete_job_history(db, BackgroundJob.id.in_(job_ids))
    await db.commit()
    return JSONResponse({"status": "deleted", **counts})


@router.post("/api/v1/admin/cache/clear", response_class=JSONResponse)
async def admin_clear_cache(_auth: AdminAuth, _csrf: CSRFCheck, _rate: RateLimitDep) -> Response:
    """Clear only cache namespaces; preserve queue, locks, metrics and sessions."""
    cleared: list[str] = []

    # 1. Clear Redis cache keys (preserve RQ jobs and other data)
    try:
        r = _pool_get_redis()
        deleted = 0
        for pattern in ("gitlab:*", "cache:*", "gp:page:*"):
            cursor = 0
            while True:
                cursor, keys = r.scan(cursor, match=pattern, count=200)
                if keys:
                    r.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
        cleared.append(f"redis:{deleted}_keys")
    except Exception:
        logger.warning("Redis cache clear failed", exc_info=True)
        raise HTTPException(status_code=503, detail="Redis cache could not be cleared") from None

    # 2. Clear Python lru_cache on get_settings
    try:
        get_settings.cache_clear()
        cleared.append("settings_cache")
    except Exception:
        logger.warning("Settings cache clear failed", exc_info=True)
        cleared.append("settings_cache:skipped")

    return JSONResponse({"cleared": cleared, "status": "ok"})
