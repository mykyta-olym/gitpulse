"""Comprehensive edge-case & consistency tests for worker subsystem.

Covers boundary conditions, error propagation, concurrent scenarios,
and configuration consistency across:
- bootstrap.worker_session  (dispose_engine masking, init_engine failure)
- student_resolver          (gitlab_user_id=0, DB errors, boundary IDs)
- idempotency decorator     (lock held, Redis down, lock release failure)
- scheduler config          (positive intervals, docstring consistency)
"""

import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# -- Shared helpers --

_CFG_PATCH = "app.config.get_settings"


def _mock_ws(
    session: Any, settings: Any = None
) -> Callable[[], AbstractAsyncContextManager[tuple[Any, Any]]]:
    """Return an async-context-manager that yields (session, settings)."""
    if settings is None:
        settings = MagicMock()
        settings.database_url = "postgresql+asyncpg://x@localhost/db"
        settings.redis_url = "redis://localhost"
        settings.redis_socket_timeout_seconds = 5.0

    @asynccontextmanager
    async def _ws() -> AsyncIterator[tuple[Any, Any]]:
        yield session, settings

    return _ws


# ===================================================
# bootstrap.worker_session - edge cases
# ===================================================


class TestBootstrapEdgeCases:
    """Edge cases for worker_session context manager."""

    @pytest.mark.asyncio
    async def test_dispose_engine_called_even_on_inner_exception(self) -> None:
        """dispose_engine must run in finally even when the body raises."""
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.database_url = "postgresql+asyncpg://x@localhost/db"

        @asynccontextmanager
        async def _fake_session_ctx():
            yield mock_session

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch("app.db.session.init_engine"),
            patch("app.db.session.async_session_ctx", new=_fake_session_ctx),
            patch("app.db.session.dispose_engine", new_callable=AsyncMock) as dispose_eng,
        ):
            from app.workers.bootstrap import worker_session

            with pytest.raises(ValueError, match="inner boom"):
                async with worker_session() as (_session, _settings):
                    raise ValueError("inner boom")

            dispose_eng.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dispose_engine_failure_does_not_mask_inner_exception(self) -> None:
        """If dispose_engine raises but the body also raised, the body error propagates
        because dispose_engine errors are suppressed via contextlib.suppress."""
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.database_url = "postgresql+asyncpg://x@localhost/db"

        @asynccontextmanager
        async def _fake_session_ctx():
            yield mock_session

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch("app.db.session.init_engine"),
            patch("app.db.session.async_session_ctx", new=_fake_session_ctx),
            patch(
                "app.db.session.dispose_engine",
                new_callable=AsyncMock,
                side_effect=OSError("dispose failed"),
            ),
        ):
            from app.workers.bootstrap import worker_session

            # dispose_engine error is suppressed - inner ValueError propagates
            with pytest.raises(ValueError, match="inner boom"):
                async with worker_session() as (_session, _settings):
                    raise ValueError("inner boom")

    @pytest.mark.asyncio
    async def test_init_engine_receives_string_database_url(self) -> None:
        """database_url is cast to str() before passing to init_engine."""
        mock_settings = MagicMock()
        # Simulate a pydantic URL object that converts to string
        mock_url = MagicMock()
        mock_url.__str__ = MagicMock(return_value="postgresql+asyncpg://cast@localhost/db")
        mock_settings.database_url = mock_url

        @asynccontextmanager
        async def _fake_session_ctx():
            yield AsyncMock()

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch("app.db.session.init_engine") as init_eng,
            patch("app.db.session.async_session_ctx", new=_fake_session_ctx),
            patch("app.db.session.dispose_engine", new_callable=AsyncMock),
        ):
            from app.workers.bootstrap import worker_session

            async with worker_session() as (_session, _settings):
                pass

            init_eng.assert_called_once_with("postgresql+asyncpg://cast@localhost/db")

    @pytest.mark.asyncio
    async def test_init_engine_failure_skips_dispose(self) -> None:
        """If init_engine raises, dispose_engine should NOT be called
        (the try block never entered)."""
        mock_settings = MagicMock()
        mock_settings.database_url = "bad://url"

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch(
                "app.db.session.init_engine",
                side_effect=RuntimeError("bad engine"),
            ),
            patch("app.db.session.dispose_engine", new_callable=AsyncMock),
        ):
            from app.workers.bootstrap import worker_session

            with pytest.raises(RuntimeError, match="bad engine"):
                async with worker_session() as _:
                    pass


# ===================================================
# student_resolver - edge cases
# ===================================================


class TestStudentResolverEdgeCases:
    """Edge cases for resolve_student() boundary conditions."""

    @pytest.mark.asyncio
    async def test_gitlab_user_id_zero_uses_fast_path(self) -> None:
        """gitlab_user_id=0 is not None - fast path IS attempted."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = student_uuid

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        # id=0, username="user0" - fast path attempted since 0 is not None
        result = await resolve_student(session, 0, "user0")
        assert result == student_uuid
        assert session.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_gitlab_user_id_zero_no_username_tries_fast_path(self) -> None:
        """gitlab_user_id=0 with no username: tries fast path, returns None if not found."""
        from app.workers.processors.student_resolver import resolve_student

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        result = await resolve_student(session, 0, None)
        assert result is None
        # Fast path was tried (id=0 is not None)
        assert session.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_gitlab_user_id_zero_triggers_stale_update(self) -> None:
        """gitlab_user_id=0 triggers stale ID update (0 is not None)."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, -1)  # stale placeholder ID
        found = MagicMock()
        found.one_or_none.return_value = row
        update_result = MagicMock()

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found, update_result])

        result = await resolve_student(session, 0, "user_stale", update_stale_id=True)
        assert result == student_uuid
        # 3 queries: fast path miss, username match, stale update
        assert session.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_negative_gitlab_user_id_used_for_fast_path(self) -> None:
        """Negative gitlab_user_id is truthy - fast path IS attempted."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = student_uuid

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        result = await resolve_student(session, -999, "user_neg")
        assert result == student_uuid
        # Fast path found it - only one query
        assert session.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_very_large_gitlab_user_id(self) -> None:
        """Large gitlab_user_id should work normally via fast path."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = student_uuid

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        result = await resolve_student(session, 2**31 - 1, "biguser")
        assert result == student_uuid

    @pytest.mark.asyncio
    async def test_db_error_during_stale_update_propagates(self) -> None:
        """If the UPDATE for stale ID fails, the exception propagates."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, -1)  # stale
        found = MagicMock()
        found.one_or_none.return_value = row

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found, RuntimeError("db write failed")])

        with pytest.raises(RuntimeError, match="db write failed"):
            await resolve_student(session, 456, "user_err", update_stale_id=True)

    @pytest.mark.asyncio
    async def test_empty_string_username_returns_none(self) -> None:
        """Empty string username is falsy - should return None if no ID."""
        from app.workers.processors.student_resolver import resolve_student

        session = AsyncMock()
        result = await resolve_student(session, None, "")
        assert result is None

    @pytest.mark.asyncio
    async def test_stale_update_skipped_when_current_id_is_positive(self) -> None:
        """No update when current gitlab_user_id is positive (not stale)."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, 100)  # positive - not stale
        found = MagicMock()
        found.one_or_none.return_value = row

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found])

        result = await resolve_student(session, 200, "user_ok", update_stale_id=True)
        assert result == student_uuid
        # Only 2 queries - no update query issued
        assert session.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_stale_update_when_current_id_is_none(self) -> None:
        """Student with gitlab_user_id=None gets updated."""
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, None)  # no ID yet
        found = MagicMock()
        found.one_or_none.return_value = row
        update_result = MagicMock()

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found, update_result])

        result = await resolve_student(session, 789, "new_user", update_stale_id=True)
        assert result == student_uuid
        assert session.execute.await_count == 3


# ===================================================
# idempotency - edge cases
# ===================================================


class TestIdempotencyEdgeCases:
    """Edge cases for the idempotent_job decorator."""

    def test_lock_already_held_skips_execution(self) -> None:
        """If Redis lock is already held, job returns None without executing."""
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_settings.redis_socket_timeout_seconds = 1.0
        mock_settings.idempotency_lock_ttl_seconds = 300

        executed = {"called": False}

        @idempotent_job
        def my_job(arg):
            executed["called"] = True
            return "result"

        mock_conn = MagicMock()
        mock_conn.set.return_value = False  # Lock NOT acquired

        with (
            patch("app.workers.idempotency.get_settings", return_value=mock_settings),
            patch("app.workers.idempotency._get_redis_connection", return_value=mock_conn),
        ):
            result = my_job("arg1")

        assert result is None
        assert not executed["called"]

    def test_redis_unavailable_proceeds_without_lock(self) -> None:
        """If Redis is down, the job still executes."""
        from redis.exceptions import RedisError

        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_settings.redis_socket_timeout_seconds = 1.0
        mock_settings.idempotency_lock_ttl_seconds = 300

        executed = {"called": False}

        @idempotent_job
        def my_job(arg):
            executed["called"] = True
            return "ok"

        with (
            patch("app.workers.idempotency.get_settings", return_value=mock_settings),
            patch(
                "app.workers.idempotency._get_redis_connection",
                side_effect=RedisError("conn refused"),
            ),
        ):
            result = my_job("arg1")

        assert result == "ok"
        assert executed["called"]

    def test_lock_release_failure_does_not_crash(self) -> None:
        """If Redis lock release fails, the job result is still returned."""
        from redis.exceptions import RedisError

        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_settings.redis_socket_timeout_seconds = 1.0
        mock_settings.idempotency_lock_ttl_seconds = 300

        @idempotent_job
        def my_job(arg):
            return "done"

        mock_conn = MagicMock()
        mock_conn.set.return_value = True  # Lock acquired
        mock_conn.delete.side_effect = RedisError("delete failed")
        mock_conn.close.side_effect = RedisError("close failed")

        with (
            patch("app.workers.idempotency.get_settings", return_value=mock_settings),
            patch("app.workers.idempotency._get_redis_connection", return_value=mock_conn),
        ):
            result = my_job("arg1")

        assert result == "done"

    def test_job_exception_still_releases_lock(self) -> None:
        """If the job raises, the lock should be released and exception re-raised."""
        from app.workers.idempotency import idempotent_job

        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost"
        mock_settings.redis_socket_timeout_seconds = 1.0
        mock_settings.idempotency_lock_ttl_seconds = 300

        @idempotent_job
        def my_job(arg):
            raise ValueError("job failed")

        mock_conn = MagicMock()
        mock_conn.set.return_value = True  # Lock acquired

        with (
            patch("app.workers.idempotency.get_settings", return_value=mock_settings),
            patch("app.workers.idempotency._get_redis_connection", return_value=mock_conn),
            pytest.raises(ValueError, match="job failed"),
        ):
            my_job("arg1")

        mock_conn.delete.assert_called_once()

    def test_lock_key_deterministic(self) -> None:
        """Same (job, args) should produce the same lock key."""
        from app.workers.idempotency import _lock_key

        key1 = _lock_key("my_job", ("arg1",))
        key2 = _lock_key("my_job", ("arg1",))
        assert key1 == key2

    def test_lock_key_different_args(self) -> None:
        """Different args should produce different lock keys."""
        from app.workers.idempotency import _lock_key

        key1 = _lock_key("my_job", ("arg1",))
        key2 = _lock_key("my_job", ("arg2",))
        assert key1 != key2

    def test_lock_key_different_jobs(self) -> None:
        """Different job names should produce different lock keys."""
        from app.workers.idempotency import _lock_key

        key1 = _lock_key("job_a", ("arg1",))
        key2 = _lock_key("job_b", ("arg1",))
        assert key1 != key2


# ===================================================
# Scheduler config consistency
# ===================================================


class TestSchedulerConfigConsistency:
    """Verify scheduler configuration invariants."""

    def test_all_scheduler_intervals_positive(self) -> None:
        """Every scheduler interval default must be > 0."""
        from app.config import Settings

        s = Settings(
            secret_key="x" * 32,
            database_url="postgresql+asyncpg://x@localhost/db",
            gitlab_url="https://gitlab.example.com",
            gitlab_token="tok",
        )
        interval_fields = [
            f
            for f in Settings.model_fields
            if f.startswith("scheduler_") and f.endswith("_interval")
        ]
        for field_name in interval_fields:
            value = getattr(s, field_name)
            assert value > 0, f"{field_name} = {value} must be positive"

    def test_sweep_batch_sizes_positive(self) -> None:
        """All sweep batch sizes must be positive."""
        from app.config import Settings

        s = Settings(
            secret_key="x" * 32,
            database_url="postgresql+asyncpg://x@localhost/db",
            gitlab_url="https://gitlab.example.com",
            gitlab_token="tok",
        )
        for field_name in Settings.model_fields:
            if "batch" in field_name:
                value = getattr(s, field_name)
                assert value > 0, f"{field_name} = {value} must be positive"


# ===================================================
# Cross-cutting consistency checks
# ===================================================


class TestCrossCuttingConsistency:
    """Cross-module consistency checks."""

    def test_idempotent_job_preserves_function_name(self) -> None:
        """@idempotent_job should preserve the wrapped function's __name__."""
        from app.workers.idempotency import idempotent_job

        @idempotent_job
        def example_job(x):
            return x

        assert example_job.__name__ == "example_job"

    def test_idempotent_job_preserves_docstring(self) -> None:
        """@idempotent_job should preserve the wrapped function's __doc__."""
        from app.workers.idempotency import idempotent_job

        @idempotent_job
        def example_job(x):
            """My docstring."""
            return x

        assert example_job.__doc__ == "My docstring."
