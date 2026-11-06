"""Simple Redis-backed rate limiting."""

import time
from typing import Any

from redis import Redis

# Lua script: atomically check-then-add so denied requests don't consume a slot.
_LUA_SLIDING_WINDOW = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_req = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current = redis.call('ZCARD', key)

if current < max_req then
    redis.call('ZADD', key, now, tostring(now))
    current = current + 1
    redis.call('EXPIRE', key, window)
    return {1, max_req - current}
else
    redis.call('EXPIRE', key, window)
    return {0, 0}
end
"""


class RateLimiter:
    """Sliding window rate limiter using Redis."""

    def __init__(self, redis_client: "Redis[Any]", prefix: str = "rl") -> None:
        self.redis = redis_client
        self.prefix = prefix
        self._script = self.redis.register_script(_LUA_SLIDING_WINDOW)  # type: ignore[attr-defined]

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining).

        Uses an atomic Lua script so that denied requests do not consume
        a window slot (prevents cascading denials).
        """
        now = time.time()
        redis_key = f"{self.prefix}:{key}"

        result = self._script(keys=[redis_key], args=[now, window_seconds, max_requests])
        allowed = bool(result[0])
        remaining = int(result[1])

        return allowed, remaining
