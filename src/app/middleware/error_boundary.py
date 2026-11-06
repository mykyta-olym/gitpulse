"""Outermost error-boundary middleware - universal black-screen prevention.

Intercepts any non-HTML error response (>= 400) destined for a browser
navigation and replaces it with the shared standalone error page.

This acts as a safety net so that even if an inner middleware (rate limiter,
CORS, etc.) returns raw JSON or plain-text, the end-user always sees a
styled error page with a "Go back" / "Home" link.

For API callers (``Accept: application/json``) and HTMX partial requests
(``HX-Request`` header) the original response is passed through unchanged.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.middleware.error_pages import build_error_page_html

logger = structlog.get_logger()


_API_PREFIX = "/api/"


def _wants_html(request: Request) -> bool:
    """True when the client is a normal browser navigation (not HTMX / API)."""
    # HTMX partial requests carry their own error handler (toast)
    if request.headers.get("hx-request"):
        return False
    # The JSON API answers JSON whatever the caller says it accepts. GitLab's
    # webhook deliveries send no Accept header, so the POST rule below turned
    # every 422 the receiver describes ("bad or missing: project.id") into an
    # HTML page in GitLab's delivery log.
    if request.url.path.startswith(_API_PREFIX):
        return False
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return True
    # Traditional form POST without explicit Accept header
    return request.method == "POST" and "application/json" not in accept


class ErrorBoundaryMiddleware:
    """Outermost ASGI middleware - ensures browsers never see raw JSON errors.

    Uses raw ASGI to avoid cancel-scope issues with SSE / streaming.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # Only intercept browser navigations
        if not _wants_html(request):
            await self.app(scope, receive, send)
            return

        # State shared between the two ``send`` intercepts
        captured_start: MutableMapping[str, Any] | None = None
        needs_replace = False
        headers_forwarded = False

        async def guarded_send(message: MutableMapping[str, Any]) -> None:
            nonlocal captured_start, needs_replace, headers_forwarded

            if message["type"] == "http.response.start":
                status: int = message.get("status", 200)
                if status < 400:
                    # Success / redirect - pass through immediately
                    headers_forwarded = True
                    await send(message)
                    return

                # 4xx / 5xx - check content-type
                raw_headers: list[tuple[bytes, bytes]] = message.get("headers", [])
                ct = b""
                for k, v in raw_headers:
                    if k.lower() == b"content-type":
                        ct = v
                        break
                if b"text/html" in ct:
                    # Already a proper HTML error page
                    headers_forwarded = True
                    await send(message)
                    return

                # Non-HTML error -> will be replaced
                captured_start = message
                needs_replace = True
                return

            if message["type"] == "http.response.body":
                if not needs_replace:
                    await send(message)
                    return

                # Consume all body chunks; send replacement on the last one
                more_body = message.get("more_body", False)
                if more_body:
                    return  # still waiting for final chunk

                status_code: int = captured_start.get("status", 500) if captured_start else 500
                html_body = build_error_page_html(
                    status_code,
                    request=request,
                    csp_nonce=str(scope.get("state", {}).get("csp_nonce", "")),
                )

                logger.debug(
                    "error_boundary_replaced",
                    status=status_code,
                    path=request.url.path,
                )

                await send(
                    {
                        "type": "http.response.start",
                        "status": status_code,
                        "headers": [
                            (b"content-type", b"text/html; charset=utf-8"),
                            (b"cache-control", b"no-store"),
                        ],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": html_body,
                    }
                )
                return

            # Any other ASGI message type - pass through
            await send(message)

        try:
            await self.app(scope, receive, guarded_send)
        except Exception:
            # If the inner app raised before sending any response, we can
            # still deliver a proper HTML error page.  If headers were
            # already forwarded, the connection may be half-broken - log
            # and let the server close the connection.
            if not headers_forwarded and not needs_replace:
                logger.exception(
                    "error_boundary_caught_unhandled",
                    path=request.url.path,
                )
                html_body = build_error_page_html(
                    500,
                    request=request,
                    csp_nonce=str(scope.get("state", {}).get("csp_nonce", "")),
                )
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [
                            (b"content-type", b"text/html; charset=utf-8"),
                            (b"cache-control", b"no-store"),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": html_body})
            else:
                logger.exception(
                    "error_boundary_unrecoverable",
                    path=request.url.path,
                    headers_sent=headers_forwarded,
                )
