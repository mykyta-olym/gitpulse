"""Every write that trusts the session cookie also checks the CSRF token.

The cookie is SameSite=Lax, which stops most cross-site posts - not all of
them. An audit on 2026-09-27 found twelve such routes with no ``verify_csrf``
(event retry and replay and ticket actions), although the app's own requests had always
sent the token. This walks the app's real routing table, so a write added
tomorrow fails here until it checks the token too.
"""

from __future__ import annotations

from typing import Any

from fastapi.routing import APIRoute

from app import dependencies as deps
from app.main import create_app

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_session_auth(call: Any) -> bool:
    """A dependency that authenticates from the dashboard session cookie."""
    if call in (
        deps.require_dashboard_auth,
        deps.get_current_user,
        deps.get_current_teacher,
        deps.get_current_admin,
    ):
        return True
    return str(getattr(call, "__qualname__", "")).startswith("require_role.")


def _calls(dependant: Any) -> list[Any]:
    """Every dependency callable a route runs, at any depth."""
    found: list[Any] = []
    for sub in dependant.dependencies:
        found.append(sub.call)
        found.extend(_calls(sub))
    return found


def _write_routes() -> list[tuple[str, str, APIRoute]]:
    """(method, path, route) for every write, including the lazily-included
    sub-routers this app defers until startup."""
    found: list[tuple[str, str, APIRoute]] = []

    def walk(routes: list[Any], prefix: str = "") -> None:
        for route in routes:
            original = getattr(route, "original_router", None)
            if original is not None:
                context = getattr(route, "include_context", None)
                walk(original.routes, prefix + (getattr(context, "prefix", "") or ""))
            elif isinstance(route, APIRoute):
                for method in sorted(set(route.methods or ()) & _WRITE_METHODS):
                    found.append((method, prefix + route.path, route))

    walk(create_app().routes)
    return found


def test_every_session_cookie_write_checks_the_csrf_token() -> None:
    missing: list[str] = []
    session_writes = 0
    for method, path, route in _write_routes():
        calls = _calls(route.dependant)
        if not any(_is_session_auth(call) for call in calls):
            continue
        session_writes += 1
        if deps.verify_csrf not in calls:
            endpoint = route.endpoint
            missing.append(f"{method} {path}  ->  {endpoint.__module__}.{endpoint.__name__}")

    assert session_writes > 40, (
        f"route discovery found only {session_writes} session-cookie writes - it broke"
    )
    assert not missing, (
        "writes authenticated by the session cookie that never check the CSRF token:\n  "
        + "\n  ".join(sorted(missing))
        + "\n\nAdd `_csrf: CSRFCheck` to the handler. The browser side already sends the "
        "token: apiCall and fetch in the X-CSRF-Token header, sendBeacon as csrf_token "
        "in the JSON body."
    )
