"""Every error page GitPulse renders, from one table and one template.

What a status is called, what it says by default, which illustration it
shows, and what the reader can still do from it. The exception handlers, the
dashboard's not-found pages and the middleware fallbacks all build their
context here and render ``errors/error.html``. They used to be nine templates,
a Python-built copy for the middleware with its own wording, and handlers
whose message two of the templates ignored - a database outage read "a
required service (cache or queue) is unavailable".

What a page offers follows from what still works:

    find         403, 404 - the app is up and the reader is looking for
                 something: search, and the way back and around.
    retry        500, 408 - one request failed: Retry, and the way around.
    back         other 4xx - the request itself was wrong: the way back.
    sign_in      401 - only signing in helps.
    wait         429 - a countdown, then the page reloads itself.
    unavailable  502, 503, 504 - the app, or something it needs, is down, so
                 search and links would fail as well: Retry, and a reload
                 every few seconds until it is back.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from html import escape
from http import HTTPStatus
from typing import Any

from starlette.requests import Request

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorPage:
    title: str
    hint: str  # the description when the error names no detail of its own
    offer: str
    image: int  # which illustration: img/error-<image>.svg


ERROR_PAGES: dict[int, ErrorPage] = {
    400: ErrorPage("Bad Request", "The server could not understand the request.", "back", 500),
    401: ErrorPage(
        "Session Expired", "Your session has expired or you are not signed in.", "sign_in", 401
    ),
    403: ErrorPage("Forbidden", "You don't have permission to access this resource.", "find", 403),
    404: ErrorPage(
        "Page not found", "Make sure the address is correct and the page hasn't moved.", "find", 404
    ),
    405: ErrorPage(
        "Method Not Allowed", "This action is not allowed on the requested resource.", "back", 500
    ),
    408: ErrorPage("Request Timeout", "The request took too long. Please try again.", "retry", 500),
    409: ErrorPage(
        "Conflict", "A conflict occurred. The resource may have been modified.", "back", 500
    ),
    422: ErrorPage("Validation Error", "The submitted data could not be processed.", "back", 500),
    429: ErrorPage(
        "Too Many Requests",
        "You're sending requests too quickly. Please wait a moment and try again.",
        "wait",
        429,
    ),
    500: ErrorPage(
        "Internal server error",
        "Whoops, something went wrong on our end. Try refreshing the page, or going back "
        "and attempting the action again.",
        "retry",
        500,
    ),
    502: ErrorPage(
        "Bad Gateway",
        "An upstream service (GitLab) could not be reached, so this page could not be served "
        "right now.",
        "unavailable",
        502,
    ),
    503: ErrorPage(
        "Service Unavailable",
        "The service is temporarily unavailable. Please try again in a moment.",
        "unavailable",
        503,
    ),
    504: ErrorPage(
        "Gateway Timeout",
        "An upstream service took too long to respond. The request was canceled to keep the "
        "page from hanging.",
        "unavailable",
        502,
    ),
}


def error_page_for(status: int) -> ErrorPage:
    if status in ERROR_PAGES:
        return ERROR_PAGES[status]
    if status >= 500:
        return ERROR_PAGES[503 if status > 500 else 500]
    return ERROR_PAGES[400]


def _says_only(text: str, *names: str) -> bool:
    """True when the text is just a name for the status - "Not Found" under
    a "404: Page not found" heading says nothing new."""
    t = text.strip().rstrip(".").casefold()
    return any(t == n.strip().rstrip(".").casefold() for n in names if n)


def error_context(
    status: int,
    *,
    title: str | None = None,
    message: str | None = None,
    suggestions: list[str] | tuple[str, ...] = (),
    **extra: Any,
) -> dict[str, Any]:
    """The template context of an error page. ``message`` is the error's own
    detail; one that only names the status (or repeats the title) gives way
    to the status's description, so the heading and the paragraph under it
    never say the same thing. ``extra`` adds to or overrides the rest
    (``offer``, ``error_id``, ``retry_after``, the feature fields...)."""
    page = error_page_for(status)
    heading = title or page.title
    text = (message or "").strip()
    try:
        phrase = HTTPStatus(status).phrase
    except ValueError:
        phrase = ""
    if not text or _says_only(text, heading, page.title, phrase):
        text = page.hint
    return {
        "status_code": status,
        "title": heading,
        "message": text,
        "suggestions": list(suggestions),
        "offer": page.offer,
        "image": page.image,
        **extra,
    }


def build_error_page_html(
    status_code: int,
    *,
    request: Request | None = None,
    retry_after: int | None = None,
    csp_nonce: str = "",
) -> bytes:
    """The error page for a middleware that has no response to style: the
    same template, rendered with the app's environment and the reader's
    locale."""
    ctx = error_context(status_code, retry_after=retry_after, csp_nonce=csp_nonce)
    try:
        from app.i18n import get_template_i18n_context
        from app.main import templates

        if request is not None:
            ctx.update(get_template_i18n_context(request), request=request)
        return templates.get_template("errors/error.html").render(ctx).encode()
    except Exception:
        # The app itself may be what is broken. A bare page still beats
        # the raw JSON this middleware exists to replace.
        logger.exception("error_page_render_failed status=%s", status_code)
        page = error_page_for(status_code)
        return (
            f"<!DOCTYPE html><html><head><meta charset=utf-8><title>{status_code}</title>"
            f'<meta name="viewport" content="width=device-width, initial-scale=1"></head>'
            f"<body><h1>{status_code}: {escape(page.title)}</h1><p>{escape(page.hint)}</p>"
            f"</body></html>"
        ).encode()
