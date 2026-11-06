"""Shared Redis connection pool - avoids per-call TCP churn.

Usage:
    from app.redis_pool import get_redis
    conn = get_redis()          # returns Redis with shared ConnectionPool
    conn.get("some_key")        # no need to close - pool manages lifecycle

Initialize once at startup via ``init_redis_pool()`` in the lifespan.
"""

from __future__ import annotations

import logging

from redis import ConnectionPool, Redis

_log = logging.getLogger(__name__)
_pool: ConnectionPool | None = None


def init_redis_pool(
    redis_url: str,
    max_connections: int = 50,
    socket_timeout: int = 5,
) -> ConnectionPool:
    """Create the global Redis connection pool. Called once at startup."""
    global _pool
    _pool = ConnectionPool.from_url(
        redis_url,
        max_connections=max_connections,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_timeout,
        decode_responses=False,
    )
    _log.info("Redis connection pool initialized (max_connections=%d)", max_connections)
    return _pool


def get_redis() -> Redis:  # type: ignore[type-arg]
    """Return a Redis client backed by the shared connection pool.

    The connection is automatically returned to the pool after each
    command, so callers should NOT call ``.close()`` on the returned
    client.
    """
    if _pool is None:
        raise RuntimeError("Redis pool not initialized - call init_redis_pool() at startup")
    return Redis(connection_pool=_pool)


def close_redis_pool() -> None:
    """Disconnect and release all pooled connections."""
    global _pool
    if _pool is not None:
        _pool.disconnect()
        _pool = None
