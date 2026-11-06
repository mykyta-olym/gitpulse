"""Middleware for adding security headers to every response.

Uses raw ASGI middleware instead of ``BaseHTTPMiddleware`` to avoid
cancel-scope leaks with SSE / streaming responses.
"""

import secrets
from urllib.parse import urlparse

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import get_settings
from app.utils.constants import CSP_FONT_ORIGINS, CSP_IMAGE_ORIGINS, CSP_STYLE_ORIGINS

# Per-request CSP nonce length: 16 bytes -> 22-char base64url, well above the
# 128-bit minimum recommended by the CSP3 spec for cryptographic unguessability.
_NONCE_BYTES = 16


class SecurityHeadersMiddleware:
    """Add security headers to every response (pure ASGI).

    These are defence-in-depth headers for when Caddy is not in front
    (e.g. local development) or as a second layer behind the proxy.

    SEC-03 - CSP nonce + strict script policy
    -----------------------------------------
    A per-request nonce is generated and stashed in
    ``scope["state"]["csp_nonce"]`` so templates can render
    ``nonce="{{ request.state.csp_nonce }}"`` on every inline ``<script>``.

    The Alpine CSP runtime always uses a per-request script nonce with
    ``strict-dynamic``; script eval and inline handlers are not allowed.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        settings = get_settings()
        parsed = urlparse(settings.gitlab_url)
        # The ORIGIN, port included: scheme + host alone did not match a GitLab
        # on a port of its own (`https://git.example:8443`, a local :8929), so
        # the browser refused its avatars and API calls. User info is dropped.
        gl_origin = f"{parsed.scheme}://{parsed.netloc.rsplit('@', 1)[-1]}"
        style_origins = " ".join(CSP_STYLE_ORIGINS)
        font_origins = " ".join(CSP_FONT_ORIGINS)
        img_origins = " ".join(CSP_IMAGE_ORIGINS)

        # -- Strict script CSP.  Uses ``{nonce}`` as a placeholder filled in
        # per-request.  ``'strict-dynamic'`` lets nonced root scripts
        # dynamically inject helpers without re-noncing each one.
        # ``'unsafe-inline'`` is intentionally still present on ``style-src``
        # because inline ``style="..."`` migration is a separate workstream;
        # it is OFF for ``script-src`` which is the actual XSS vector.
        self._strict_csp_template = (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{{nonce}}' 'strict-dynamic'; "
            f"style-src 'self' 'unsafe-inline' "
            f"{style_origins}; "
            f"img-src 'self' data: {img_origins} "
            f"{gl_origin}; "
            f"font-src 'self' {font_origins}; "
            f"connect-src 'self' "
            f"{gl_origin}; "
            f"object-src 'none'; "
            f"frame-ancestors 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self' {gl_origin}; "
            f"upgrade-insecure-requests; "
            f"report-uri /csp/report; "
            f"report-to csp-endpoint"
        )

        # ``Reporting-Endpoints`` is the CSP3 successor to ``Report-To`` and is
        # honoured by Chromium ≥ 96 / Edge.  Same-origin endpoint avoids CORS.
        self._reporting_endpoints = b'csp-endpoint="/csp/report"'

        from app.build_info import BUILD_HASH

        self._build_hash = BUILD_HASH.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # SEC-03: derive a fresh per-request nonce and stash it in
        # ``scope["state"]`` so downstream middleware, dependencies, and
        # Jinja2 templates (via ``request.state.csp_nonce``) can read it.
        nonce = secrets.token_urlsafe(_NONCE_BYTES)
        state = scope.setdefault("state", {})
        state["csp_nonce"] = nonce

        request = Request(scope)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                csp_enforced = self._strict_csp_template.format(nonce=nonce).encode()
                extra: list[tuple[bytes, bytes]] = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                    (b"content-security-policy", csp_enforced),
                    (b"x-app-version", self._build_hash),
                    # Always set HSTS - site is behind university HTTPS proxy
                    (
                        b"strict-transport-security",
                        b"max-age=31536000; includeSubDomains",
                    ),
                ]

                extra.append((b"reporting-endpoints", self._reporting_endpoints))

                # Prevent caching of authenticated pages
                path = request.url.path
                if path.startswith("/dashboard"):
                    extra.append(
                        (
                            b"cache-control",
                            b"no-store, no-cache, must-revalidate, private",
                        )
                    )
                    extra.append((b"pragma", b"no-cache"))

                # Enforce noindex for private paths via X-Robots-Tag
                # Public paths are / (redirect), /dashboard/login, /project-docs, /static, etc.
                is_private = False
                if path.startswith("/dashboard"):
                    if path not in ("/dashboard/login", "/dashboard/login/"):
                        is_private = True
                elif path.startswith(("/api", "/health", "/oauth")):
                    is_private = True

                if is_private:
                    extra.append((b"x-robots-tag", b"noindex, nofollow, noarchive"))

                raw_headers = list(message.get("headers", []))
                raw_headers.extend(extra)
                message = {**message, "headers": raw_headers}

            await send(message)

        await self.app(scope, receive, send_wrapper)
