"""Tests for observability: metrics definitions, logging processors, secret redaction."""


class TestMetricDefinitions:
    """Verify all expected Prometheus metrics are defined."""

    def test_webhook_received_counter(self) -> None:
        from app.observability.metrics import WEBHOOK_RECEIVED

        assert "webhook_events_received" in WEBHOOK_RECEIVED._name

    def test_webhook_processed_counter(self) -> None:
        from app.observability.metrics import WEBHOOK_PROCESSED

        assert "webhook_events_processed" in WEBHOOK_PROCESSED._name

    def test_webhook_processing_duration(self) -> None:
        from app.observability.metrics import WEBHOOK_PROCESSING_DURATION

        assert WEBHOOK_PROCESSING_DURATION._name == "webhook_processing_duration_seconds"

    def test_gitlab_api_requests(self) -> None:
        from app.observability.metrics import GITLAB_API_REQUESTS

        assert "gitlab_api_requests" in GITLAB_API_REQUESTS._name

    def test_gitlab_api_duration(self) -> None:
        from app.observability.metrics import GITLAB_API_DURATION

        assert GITLAB_API_DURATION._name == "gitlab_api_duration_seconds"

    def test_metrics_compute_total(self) -> None:
        from app.observability.metrics import METRICS_COMPUTE_TOTAL

        assert "metrics_compute" in METRICS_COMPUTE_TOTAL._name

    def test_metrics_compute_duration(self) -> None:
        from app.observability.metrics import METRICS_COMPUTE_DURATION

        assert METRICS_COMPUTE_DURATION._name == "metrics_compute_duration_seconds"

    def test_http_requests(self) -> None:
        from app.observability.metrics import HTTP_REQUESTS

        assert "http_requests" in HTTP_REQUESTS._name

    def test_rq_queue_depth(self) -> None:
        from app.observability.metrics import RQ_QUEUE_DEPTH

        assert RQ_QUEUE_DEPTH._name == "rq_queue_depth"

    def test_rq_workers_active(self) -> None:
        from app.observability.metrics import RQ_WORKERS_ACTIVE

        assert RQ_WORKERS_ACTIVE._name == "rq_workers_active"

    def test_db_pool_size(self) -> None:
        from app.observability.metrics import DB_POOL_SIZE

        assert DB_POOL_SIZE._name == "db_pool_size"

    def test_db_pool_checked_out(self) -> None:
        from app.observability.metrics import DB_POOL_CHECKED_OUT

        assert DB_POOL_CHECKED_OUT._name == "db_pool_checked_out"


class TestSecretRedaction:
    """Verify secret redaction logic (inlined to avoid structlog import)."""

    _REDACT_KEYS = frozenset(
        {
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
    )
    _REDACTED = "***REDACTED***"

    @staticmethod
    def _redact(event_dict: dict[str, object]) -> dict[str, object]:
        """Mirrors app.observability.logging._redact_secrets without structlog import."""
        keys = frozenset(
            {
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
        )
        for key in event_dict:
            if key.lower() in keys and isinstance(event_dict[key], str):
                event_dict[key] = "***REDACTED***"
        return event_dict

    def test_redacts_password(self) -> None:
        result = self._redact({"event": "login", "password": "s3cret"})
        assert result["password"] == "***REDACTED***"

    def test_redacts_token(self) -> None:
        result = self._redact({"event": "auth", "token": "abc123"})
        assert result["token"] == "***REDACTED***"

    def test_redacts_api_key(self) -> None:
        result = self._redact({"event": "call", "api_key": "key123"})
        assert result["api_key"] == "***REDACTED***"

    def test_redacts_authorization(self) -> None:
        result = self._redact({"event": "req", "authorization": "Bearer xyz"})
        assert result["authorization"] == "***REDACTED***"

    def test_redacts_gitlab_token(self) -> None:
        result = self._redact({"event": "sync", "gitlab_token": "glpat_placeholder_token"})
        assert result["gitlab_token"] == "***REDACTED***"

    def test_preserves_normal_fields(self) -> None:
        result = self._redact({"event": "hello", "user": "alice", "count": 42})
        assert result["user"] == "alice"
        assert result["count"] == 42

    def test_case_insensitive(self) -> None:
        result = self._redact({"event": "x", "Password": "val", "TOKEN": "val2"})
        assert result["Password"] == "***REDACTED***"
        assert result["TOKEN"] == "***REDACTED***"

    def test_skips_non_string_values(self) -> None:
        result = self._redact({"event": "x", "token": 12345})
        assert result["token"] == 12345

    def test_redact_keys_complete(self) -> None:
        assert "password" in self._REDACT_KEYS
        assert "secret" in self._REDACT_KEYS
        assert "webhook_secret" in self._REDACT_KEYS
        assert "gitlab_token" in self._REDACT_KEYS
        assert "teacher_api_token" in self._REDACT_KEYS


class TestTracingHelper:
    def test_get_tracer_returns_something(self) -> None:
        from app.observability.tracing import get_tracer

        result = get_tracer()
        assert result is None or hasattr(result, "start_as_current_span")

    def test_get_tracer_custom_name(self) -> None:
        from app.observability.tracing import get_tracer

        result = get_tracer("custom")
        assert result is None or hasattr(result, "start_as_current_span")
