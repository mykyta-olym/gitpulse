"""Data types for GitLab API cache."""

from dataclasses import dataclass
from typing import Any, Protocol

import redis.asyncio as aioredis


class _AsyncRedisModule(Protocol):
    def from_url(self, url: str, **kwargs: Any) -> "aioredis.Redis[bytes]": ...


@dataclass
class CacheConfig:
    """Cache configuration with TTL settings."""

    # TTLs in seconds
    default_ttl: int = 300  # 5 min
    list_ttl: int = 120  # 2 min
    user_ttl: int = 900  # 15 min

    # Compression threshold (bytes)
    compress_threshold: int = 1024

    # Feature flag
    enabled: bool = True
