"""Every course-scoped write ROUTE is either guarded or explicitly excused.

`test_archived_course_readonly.py` asserts the same property against a
hand-maintained list of handlers, which is exactly where a new endpoint slips
through: nobody remembers to add it. This test walks the app's real routing
table instead, so a mutation added tomorrow fails here until someone either
adds the archived guard or records - in `_ALLOWED_ON_ARCHIVED`, with a reason -
why the action must stay available on an archived course.

An audit with this test found four unguarded writes, including two that start a
paid LLM call and one that issues a live webhook secret.
"""

from __future__ import annotations

import inspect
import re
from typing import Any

from fastapi.routing import APIRoute

from app.main import create_app

# Any of these in the handler source counts as the archived guard.
_GUARDS = (
    "ensure_course_active",
    "_archived_block",
    "course.is_active",
    "_ensure_not_archived",
    "course_archived",
)

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Path params that make a route course-scoped.
_SCOPED_PARAM = re.compile(r"\{(course_id|team_id|project_id|student_id)\}")

# Routes that MUST keep working while a course is archived, and why. Anything
# not listed needs a guard.
_ALLOWED_ON_ARCHIVED: dict[str, str] = {
    # -- getting out of, or past, the archived state --
    "POST /api/v1/courses/{course_id}/activate": "reactivation is the way out of archived",
    "POST /dashboard/courses/{course_id}/activate": "reactivation is the way out of archived",
    "POST /dashboard/courses/{course_id}/archive": "archiving an archived course is a no-op",
    "POST /api/v1/courses/{course_id}/transfer": (
        "carrying a finished course into the next semester is what you do with an archived one; "
        "it reads the source and creates a NEW course"
    ),
    # -- purging: only ever allowed once archived --
    "DELETE /api/v1/teams/{team_id}/permanent": "purge requires the course to be archived first",
    "DELETE /api/v1/projects/{project_id}/permanent": (
        "purge requires the course to be archived first"
    ),
    # -- stopping work already in flight --
    "POST /api/v1/courses/{course_id}/jobs/cancel": "cancelling running jobs must stay possible",
    "POST /dashboard/teams/{team_id}/llm-analysis-cancel": "cancelling a running analysis",
    "POST /dashboard/projects/{project_id}/llm-analysis-cancel": "cancelling a running analysis",
    "POST /dashboard/projects/{project_id}/dismiss-llm-error": (
        "dismisses an error banner; changes no course data"
    ),
}


def _routes() -> list[tuple[str, list[str], Any]]:
    """(path, methods, endpoint) for every concrete route, including the
    lazily-included sub-routers this app defers until startup."""
    found: list[tuple[str, list[str], Any]] = []

    def walk(routes: list[Any], prefix: str = "") -> None:
        for route in routes:
            original = getattr(route, "original_router", None)
            if original is not None:
                context = getattr(route, "include_context", None)
                walk(original.routes, prefix + (getattr(context, "prefix", "") or ""))
            elif isinstance(route, APIRoute):
                found.append((prefix + route.path, sorted(route.methods or []), route.endpoint))

    walk(create_app().routes)
    return found


def test_every_course_scoped_write_route_is_guarded_or_excused() -> None:
    unguarded: list[str] = []
    checked = 0
    for path, methods, endpoint in _routes():
        writes = sorted(set(methods) & _WRITE_METHODS)
        if not writes or not _SCOPED_PARAM.search(path):
            continue
        try:
            source = inspect.getsource(endpoint)
        except (OSError, TypeError):  # pragma: no cover - builtins / C callables
            continue
        for method in writes:
            checked += 1
            key = f"{method} {path}"
            if key in _ALLOWED_ON_ARCHIVED:
                continue
            if not any(guard in source for guard in _GUARDS):
                unguarded.append(f"{key}  ->  {endpoint.__module__}.{endpoint.__name__}")

    assert checked > 30, f"route discovery found only {checked} course-scoped writes - it broke"
    assert not unguarded, (
        "course-scoped write routes with no archived-course guard:\n  "
        + "\n  ".join(sorted(unguarded))
        + "\n\nAdd `await ensure_course_active(db, <course_id>)` (or `_archived_block`), or list "
        "the route in _ALLOWED_ON_ARCHIVED with the reason it must stay available."
    )


def test_the_allowlist_has_no_stale_entries() -> None:
    """A renamed or deleted route must not leave a permanent hole behind."""
    live = {
        f"{method} {path}"
        for path, methods, _ in _routes()
        for method in sorted(set(methods) & _WRITE_METHODS)
    }
    stale = sorted(set(_ALLOWED_ON_ARCHIVED) - live)
    assert not stale, f"_ALLOWED_ON_ARCHIVED names routes that no longer exist: {stale}"
