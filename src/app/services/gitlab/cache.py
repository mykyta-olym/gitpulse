"""GitLab API response caching with ETags and Redis.

Implements HTTP conditional requests (If-None-Match) for GitLab API
to reduce redundant data transfer and respect rate limits.

Cache structure (Redis keys):
  gitlab:etag:{endpoint_hash}     -> ETag string
  gitlab:response:{endpoint_hash} -> Cached JSON response (compressed)

TTL strategy:
  - Entity data (MRs, issues): 5 minutes
  - List data (paginated): 2 minutes
  - User data: 15 minutes (less volatile)

Compression:
  Responses > 1KB are gzip-compressed before storing in Redis.
"""

import contextlib
import gzip
import hashlib
import json
import logging
import re
from typing import Any, Self, cast

import redis.asyncio as aioredis
from redis import exceptions as redis_exceptions

from app.services.gitlab.cache_types import (
    CacheConfig,
    _AsyncRedisModule,
)

logger = logging.getLogger(__name__)


__all__ = [
    "CacheConfig",
    "GitLabAPICache",
    "_AsyncRedisModule",
]


class GitLabAPICache:
    """Redis-backed cache for GitLab API responses with ETag support."""

    def __init__(
        self,
        redis_url: str,
        config: CacheConfig | None = None,
    ) -> None:
        self._redis_url = redis_url
        self._redis: aioredis.Redis[bytes] | None = None
        self.config = config or CacheConfig()

    async def connect(self) -> None:
        """Initialize Redis connection."""
        if self._redis is None:
            async_redis = cast(_AsyncRedisModule, aioredis)
            self._redis = async_redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle bytes for compression
            )

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def _make_key(self, endpoint: str, params: dict[str, Any] | None = None) -> str:
        """Generate a cache key from endpoint and params."""
        key_data = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def _get_ttl(self, endpoint: str) -> int:
        """Determine TTL based on endpoint type."""
        if "/users/" in endpoint:
            return self.config.user_ttl
        if endpoint.endswith(("/issues", "/merge_requests", "/pipelines", "/notes")):
            return self.config.list_ttl
        return self.config.default_ttl

    def _compress(self, data: bytes) -> bytes:
        """Compress data if above threshold."""
        if len(data) >= self.config.compress_threshold:
            return b"gz:" + gzip.compress(data, compresslevel=6)
        return b"raw:" + data

    def _decompress(self, data: bytes) -> bytes:
        """Decompress data if compressed."""
        if data.startswith(b"gz:"):
            return gzip.decompress(data[3:])
        if data.startswith(b"raw:"):
            return data[4:]
        # Legacy: no prefix
        return data

    async def get_cached_response(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> tuple[Any | None, str | None]:
        """Get cached response and ETag for an endpoint.

        Returns:
            (cached_response, etag) - either may be None
        """
        if not self.config.enabled or self._redis is None:
            return None, None

        key = self._make_key(endpoint, params)

        try:
            pipe = self._redis.pipeline()
            pipe.get(f"gitlab:etag:{key}")
            pipe.get(f"gitlab:response:{key}")
            etag_bytes, response_bytes = await pipe.execute()

            etag = etag_bytes.decode() if etag_bytes else None

            if response_bytes:
                decompressed = self._decompress(response_bytes)
                return json.loads(decompressed), etag

            return None, etag

        except (json.JSONDecodeError, gzip.BadGzipFile) as exc:
            logger.error("Cache data corruption for %s: %s - invalidating", endpoint, exc)
            # Best-effort cleanup of corrupted entry
            with contextlib.suppress(redis_exceptions.RedisError):
                await self._redis.delete(f"gitlab:etag:{key}", f"gitlab:response:{key}")
            return None, None
        except redis_exceptions.RedisError as exc:
            logger.warning("Cache read unavailable: %s", exc)
            return None, None

    async def store_response(
        self,
        endpoint: str,
        params: dict[str, Any] | None,
        response: Any,
        etag: str | None = None,
    ) -> None:
        """Store API response and ETag in cache."""
        if not self.config.enabled or self._redis is None:
            return

        key = self._make_key(endpoint, params)
        ttl = self._get_ttl(endpoint)

        try:
            response_bytes = json.dumps(response).encode()
            compressed = self._compress(response_bytes)

            pipe = self._redis.pipeline()
            pipe.setex(f"gitlab:response:{key}", ttl, compressed)
            if etag:
                pipe.setex(f"gitlab:etag:{key}", ttl, etag.encode())

            # Track key->project mapping for targeted invalidation
            project_id = self._extract_project_id(endpoint)
            if project_id is not None:
                set_key = f"gitlab:project_keys:{project_id}"
                pipe.sadd(set_key, key)
                pipe.expire(set_key, max(ttl, 900))  # keep mapping at least 15 min

            await pipe.execute()

        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("Cache serialization error for %s: %s", endpoint, exc)
        except redis_exceptions.RedisError as exc:
            logger.warning("Cache write unavailable: %s", exc)

    async def invalidate(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Invalidate a cached entry."""
        if self._redis is None:
            return

        key = self._make_key(endpoint, params)
        try:
            await self._redis.delete(
                f"gitlab:etag:{key}",
                f"gitlab:response:{key}",
            )
        except redis_exceptions.RedisError as exc:
            logger.warning("Cache invalidate error: %s", exc)

    async def invalidate_project(self, project_id: int) -> None:
        """Invalidate all cached data for a project."""
        if self._redis is None:
            return

        set_key = f"gitlab:project_keys:{project_id}"
        try:
            keys = await self._redis.smembers(set_key)  # type: ignore[attr-defined]
            if not keys:
                logger.debug("Project %d cache invalidation: no tracked keys", project_id)
                return

            pipe = self._redis.pipeline()
            for key in keys:
                k = key.decode() if isinstance(key, bytes) else key
                pipe.delete(f"gitlab:etag:{k}", f"gitlab:response:{k}")
            pipe.delete(set_key)
            await pipe.execute()
            logger.info("Invalidated %d cached entries for project %d", len(keys), project_id)
        except redis_exceptions.RedisError as exc:
            logger.warning("Project %d cache invalidation failed: %s", project_id, exc)

    @staticmethod
    def _extract_project_id(endpoint: str) -> int | None:
        """Extract GitLab project ID from API endpoint path."""

        m = re.search(r"/projects/(\d+)/", endpoint)
        return int(m.group(1)) if m else None
