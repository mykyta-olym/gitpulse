"""Global rate-limiting middleware - anti-spam protection.

Provides tiered rate limits:
- **authentication** endpoints (login): strict (10 req/min)
- **mutations** (POST/PUT/PATCH/DELETE): moderate (30 req/min)
- **reads** (GET/HEAD/OPTIONS): generous (120 req/min)

Uses an in-memory sliding-window counter per IP+session (no Redis dependency).
The client IP is read from ``request.client`` after the trusted proxy middleware
has normalised forwarded headers; this middleware does not trust raw
``X-Forwarded-For`` on its own.

Returns an HTML countdown page for browser navigations and JSON for
API / HTMX requests (HTMX ``htmx:responseError`` handler shows a toast).

Gated behind ``feature_security_hardening``.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import MutableMapping
from threading import Lock
from typing import Any

import structlog
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.middleware.error_pages import build_error_page_html

logger = structlog.get_logger()

# -- Tier configuration --
# (max_requests, window_seconds)
_TIER_AUTH = (10, 60)  # login / OAuth endpoints
_TIER_MUTATION = (30, 60)  # POST/PUT/PATCH/DELETE
# A dashboard page is not one request. It lazy-swaps several htmx regions,
# opens SSE streams and polls job state, so 120/min was exhausted by the app
# talking to itself - and once tripped, every subsequent page 429'd.
_TIER_READ = (600, 60)  # GET/HEAD/OPTIONS
_TIER_WEBHOOK = (100, 60)  # webhook ingestion (external)

# Paths that are always exempt from rate limiting
_EXEMPT_PREFIXES = (
    "/static/",
    "/favicon",
    "/docs",
    "/redoc",
    "/openapi.json",
)

# The app's own live-update channels. Counting these is meaningless: an SSE
# stream is ONE long-lived connection whose cost is unrelated to request count,
# and the pollers are already bounded client-side by the cross-tab leader lease.
# Leaving them in the read tier meant a user with two tabs open could rate-limit
# themselves out of the product.
_EXEMPT_SUFFIXES = ("/stream", "/events", "/sse")
_EXEMPT_POLL_PATHS = frozenset(
    {
        "/dashboard/session-check",
        "/dashboard/sidebar-badges",
        "/dashboard/notifications",
        "/dashboard/attention-items",
        "/dashboard/stats",
        # Caddy asks it about EVERY request to Grafana and the rest: one
        # dashboard is a hundred assets and a query per panel per refresh, on
        # the reader's own budget. It only answers yes or no.
        "/internal/monitoring-authz",
    }
)
_EXEMPT_PATHS = frozenset({"/health", "/health/live", "/health/ready", "/metrics"})

# Auth-tier paths
_AUTH_PATHS = (
    "/dashboard/login",
    "/dashboard/auth/callback",
    "/dashboard/oauth/callback",
    "/api/v1/auth",
)


class _InMemoryLimiter:
    """Thread-safe in-memory sliding-window counter using deques.

    Each key maps to a deque of monotonic timestamps.
    The deque is pruned from the left (oldest entries) on each check - O(expired) amortised.
    Cleanup runs incrementally every ``_CLEANUP_INTERVAL`` seconds,
    removing stale keys in batches to avoid lock contention spikes.
    """

    _MAX_ENTRIES = 100_000
    _CLEANUP_BATCH = 2_000  # max keys scanned per cleanup pass

    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = {}
        self._lock = Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            dq = self._windows.get(key)
            if dq is None:
                dq = deque()
                self._windows[key] = dq
            # Prune expired from left - O(expired) amortised
            while dq and dq[0] <= cutoff:
                dq.popleft()
            dq.append(now)
            count = len(dq)
            # Trigger cleanup when entry count exceeds threshold
            if len(self._windows) > self._MAX_ENTRIES:
                self._cleanup_unlocked(now)
        remaining = max(0, max_requests - count)
        return (count <= max_requests, remaining)

    def _cleanup_unlocked(self, now: float, older_than: float = 300) -> None:
        """Inner cleanup - caller must hold ``self._lock``."""
        cutoff = now - older_than
        if len(self._windows) <= 100:
            stale = [k for k, v in self._windows.items() if not v or v[-1] <= cutoff]
            for k in stale:
                del self._windows[k]
        else:
            stale_keys: list[str] = []
            for scanned, (k, v) in enumerate(self._windows.items()):
                if scanned >= self._CLEANUP_BATCH:
                    break
                last = v[-1] if v else 0
                if not v or last <= cutoff:
                    stale_keys.append(k)
            for k in stale_keys:
                del self._windows[k]
        # Hard cap safety: if still over limit, purge oldest half
        if len(self._windows) > self._MAX_ENTRIES:
            all_keys = sorted(
                self._windows.keys(),
                key=lambda k: self._windows[k][-1] if self._windows[k] else 0,
            )
            for k in all_keys[: len(all_keys) // 2]:
                del self._windows[k]

    def cleanup(self, older_than: float = 300) -> None:
        """Remove stale entries incrementally to avoid long lock holds."""
        now = time.monotonic()
        with self._lock:
            self._cleanup_unlocked(now, older_than)


_global_limiter = _InMemoryLimiter()
_last_cleanup = time.monotonic()
_CLEANUP_INTERVAL = 120  # seconds


def _get_tier(path: str, method: str) -> tuple[int, int]:
    """Return (max_requests, window_seconds) for the request tier."""
    for auth_path in _AUTH_PATHS:
        if path.startswith(auth_path):
            return _TIER_AUTH

    if path.startswith("/api/v1/webhooks"):
        return _TIER_WEBHOOK

    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return _TIER_MUTATION

    return _TIER_READ


def _get_client_ip(request: Request) -> str:
    """Extract client IP after trusted proxy header normalisation."""
    if request.client:
        return request.client.host
    return "unknown"


def _is_exempt_path(path: str) -> bool:
    """Return True for endpoints that must not consume rate-limit budget."""
    return (
        path in _EXEMPT_PATHS
        or path in _EXEMPT_POLL_PATHS
        or any(path.startswith(prefix) for prefix in _EXEMPT_PREFIXES)
        or any(path.endswith(suffix) for suffix in _EXEMPT_SUFFIXES)
    )


def _is_browser_navigation(request: Request) -> bool:
    """Return True when the request comes from a normal browser navigation
    (not HTMX, not a JSON API call)."""
    if request.headers.get("hx-request"):
        return False
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return True
    # Form POST without Accept header - treat as browser
    return request.method == "POST" and "application/json" not in accept


class RateLimitMiddleware:
    """Global rate-limiting middleware with tiered limits.

    Uses raw ASGI instead of BaseHTTPMiddleware to avoid cancel-scope
    issues with SSE / streaming responses that leak asyncpg connections.
    """

    def __init__(self, app: ASGIApp, *, enabled: bool = True, dev_mode: bool = False) -> None:
        self.app = app
        self._enabled = enabled
        self._dev_mode = dev_mode

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._enabled:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        path = request.url.path
        method = request.method

        # Skip exempt paths
        if _is_exempt_path(path):
            await self.app(scope, receive, send)
            return

        # In development mode, localhost is exempt so testing / development workflows don't hit 429
        ip = _get_client_ip(request)
        if self._dev_mode and ip in ("127.0.0.1", "::1", "localhost", "testclient"):
            await self.app(scope, receive, send)
            return

        # Periodic cleanup of stale tracking data
        global _last_cleanup
        now = time.monotonic()
        if now - _last_cleanup > _CLEANUP_INTERVAL:
            _last_cleanup = now
            _global_limiter.cleanup()

        ip = _get_client_ip(request)
        max_req, window = _get_tier(path, method)

        # Per-IP + tier key.  For authenticated users, include the session
        # username so that different users behind the same IP/proxy are not
        # penalised collectively.
        tier_key = (
            "auth"
            if any(path.startswith(p) for p in _AUTH_PATHS)
            else (
                "webhook"
                if path.startswith("/api/v1/webhooks")
                else ("mutation" if method in ("POST", "PUT", "PATCH", "DELETE") else "read")
            )
        )
        session_user = request.cookies.get("gitpulse_session", "")[:64]
        identity = f"{ip}:{session_user}" if session_user else ip
        rate_key = f"{identity}:{tier_key}"

        allowed, remaining = _global_limiter.is_allowed(rate_key, max_req, window)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                ip=ip,
                path=path,
                method=method,
                tier=tier_key,
            )

            rate_headers = {
                "Retry-After": str(window),
                "X-RateLimit-Limit": str(max_req),
                "X-RateLimit-Remaining": "0",
            }

            if _is_browser_navigation(request):
                html = build_error_page_html(
                    429,
                    request=request,
                    retry_after=window,
                    csp_nonce=str(scope.get("state", {}).get("csp_nonce", "")),
                )
                rate_response: HTMLResponse | JSONResponse = HTMLResponse(
                    content=html,
                    status_code=429,
                    headers=rate_headers,
                )
            else:
                rate_response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers=rate_headers,
                )
            await rate_response(scope, receive, send)
            return

        # Inject rate-limit headers into response
        async def send_with_headers(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-ratelimit-limit", str(max_req).encode()))
                headers.append((b"x-ratelimit-remaining", str(remaining).encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
