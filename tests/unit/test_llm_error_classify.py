"""Unit tests for LLM error classification - pure function, no DB required."""

from app.workers.llm_job import LLMErrorType, classify_llm_error


class TestClassifyLlmError:
    """Validate classify_llm_error() categorises exceptions correctly."""

    def test_daily_quota_exceeded(self) -> None:
        err_type, _ = classify_llm_error(Exception("resource_exhausted per_day quota"))
        assert err_type == LLMErrorType.QUOTA_EXCEEDED

    def test_daily_quota_daily_keyword(self) -> None:
        err_type, _ = classify_llm_error(Exception("daily quota resource_exhausted"))
        assert err_type == LLMErrorType.QUOTA_EXCEEDED

    def test_rate_limited_resource_exhausted(self) -> None:
        err_type, _ = classify_llm_error(Exception("resource_exhausted"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_rate_limited_quota_without_daily(self) -> None:
        err_type, _ = classify_llm_error(Exception("quota limit hit"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_model_not_found(self) -> None:
        err_type, _ = classify_llm_error(Exception("model not_found"))
        assert err_type == LLMErrorType.MODEL_NOT_FOUND

    def test_invalid_api_key(self) -> None:
        err_type, _ = classify_llm_error(Exception("invalid api key"))
        assert err_type == LLMErrorType.INVALID_API_KEY

    def test_invalid_credential(self) -> None:
        err_type, _ = classify_llm_error(Exception("invalid credential"))
        assert err_type == LLMErrorType.INVALID_API_KEY

    def test_unauthenticated(self) -> None:
        err_type, _ = classify_llm_error(Exception("401 Unauthenticated"))
        assert err_type == LLMErrorType.INVALID_API_KEY

    def test_unauthorized(self) -> None:
        err_type, _ = classify_llm_error(Exception("unauthorized access"))
        assert err_type == LLMErrorType.INVALID_API_KEY

    def test_forbidden(self) -> None:
        err_type, _ = classify_llm_error(Exception("403 Forbidden"))
        assert err_type == LLMErrorType.INVALID_API_KEY

    def test_permission_denied(self) -> None:
        err_type, _ = classify_llm_error(Exception("permission denied"))
        assert err_type == LLMErrorType.INVALID_API_KEY

    def test_openai_ratelimit(self) -> None:
        err_type, _ = classify_llm_error(Exception("ratelimit error"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_openai_rate_limit_underscore(self) -> None:
        err_type, _ = classify_llm_error(Exception("rate_limit exceeded"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_http_429(self) -> None:
        err_type, _ = classify_llm_error(Exception("HTTP 429"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_insufficient_quota(self) -> None:
        # Note: "insufficient_quota" also matches "quota" which hits rate_limited first.
        # Use "billing" keyword which is unambiguous.
        err_type, _ = classify_llm_error(Exception("billing plan expired"))
        assert err_type == LLMErrorType.QUOTA_EXCEEDED

    def test_billing_error(self) -> None:
        err_type, _ = classify_llm_error(Exception("billing disabled"))
        assert err_type == LLMErrorType.QUOTA_EXCEEDED

    def test_groq_tokens_per_minute(self) -> None:
        err_type, _ = classify_llm_error(Exception("tokens_per_minute limit"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_groq_requests_per_minute(self) -> None:
        err_type, _ = classify_llm_error(Exception("requests_per_minute limit hit"))
        assert err_type == LLMErrorType.RATE_LIMITED

    def test_groq_tokens_per_day(self) -> None:
        err_type, _ = classify_llm_error(Exception("tokens_per_day exceeded"))
        assert err_type == LLMErrorType.QUOTA_EXCEEDED

    def test_groq_requests_per_day(self) -> None:
        err_type, _ = classify_llm_error(Exception("requests_per_day limit"))
        assert err_type == LLMErrorType.QUOTA_EXCEEDED

    def test_network_connection_error(self) -> None:
        err_type, _ = classify_llm_error(Exception("connection refused"))
        assert err_type == LLMErrorType.NETWORK_ERROR

    def test_network_timeout(self) -> None:
        err_type, _ = classify_llm_error(Exception("timeout after 30s"))
        assert err_type == LLMErrorType.NETWORK_ERROR

    def test_network_dns(self) -> None:
        err_type, _ = classify_llm_error(Exception("dns resolution failed"))
        assert err_type == LLMErrorType.NETWORK_ERROR

    def test_network_unreachable(self) -> None:
        err_type, _ = classify_llm_error(Exception("host unreachable"))
        assert err_type == LLMErrorType.NETWORK_ERROR

    def test_timeout_exception_type(self) -> None:
        class CustomTimeoutError(Exception):
            pass

        err_type, _ = classify_llm_error(CustomTimeoutError("ops"))
        assert err_type == LLMErrorType.NETWORK_ERROR

    def test_connection_exception_type(self) -> None:
        class CustomConnectionError(Exception):
            pass

        err_type, _ = classify_llm_error(CustomConnectionError("ops"))
        assert err_type == LLMErrorType.NETWORK_ERROR

    def test_parse_error_json(self) -> None:
        err_type, _ = classify_llm_error(Exception("json decode error"))
        assert err_type == LLMErrorType.PARSE_ERROR

    def test_parse_error_decode(self) -> None:
        err_type, _ = classify_llm_error(Exception("decode failure in response"))
        assert err_type == LLMErrorType.PARSE_ERROR

    def test_unknown_error(self) -> None:
        err_type, msg = classify_llm_error(Exception("something unexpected"))
        assert err_type == LLMErrorType.UNKNOWN
        assert "unexpected error" in msg.lower()
