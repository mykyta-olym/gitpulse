"""Tests for the HTTP rate-limiting middleware (in-memory sliding window).

Covers:
- _InMemoryLimiter: window expiry, cleanup, max-entries safeguard
- _get_tier: correct tier classification for auth/webhook/mutation/read
- _get_client_ip: forwarded-for parsing
- _is_browser_navigation: HTMX vs browser detection
- RateLimitMiddleware: full ASGI integration (allow / deny / headers)
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any
from unittest.mock import patch

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.middleware.rate_limit import (
    _AUTH_PATHS,
    _EXEMPT_PATHS,
    _EXEMPT_PREFIXES,
    _TIER_AUTH,
    _TIER_MUTATION,
    _TIER_READ,
    _TIER_WEBHOOK,
    RateLimitMiddleware,
    _get_client_ip,
    _get_tier,
    _InMemoryLimiter,
    _is_browser_navigation,
    _is_exempt_path,
)

# -- _InMemoryLimiter unit tests -----------------------------------------


class TestInMemoryLimiter:
    """Direct tests for the sliding-window counter."""

    def test_first_request_allowed(self) -> None:
        limiter = _InMemoryLimiter()
        allowed, remaining = limiter.is_allowed("k", 5, 60)
        assert allowed is True
        assert remaining == 4

    def test_requests_up_to_limit(self) -> None:
        limiter = _InMemoryLimiter()
        for _i in range(5):
            allowed, remaining = limiter.is_allowed("k", 5, 60)
        assert allowed is True
        assert remaining == 0

    def test_request_over_limit_denied(self) -> None:
        limiter = _InMemoryLimiter()
        for _ in range(5):
            limiter.is_allowed("k", 5, 60)
        allowed, remaining = limiter.is_allowed("k", 5, 60)
        assert allowed is False
        assert remaining == 0

    def test_different_keys_independent(self) -> None:
        limiter = _InMemoryLimiter()
        for _ in range(5):
            limiter.is_allowed("a", 5, 60)
        # key "b" should still be allowed
        allowed, _ = limiter.is_allowed("b", 5, 60)
        assert allowed is True

    def test_window_expiry(self) -> None:
        limiter = _InMemoryLimiter()
        # Fill up the window
        for _ in range(5):
            limiter.is_allowed("k", 5, 60)
        # Simulate time passing beyond the window
        with patch("app.middleware.rate_limit.time") as mock_time:
            # All existing entries were created at ~real time.monotonic()
            # We advance monotonic so they become stale
            mock_time.monotonic.return_value = time.monotonic() + 61
            allowed, remaining = limiter.is_allowed("k", 5, 61)
        # Old entries pruned, only the new one remains
        assert allowed is True
        assert remaining == 4

    def test_cleanup_removes_stale_keys(self) -> None:
        limiter = _InMemoryLimiter()
        limiter.is_allowed("old_key", 10, 60)
        # Artificially age the entries
        with limiter._lock:
            limiter._windows["old_key"] = deque([time.monotonic() - 400])
        limiter.cleanup(older_than=300)
        with limiter._lock:
            assert "old_key" not in limiter._windows

    def test_cleanup_keeps_fresh_keys(self) -> None:
        limiter = _InMemoryLimiter()
        limiter.is_allowed("fresh", 10, 60)
        limiter.cleanup(older_than=300)
        with limiter._lock:
            assert "fresh" in limiter._windows

    def test_max_entries_safeguard(self) -> None:
        limiter = _InMemoryLimiter()
        limiter._MAX_ENTRIES = 10  # lower for testing
        # Fill with stale entries
        with limiter._lock:
            for i in range(15):
                limiter._windows[f"stale_{i}"] = deque([time.monotonic() - 200])
        # Next call should trigger cleanup
        allowed, _ = limiter.is_allowed("new_key", 100, 60)
        assert allowed is True
        with limiter._lock:
            # Stale entries should be cleaned up
            assert len(limiter._windows) <= 12  # some cleaned + new_key

    def test_remaining_count_decreases(self) -> None:
        limiter = _InMemoryLimiter()
        _, r1 = limiter.is_allowed("k", 3, 60)
        _, r2 = limiter.is_allowed("k", 3, 60)
        _, r3 = limiter.is_allowed("k", 3, 60)
        assert r1 == 2
        assert r2 == 1
        assert r3 == 0


# -- Tier classification tests -------------------------------------------


class TestGetTier:
    """Verify request routing to the correct rate-limit tier."""

    def test_auth_login_path(self) -> None:
        assert _get_tier("/dashboard/login", "GET") == _TIER_AUTH

    def test_auth_callback_path(self) -> None:
        assert _get_tier("/dashboard/oauth/callback", "GET") == _TIER_AUTH

    def test_auth_api_path(self) -> None:
        assert _get_tier("/api/v1/auth", "POST") == _TIER_AUTH

    def test_webhook_path(self) -> None:
        assert _get_tier("/api/v1/webhooks/push", "POST") == _TIER_WEBHOOK

    def test_mutation_post(self) -> None:
        assert _get_tier("/dashboard/courses/1/settings", "POST") == _TIER_MUTATION

    def test_mutation_put(self) -> None:
        assert _get_tier("/api/v1/check", "PUT") == _TIER_MUTATION

    def test_mutation_patch(self) -> None:
        assert _get_tier("/api/v1/check", "PATCH") == _TIER_MUTATION

    def test_mutation_delete(self) -> None:
        assert _get_tier("/api/v1/check", "DELETE") == _TIER_MUTATION

    def test_read_get(self) -> None:
        assert _get_tier("/dashboard/courses", "GET") == _TIER_READ

    def test_read_head(self) -> None:
        assert _get_tier("/dashboard/courses", "HEAD") == _TIER_READ

    def test_read_options(self) -> None:
        assert _get_tier("/dashboard/courses", "OPTIONS") == _TIER_READ

    def test_auth_takes_precedence_over_mutation(self) -> None:
        """POST to login should be auth tier, not mutation."""
        assert _get_tier("/dashboard/login", "POST") == _TIER_AUTH

    def test_webhook_takes_precedence_over_mutation(self) -> None:
        """POST to webhooks should be webhook tier, not mutation."""
        assert _get_tier("/api/v1/webhooks/push", "POST") == _TIER_WEBHOOK


# -- Client IP extraction tests ------------------------------------------


class TestGetClientIp:
    """Verify IP extraction from forwarded headers and direct connections."""

    def _make_request(
        self,
        headers: dict[str, str] | None = None,
        client_host: str | None = "127.0.0.1",
    ) -> Request:
        scope: dict[str, Any] = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "query_string": b"",
        }
        if client_host:
            scope["client"] = (client_host, 12345)
        return Request(scope)

    def test_direct_connection(self) -> None:
        req = self._make_request()
        assert _get_client_ip(req) == "127.0.0.1"

    def test_single_forwarded_ip(self) -> None:
        req = self._make_request(headers={"x-forwarded-for": "10.0.0.1"})
        assert _get_client_ip(req) == "127.0.0.1"

    def test_multiple_forwarded_ips_uses_normalised_client(self) -> None:
        req = self._make_request(headers={"x-forwarded-for": "10.0.0.1, 172.16.0.1, 192.168.1.1"})
        assert _get_client_ip(req) == "127.0.0.1"

    def test_no_client_returns_unknown(self) -> None:
        scope: dict[str, Any] = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }
        req = Request(scope)
        assert _get_client_ip(req) == "unknown"


# -- Browser navigation detection tests ----------------------------------


class TestIsBrowserNavigation:
    def _make_request(self, method: str = "GET", headers: dict[str, str] | None = None) -> Request:
        scope: dict[str, Any] = {
            "type": "http",
            "method": method,
            "path": "/",
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
        }
        return Request(scope)

    def test_html_accept_is_browser(self) -> None:
        req = self._make_request(headers={"accept": "text/html,application/xhtml+xml"})
        assert _is_browser_navigation(req) is True

    def test_htmx_request_is_not_browser(self) -> None:
        req = self._make_request(headers={"hx-request": "true", "accept": "text/html"})
        assert _is_browser_navigation(req) is False

    def test_json_api_is_not_browser(self) -> None:
        req = self._make_request(headers={"accept": "application/json"})
        assert _is_browser_navigation(req) is False

    def test_form_post_without_accept_is_browser(self) -> None:
        req = self._make_request(method="POST")
        assert _is_browser_navigation(req) is True

    def test_json_post_is_not_browser(self) -> None:
        req = self._make_request(method="POST", headers={"accept": "application/json"})
        assert _is_browser_navigation(req) is False


# -- Full middleware ASGI integration tests ------------------------------


def _make_test_app(enabled: bool = True, dev_mode: bool = False) -> TestClient:
    """Build a minimal Starlette app wrapped with RateLimitMiddleware."""

    async def homepage(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def login(request: Request) -> PlainTextResponse:
        return PlainTextResponse("login")

    async def webhook(request: Request) -> PlainTextResponse:
        return PlainTextResponse("webhook")

    async def health(request: Request) -> PlainTextResponse:
        return PlainTextResponse("healthy")

    async def api_data(request: Request) -> PlainTextResponse:
        return PlainTextResponse("data")

    app = Starlette(
        routes=[
            Route("/dashboard/", homepage),
            Route("/dashboard/login", login, methods=["GET", "POST"]),
            Route("/api/v1/webhooks/push", webhook, methods=["POST"]),
            Route("/api/v1/webhooks/gitlab", webhook, methods=["POST"]),
            Route("/api/v1/data", api_data, methods=["GET", "POST", "PUT", "DELETE", "PATCH"]),
            Route("/health", health),
            Route("/static/test.js", homepage),
        ],
    )
    app.add_middleware(RateLimitMiddleware, enabled=enabled, dev_mode=dev_mode)
    return TestClient(app, raise_server_exceptions=False)


class TestRateLimitMiddlewareIntegration:
    """End-to-end tests for the ASGI middleware."""

    def test_allowed_request_has_rate_headers(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(True, 119)):
            resp = client.get("/dashboard/")
        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == str(_TIER_READ[0])
        assert resp.headers["x-ratelimit-remaining"] == "119"

    def test_denied_browser_returns_html_429(self) -> None:
        # The app's one error page, its assets linked like every other page's.
        from app.main import static_url

        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(False, 0)):
            resp = client.get("/dashboard/", headers={"accept": "text/html"})
        assert resp.status_code == 429
        assert "429" in resp.text
        assert resp.headers["retry-after"] == "60"
        assert static_url("favicon.svg") in resp.text
        assert static_url("css/error.css") in resp.text
        assert static_url("img/error-429.svg") in resp.text

    def test_denied_api_returns_json_429(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(False, 0)):
            resp = client.get("/dashboard/", headers={"accept": "application/json"})
        assert resp.status_code == 429
        data = resp.json()
        assert "rate limit" in data["detail"].lower()

    def test_denied_htmx_returns_json_429(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(False, 0)):
            resp = client.get(
                "/dashboard/",
                headers={"hx-request": "true", "accept": "text/html"},
            )
        assert resp.status_code == 429
        data = resp.json()
        assert "rate limit" in data["detail"].lower()

    def test_exempt_static_path(self) -> None:
        client = _make_test_app()
        # Static paths skip rate limiting entirely - limiter not called
        with patch.object(_InMemoryLimiter, "is_allowed") as mock_allowed:
            resp = client.get("/static/test.js")
        mock_allowed.assert_not_called()
        assert resp.status_code == 200

    def test_exempt_health_path(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed") as mock_allowed:
            resp = client.get("/health")
        mock_allowed.assert_not_called()
        assert resp.status_code == 200

    def test_disabled_middleware_passes_through(self) -> None:
        client = _make_test_app(enabled=False)
        with patch.object(_InMemoryLimiter, "is_allowed") as mock_allowed:
            resp = client.get("/dashboard/")
        mock_allowed.assert_not_called()
        assert resp.status_code == 200

    def test_dev_mode_exempts_localhost(self) -> None:
        client = _make_test_app(enabled=True, dev_mode=True)
        with patch.object(_InMemoryLimiter, "is_allowed") as mock_allowed:
            resp = client.get("/dashboard/login")
        mock_allowed.assert_not_called()
        assert resp.status_code == 200

    def test_auth_tier_used_for_login(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(True, 9)) as mock:
            client.get("/dashboard/login")
        call_args = mock.call_args
        assert call_args[0][1] == _TIER_AUTH[0]  # max_requests=10
        assert call_args[0][2] == _TIER_AUTH[1]  # window=60

    def test_webhook_tier_used(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(True, 99)) as mock:
            client.post("/api/v1/webhooks/push")
        call_args = mock.call_args
        assert call_args[0][1] == _TIER_WEBHOOK[0]  # max_requests=100

    def test_mutation_tier_for_post(self) -> None:
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(True, 29)) as mock:
            client.post("/dashboard/")
        call_args = mock.call_args
        assert call_args[0][1] == _TIER_MUTATION[0]  # max_requests=30

    def test_rate_key_includes_session_cookie(self) -> None:
        """Authenticated users get their own counter, not shared by IP."""
        client = _make_test_app()
        client.cookies.set("gitpulse_session", "user123")
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(True, 119)) as mock:
            client.get("/dashboard/")
        rate_key = mock.call_args[0][0]
        assert "user123" in rate_key

    def test_rate_key_without_session(self) -> None:
        """Unauthenticated users are tracked by IP only."""
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(True, 119)) as mock:
            client.get("/dashboard/")
        rate_key = mock.call_args[0][0]
        assert ":read" in rate_key
        # No session portion in key - just IP:tier
        parts = rate_key.split(":")
        assert len(parts) == 2  # "ip:tier"


# -- Exempt prefixes coverage --------------------------------------------


class TestExemptPrefixes:
    """Ensure all documented exempt prefixes are checked."""

    def test_all_exempt_prefixes_exist(self) -> None:
        expected = {"/static/", "/favicon", "/docs", "/redoc", "/openapi.json"}
        assert set(_EXEMPT_PREFIXES) == expected
        assert frozenset({"/health", "/health/live", "/health/ready", "/metrics"}) == _EXEMPT_PATHS
        assert _is_exempt_path("/health")
        assert not _is_exempt_path("/health/gitlab")

    def test_auth_paths_exist(self) -> None:
        expected = {
            "/dashboard/login",
            "/dashboard/auth/callback",
            "/dashboard/oauth/callback",
            "/api/v1/auth",
        }
        assert set(_AUTH_PATHS) == expected


# -- Edge-case & stress tests -------------------------------------------


class TestLimiterEdgeCases:
    """Stress & edge-case tests for the sliding-window limiter."""

    def test_burst_exactly_at_limit(self) -> None:
        """Burst of exactly N requests should allow all N, deny N+1."""
        limiter = _InMemoryLimiter()
        for i in range(10):
            allowed, _ = limiter.is_allowed("burst", 10, 60)
            assert allowed is True, f"Request {i + 1} should be allowed"
        allowed, remaining = limiter.is_allowed("burst", 10, 60)
        assert allowed is False
        assert remaining == 0

    def test_window_rollover(self) -> None:
        """After window expires, requests should be allowed again."""
        limiter = _InMemoryLimiter()
        # Fill the window
        for _ in range(5):
            limiter.is_allowed("roll", 5, 1)
        allowed, _ = limiter.is_allowed("roll", 5, 1)
        assert allowed is False
        # Simulate time passing beyond window
        with patch("app.middleware.rate_limit.time") as mock_time:
            mock_time.monotonic.return_value = time.monotonic() + 2
            # Internal entries were recorded with real monotonic, so
            # the cutoff calculation should prune them
        # Use a fresh limiter to test rollover conceptually
        limiter2 = _InMemoryLimiter()
        # Inject old timestamps
        old_time = time.monotonic() - 120
        limiter2._windows["roll2"] = deque([old_time, old_time + 0.1, old_time + 0.2])
        allowed, remaining = limiter2.is_allowed("roll2", 5, 60)
        assert allowed is True
        assert remaining == 4  # old entries pruned, only new one counts

    def test_independent_keys_isolated(self) -> None:
        """Different keys should have independent counters."""
        limiter = _InMemoryLimiter()
        for _ in range(5):
            limiter.is_allowed("user_a", 5, 60)
        # user_a is at limit
        allowed_a, _ = limiter.is_allowed("user_a", 5, 60)
        assert allowed_a is False
        # user_b should be unaffected
        allowed_b, remaining_b = limiter.is_allowed("user_b", 5, 60)
        assert allowed_b is True
        assert remaining_b == 4

    def test_max_entries_safeguard_triggers_cleanup(self) -> None:
        """When > _MAX_ENTRIES keys exist, stale entries are purged."""
        limiter = _InMemoryLimiter()
        # Directly inject many stale keys
        stale_time = time.monotonic() - 600
        for i in range(limiter._MAX_ENTRIES + 100):
            limiter._windows[f"stale_{i}"] = deque([stale_time])
        # Next request should trigger cleanup
        allowed, _ = limiter.is_allowed("fresh", 5, 60)
        assert allowed is True
        # Stale entries should be cleaned
        assert len(limiter._windows) < limiter._MAX_ENTRIES

    def test_cleanup_removes_old_entries(self) -> None:
        """cleanup() purges entries older than the specified threshold."""
        limiter = _InMemoryLimiter()
        old_time = time.monotonic() - 600
        limiter._windows["old_key"] = deque([old_time])
        limiter._windows["fresh_key"] = deque([time.monotonic()])
        limiter.cleanup(older_than=300)
        assert "old_key" not in limiter._windows
        assert "fresh_key" in limiter._windows

    def test_cleanup_keeps_empty_if_no_stale(self) -> None:
        """cleanup() on fresh data is a no-op."""
        limiter = _InMemoryLimiter()
        now = time.monotonic()
        limiter._windows["active"] = deque([now])
        limiter.cleanup(older_than=300)
        assert "active" in limiter._windows

    def test_remaining_never_negative(self) -> None:
        """remaining should never go below 0 even with over-limit burst."""
        limiter = _InMemoryLimiter()
        for _ in range(20):
            _, remaining = limiter.is_allowed("neg", 3, 60)
        assert remaining == 0  # never negative

    def test_zero_limit_denies_everything(self) -> None:
        """A limit of 0 should deny all requests."""
        limiter = _InMemoryLimiter()
        allowed, remaining = limiter.is_allowed("zero", 0, 60)
        assert allowed is False
        assert remaining == 0


class TestXForwardedForEdgeCases:
    """Edge cases for IP extraction from proxy headers."""

    def _make_scope(self, headers: dict[str, str], client_ip: str = "10.0.0.1") -> dict[str, Any]:
        raw_headers = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
        return {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": raw_headers,
            "query_string": b"",
            "root_path": "",
            "client": (client_ip, 12345),
        }

    def test_single_forwarded_ip(self) -> None:
        scope = self._make_scope({"x-forwarded-for": "203.0.113.50"})
        req = Request(scope)
        assert _get_client_ip(req) == "10.0.0.1"

    def test_multiple_forwarded_ips_uses_normalised_client(self) -> None:
        scope = self._make_scope({"x-forwarded-for": "spoofed, 198.51.100.1, 203.0.113.50"})
        req = Request(scope)
        assert _get_client_ip(req) == "10.0.0.1"

    def test_forwarded_with_spaces(self) -> None:
        scope = self._make_scope({"x-forwarded-for": "  10.0.0.1 ,  192.168.1.1  "})
        req = Request(scope)
        assert _get_client_ip(req) == "10.0.0.1"

    def test_no_forwarded_uses_client(self) -> None:
        scope = self._make_scope({}, client_ip="127.0.0.1")
        req = Request(scope)
        assert _get_client_ip(req) == "127.0.0.1"

    def test_empty_forwarded_header(self) -> None:
        scope = self._make_scope({"x-forwarded-for": ""})
        req = Request(scope)
        assert _get_client_ip(req) == "10.0.0.1"

    def test_no_client_returns_unknown(self) -> None:
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
            "root_path": "",
        }
        req = Request(scope)
        assert _get_client_ip(req) == "unknown"


class TestTierClassificationEdgeCases:
    """Edge cases for request tier assignment."""

    def test_auth_nested_path(self) -> None:
        """Nested auth paths still match the auth tier."""
        max_req, window = _get_tier("/dashboard/login/callback/extra", "GET")
        assert (max_req, window) == _TIER_AUTH

    def test_webhook_post(self) -> None:
        max_req, window = _get_tier("/api/v1/webhooks/gitlab", "POST")
        assert (max_req, window) == _TIER_WEBHOOK

    def test_webhook_overrides_mutation_detection(self) -> None:
        """POST to webhook should use webhook tier, not mutation."""
        max_req, _ = _get_tier("/api/v1/webhooks/test", "POST")
        assert max_req == _TIER_WEBHOOK[0]

    def test_options_is_read_tier(self) -> None:
        max_req, _ = _get_tier("/api/v1/test", "OPTIONS")
        assert max_req == _TIER_READ[0]

    def test_head_is_read_tier(self) -> None:
        max_req, _ = _get_tier("/api/v1/test", "HEAD")
        assert max_req == _TIER_READ[0]

    def test_delete_is_mutation(self) -> None:
        max_req, _ = _get_tier("/api/v1/courses/123", "DELETE")
        assert max_req == _TIER_MUTATION[0]

    def test_patch_is_mutation(self) -> None:
        max_req, _ = _get_tier("/dashboard/settings", "PATCH")
        assert max_req == _TIER_MUTATION[0]


class TestBrowserDetectionEdgeCases:
    """Edge cases for browser vs API detection."""

    def _make_scope(self, headers: dict[str, str], method: str = "GET") -> dict[str, Any]:
        raw_headers = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
        return {
            "type": "http",
            "method": method,
            "path": "/test",
            "headers": raw_headers,
            "query_string": b"",
            "root_path": "",
        }

    def test_form_post_without_accept_is_browser(self) -> None:
        scope = self._make_scope({}, method="POST")
        req = Request(scope)
        assert _is_browser_navigation(req) is True

    def test_form_post_with_json_accept_is_not_browser(self) -> None:
        scope = self._make_scope({"accept": "application/json"}, method="POST")
        req = Request(scope)
        assert _is_browser_navigation(req) is False

    def test_htmx_overrides_html_accept(self) -> None:
        scope = self._make_scope({"accept": "text/html", "hx-request": "true"})
        req = Request(scope)
        assert _is_browser_navigation(req) is False

    def test_wildcard_accept_not_browser(self) -> None:
        scope = self._make_scope({"accept": "*/*"})
        req = Request(scope)
        assert _is_browser_navigation(req) is False

    def test_no_headers_get_not_browser(self) -> None:
        scope = self._make_scope({})
        req = Request(scope)
        assert _is_browser_navigation(req) is False


class TestMiddlewareDDoSSimulation:
    """Simulate DDoS-like burst traffic patterns."""

    @pytest.fixture(autouse=True)
    def _reset_global_limiter(self) -> None:
        """Each test gets a fresh global limiter."""
        import app.middleware.rate_limit as rlm

        rlm._global_limiter = _InMemoryLimiter()

    def test_rapid_burst_same_ip(self) -> None:
        """Rapid burst from same IP gets throttled at the right point."""
        client = _make_test_app()
        allowed_count = 0
        denied_count = 0
        budget = _TIER_READ[0]
        for _ in range(budget + 30):
            resp = client.get("/dashboard/", headers={"accept": "application/json"})
            if resp.status_code == 200:
                allowed_count += 1
            elif resp.status_code == 429:
                denied_count += 1
        # Exactly the tier budget is served; the surplus is refused.
        assert allowed_count == budget
        assert denied_count == 30

    def test_auth_endpoint_strict_limit(self) -> None:
        """Auth endpoints have strict 10/min limit."""
        client = _make_test_app()
        for i in range(15):
            resp = client.get("/dashboard/login", headers={"accept": "application/json"})
            if i < 10:
                assert resp.status_code == 200, f"Request {i + 1} should pass"
            else:
                assert resp.status_code == 429, f"Request {i + 1} should be denied"

    def test_mutation_endpoint_moderate_limit(self) -> None:
        """POST/PUT/PATCH/DELETE get 30/min limit."""
        client = _make_test_app()
        for i in range(35):
            resp = client.post("/api/v1/data", headers={"accept": "application/json"})
            if i < 30:
                assert resp.status_code == 200, f"Request {i + 1} should pass"
            else:
                assert resp.status_code == 429, f"Request {i + 1} should be denied"

    def test_mixed_tiers_independent(self) -> None:
        """Read and mutation tiers don't affect each other."""
        client = _make_test_app()
        # Use up half the mutation limit
        for _ in range(15):
            client.post("/api/v1/data", headers={"accept": "application/json"})
        # Read tier should still be fully available
        resp = client.get("/dashboard/", headers={"accept": "application/json"})
        assert resp.status_code == 200

    def test_429_response_headers_complete(self) -> None:
        """Denied response includes all required headers."""
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(False, 0)):
            resp = client.get("/dashboard/", headers={"accept": "application/json"})
        assert resp.status_code == 429
        assert "retry-after" in resp.headers
        assert "x-ratelimit-limit" in resp.headers
        assert "x-ratelimit-remaining" in resp.headers
        assert resp.headers["x-ratelimit-remaining"] == "0"

    def test_429_html_uses_shared_external_countdown(self) -> None:
        """Browser 429 page delegates countdown behavior to the shared script."""
        client = _make_test_app()
        with patch.object(_InMemoryLimiter, "is_allowed", return_value=(False, 0)):
            resp = client.get("/dashboard/", headers={"accept": "text/html"})
        assert resp.status_code == 429
        assert 'data-countdown-seconds="60"' in resp.text
        assert "/static/dist/js/error-actions." in resp.text
        assert "/static/dist/js/theme-bootstrap." in resp.text
        assert "setInterval" not in resp.text
        assert "javascript:" not in resp.text

    def test_disabled_middleware_passes_everything(self) -> None:
        """When disabled, all requests pass through."""
        client = _make_test_app(enabled=False)
        for _ in range(200):
            resp = client.get("/dashboard/")
            assert resp.status_code == 200

    def test_static_exempt_under_heavy_load(self) -> None:
        """Static files are never rate-limited even under heavy load."""
        client = _make_test_app()
        # First exhaust normal rate limits
        for _ in range(130):
            client.get("/dashboard/")
        # Static should still work
        resp = client.get("/static/test.js")
        assert resp.status_code == 200

    def test_health_exempt_always(self) -> None:
        """Health endpoint never rate-limited."""
        client = _make_test_app()
        for _ in range(200):
            resp = client.get("/health")
            assert resp.status_code == 200


class TestSessionIsolation:
    """Test that different sessions/users behind same IP are isolated."""

    @pytest.fixture(autouse=True)
    def _reset_global_limiter(self) -> None:
        import app.middleware.rate_limit as rlm

        rlm._global_limiter = _InMemoryLimiter()

    def test_different_sessions_have_separate_limits(self) -> None:
        """Users with different session cookies get separate rate buckets."""
        client = _make_test_app()
        client.cookies.set("gitpulse_session", "user_a_session_token")
        # User A: exhaust limit
        for _ in range(_TIER_READ[0]):
            client.get(
                "/dashboard/",
                headers={"accept": "application/json"},
            )
        # User A should be denied
        resp_a = client.get(
            "/dashboard/",
            headers={"accept": "application/json"},
        )
        assert resp_a.status_code == 429
        # User B should still be allowed
        client.cookies.set("gitpulse_session", "user_b_session_token")
        resp_b = client.get(
            "/dashboard/",
            headers={"accept": "application/json"},
        )
        assert resp_b.status_code == 200


class TestAppOwnChannelsAreNotRateLimited:
    """The dashboard talks to itself constantly - SSE streams plus job-state
    and badge pollers. Counting those against the user's read budget meant a
    single session with two tabs open could 429 itself out of the product,
    and once tripped every subsequent page failed to load.
    """

    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard/session-check",
            "/dashboard/sidebar-badges",
            "/dashboard/notifications",
            "/dashboard/attention-items",
            "/dashboard/stats",
        ],
    )
    def test_poll_endpoints_consume_no_budget(self, path: str) -> None:
        from app.middleware.rate_limit import _is_exempt_path

        assert _is_exempt_path(path) is True

    @pytest.mark.parametrize(
        "path",
        [
            "/dashboard/admin/users/enrich-gitlab/stream",
            "/api/v1/courses/abc/events",
            "/dashboard/some/feed/sse",
        ],
    )
    def test_live_streams_consume_no_budget(self, path: str) -> None:
        """An SSE stream is one long-lived connection; its cost has nothing to
        do with request count."""
        from app.middleware.rate_limit import _is_exempt_path

        assert _is_exempt_path(path) is True

    def test_ordinary_pages_are_still_limited(self) -> None:
        """The exemption must stay narrow - it is not a bypass."""
        from app.middleware.rate_limit import _is_exempt_path

        assert _is_exempt_path("/dashboard/") is False
        assert _is_exempt_path("/dashboard/admin/users") is False
        assert _is_exempt_path("/api/v1/courses") is False

    def test_the_read_budget_survives_a_realistic_page_load(self) -> None:
        """A dashboard page lazy-swaps regions and fires several API calls; the
        tier has to leave room for that, not just for one request."""
        from app.middleware.rate_limit import _TIER_READ

        assert _TIER_READ[0] >= 300, "read tier too tight for one page's own traffic"
