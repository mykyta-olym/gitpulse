"""Tests for rate limiting module."""

from unittest.mock import MagicMock


class TestRateLimiterClass:
    """Tests for RateLimiter class."""

    def test_rate_limiter_class_exists(self) -> None:
        from app.security.rate_limit import RateLimiter

        assert RateLimiter is not None

    def test_rate_limiter_init(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        limiter = RateLimiter(mock_redis, prefix="test")
        assert limiter.redis is mock_redis
        assert limiter.prefix == "test"

    def test_rate_limiter_default_prefix(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        limiter = RateLimiter(mock_redis)
        assert limiter.prefix == "rl"

    def test_is_allowed_method_exists(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        limiter = RateLimiter(mock_redis)
        assert hasattr(limiter, "is_allowed")
        assert callable(limiter.is_allowed)

    def test_is_allowed_under_limit(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        # Lua script returns [allowed=1, remaining=5]
        mock_script = MagicMock(return_value=[1, 5])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis)
        allowed, remaining = limiter.is_allowed("test_key", max_requests=10, window_seconds=60)

        assert allowed is True
        assert remaining == 5

    def test_is_allowed_at_limit(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        # Lua script returns [allowed=1, remaining=0]
        mock_script = MagicMock(return_value=[1, 0])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis)
        allowed, remaining = limiter.is_allowed("test_key", max_requests=10, window_seconds=60)

        assert allowed is True
        assert remaining == 0

    def test_is_allowed_over_limit(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        # Lua script returns [allowed=0, remaining=0]
        mock_script = MagicMock(return_value=[0, 0])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis)
        allowed, remaining = limiter.is_allowed("test_key", max_requests=10, window_seconds=60)

        assert allowed is False
        assert remaining == 0

    def test_is_allowed_builds_correct_key(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        mock_script = MagicMock(return_value=[1, 9])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis, prefix="custom")
        limiter.is_allowed("user:123", max_requests=10, window_seconds=60)

        # Verify Lua script was called with correct key
        mock_script.assert_called_once()
        call_kwargs = mock_script.call_args
        assert call_kwargs[1]["keys"] == ["custom:user:123"]

    def test_is_allowed_calls_lua_script(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        mock_script = MagicMock(return_value=[1, 5])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis)
        limiter.is_allowed("key", max_requests=10, window_seconds=60)

        # Verify Lua script was called once
        mock_script.assert_called_once()
        call_kwargs = mock_script.call_args
        assert call_kwargs[1]["keys"] == ["rl:key"]
        args = call_kwargs[1]["args"]
        assert args[1] == 60  # window_seconds
        assert args[2] == 10  # max_requests

    def test_is_allowed_custom_window(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        mock_script = MagicMock(return_value=[1, 99])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis)
        limiter.is_allowed("key", max_requests=100, window_seconds=3600)

        # Should pass 3600 second window to Lua script
        call_kwargs = mock_script.call_args
        args = call_kwargs[1]["args"]
        assert args[1] == 3600

    def test_remaining_never_negative(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        # Lua script handles clamping - returns [0, 0] when over limit
        mock_script = MagicMock(return_value=[0, 0])
        mock_redis.register_script.return_value = mock_script

        limiter = RateLimiter(mock_redis)
        allowed, remaining = limiter.is_allowed("key", max_requests=10, window_seconds=60)

        assert allowed is False
        assert remaining == 0  # Should be 0, not negative


class TestLuaScript:
    """Tests for Lua-based rate limiting script."""

    def test_script_registered_on_init(self) -> None:
        from app.security.rate_limit import RateLimiter

        mock_redis = MagicMock()
        RateLimiter(mock_redis)
        mock_redis.register_script.assert_called_once()
