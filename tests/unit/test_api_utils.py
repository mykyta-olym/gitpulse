"""Unit tests for app.api.helpers.utils helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestGetActor:
    def test_returns_username_from_session(self):
        from app.api.helpers.utils import get_actor

        request = MagicMock()
        mock_settings = MagicMock()
        mock_settings.secret_key = "s"
        mock_settings.session_max_age_seconds = 3600
        mock_settings.app_base_url = "http://localhost"

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch(
                "app.security.session_auth.get_current_session",
                return_value={"user": "alice"},
            ),
        ):
            result = get_actor(request)
        assert result == "alice"

    def test_returns_fallback_when_no_session(self):
        from app.api.helpers.utils import get_actor

        request = MagicMock()
        mock_settings = MagicMock()
        mock_settings.secret_key = "s"
        mock_settings.session_max_age_seconds = 3600
        mock_settings.app_base_url = "http://localhost"

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch("app.security.session_auth.get_current_session", return_value=None),
        ):
            result = get_actor(request)
        assert result == "session"

    def test_returns_fallback_on_exception(self):
        from app.api.helpers.utils import get_actor

        request = MagicMock()

        with patch("app.config.get_settings", side_effect=RuntimeError("boom")):
            result = get_actor(request, fallback="anon")
        assert result == "anon"

    def test_custom_fallback(self):
        from app.api.helpers.utils import get_actor

        request = MagicMock()
        mock_settings = MagicMock()
        mock_settings.secret_key = "s"
        mock_settings.session_max_age_seconds = 3600
        mock_settings.app_base_url = "http://localhost"

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch("app.security.session_auth.get_current_session", return_value=None),
        ):
            result = get_actor(request, fallback="system")
        assert result == "system"


class TestCheckCourseAccess:
    @pytest.mark.asyncio
    async def test_api_token_skips_checks(self):
        from app.api.helpers.utils import check_course_access

        await check_course_access(
            course=MagicMock(),
            auth_kind="api_token",
            request=MagicMock(),
            db=MagicMock(),
        )

    @pytest.mark.asyncio
    async def test_admin_role_allowed(self):
        from app.api.helpers.utils import check_course_access

        mock_settings = MagicMock()

        with (
            patch("app.config.get_settings", return_value=mock_settings),
            patch(
                "app.dependencies._validate_session",
                return_value={"role": "admin", "gitlab_username": "a", "user": "a"},
            ),
        ):
            await check_course_access(
                course=MagicMock(),
                auth_kind="session",
                request=MagicMock(),
                db=MagicMock(),
            )


class TestResolveCaller:
    @pytest.mark.asyncio
    async def test_api_token_returns_none_admin(self):
        from app.api.helpers.utils import _resolve_caller

        user, role = await _resolve_caller(MagicMock(), MagicMock(), "api_token")
        assert user is None
        assert role == "admin"
