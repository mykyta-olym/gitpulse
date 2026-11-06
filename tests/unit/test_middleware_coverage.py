"""Tests for ASGI middleware coverage: correlation, logging, performance, security."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.types import Receive, Scope, Send

# -- Helpers --


async def _make_asgi_call(
    middleware_cls: type,
    path: str = "/test",
    method: str = "GET",
    headers: list[tuple[bytes, bytes]] | None = None,
    query_string: bytes = b"",
    *,
    response_status: int = 200,
    response_headers: list[tuple[bytes, bytes]] | None = None,
    scope_type: str = "http",
    **kwargs: object,
) -> list[dict[str, Any]]:
    """Call an ASGI middleware with a fake inner app and collect sent messages."""
    sent: list[dict[str, Any]] = []

    async def inner_app(scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": response_status,
                "headers": response_headers or [],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    mw = middleware_cls(inner_app, **kwargs)

    scope: Scope = {
        "type": scope_type,
        "method": method,
        "path": path,
        "query_string": query_string,
        "root_path": "",
        "headers": headers or [],
        "server": ("localhost", 8000),
        "scheme": "http",
    }

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b""}

    async def send(msg: dict[str, Any]) -> None:
        sent.append(msg)

    await mw(scope, receive, send)
    return sent


# -- CorrelationIdMiddleware --


class TestCorrelationIdMiddleware:
    @pytest.mark.asyncio
    async def test_generates_correlation_id(self) -> None:
        from app.middleware.correlation import CorrelationIdMiddleware

        sent = await _make_asgi_call(CorrelationIdMiddleware)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        header_names = [h[0] for h in start_msg["headers"]]
        assert b"x-correlation-id" in header_names

    @pytest.mark.asyncio
    async def test_uses_provided_correlation_id(self) -> None:
        from app.middleware.correlation import CorrelationIdMiddleware

        sent = await _make_asgi_call(
            CorrelationIdMiddleware,
            headers=[(b"x-correlation-id", b"test-123")],
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        cid_header = next(h for h in start_msg["headers"] if h[0] == b"x-correlation-id")
        assert cid_header[1] == b"test-123"

    @pytest.mark.asyncio
    async def test_passthrough_non_http(self) -> None:
        from app.middleware.correlation import CorrelationIdMiddleware

        called = False

        async def inner(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal called
            called = True

        mw = CorrelationIdMiddleware(inner)
        await mw({"type": "lifespan"}, AsyncMock(), AsyncMock())
        assert called


# -- StaticCacheMiddleware --


class TestStaticCacheMiddleware:
    @pytest.mark.asyncio
    async def test_dev_mode_no_cache(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(StaticCacheMiddleware, path="/static/app.js", dev_mode=True)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert headers_dict[b"cache-control"] == b"no-cache"

    @pytest.mark.asyncio
    async def test_dev_mode_caches_the_fonts_as_prod_does(self) -> None:
        """A face revalidated on every page load sometimes arrived after
        `font-display: optional` had given up on it: that page stayed in the
        fallback, the next one in GitLab Sans, and the search box's text
        jumped between them on the local server."""
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(
            StaticCacheMiddleware, path="/static/fonts/GitLabSans.woff2", dev_mode=True
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert headers_dict[b"cache-control"] == b"public, max-age=31536000, immutable"

    @pytest.mark.asyncio
    async def test_prod_mode_immutable_for_versioned_assets(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(
            StaticCacheMiddleware,
            path="/static/app.js",
            query_string=b"v=abc123ef",
            dev_mode=False,
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert b"immutable" in headers_dict[b"cache-control"]
        assert b"max-age=31536000" in headers_dict[b"cache-control"]

    @pytest.mark.asyncio
    async def test_prod_mode_short_cache_for_unversioned_assets(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(StaticCacheMiddleware, path="/static/app.js", dev_mode=False)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert headers_dict[b"cache-control"] == b"public, max-age=300"
        assert b"immutable" not in headers_dict[b"cache-control"]

    @pytest.mark.asyncio
    async def test_prod_mode_immutable_for_fonts_without_a_version(self) -> None:
        """A font is versioned by its filename, and must be cached like it.

        `fonts.css` and the `<link rel=preload>` in base.html both reference
        `/static/fonts/GitLabSans.woff2` unversioned, because a preload matches
        a request by exact URL. That put a 325 KB face in the five-minute
        bucket, so it was re-downloaded all day - and it is declared
        `font-display: optional`, which uses a face only when it is already
        available. A font that is never cached is therefore never applied: the
        reader saw the fallback and Chrome logged "preloaded but not used
        within a few seconds from the window's load event" every time.
        """
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(
            StaticCacheMiddleware, path="/static/fonts/GitLabSans.woff2", dev_mode=False
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert b"immutable" in headers_dict[b"cache-control"]
        assert b"max-age=31536000" in headers_dict[b"cache-control"]

    @pytest.mark.asyncio
    async def test_prod_mode_immutable_for_build_outputs(self) -> None:
        """A dist/ file's name carries its content hash: a change is a new URL."""
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(
            StaticCacheMiddleware, path="/static/dist/js/core.bundle.1005fb0c.js", dev_mode=False
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert b"immutable" in headers_dict[b"cache-control"]
        assert b"max-age=31536000" in headers_dict[b"cache-control"]

    @pytest.mark.asyncio
    async def test_prod_mode_short_cache_for_invalid_version_token(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(
            StaticCacheMiddleware,
            path="/static/app.js",
            query_string=b"v=manual-cache-bust",
            dev_mode=False,
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert headers_dict[b"cache-control"] == b"public, max-age=300"

    @pytest.mark.asyncio
    async def test_static_headers_replace_cache_control_and_merge_vary(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(
            StaticCacheMiddleware,
            path="/static/app.js",
            query_string=b"v=abc123ef",
            response_headers=[
                (b"cache-control", b"private"),
                (b"vary", b"Origin"),
            ],
            dev_mode=False,
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        cache_headers = [v for k, v in start_msg["headers"] if k == b"cache-control"]
        vary = next(v for k, v in start_msg["headers"] if k == b"vary")
        assert cache_headers == [b"public, max-age=31536000, immutable"]
        assert vary == b"Origin, Accept-Encoding"

    @pytest.mark.asyncio
    async def test_non_static_passthrough(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        sent = await _make_asgi_call(StaticCacheMiddleware, path="/api/health", dev_mode=True)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        header_names = [h[0] for h in start_msg["headers"]]
        assert b"cache-control" not in header_names

    @pytest.mark.asyncio
    async def test_non_http_passthrough(self) -> None:
        from app.middleware.performance import StaticCacheMiddleware

        called = False

        async def inner(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal called
            called = True

        mw = StaticCacheMiddleware(inner, dev_mode=False)
        await mw({"type": "lifespan"}, AsyncMock(), AsyncMock())
        assert called


# -- RequestLoggingMiddleware --


class TestRequestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_logs_and_records_metrics(self) -> None:
        from app.middleware.logging import RequestLoggingMiddleware

        sent = await _make_asgi_call(RequestLoggingMiddleware)
        assert any(m["type"] == "http.response.body" for m in sent)

    @pytest.mark.asyncio
    async def test_non_http_passthrough(self) -> None:
        from app.middleware.logging import RequestLoggingMiddleware

        called = False

        async def inner(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal called
            called = True

        mw = RequestLoggingMiddleware(inner)
        await mw({"type": "lifespan"}, AsyncMock(), AsyncMock())
        assert called


# -- SecurityHeadersMiddleware --


class TestSecurityHeadersMiddleware:
    @pytest.fixture(autouse=True)
    def _mock_settings(self) -> Generator[None, Any, None]:
        mock_settings = MagicMock()
        mock_settings.gitlab_url = "https://gitlab.example.com"
        with patch("app.middleware.security.get_settings", return_value=mock_settings):
            yield

    @pytest.mark.asyncio
    async def test_adds_security_headers(self) -> None:
        from app.middleware.security import SecurityHeadersMiddleware

        sent = await _make_asgi_call(SecurityHeadersMiddleware)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        header_names = {h[0] for h in start_msg["headers"]}
        assert b"x-content-type-options" in header_names
        assert b"x-frame-options" in header_names
        assert b"content-security-policy" in header_names

    @pytest.mark.asyncio
    async def test_a_gitlab_on_its_own_port_is_its_own_origin(self) -> None:
        """Scheme + host alone did not match a GitLab on a port of its own, so
        the browser refused its avatars and API calls (a local :8929, or any
        `https://git.example:8443`); user info in the URL is no part of it."""
        from app.middleware.security import SecurityHeadersMiddleware

        settings = MagicMock()
        settings.gitlab_url = "https://bot:secret@git.example:8443/"
        with patch("app.middleware.security.get_settings", return_value=settings):
            sent = await _make_asgi_call(SecurityHeadersMiddleware)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        csp = dict(start_msg["headers"])[b"content-security-policy"].decode()
        img = next(d for d in csp.split(";") if d.strip().startswith("img-src"))
        connect = next(d for d in csp.split(";") if d.strip().startswith("connect-src"))
        assert "https://git.example:8443" in img.split()
        assert "https://git.example:8443" in connect.split()
        assert "secret" not in csp
        # GitLab's own default avatars, on whichever gravatar host it uses.
        assert {"https://secure.gravatar.com", "https://www.gravatar.com"} <= set(img.split())

    @pytest.mark.asyncio
    async def test_hsts_on_https(self) -> None:
        from app.middleware.security import SecurityHeadersMiddleware

        sent = await _make_asgi_call(
            SecurityHeadersMiddleware,
            headers=[(b"x-forwarded-proto", b"https")],
        )
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        header_names = {h[0] for h in start_msg["headers"]}
        assert b"strict-transport-security" in header_names

    @pytest.mark.asyncio
    async def test_cache_control_for_dashboard(self) -> None:
        from app.middleware.security import SecurityHeadersMiddleware

        sent = await _make_asgi_call(SecurityHeadersMiddleware, path="/dashboard/courses")
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers_dict = {h[0]: h[1] for h in start_msg["headers"]}
        assert b"no-store" in headers_dict.get(b"cache-control", b"")

    @pytest.mark.asyncio
    async def test_non_http_passthrough(self) -> None:
        from app.middleware.security import SecurityHeadersMiddleware

        called = False

        async def inner(scope: Scope, receive: Receive, send: Send) -> None:
            nonlocal called
            called = True

        mw = SecurityHeadersMiddleware(inner)
        await mw({"type": "lifespan"}, AsyncMock(), AsyncMock())
        assert called

    # -- SEC-03: per-request nonce + enforced strict CSP --

    @pytest.mark.asyncio
    async def test_enforces_strict_csp_with_nonce(self) -> None:
        """The enforced script policy carries a fresh nonce and no eval fallback."""
        from app.middleware.security import SecurityHeadersMiddleware

        with patch("app.middleware.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gitlab_url="https://git.example.com",
            )
            sent = await _make_asgi_call(SecurityHeadersMiddleware)
        start_msg = next(m for m in sent if m["type"] == "http.response.start")
        headers = {h[0]: h[1] for h in start_msg["headers"]}

        enforced = headers.get(b"content-security-policy", b"").decode()
        assert "nonce-" in enforced, "Enforced CSP must carry the per-request nonce"
        assert "'unsafe-eval'" not in enforced
        # script-src in the strict policy must NOT permit inline scripts.
        script_src = next(
            d.strip() for d in enforced.split(";") if d.strip().startswith("script-src")
        )
        assert "'unsafe-inline'" not in script_src
        assert "'strict-dynamic'" in script_src
        assert "report-uri /csp/report" in enforced
        assert b"reporting-endpoints" in headers
        assert b"content-security-policy-report-only" not in headers

    @pytest.mark.asyncio
    async def test_nonce_is_unique_per_request(self) -> None:
        """Each request must receive an unguessable, distinct nonce value."""
        from app.middleware.security import SecurityHeadersMiddleware

        with patch("app.middleware.security.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                gitlab_url="https://git.example.com",
            )
            sent_a = await _make_asgi_call(SecurityHeadersMiddleware, path="/a")
            sent_b = await _make_asgi_call(SecurityHeadersMiddleware, path="/b")

        def _nonce(messages: list[dict[str, Any]]) -> str:
            start = next(m for m in messages if m["type"] == "http.response.start")
            csp = next(v for k, v in start["headers"] if k == b"content-security-policy").decode()
            tag: str = next(tok for tok in csp.split() if tok.startswith("'nonce-"))
            return tag

        nonce_a = _nonce(sent_a)
        nonce_b = _nonce(sent_b)
        assert nonce_a != nonce_b, "Nonce must change between requests"
        # 16 bytes -> 22 char base64url payload, plus the `'nonce-` prefix and trailing `'`.
        assert len(nonce_a) >= len("'nonce-") + 16

    @pytest.mark.asyncio
    async def test_nonce_published_on_request_state(self) -> None:
        """Templates read the nonce via ``request.state.csp_nonce``; ensure it's set."""
        from starlette.requests import Request

        from app.middleware.security import SecurityHeadersMiddleware

        captured: dict[str, str] = {}

        async def inner_app(scope: Scope, receive: Receive, send: Send) -> None:
            captured["nonce"] = Request(scope).state.csp_nonce
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        mw = SecurityHeadersMiddleware(inner_app)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/x",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "server": ("localhost", 8000),
            "scheme": "http",
        }
        await mw(scope, AsyncMock(), AsyncMock())

        assert captured.get("nonce")
        assert len(captured["nonce"]) >= 16
