"""Tests for app.services.llm.course_context - HTML extraction, caching, context builder."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.course_context import (
    _cache,
    _extract_text,
    _TextExtractor,
    build_course_context,
    fetch_url_content,
)

# -- _TextExtractor --


class TestTextExtractor:
    def test_plain_text(self) -> None:
        p = _TextExtractor()
        p.feed("Hello world")
        assert p.get_text() == "Hello world"

    def test_strips_script_style(self) -> None:
        html = "<div>before<script>alert(1)</script>after<style>.a{}</style>end</div>"
        p = _TextExtractor()
        p.feed(html)
        text = p.get_text()
        assert "alert" not in text
        assert "before" in text
        assert "after" in text
        assert "end" in text

    def test_strips_nav_footer_header(self) -> None:
        html = "<nav>menu</nav><main>content</main><footer>foot</footer>"
        p = _TextExtractor()
        p.feed(html)
        text = p.get_text()
        assert "menu" not in text
        assert "content" in text
        assert "foot" not in text

    def test_adds_newlines_for_block_tags(self) -> None:
        html = "<p>one</p><p>two</p><br><div>three</div>"
        p = _TextExtractor()
        p.feed(html)
        text = p.get_text()
        assert "one" in text
        assert "two" in text
        assert "three" in text

    def test_heading_tags(self) -> None:
        html = "<h1>Title</h1><h2>Sub</h2><li>item</li>"
        p = _TextExtractor()
        p.feed(html)
        text = p.get_text()
        assert "Title" in text
        assert "Sub" in text
        assert "item" in text

    def test_collapses_whitespace(self) -> None:
        html = "<p>  lots   of    spaces  </p>"
        p = _TextExtractor()
        p.feed(html)
        text = p.get_text()
        assert "  " not in text

    def test_nested_skip_tags(self) -> None:
        html = "<noscript><div>hidden<script>inner</script></div></noscript>visible"
        p = _TextExtractor()
        p.feed(html)
        text = p.get_text()
        assert "hidden" not in text
        assert "inner" not in text
        assert "visible" in text

    def test_skip_tags_list(self) -> None:
        for tag in ("svg", "head", "meta", "link", "iframe", "object", "embed"):
            html = f"<{tag}>skip</{tag}>keep"
            p = _TextExtractor()
            p.feed(html)
            assert "keep" in p.get_text()


# -- _extract_text --


class TestExtractText:
    def test_basic_html(self) -> None:
        result = _extract_text("<html><body><p>Hello</p></body></html>")
        assert "Hello" in result

    def test_empty(self) -> None:
        assert _extract_text("") == ""


# -- fetch_url_content --


class TestFetchUrlContent:
    @pytest.fixture(autouse=True)
    def _clear(self):
        _cache.clear()
        with patch("app.services.llm.course_context._is_safe_url", return_value=True):
            yield
        _cache.clear()

    @pytest.mark.asyncio
    async def test_cache_hit(self) -> None:
        _cache["http://example.com"] = (time.monotonic(), "cached text")
        result = await fetch_url_content("http://example.com")
        assert result == "cached text"

    @pytest.mark.asyncio
    async def test_html_response(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/html; charset=utf-8"}
        mock_resp.text = "<html><body><p>Page content</p></body></html>"
        mock_resp.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.llm.course_context.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url_content("http://example.com/page")

        assert result is not None
        assert "Page content" in result

    @pytest.mark.asyncio
    async def test_plain_text_response(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "text/plain"}
        mock_resp.text = "Plain text body"
        mock_resp.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.llm.course_context.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url_content("http://example.com/txt")

        assert result == "Plain text body"

    @pytest.mark.asyncio
    async def test_unsupported_content_type(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.llm.course_context.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url_content("http://example.com/api")

        assert result is None

    @pytest.mark.asyncio
    async def test_http_error(self) -> None:
        import httpx

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_resp
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.llm.course_context.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url_content("http://example.com/missing")

        assert result is None

    @pytest.mark.asyncio
    async def test_request_error(self) -> None:
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection refused", request=MagicMock())
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.llm.course_context.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url_content("http://unreachable.test")

        assert result is None

    @pytest.mark.asyncio
    async def test_unexpected_error(self) -> None:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=RuntimeError("boom"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.llm.course_context.httpx.AsyncClient", return_value=mock_client):
            result = await fetch_url_content("http://boom.test")

        assert result is None


# -- build_course_context --


class TestBuildCourseContext:
    @pytest.mark.asyncio
    async def test_zsi_course_type(self) -> None:
        result = await build_course_context("zsi", [])
        assert "Software Engineering" in result

    @pytest.mark.asyncio
    async def test_devops_course_type(self) -> None:
        result = await build_course_context("devops", [])
        assert "DevOps" in result

    @pytest.mark.asyncio
    async def test_generic_course_type(self) -> None:
        result = await build_course_context("other", [], course_name="My Course")
        assert "My Course" in result
        assert "university course" in result

    @pytest.mark.asyncio
    async def test_with_description(self) -> None:
        result = await build_course_context("zsi", [], course_description="Learn Git")
        assert "Learn Git" in result

    @pytest.mark.asyncio
    async def test_with_resource_urls(self) -> None:
        with patch(
            "app.services.llm.course_context.fetch_url_content",
            new_callable=AsyncMock,
            return_value="Assignment details here",
        ):
            result = await build_course_context(
                "zsi",
                [{"url": "http://example.com/assignment", "label": "Assignment 1"}],
            )
        assert "Assignment 1" in result
        assert "Assignment details here" in result

    @pytest.mark.asyncio
    async def test_with_empty_url(self) -> None:
        with patch(
            "app.services.llm.course_context.fetch_url_content",
            new_callable=AsyncMock,
        ) as mock_fetch:
            await build_course_context("zsi", [{"url": "", "label": "empty"}])
        mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_returns_none(self) -> None:
        with patch(
            "app.services.llm.course_context.fetch_url_content",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await build_course_context(
                "zsi", [{"url": "http://fail.test", "label": "Fail"}]
            )
        assert "extracted from configured" not in result
