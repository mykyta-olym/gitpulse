"""Health, readiness, liveness, and Prometheus metrics endpoints.

Production-grade health check implementation with:
- Async Redis checks (no event loop blocking)
- Per-component timeouts with asyncio.wait_for
- Overall request timeout guard
- Human-readable uptime
- Readiness probe checks both DB and Redis
- Structured Pydantic responses everywhere
"""

import asyncio
import json
import socket
import time
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import uuid4

import structlog
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST
from sqlalchemy import text as sa_text

from app.config import get_settings
from app.db.session import get_engine
from app.observability.metrics import (
    APP_INFO,
    collect_db_pool_metrics,
    collect_rq_queue_metrics,
    render_latest,
)
from app.schemas.common import StatusResponse
from app.schemas.health import (
    ComponentHealth,
    ComponentStatus,
    HealthResponse,
    OverallStatus,
    ReadinessResponse,
)

logger = structlog.get_logger(__name__)
health_router = APIRouter()

_start_time = time.monotonic()

# Per-component check timeout (seconds)
_COMPONENT_TIMEOUT = 5.0
# Overall health endpoint timeout (seconds)
_OVERALL_TIMEOUT = 12.0

# Set app info once at import
APP_INFO.labels(version=get_settings().app_version, service="gitpulse").set(1)


def _format_uptime(seconds: float) -> str:
    """Convert seconds to human-readable uptime string."""
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


async def _check_database() -> ComponentHealth:
    """Check database connectivity with timeout."""
    try:
        engine = get_engine()
        start = time.perf_counter()
        async with asyncio.timeout(_COMPONENT_TIMEOUT), engine.connect() as conn:
            result = await conn.execute(sa_text("SELECT 1"))
            result.close()
        latency = (time.perf_counter() - start) * 1000

        # Gather pool stats
        pool = engine.pool
        details: dict[str, str | int | float | bool | None] = {}
        if hasattr(pool, "size"):
            details["pool_size"] = pool.size()
        if hasattr(pool, "checkedin"):
            details["pool_idle"] = pool.checkedin()
        if hasattr(pool, "checkedout"):
            details["pool_active"] = pool.checkedout()
        if hasattr(pool, "overflow"):
            details["pool_overflow"] = max(0, pool.overflow())

        return ComponentHealth(
            status=ComponentStatus.OK,
            latency_ms=round(latency, 2),
            details=details or None,
        )
    except TimeoutError:
        return ComponentHealth(
            status=ComponentStatus.ERROR,
            error=f"Database check timed out after {_COMPONENT_TIMEOUT}s",
        )
    except Exception as exc:
        return ComponentHealth(status=ComponentStatus.ERROR, error=str(exc))


async def _check_redis() -> ComponentHealth:
    """Check Redis connectivity using async client with timeout."""
    settings = get_settings()
    try:
        from redis.asyncio import Redis as AsyncRedis

        start = time.perf_counter()
        r = AsyncRedis.from_url(str(settings.redis_url), decode_responses=True)
        try:
            await asyncio.wait_for(r.ping(), timeout=_COMPONENT_TIMEOUT)
            latency = (time.perf_counter() - start) * 1000

            # Gather server, client and memory info in one round-trip
            details: dict[str, str | int | float | bool | None] = {}
            try:
                info = await asyncio.wait_for(r.info(), timeout=2.0)
                details["redis_version"] = info.get("redis_version", "unknown")
                details["connected_clients"] = info.get("connected_clients")
                details["used_memory_human"] = info.get("used_memory_human")
            except Exception:
                logger.debug("redis_info_unavailable")  # Non-critical

            return ComponentHealth(
                status=ComponentStatus.OK,
                latency_ms=round(latency, 2),
                details=details or None,
            )
        finally:
            await r.aclose()
    except TimeoutError:
        return ComponentHealth(
            status=ComponentStatus.ERROR,
            error=f"Redis check timed out after {_COMPONENT_TIMEOUT}s",
        )
    except Exception as exc:
        return ComponentHealth(status=ComponentStatus.ERROR, error=str(exc))


async def _check_session_store_probe() -> ComponentHealth:
    """Short Redis write/read probe for the server-side session store."""
    settings = get_settings()
    try:
        from redis.asyncio import Redis as AsyncRedis

        start = time.perf_counter()
        r = AsyncRedis.from_url(str(settings.redis_url))
        key = f"{settings.session_redis_key_prefix}readiness:{uuid4()}"
        value = b"ok"
        try:
            await asyncio.wait_for(r.set(key, value, ex=5), timeout=2.0)
            got = await asyncio.wait_for(r.get(key), timeout=2.0)
            await asyncio.wait_for(r.delete(key), timeout=2.0)
            if got not in {value, "ok"}:
                return ComponentHealth(
                    status=ComponentStatus.ERROR,
                    error="Session store probe readback mismatch",
                )
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(status=ComponentStatus.OK, latency_ms=round(latency, 2))
        finally:
            await r.aclose()
    except TimeoutError:
        return ComponentHealth(status=ComponentStatus.ERROR, error="Session store probe timed out")
    except Exception as exc:
        return ComponentHealth(status=ComponentStatus.ERROR, error=str(exc))


async def _check_gitlab() -> ComponentHealth:
    """Check GitLab API reachability. Informational: never flips overall status
    (a dead token or a GitLab blip must not mark the whole app unhealthy)."""
    settings = get_settings()
    if not settings.gitlab_api_token:
        return ComponentHealth(status=ComponentStatus.DEGRADED, error="No API token configured")
    try:
        import httpx

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=_COMPONENT_TIMEOUT, trust_env=False) as client:
            resp = await client.get(
                f"{settings.gitlab_url.rstrip('/')}/api/v4/version",
                headers={"PRIVATE-TOKEN": settings.gitlab_api_token},
            )
        latency = round((time.perf_counter() - start) * 1000, 2)
        if resp.status_code == 200:
            details: dict[str, str | int | float | bool | None] = {}
            with suppress(Exception):
                details["gitlab_version"] = resp.json().get("version")
            return ComponentHealth(
                status=ComponentStatus.OK, latency_ms=latency, details=details or None
            )
        return ComponentHealth(
            status=ComponentStatus.DEGRADED,
            latency_ms=latency,
            error=f"HTTP {resp.status_code}",
        )
    except Exception as exc:
        return ComponentHealth(status=ComponentStatus.ERROR, error=str(exc)[:200])


async def _check_smtp() -> ComponentHealth:
    """Check SMTP TCP reachability. Informational: never flips overall status."""
    settings = get_settings()
    if not settings.smtp_host:
        return ComponentHealth(status=ComponentStatus.DEGRADED, error="Not configured")

    def _probe() -> None:

        sock = socket.create_connection(
            (settings.smtp_host, settings.smtp_port), timeout=_COMPONENT_TIMEOUT
        )
        sock.close()

    try:
        start = time.perf_counter()
        await asyncio.wait_for(asyncio.to_thread(_probe), timeout=_COMPONENT_TIMEOUT + 1)
        latency = round((time.perf_counter() - start) * 1000, 2)
        return ComponentHealth(
            status=ComponentStatus.OK,
            latency_ms=latency,
            details={"endpoint": f"{settings.smtp_host}:{settings.smtp_port}"},
        )
    except Exception as exc:
        return ComponentHealth(status=ComponentStatus.ERROR, error=str(exc)[:200])


def _resolve_overall(components: dict[str, ComponentHealth]) -> OverallStatus:
    """Determine overall status from component statuses."""
    statuses = {c.status for c in components.values()}
    if all(s == ComponentStatus.OK for s in statuses):
        return OverallStatus.OK
    if ComponentStatus.ERROR in statuses:
        # If ALL components are down, overall is DOWN
        if all(s == ComponentStatus.ERROR for s in statuses):
            return OverallStatus.DOWN
        return OverallStatus.DEGRADED
    return OverallStatus.DEGRADED


# Short-lived cache for the full health payload.
#
# The browser health monitor polls this endpoint from EVERY page, and the check
# includes a live GitLab API round-trip. Measured across the dashboard it was
# the slowest call on nearly every page (660-1730 ms), and it put one outbound
# GitLab request on every page view of every user. The information does not
# change meaningfully within a few seconds, so serving a recent result collapses
# that entirely while the banner it feeds stays just as current.
T = TypeVar("T")


class _Recent(Generic[T]):
    """The last answer, served again while it is younger than ``ttl_s``."""

    def __init__(self, ttl_s: float) -> None:
        self.ttl_s = ttl_s
        self._value: T | None = None
        self._at = 0.0
        self._lock = asyncio.Lock()

    def get(self) -> T | None:
        if self._value is not None and time.monotonic() - self._at < self.ttl_s:
            return self._value
        return None

    def set(self, value: T) -> T:
        self._value, self._at = value, time.monotonic()
        return value

    async def get_or_compute(
        self,
        compute: Callable[[], Awaitable[T]],
        *,
        force: bool = False,
    ) -> T:
        if not force:
            cached = self.get()
            if cached is not None:
                return cached
        async with self._lock:
            if not force:
                cached = self.get()
                if cached is not None:
                    return cached
            return self.set(await compute())


_HEALTH_CACHE_TTL_S = 10.0
_recent_health: _Recent[HealthResponse] = _Recent(_HEALTH_CACHE_TTL_S)


async def _compute_health_report() -> HealthResponse:
    """Run all component health probes concurrently under one overall deadline."""
    settings = get_settings()
    check_start = time.perf_counter()
    include_sessions = bool(settings.feature_redis_sessions)

    probes: list[Awaitable[ComponentHealth]] = [
        _check_database(),
        _check_redis(),
        _check_gitlab(),
        _check_smtp(),
    ]
    if include_sessions:
        probes.append(_check_session_store_probe())

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*probes, return_exceptions=False),
            timeout=_OVERALL_TIMEOUT,
        )
        db_result, redis_result, gitlab_result, smtp_result = results[:4]
        session_result = results[4] if include_sessions else None
    except TimeoutError:
        timeout_err = f"Overall health check timed out after {_OVERALL_TIMEOUT}s"
        db_result = ComponentHealth(status=ComponentStatus.ERROR, error=timeout_err)
        redis_result = ComponentHealth(status=ComponentStatus.ERROR, error=timeout_err)
        gitlab_result = ComponentHealth(status=ComponentStatus.ERROR, error=timeout_err)
        smtp_result = ComponentHealth(status=ComponentStatus.ERROR, error=timeout_err)
        session_result = (
            ComponentHealth(status=ComponentStatus.ERROR, error=timeout_err)
            if include_sessions
            else None
        )
    except Exception as exc:
        logger.error("health_check_unexpected_error", error=str(exc))
        err_msg = str(exc)
        db_result = ComponentHealth(status=ComponentStatus.ERROR, error=err_msg)
        redis_result = ComponentHealth(status=ComponentStatus.ERROR, error=err_msg)
        gitlab_result = ComponentHealth(status=ComponentStatus.ERROR, error=err_msg)
        smtp_result = ComponentHealth(status=ComponentStatus.ERROR, error=err_msg)
        session_result = (
            ComponentHealth(status=ComponentStatus.ERROR, error=err_msg)
            if include_sessions
            else None
        )

    core_components: dict[str, ComponentHealth] = {
        "database": db_result,
        "redis": redis_result,
    }
    if session_result is not None:
        core_components["session_store"] = session_result
    # Overall status is derived from CORE components only.
    overall = _resolve_overall(core_components)

    # External dependencies (GitLab, SMTP) are surfaced in System Health + Raw JSON
    # for ops visibility, but they never flip the overall status.
    components = {
        **core_components,
        "gitlab": gitlab_result,
        "smtp": smtp_result,
    }
    checks_duration = (time.perf_counter() - check_start) * 1000
    uptime = time.monotonic() - _start_time

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.app_env.value,
        uptime_seconds=round(uptime, 1),
        uptime_human=_format_uptime(uptime),
        components=components,
        timestamp=datetime.now(UTC),
        checks_duration_ms=round(checks_duration, 2),
    )


async def get_health_report(*, force: bool = False) -> HealthResponse:
    """Return the recent health report, or run a fresh probe when ``force`` is True."""
    return await _recent_health.get_or_compute(_compute_health_report, force=force)


@health_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Full health check - verifies DB and Redis connectivity.

    Returns per-component latency, pool stats, and overall status.
    Aborts if total check time exceeds the overall timeout.

    Cached for a few seconds - see ``_HEALTH_CACHE_TTL_S``. Liveness and
    readiness probes are separate endpoints and are never cached.
    """
    return await get_health_report(force=False)


@health_router.get("/health/live", response_model=StatusResponse)
async def liveness() -> StatusResponse:
    """Liveness probe - always returns OK if the process is running."""
    return StatusResponse(status="alive")


@health_router.get("/health/ready", response_model=ReadinessResponse)
async def readiness() -> Response:
    """Readiness probe - checks if DB and Redis are reachable.

    Returns 503 if any critical dependency is unavailable.
    """
    component_status: dict[str, str] = {}
    all_ready = True

    # Database
    try:
        engine = get_engine()
        async with asyncio.timeout(_COMPONENT_TIMEOUT), engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
        component_status["database"] = "ready"
    except Exception as exc:
        logger.error("readiness_db_failed", error=str(exc))
        component_status["database"] = "not_ready"
        all_ready = False

    # Redis
    try:
        from redis.asyncio import Redis as AsyncRedis

        settings = get_settings()
        r = AsyncRedis.from_url(str(settings.redis_url))
        try:
            await asyncio.wait_for(r.ping(), timeout=_COMPONENT_TIMEOUT)
            component_status["redis"] = "ready"
        finally:
            await r.aclose()
    except Exception as exc:
        logger.error("readiness_redis_failed", error=str(exc))
        component_status["redis"] = "not_ready"
        all_ready = False

    if get_settings().feature_redis_sessions:
        session_probe = await _check_session_store_probe()
        if session_probe.status == ComponentStatus.OK:
            component_status["session_store"] = "ready"
        else:
            logger.error("readiness_session_store_failed", error=session_probe.error)
            component_status["session_store"] = "not_ready"
            all_ready = False

    resp = ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        reason=None if all_ready else "One or more dependencies unavailable",
        components=component_status,
    )

    status_code = 200 if all_ready else 503
    return Response(
        content=resp.model_dump_json(),
        status_code=status_code,
        media_type="application/json",
    )


@health_router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Prometheus scrape endpoint.

    Collects DB pool and RQ queue metrics on each scrape.
    """
    collect_db_pool_metrics()
    collect_rq_queue_metrics()

    return Response(
        content=render_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Same reasoning as the /health cache: this fires from every page to drive the
# "GitLab unreachable" banner, and each call is an outbound round-trip to
# GitLab. Measured at ~640 ms and, once /health was cached, it became the
# slowest call on nearly every page. Connectivity does not change second to
# second, so a recent answer is just as truthful.
_GITLAB_HEALTH_TTL_S = 15.0
_recent_gitlab_health: _Recent[tuple[bytes, int]] = _Recent(_GITLAB_HEALTH_TTL_S)


@health_router.get("/health/gitlab")
async def gitlab_health() -> Response:
    """Connectivity probe: HTTP 503 when GitLab cannot be reached.

    Cached briefly - see ``_GITLAB_HEALTH_TTL_S``.
    """

    import httpx

    async def _probe_gitlab() -> tuple[bytes, int]:
        settings = get_settings()
        gitlab_url = str(settings.gitlab_url).rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
                resp = await client.get(f"{gitlab_url}/users/sign_in")
                if 200 <= resp.status_code < 400:
                    return json.dumps({"status": "ok", "gitlab_url": gitlab_url}).encode(), 200
                return (
                    json.dumps({"status": "error", "detail": f"HTTP {resp.status_code}"}).encode(),
                    503,
                )
        except (httpx.RequestError, TimeoutError) as exc:
            return json.dumps({"status": "unreachable", "detail": str(exc)}).encode(), 503

    body, status = await _recent_gitlab_health.get_or_compute(_probe_gitlab)
    return Response(content=body, status_code=status, media_type="application/json")


@health_router.get("/health/gitlab/status")
async def gitlab_status() -> Response:
    """Return the cached connectivity report for the UI, including outage states.

    Reading the report succeeds even when GitLab is down. Monitoring clients
    use /health/gitlab, which retains its HTTP 503 failure signal.
    """
    report = await gitlab_health()
    return Response(content=report.body, media_type="application/json")
