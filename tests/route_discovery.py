"""Discover the app's real page routes instead of hard-coding them.

Hard-coded lists rot silently. Both page-walk suites carried
`/dashboard/courses/`, which does not exist - it 404s, and because a 404 was
on the ignored-console list the browser test asserted nothing at all while
looking green.

Enumeration needs a walk rather than a read of ``app.routes``: this FastAPI
defers ``include_router`` into ``_IncludedRouter`` placeholders that are only
flattened when the app starts, so a plain read reports 19 routes and no
dashboard at all. Unwrapping ``original_router`` finds the actual routes.
"""

from __future__ import annotations

from typing import Any

from fastapi.routing import APIRoute

# Endpoints that are not pages: JSON for the client, SSE streams, OAuth
# plumbing, and partials fetched by htmx. Walking them proves nothing about
# rendering and, for the streams, would simply hang.
_NON_PAGE_MARKERS = (
    "/api/",
    "/stream",
    "/status",
    "/oauth/",
    "/session-check",
    "/sidebar-badges",
    "/semester-presets",
    "/attention-items",
    "/stats",
    "/search",
    "/users/list",
    "/tour/",
    # Both live under /dashboard and answer GET, but neither is a page:
    # /dashboard/activity returns the bare activity-feed FRAGMENT that
    # 20-live-updates.js swaps into the home page, and /dashboard/notifications
    # is a JSONResponse the toast poller consumes. The browser walk was loading
    # a fragment and a JSON document as top-level pages - no <head>, no
    # #main-content, no scripts - and reporting them as two clean pages.
    # Written full-length so /dashboard/courses/{id}/activity is unaffected.
    "/dashboard/activity",
    "/dashboard/notifications",
)


def iter_routes(routes: list[Any], prefix: str = "") -> list[tuple[str, list[str]]]:
    """Return ``(path, methods)`` for every concrete route, recursing lazily-
    included sub-routers."""
    found: list[tuple[str, list[str]]] = []
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            context = getattr(route, "include_context", None)
            found += iter_routes(original.routes, prefix + (getattr(context, "prefix", "") or ""))
        elif isinstance(route, APIRoute):
            found.append((prefix + route.path, sorted(route.methods or [])))
    return found


def dashboard_pages(app: Any, *, exclude: tuple[str, ...] = ()) -> list[str]:
    """Parameterless dashboard pages that render HTML, sorted."""
    pages = {
        path
        for path, methods in iter_routes(app.routes)
        if "GET" in methods
        and path.startswith("/dashboard")
        and "{" not in path
        and not any(marker in path for marker in _NON_PAGE_MARKERS)
        and path not in exclude
    }
    return sorted(pages)
