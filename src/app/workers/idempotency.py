"""Idempotency helpers for RQ jobs.

Three-layer deduplication strategy
-----------------------------------
Layer 1 - Event-level:  ``webhook_events.gitlab_event_uuid`` UNIQUE constraint
          prevents the same GitLab event from being stored twice.

Layer 2 - Entity-level: Every processor UPSERTs via unique business keys
          (e.g. ``issues(project_id, gitlab_iid)``).  Re-processing the same
          event overwrites the row with identical data - safe and idempotent.

Layer 3 - Metrics:      ``compute_team_metrics`` is a pure function of current
          DB state -> snapshot.  Running it twice produces identical snapshots
          (deduplicated by ``(team_id, student_id, computed_at)`` truncated to
          the minute).

This module adds a Redis-based *job dedup lock* on top of those layers.
It prevents RQ from *starting* a duplicate job while one is already running,
which avoids wasted CPU - **not** for correctness (the layers above handle
that).
"""

import contextlib
import functools
import hashlib
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from redis import Redis
from redis.exceptions import RedisError

from app.config import get_settings

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


def _lock_key(job_name: str, args: tuple[Any, ...]) -> str:
    """Deterministic Redis key for a (job, args) pair."""
    raw = f"{job_name}:{args!r}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"joblock:{job_name}:{digest}"


def _get_redis_connection(settings: "Settings") -> "Redis[bytes]":
    """Create a fresh Redis connection for idempotency locking."""
    return Redis.from_url(
        str(settings.redis_url),
        socket_connect_timeout=settings.redis_socket_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
    )


def idempotent_job(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that acquires a Redis dedup lock before running a job.

    If another instance of the *same job with the same arguments* is already
    running, this invocation logs a warning and returns immediately - the
    in-flight job will produce the same result.

    The lock auto-expires after the configured TTL so a crashed worker
    never leaves a permanent lock.

    If Redis is unavailable, the job proceeds without the dedup lock
    (safety: the database-level idempotency layers still protect correctness).
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        settings = get_settings()
        lock_ttl = settings.idempotency_lock_ttl_seconds
        key = _lock_key(fn.__qualname__, args)
        conn: Redis[bytes] | None = None
        acquired = False

        try:
            conn = _get_redis_connection(settings)
            acquired = bool(conn.set(key, "1", nx=True, ex=lock_ttl))
            if not acquired:
                logger.warning(
                    "Skipping duplicate job %s(%s) - lock held",
                    fn.__qualname__,
                    args,
                )
                return None
        except RedisError:
            # Redis unavailable - proceed without lock (DB layers handle safety)
            logger.warning(
                "Redis unavailable for idempotency lock on %s - proceeding without lock",
                fn.__qualname__,
            )
            acquired = False

        try:
            return fn(*args, **kwargs)
        finally:
            # Release lock if we acquired it
            if conn and acquired:
                try:
                    conn.delete(key)
                except RedisError:
                    logger.debug("Failed to release idempotency lock for %s", fn.__qualname__)
            if conn:
                with contextlib.suppress(RedisError):
                    conn.close()

    return wrapper
