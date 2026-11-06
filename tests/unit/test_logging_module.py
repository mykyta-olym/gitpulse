"""Tests for observability logging module."""

from collections.abc import MutableMapping
from typing import Any


class TestRedactSecretsProcessor:
    """Tests for _redact_secrets processor function."""

    def test_redact_secrets_function_exists(self) -> None:
        from app.observability.logging import _redact_secrets

        assert callable(_redact_secrets)

    def test_redact_password(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "password": "secret123"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["password"] == "***REDACTED***"

    def test_redact_token(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "token": "abc123"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["token"] == "***REDACTED***"

    def test_redact_secret(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "secret": "mysecret"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["secret"] == "***REDACTED***"

    def test_redact_api_key(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "api_key": "key123"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["api_key"] == "***REDACTED***"

    def test_redact_authorization(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "authorization": "Bearer xxx"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["authorization"] == "***REDACTED***"

    def test_redact_private_token(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "private_token": "glpat_placeholder_token"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["private_token"] == "***REDACTED***"

    def test_redact_secret_key(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "secret_key": "mykey"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["secret_key"] == "***REDACTED***"

    def test_redact_gitlab_token(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "gitlab_token": "glpat_placeholder_token"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["gitlab_token"] == "***REDACTED***"

    def test_redact_teacher_api_token(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "teacher_api_token": "token"}
        result = _redact_secrets(None, "info", event_dict)
        assert result["teacher_api_token"] == "***REDACTED***"

    def test_preserves_non_secret_fields(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {
            "event": "test",
            "user": "alice",
            "count": 42,
        }
        result = _redact_secrets(None, "info", event_dict)
        assert result["event"] == "test"
        assert result["user"] == "alice"
        assert result["count"] == 42

    def test_skips_non_string_values(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test", "token": 12345}
        result = _redact_secrets(None, "info", event_dict)
        assert result["token"] == 12345  # Not redacted because not a string

    def test_returns_same_dict(self) -> None:
        from app.observability.logging import _redact_secrets

        event_dict: MutableMapping[str, Any] = {"event": "test"}
        result = _redact_secrets(None, "info", event_dict)
        assert result is event_dict


class TestAddServiceNameProcessor:
    """Tests for _add_service_name processor function."""

    def test_add_service_name_function_exists(self) -> None:
        from app.observability.logging import _add_service_name

        assert callable(_add_service_name)

    def test_adds_service_name(self) -> None:
        from app.observability.logging import _add_service_name

        event_dict: MutableMapping[str, Any] = {"event": "test"}
        result = _add_service_name(None, "info", event_dict)
        assert result["service"] == "gitpulse"

    def test_preserves_existing_fields(self) -> None:
        from app.observability.logging import _add_service_name

        event_dict: MutableMapping[str, Any] = {"event": "test", "user": "alice"}
        result = _add_service_name(None, "info", event_dict)
        assert result["event"] == "test"
        assert result["user"] == "alice"
        assert result["service"] == "gitpulse"


class TestAddOtelTraceContext:
    """Tests for _add_otel_trace_context processor function."""

    def test_add_otel_trace_context_function_exists(self) -> None:
        from app.observability.logging import _add_otel_trace_context

        assert callable(_add_otel_trace_context)

    def test_handles_no_otel_installed(self) -> None:
        from app.observability.logging import _add_otel_trace_context

        event_dict: MutableMapping[str, Any] = {"event": "test"}
        # Should not raise even if OpenTelemetry is not configured
        result = _add_otel_trace_context(None, "info", event_dict)
        assert result is event_dict

    def test_preserves_event_dict(self) -> None:
        from app.observability.logging import _add_otel_trace_context

        event_dict: MutableMapping[str, Any] = {"event": "test", "data": "value"}
        result = _add_otel_trace_context(None, "info", event_dict)
        assert result["event"] == "test"
        assert result["data"] == "value"


class TestRedactKeysConstant:
    """Tests for _REDACT_KEYS constant."""

    def test_redact_keys_contains_expected_keys(self) -> None:
        from app.observability.logging import _REDACT_KEYS

        expected_keys = {
            "password",
            "token",
            "secret",
            "api_key",
            "authorization",
            "private_token",
            "secret_key",
            "password_hash",
            "webhook_secret",
            "gitlab_token",
            "teacher_api_token",
            "dashboard_password_hash",
        }
        assert expected_keys.issubset(_REDACT_KEYS)

    def test_redact_keys_is_frozenset(self) -> None:
        from app.observability.logging import _REDACT_KEYS

        assert isinstance(_REDACT_KEYS, frozenset)


class TestRedactedConstant:
    """Tests for _REDACTED constant."""

    def test_redacted_value(self) -> None:
        from app.observability.logging import _REDACTED

        assert _REDACTED == "***REDACTED***"


class TestRedactUrlCredentials:
    def test_redacts_password_with_empty_redis_username(self) -> None:
        from app.observability.logging import redact_url_credentials

        redacted = redact_url_credentials("redis://:secret@redis:6379/0")
        assert redacted == "redis://:***REDACTED***@redis:6379/0"
        assert "secret" not in redacted

    def test_redacts_username_password_pair(self) -> None:
        from app.observability.logging import redact_url_credentials

        redacted = redact_url_credentials("postgresql://user:secret@db:5432/app")
        assert redacted == "postgresql://user:***REDACTED***@db:5432/app"
        assert "secret" not in redacted

    def test_preserves_url_without_credentials(self) -> None:
        from app.observability.logging import redact_url_credentials

        assert redact_url_credentials("redis://redis:6379/0") == "redis://redis:6379/0"


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_function_exists(self) -> None:
        from app.observability.logging import setup_logging

        assert callable(setup_logging)

    def test_setup_logging_with_json_format(self) -> None:
        from app.config import LogFormat
        from app.observability.logging import setup_logging

        # Should not raise
        setup_logging(level="info", fmt=LogFormat.JSON)

    def test_setup_logging_with_console_format(self) -> None:
        from app.config import LogFormat
        from app.observability.logging import setup_logging

        # Should not raise
        setup_logging(level="debug", fmt=LogFormat.CONSOLE)

    def test_setup_logging_default_params(self) -> None:
        from app.observability.logging import setup_logging

        # Should not raise with defaults
        setup_logging()

    def test_setup_logging_various_levels(self) -> None:
        from app.config import LogFormat
        from app.observability.logging import setup_logging

        for level in ["debug", "info", "warning", "error", "critical"]:
            # Should not raise
            setup_logging(level=level, fmt=LogFormat.JSON)
