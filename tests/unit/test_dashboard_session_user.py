"""Tests for _ensure_session_user_in_db resilience helper.

After a DB restart/wipe the session cookie may still be valid while
the Users table is empty.  The helper should auto-create the user
so that stat cards never show "0 Active Users" while a user is
logged in.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _settings(*, debug: bool = True) -> SimpleNamespace:
    return SimpleNamespace(debug=debug)


def _auth(**overrides: str) -> dict[str, str]:
    base: dict[str, str] = {
        "user": "testuser",
        "role": "admin",
        "full_name": "Test User",
        "email": "testuser@dev.local",
        "gitlab_username": "testuser",
        "user_id": "dev-0",
    }
    base.update(overrides)
    return base


def _mock_db(existing_user: object | None = None) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing_user
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


class TestEnsureSessionUserInDb:
    """Test suite for _ensure_session_user_in_db."""

    @pytest.mark.asyncio
    async def test_creates_user_when_missing(self) -> None:
        """User is created when not found in DB (debug mode)."""
        from app.api.dashboard._access import _ensure_session_user_in_db

        db = _mock_db(existing_user=None)
        auth = _auth()

        with patch("app.api.dashboard._access.get_settings", return_value=_settings(debug=True)):
            await _ensure_session_user_in_db(db, auth)

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        created = db.add.call_args[0][0]
        assert created.username == "testuser"
        assert created.full_name == "Test User"
        assert created.email == "testuser@dev.local"
        assert created.is_active is True
        assert created.role == "admin"
        assert created.gitlab_username == "testuser"

    @pytest.mark.asyncio
    async def test_skips_when_user_already_exists(self) -> None:
        """No new user is created when one already exists."""
        from app.api.dashboard._access import _ensure_session_user_in_db

        existing = MagicMock()
        db = _mock_db(existing_user=existing)
        auth = _auth()

        with patch("app.api.dashboard._access.get_settings", return_value=_settings(debug=True)):
            await _ensure_session_user_in_db(db, auth)

        db.add.assert_not_called()
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_create_when_not_debug(self) -> None:
        """Helper checks DB but does NOT create users outside debug mode."""
        from app.api.dashboard._access import _ensure_session_user_in_db

        db = _mock_db(existing_user=None)
        auth = _auth()

        with patch("app.api.dashboard._access.get_settings", return_value=_settings(debug=False)):
            await _ensure_session_user_in_db(db, auth)

        db.execute.assert_awaited_once()
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_noop_when_no_username(self) -> None:
        """Helper does nothing if auth dict has no username."""
        from app.api.dashboard._access import _ensure_session_user_in_db

        db = _mock_db(existing_user=None)
        auth = _auth(user="")

        with patch("app.api.dashboard._access.get_settings", return_value=_settings(debug=True)):
            await _ensure_session_user_in_db(db, auth)

        db.execute.assert_not_awaited()
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_uses_fallbacks_for_optional_fields(self) -> None:
        """When auth dict has minimal info, sensible defaults are used."""
        from app.api.dashboard._access import _ensure_session_user_in_db

        db = _mock_db(existing_user=None)
        auth: dict[str, str] = {"user": "minimal"}

        with patch("app.api.dashboard._access.get_settings", return_value=_settings(debug=True)):
            await _ensure_session_user_in_db(db, auth)

        db.add.assert_called_once()
        created = db.add.call_args[0][0]
        assert created.username == "minimal"
        assert created.full_name == "minimal"
        assert created.email == "minimal@dev.local"
        assert created.gitlab_username == "minimal"
        assert created.role == "student"
