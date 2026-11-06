"""Tests for scale optimization components: caching, backpressure, queue safety."""

from unittest.mock import AsyncMock, MagicMock

import pytest

# ===============================================================================
# GITLAB API CACHE TESTS
# ===============================================================================


class TestGitLabAPICache:
    """Tests for GitLab API caching with ETags."""

    @pytest.fixture
    def cache_config(self):
        """Create test cache configuration."""
        from app.services.gitlab.cache import CacheConfig

        return CacheConfig(
            default_ttl=60,
            list_ttl=30,
            user_ttl=120,
            compress_threshold=100,
            enabled=True,
        )

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        pipeline = AsyncMock()
        pipeline.execute = AsyncMock(return_value=[None, None])
        redis.pipeline.return_value = pipeline
        return redis

    def test_cache_key_generation(self, cache_config) -> None:
        """Test that cache keys are deterministic."""
        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache("redis://localhost", cache_config)

        # Same inputs should produce same key
        key1 = cache._make_key("/projects/123/issues", {"state": "all"})
        key2 = cache._make_key("/projects/123/issues", {"state": "all"})
        assert key1 == key2

        # Different inputs should produce different keys
        key3 = cache._make_key("/projects/123/issues", {"state": "open"})
        assert key1 != key3

    def test_ttl_selection(self, cache_config) -> None:
        """Test TTL selection based on endpoint type."""
        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache("redis://localhost", cache_config)

        # User endpoints get longer TTL
        assert cache._get_ttl("/users/42") == 120

        # List endpoints get shorter TTL
        assert cache._get_ttl("/projects/123/issues") == 30
        assert cache._get_ttl("/projects/123/merge_requests") == 30

        # Other endpoints get default TTL
        assert cache._get_ttl("/projects/123/issues/5") == 60

    def test_compression(self, cache_config) -> None:
        """Test data compression above threshold."""
        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache("redis://localhost", cache_config)

        # Small data should not be compressed
        small_data = b"small"
        compressed_small = cache._compress(small_data)
        assert compressed_small.startswith(b"raw:")

        # Large data should be compressed
        large_data = b"x" * 200
        compressed_large = cache._compress(large_data)
        assert compressed_large.startswith(b"gz:")
        assert len(compressed_large) < len(large_data)

        # Decompression should restore original
        assert cache._decompress(compressed_small) == small_data
        assert cache._decompress(compressed_large) == large_data

    @pytest.mark.asyncio
    async def test_cache_disabled_returns_none(self, cache_config):
        """Test cache returns None when disabled."""
        from app.services.gitlab.cache import GitLabAPICache

        cache_config.enabled = False
        cache = GitLabAPICache("redis://localhost", cache_config)

        response, etag = await cache.get_cached_response("/projects/123/issues")

        assert response is None
        assert etag is None


# ===============================================================================
# BACKPRESSURE TESTS
# ===============================================================================


class TestQueueBackpressure:
    """Tests for queue backpressure management."""

    @pytest.fixture
    def backpressure_config(self):
        """Create test backpressure configuration."""
        from app.services.backpressure import BackpressureConfig

        return BackpressureConfig(
            queue_high_watermark=100,
            queue_critical_watermark=500,
            enabled=True,
        )

    @pytest.fixture
    def mock_redis_sync(self):
        """Create mock synchronous Redis client."""
        redis = MagicMock()
        redis.llen.return_value = 0
        return redis

    def test_throttle_factor_below_threshold(self, backpressure_config, mock_redis_sync) -> None:
        """Test no throttling when queue depth is low."""
        from app.services.backpressure import QueueBackpressure

        mock_redis_sync.llen.return_value = 50  # Below high watermark

        bp = QueueBackpressure(mock_redis_sync, backpressure_config)
        factor = bp.calculate_throttle_factor("high")

        assert factor == 1.0

    def test_throttle_factor_above_critical(self, backpressure_config, mock_redis_sync) -> None:
        """Test full throttle above critical watermark."""
        from app.services.backpressure import QueueBackpressure

        mock_redis_sync.llen.return_value = 600  # Above critical

        bp = QueueBackpressure(mock_redis_sync, backpressure_config)
        factor = bp.calculate_throttle_factor("high")

        assert factor == 0.0

    def test_throttle_factor_interpolation(self, backpressure_config, mock_redis_sync) -> None:
        """Test linear interpolation between watermarks."""
        from app.services.backpressure import QueueBackpressure

        # Midpoint between 100 (high) and 500 (critical) = 300
        mock_redis_sync.llen.return_value = 300

        bp = QueueBackpressure(mock_redis_sync, backpressure_config)
        factor = bp.calculate_throttle_factor("high")

        assert 0.4 < factor < 0.6  # Should be ~0.5

    def test_should_accept_job_high_priority(self, backpressure_config, mock_redis_sync) -> None:
        """Test high priority jobs accepted even under pressure."""
        from app.services.backpressure import QueueBackpressure

        mock_redis_sync.llen.return_value = 600  # Full throttle

        bp = QueueBackpressure(mock_redis_sync, backpressure_config)

        # Priority 1 (highest) should still be accepted
        assert bp.should_accept_job("high", priority=1) is True


# ===============================================================================
# CONFIGURATION TESTS
# ===============================================================================


class TestScaleConfiguration:
    """Tests for scale optimization configuration."""

    def test_feature_flags_exist(self) -> None:
        """Test that scale feature flags are defined."""
        from app.config import Settings

        # Create settings with required fields
        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-secret-key-minimum-16-chars",
            teacher_api_token="test-token",
            app_env="test",
            _env_file=None,
            _env_prefix="__TEST__",
        )

        assert hasattr(settings, "feature_gitlab_cache")
        assert hasattr(settings, "feature_backpressure")

    def test_default_cache_settings(self) -> None:
        """Test default cache TTL settings."""
        from app.config import Settings

        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-secret-key-minimum-16-chars",
            teacher_api_token="test-token",
            app_env="test",
            _env_file=None,
            _env_prefix="__TEST__",
        )

        assert settings.feature_gitlab_cache is True

    def test_default_rate_limit_settings(self) -> None:
        """Test default rate limit settings."""
        from app.config import Settings

        settings = Settings(
            database_url="postgresql+asyncpg://test:test@localhost/test",
            secret_key="test-secret-key-minimum-16-chars",
            teacher_api_token="test-token",
            app_env="test",
            _env_file=None,
            _env_prefix="__TEST__",
        )

        assert settings.rate_limit_requests_per_minute == 60
        assert settings.queue_high_watermark == 1000
        assert settings.queue_critical_watermark == 5000
