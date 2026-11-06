"""Middleware for resolving and persisting the request locale.

Uses raw ASGI middleware instead of ``BaseHTTPMiddleware`` to avoid
cancel-scope leaks with SSE / streaming responses.
"""

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.i18n import (
    LOCALE_COOKIE_NAME,
    LOCALE_QUERY_PARAM,
    _current_locale_var,
    normalize_locale,
    resolve_locale,
)


class LocaleMiddleware:
    """Resolve request locale and expose it to templates/handlers (pure ASGI)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        locale = resolve_locale(request)
        request.state.locale = locale
        _current_locale_var.set(locale)

        # Detect explicit lang query param for cookie persistence
        query_locale = normalize_locale(request.query_params.get(LOCALE_QUERY_PARAM))
        need_cookie = bool(query_locale and request.cookies.get(LOCALE_COOKIE_NAME) != query_locale)
        secure = request.headers.get("X-Forwarded-Proto") == "https"

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                # Report what was actually rendered. `require_dashboard_auth`
                # loads the account's `preferred_language` AFTER this
                # middleware has run and refines `request.state.locale` with
                # it, so the value captured above can be one step behind.
                rendered = normalize_locale(getattr(request.state, "locale", None)) or locale
                raw_headers.append((b"content-language", rendered.encode()))

                # Persist explicit lang switch as a cookie
                if need_cookie and query_locale:
                    # Build Set-Cookie header manually (ASGI middleware level)
                    cookie_parts = [
                        f"{LOCALE_COOKIE_NAME}={query_locale}",
                        "Path=/",
                        "SameSite=Lax",
                        "Max-Age=31536000",  # 1 year
                    ]
                    if secure:
                        cookie_parts.append("Secure")
                    raw_headers.append((b"set-cookie", "; ".join(cookie_parts).encode()))

                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
