"""Unit tests for RQ worker jobs - bootstrap and student_resolver.

All async inner functions are tested via mocked worker_session / DB sessions.
"""

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# -- Helper: mock worker_session context manager --


def _mock_ws(session, settings=None):
    """Return an async-context-manager that yields (session, settings)."""
    if settings is None:
        settings = MagicMock()
        settings.database_url = "postgresql+asyncpg://x@localhost/db"
        settings.redis_url = "redis://localhost"
        settings.redis_socket_timeout_seconds = 5.0

    @asynccontextmanager
    async def _ws():
        yield session, settings

    return _ws


# ===================================================
# bootstrap.worker_session
# ===================================================


class TestWorkerSessionBootstrap:
    """Cover src/app/workers/bootstrap.py (8 missed lines)."""

    @pytest.mark.asyncio
    async def test_worker_session_yields_session_and_settings(self) -> None:
        mock_session = AsyncMock()
        mock_settings = MagicMock()
        mock_settings.database_url = "postgresql+asyncpg://x@localhost/db"

        @asynccontextmanager
        async def _fake_session_ctx():
            yield mock_session

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch("app.db.session.init_engine") as init_eng,
            patch("app.db.session.async_session_ctx", new=_fake_session_ctx),
            patch("app.db.session.dispose_engine", new_callable=AsyncMock) as dispose_eng,
        ):
            from app.workers.bootstrap import worker_session

            async with worker_session() as (session, settings):
                assert session is mock_session
                assert settings is mock_settings

            init_eng.assert_called_once_with(str(mock_settings.database_url))
            dispose_eng.assert_awaited_once()


# ===================================================
# shared patch paths
# ===================================================

_CFG_PATCH = "app.config.get_settings"
_WS_PATCH = "app.workers.bootstrap.worker_session"


# ===================================================
# student_resolver
# ===================================================


class TestResolveStudent:
    """Cover resolve_student() in student_resolver.py (~19 missed lines)."""

    @pytest.mark.asyncio
    async def test_no_id_no_username_returns_none(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        result = await resolve_student(AsyncMock(), None, None)
        assert result is None

    @pytest.mark.asyncio
    async def test_fast_path_by_gitlab_id(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = student_uuid

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        result = await resolve_student(session, 123, "user1")
        assert result == student_uuid

    @pytest.mark.asyncio
    async def test_fallback_by_username(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, 123)
        found = MagicMock()
        found.one_or_none.return_value = row

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found])

        result = await resolve_student(session, 123, "user1")
        assert result == student_uuid

    @pytest.mark.asyncio
    async def test_username_match_updates_stale_id(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, -999)
        found = MagicMock()
        found.one_or_none.return_value = row
        update_result = MagicMock()

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found, update_result])

        result = await resolve_student(session, 456, "user2", update_stale_id=True)
        assert result == student_uuid
        assert session.execute.await_count == 3

    @pytest.mark.asyncio
    async def test_username_not_found(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        not_found = MagicMock()
        not_found.one_or_none.return_value = None

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, not_found])

        result = await resolve_student(session, 789, "ghost")
        assert result is None

    @pytest.mark.asyncio
    async def test_only_username_no_id(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()
        row = (student_uuid, None)
        found = MagicMock()
        found.one_or_none.return_value = row

        session = AsyncMock()
        session.execute = AsyncMock(return_value=found)

        result = await resolve_student(session, None, "onlyname")
        assert result == student_uuid

    @pytest.mark.asyncio
    async def test_no_update_when_flag_false(self) -> None:
        from app.workers.processors.student_resolver import resolve_student

        student_uuid = uuid.uuid4()

        no_match = MagicMock()
        no_match.scalar_one_or_none.return_value = None
        row = (student_uuid, -1)
        found = MagicMock()
        found.one_or_none.return_value = row

        session = AsyncMock()
        session.execute = AsyncMock(side_effect=[no_match, found])

        result = await resolve_student(session, 100, "user", update_stale_id=False)
        assert result == student_uuid
        assert session.execute.await_count == 2
