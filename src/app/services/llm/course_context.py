"""Dynamic course-context fetcher for LLM prompts.

Fetches configured resource URLs, extracts readable text, and caches
results so the LLM gets up-to-date course information without hardcoded
domain knowledge.
"""

import asyncio
import html.parser
import ipaddress
import logging
import re
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# Cache: {url: (timestamp, extracted_text)}
_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 24 * 3600  # 24 hours
_FETCH_TIMEOUT = 10  # seconds
_MAX_CONTENT_LEN = 200_000  # 200 KB raw HTML limit
_MAX_EXTRACTED_CHARS = 4000  # per-URL text limit sent to LLM


class _TextExtractor(html.parser.HTMLParser):
    """Minimal HTML->text extractor using only the stdlib."""

    _SKIP_TAGS = frozenset(
        {
            "script",
            "style",
            "noscript",
            "svg",
            "head",
            "meta",
            "link",
            "nav",
            "footer",
            "header",
            "iframe",
            "object",
            "embed",
        }
    )

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        if tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._pieces.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse whitespace
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _extract_text(html_content: str) -> str:
    """Extract readable text from HTML."""
    parser = _TextExtractor()
    parser.feed(html_content)
    return parser.get_text()


def _is_safe_url(url: str) -> bool:
    """Reject URLs targeting private/reserved IPs or non-HTTP(S) schemes (SSRF protection)."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    # Block obvious internal hostnames
    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return False

    try:
        resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _family, _type, _proto, _canonname, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                logger.warning("llm_fetch_ssrf_blocked url=%s resolved_ip=%s", url, ip)
                return False
    except (socket.gaierror, ValueError):
        return False

    return True


async def fetch_url_content(url: str) -> str | None:
    """Fetch a single URL and return extracted text, or None on failure."""
    if not _is_safe_url(url):
        return None

    # Check cache
    now = time.monotonic()
    cached = _cache.get(url)
    if cached and (now - cached[0]) < _CACHE_TTL:
        return cached[1]

    try:
        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "GitPulse-CourseContext/1.0"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                logger.warning("llm_fetch_skip_content_type url=%s type=%s", url, content_type)
                return None

            body = resp.text[:_MAX_CONTENT_LEN]
            text = _extract_text(body) if "text/html" in content_type else body

            text = text[:_MAX_EXTRACTED_CHARS]
            _cache[url] = (now, text)
            return text

    except httpx.HTTPStatusError as exc:
        logger.debug("llm_fetch_http_error url=%s status=%s", url, exc.response.status_code)
    except httpx.RequestError as exc:
        logger.warning("llm_fetch_request_error url=%s error=%s", url, exc)
    except Exception:
        logger.warning("llm_fetch_unexpected_error url=%s", url, exc_info=True)
    return None


async def build_course_context(
    course_type: str,
    resource_urls: list[dict[str, Any]],
    course_name: str = "",
    course_description: str = "",
) -> str:
    """Build a dynamic course-context string for the LLM system prompt.

    1. Start with a base description derived from course_type.
    2. Fetch each configured resource URL and append extracted content.
    """
    # Base context from course_type
    if course_type == "zsi":
        base = (
            "This is a Software Engineering Fundamentals course (ZSI) at a university. "
            "Students work in teams on a software project using Git, GitLab, branches, "
            "Merge Requests, code review, and unit tests.\n"
        )
    elif course_type == "devops":
        base = (
            "This is a DevOps Fundamentals course at a university. "
            "Students learn CI/CD, version control, teamwork, automated "
            "workflows, and proper merge processes.\n"
        )
    else:
        base = (
            "This is a university course"
            + (f" ({course_name})" if course_name else "")
            + ". Students work in teams on software projects.\n"
        )

    if course_description:
        base += f"Course description: {course_description}\n"

    # Fetch and append resource URL content
    if not resource_urls:
        return base

    # Prepare fetch tasks (concurrent)
    valid_entries = [
        (e.get("label", "") or e.get("url", ""), e.get("url", ""))
        for e in resource_urls
        if e.get("url")
    ]
    if not valid_entries:
        return base

    results = await asyncio.gather(
        *(fetch_url_content(url) for _label, url in valid_entries),
        return_exceptions=True,
    )

    fetched_parts: list[str] = []
    for (label, _url), result in zip(valid_entries, results, strict=True):
        if isinstance(result, str) and result:
            fetched_parts.append(f"--- {label} ---\n{result}")

    if fetched_parts:
        base += (
            "\nThe following content was extracted from configured course resource pages. "
            "Use it to understand the specific assignments, grading criteria, "
            "and requirements for this course:\n\n" + "\n\n".join(fetched_parts) + "\n"
        )

    return base
