"""Shared job-progress publisher for Redis pub/sub -> SSE bridge.

All worker jobs use this single helper to publish progress updates
so the frontend can stream live status via SSE.
"""

import json
import logging
import threading
from typing import Any

from redis import Redis

logger = logging.getLogger(__name__)

# Module-level cached Redis connection - avoids creating a new connection
# per publish call which would exhaust the Redis connection pool under load.
_redis_conn: Any = None
_redis_lock = threading.Lock()
_DASHBOARD_LIVE_CACHE_PATTERNS = ("dashboard:stats:*", "dashboard:badges:*")


def _get_publish_conn() -> Any:
    """Return a cached Redis connection for publishing, creating one if needed."""
    global _redis_conn
    if _redis_conn is not None:
        try:
            _redis_conn.ping()
            return _redis_conn
        except Exception:
            _redis_conn = None

    with _redis_lock:
        # Double-check after acquiring lock
        if _redis_conn is not None:
            try:
                _redis_conn.ping()
                return _redis_conn
            except Exception:
                _redis_conn = None

        from app.config import get_settings

        settings = get_settings()
        _redis_conn = Redis.from_url(
            str(settings.redis_url), socket_timeout=settings.redis_socket_timeout_seconds
        )
        return _redis_conn


def _delete_cache_pattern(conn: Any, pattern: str, *, batch_size: int = 200) -> int:
    """Best-effort Redis pattern delete used before dashboard live pushes."""
    removed = 0
    batch: list[Any] = []
    for key in conn.scan_iter(match=pattern, count=batch_size):
        batch.append(key)
        if len(batch) >= batch_size:
            conn.delete(*batch)
            removed += len(batch)
            batch.clear()
    if batch:
        conn.delete(*batch)
        removed += len(batch)
    return removed


def _invalidate_dashboard_live_cache(conn: Any) -> None:
    """Drop short-lived dashboard JSON caches before notifying SSE clients."""
    for pattern in _DASHBOARD_LIVE_CACHE_PATTERNS:
        try:
            _delete_cache_pattern(conn, pattern)
        except Exception:
            logger.debug("dashboard_live_cache_invalidate_failed", extra={"pattern": pattern})


def publish_progress(
    job_id: str,
    status: str,
    message: str | None = None,
    *,
    extra: dict[str, Any] | None = None,
    course_id: str | None = None,
    llm_project_id: str | None = None,
    enrichment: bool = False,
    analytics_course_id: str | None = None,
    dashboard_team_id: str | None = None,
    dashboard_course_id: str | None = None,
) -> None:
    """Publish job progress via Redis pub/sub.  Best-effort - never raises."""
    try:
        conn = _get_publish_conn()
        payload: dict[str, Any] = {
            "job_id": job_id,
            "status": status,
            "message": message,
        }
        if extra:
            payload.update(extra)
        data = json.dumps(payload, default=str)
        conn.publish(
            f"job_progress:{job_id}",
            data,
        )
        # Also broadcast to course-level channel for SSE sync stream
        if course_id:
            conn.publish(
                f"course_sync:{course_id}",
                data,
            )
        # LLM analysis channel for per-project SSE streaming
        if llm_project_id:
            conn.publish(
                f"llm_analysis:{llm_project_id}",
                data,
            )
        # Enrichment channel for admin SSE streaming
        if enrichment:
            conn.publish(
                "enrichment_progress",
                data,
            )
        # Analytics channel for course analytics SSE streaming
        if analytics_course_id:
            conn.publish(
                f"analytics:{analytics_course_id}",
                data,
            )
        # Dashboard live-data channels - notify SSE clients to refresh
        if dashboard_team_id:
            conn.publish(
                f"dashboard:team:{dashboard_team_id}",
                data,
            )
        if dashboard_course_id:
            conn.publish(
                f"dashboard:course:{dashboard_course_id}",
                data,
            )
    except Exception:
        logger.debug("SSE publish failed (non-critical)", exc_info=True)


def publish_dashboard_update(
    entity_type: str,
    entity_id: str,
    event: str = "updated",
    *,
    extra: dict[str, Any] | None = None,
) -> None:
    """Publish a dashboard update notification via Redis pub/sub.

    Notifies connected SSE clients that entity data has changed so the
    frontend can fetch fresh data from the live-data endpoints.

    Parameters
    ----------
    entity_type:
        ``"team"`` or ``"course"``.
    entity_id:
        UUID of the team or course.
    event:
        Event label (e.g. ``"updated"``, ``"metrics_computed"``, ``"member_changed"``).
    extra:
        Additional key/value pairs to include in the notification payload.
    """
    try:
        conn = _get_publish_conn()
        payload: dict[str, Any] = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event": event,
        }
        if extra:
            payload.update(extra)
        data = json.dumps(payload, default=str)
        _invalidate_dashboard_live_cache(conn)
        conn.publish(
            f"dashboard:{entity_type}:{entity_id}",
            data,
        )
        # Also broadcast to global dashboard channel for home page
        conn.publish(
            "dashboard:global",
            data,
        )
    except Exception:
        logger.debug("SSE dashboard publish failed (non-critical)", exc_info=True)
