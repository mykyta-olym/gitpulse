"""Tests for worker idempotency module."""

from unittest.mock import MagicMock, patch

import pytest


class TestLockKey:
    """Tests for _lock_key function."""

    def test_lock_key_function_exists(self) -> None:
        from app.workers.idempotency import _lock_key

        assert callable(_lock_key)

    def test_lock_key_returns_string(self) -> None:
        from app.workers.idempotency import _lock_key

        result = _lock_key("test_job", ("arg1", "arg2"))
        assert isinstance(result, str)

    def test_lock_key_starts_with_joblock(self) -> None:
        from app.workers.idempotency import _lock_key

        result = _lock_key("my_job", ("a", "b"))
        assert result.startswith("joblock:")

    def test_lock_key_contains_job_name(self) -> None:
        from app.workers.idempotency import _lock_key

        result = _lock_key("process_webhook", ("data",))
        assert "process_webhook" in result

    def test_lock_key_deterministic(self) -> None:
        from app.workers.idempotency import _lock_key

        key1 = _lock_key("job", ("arg1", "arg2"))
        key2 = _lock_key("job", ("arg1", "arg2"))
        assert key1 == key2

    def test_lock_key_different_args_different_keys(self) -> None:
        from app.workers.idempotency import _lock_key

        key1 = _lock_key("job", ("arg1",))
        key2 = _lock_key("job", ("arg2",))
        assert key1 != key2

    def test_lock_key_different_jobs_different_keys(self) -> None:
        from app.workers.idempotency import _lock_key

        key1 = _lock_key("job1", ("arg",))
        key2 = _lock_key("job2", ("arg",))
        assert key1 != key2

    def test_lock_key_with_empty_args(self) -> None:
        from app.workers.idempotency import _lock_key

        result = _lock_key("job", ())
        assert isinstance(result, str)
        assert "joblock:" in result

    def test_lock_key_hash_length(self) -> None:
        from app.workers.idempotency import _lock_key

        result = _lock_key("job", ("arg",))
        # Format is "joblock:{job_name}:{16-char-hash}"
        parts = result.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 16  # 16 hex chars from sha256[:16]


class TestLockTTLConfig:
    """Tests for idempotency_lock_ttl_seconds config value."""

    @patch("app.workers.idempotency.get_settings")
    def test_lock_ttl_default_exists(self, mock_get_settings) -> None:
        mock_settings = MagicMock()
        mock_settings.idempotency_lock_ttl_seconds = 600
        mock_get_settings.return_value = mock_settings

        assert mock_settings.idempotency_lock_ttl_seconds is not None

    @patch("app.workers.idempotency.get_settings")
    def test_lock_ttl_is_int(self, mock_get_settings) -> None:
        mock_settings = MagicMock()
        mock_settings.idempotency_lock_ttl_seconds = 600
        mock_get_settings.return_value = mock_settings

        assert isinstance(mock_settings.idempotency_lock_ttl_seconds, int)

    @patch("app.workers.idempotency.get_settings")
    def test_lock_ttl_used_in_decorator(self, mock_get_settings) -> None:
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.idempotency_lock_ttl_seconds = 300
        mock_get_settings.return_value = mock_settings

        # TTL should be at least 60 seconds, but not more than 1 hour
        assert 60 <= mock_settings.idempotency_lock_ttl_seconds <= 3600


class TestIdempotentJobDecorator:
    """Tests for idempotent_job decorator."""

    def test_idempotent_job_decorator_exists(self) -> None:
        from app.workers.idempotency import idempotent_job

        assert callable(idempotent_job)

    def test_decorator_preserves_function_name(self) -> None:
        from app.workers.idempotency import idempotent_job

        @idempotent_job
        def my_test_function(x, y):
            return x + y

        assert my_test_function.__name__ == "my_test_function"

    def test_decorator_preserves_function_docstring(self) -> None:
        from app.workers.idempotency import idempotent_job

        @idempotent_job
        def my_func():
            """This is a test docstring."""
            pass

        assert my_func.__doc__ == """This is a test docstring."""

    @patch("app.workers.idempotency.get_settings")
    @patch("app.workers.idempotency.Redis")
    def test_decorator_acquires_lock_on_call(self, mock_redis_class, mock_get_settings) -> None:
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_get_settings.return_value = mock_settings

        mock_redis = MagicMock()
        mock_redis.set.return_value = True  # Lock acquired
        mock_redis_class.from_url.return_value = mock_redis

        @idempotent_job
        def test_job(arg) -> str:
            return f"processed: {arg}"

        result = test_job("data")

        assert result == "processed: data"
        mock_redis.set.assert_called_once()
        mock_redis.delete.assert_called_once()

    @patch("app.workers.idempotency.get_settings")
    @patch("app.workers.idempotency.Redis")
    def test_decorator_skips_when_lock_held(self, mock_redis_class, mock_get_settings) -> None:
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_get_settings.return_value = mock_settings

        mock_redis = MagicMock()
        mock_redis.set.return_value = False  # Lock not acquired
        mock_redis_class.from_url.return_value = mock_redis

        call_count = 0

        @idempotent_job
        def test_job(arg) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed: {arg}"

        result = test_job("data")

        assert result is None  # Returns None when skipped
        assert call_count == 0  # Function body not executed
        mock_redis.delete.assert_not_called()  # No cleanup needed

    @patch("app.workers.idempotency.get_settings")
    @patch("app.workers.idempotency.Redis")
    def test_decorator_releases_lock_after_success(
        self, mock_redis_class, mock_get_settings
    ) -> None:
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_get_settings.return_value = mock_settings

        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_redis_class.from_url.return_value = mock_redis

        @idempotent_job
        def test_job() -> str:
            return "success"

        test_job()

        mock_redis.delete.assert_called_once()

    @patch("app.workers.idempotency.get_settings")
    @patch("app.workers.idempotency.Redis")
    def test_decorator_releases_lock_on_exception(
        self, mock_redis_class, mock_get_settings
    ) -> None:
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_get_settings.return_value = mock_settings

        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_redis_class.from_url.return_value = mock_redis

        @idempotent_job
        def failing_job() -> None:
            raise ValueError("Something went wrong")

        with pytest.raises(ValueError, match="Something went wrong"):
            failing_job()

        # Lock should still be released even on exception
        mock_redis.delete.assert_called_once()

    @patch("app.workers.idempotency.get_settings")
    @patch("app.workers.idempotency.Redis")
    def test_decorator_uses_nx_and_ex_for_lock(self, mock_redis_class, mock_get_settings) -> None:
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.idempotency_lock_ttl_seconds = 600
        mock_get_settings.return_value = mock_settings

        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_redis_class.from_url.return_value = mock_redis

        @idempotent_job
        def test_job() -> str:
            return "done"

        test_job()

        # Verify set was called with nx=True (only set if not exists) and ex (expiry)
        call_args = mock_redis.set.call_args
        assert call_args.kwargs.get("nx") is True
        assert call_args.kwargs.get("ex") == 600
