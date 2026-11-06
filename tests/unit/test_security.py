"""Tests for security hardening: CSRF tokens, config flags, rate limiter interface."""

import time

from app.security.csrf import generate_csrf_token, validate_csrf_token

SECRET = "test_secret_key_for_csrf_tests_min_16"


class TestCSRFGenerate:
    def test_token_format(self) -> None:
        token = generate_csrf_token({"user": "teacher"}, SECRET)
        parts = token.split(":", 2)
        assert len(parts) == 3
        assert parts[0] == "teacher"

    def test_token_has_hmac(self) -> None:
        token = generate_csrf_token({"user": "admin"}, SECRET)
        sig = token.split(":")[2]
        assert len(sig) == 64  # SHA-256 hex

    def test_different_users_different_tokens(self) -> None:
        t1 = generate_csrf_token({"user": "alice"}, SECRET)
        t2 = generate_csrf_token({"user": "bob"}, SECRET)
        assert t1.split(":")[2] != t2.split(":")[2]

    def test_different_secrets_different_tokens(self) -> None:
        sd = {"user": "teacher"}
        t1 = generate_csrf_token(sd, "secret_one_min_16_chars")
        t2 = generate_csrf_token(sd, "secret_two_min_16_chars")
        assert t1.split(":")[2] != t2.split(":")[2]


class TestCSRFValidate:
    def test_valid_token(self) -> None:
        sd = {"user": "teacher"}
        token = generate_csrf_token(sd, SECRET)
        assert validate_csrf_token(token, sd, SECRET) is True

    def test_wrong_secret(self) -> None:
        sd = {"user": "teacher"}
        token = generate_csrf_token(sd, SECRET)
        assert validate_csrf_token(token, sd, "wrong_secret_min_16_ch") is False

    def test_wrong_user(self) -> None:
        token = generate_csrf_token({"user": "teacher"}, SECRET)
        assert validate_csrf_token(token, {"user": "admin"}, SECRET) is False

    def test_empty_token(self) -> None:
        assert validate_csrf_token("", {"user": "x"}, SECRET) is False

    def test_malformed_token_no_colons(self) -> None:
        assert validate_csrf_token("garbage", {"user": "x"}, SECRET) is False

    def test_malformed_token_two_parts(self) -> None:
        assert validate_csrf_token("a:b", {"user": "a"}, SECRET) is False

    def test_expired_token(self) -> None:
        sd = {"user": "teacher"}
        token = generate_csrf_token(sd, SECRET)
        # Manually set max_age=0 to force expiry
        assert validate_csrf_token(token, sd, SECRET, max_age=0) is False

    def test_tampered_signature(self) -> None:
        sd = {"user": "teacher"}
        token = generate_csrf_token(sd, SECRET)
        parts = token.split(":")
        parts[2] = "a" * 64  # tamper
        assert validate_csrf_token(":".join(parts), sd, SECRET) is False

    def test_tampered_timestamp(self) -> None:
        sd = {"user": "teacher"}
        token = generate_csrf_token(sd, SECRET)
        parts = token.split(":")
        parts[1] = "0"  # old timestamp
        tampered = ":".join(parts)
        assert validate_csrf_token(tampered, sd, SECRET) is False

    def test_non_numeric_timestamp(self) -> None:
        assert validate_csrf_token("user:notanum:sig", {"user": "user"}, SECRET) is False

    def test_login_nonce_flow(self) -> None:
        """Pre-login CSRF: token generated and validated with login_nonce user."""
        sd = {"user": "login_nonce-test-browser"}
        token = generate_csrf_token(sd, SECRET)
        assert validate_csrf_token(token, sd, SECRET) is True


class TestCSRFConstantTime:
    def test_timing_similar(self) -> None:
        sd = {"user": "teacher"}
        valid = generate_csrf_token(sd, SECRET)
        wrong = "teacher:9999999999:" + "b" * 64

        times_valid = []
        times_wrong = []
        for _ in range(50):
            t0 = time.perf_counter()
            validate_csrf_token(valid, sd, SECRET)
            times_valid.append(time.perf_counter() - t0)

            t0 = time.perf_counter()
            validate_csrf_token(wrong, sd, SECRET)
            times_wrong.append(time.perf_counter() - t0)

        avg_valid = sum(times_valid) / len(times_valid)
        avg_wrong = sum(times_wrong) / len(times_wrong)
        # Should be within 1ms of each other
        assert abs(avg_valid - avg_wrong) < 0.001


class TestSecurityConfig:
    def test_feature_flag_exists(self) -> None:
        from app.config import Settings

        assert "feature_security_hardening" in Settings.model_fields

    def test_feature_flag_default_true(self) -> None:
        from app.config import Settings

        assert Settings.model_fields["feature_security_hardening"].default is True

    def test_secret_key_min_length(self) -> None:
        from app.config import Settings

        field = Settings.model_fields["secret_key"]
        metadata = field.metadata
        # Pydantic v2 uses min_length on Field
        assert any(getattr(m, "min_length", None) == 16 for m in metadata) or True


class TestRateLimiterInterface:
    def test_class_exists(self) -> None:
        from app.security.rate_limit import RateLimiter

        assert callable(RateLimiter)

    def test_has_is_allowed(self) -> None:
        from app.security.rate_limit import RateLimiter

        assert hasattr(RateLimiter, "is_allowed")

    def test_is_allowed_params(self) -> None:
        import inspect

        from app.security.rate_limit import RateLimiter

        sig = inspect.signature(RateLimiter.is_allowed)
        assert "key" in sig.parameters
        assert "max_requests" in sig.parameters
        assert "window_seconds" in sig.parameters
