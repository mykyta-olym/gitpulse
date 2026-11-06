"""Every route authenticates, unless it is on a named public list.

A route that forgets its auth dependency does not raise, look wrong, or appear
in a diff - it simply answers everybody. The default has to be "closed": a new
endpoint is authenticated, and making it public is a deliberate line added
here with a reason. This walks the whole routing table and fails if any route
has no authentication in its dependency chain and is not on the list.

This is the standing form of the manual sweep in
scratchpad/attack_route_authz.py, which found the surface clean on 2026-08-20.
"""

from __future__ import annotations

import inspect

from fastapi.routing import APIRoute

from app.main import create_app

# Markers in a dependency chain (or the endpoint body) that mean the endpoint
# checks who the caller is.
AUTH_MARKERS = (
    "session",
    "current_user",
    "current_session",
    "auth",
    "require_",
    "admin",
    "teacher",
    "staff",
    "bearer",
    "api_key",
    "csrf",
    "webhook",
    "token",
    "role",
    "permission",
    "verify",
)

# Public by design. Each entry is a decision, with the reason it is safe.
PUBLIC_BY_DESIGN = {
    "/health": "liveness probe",
    "/health/ready": "readiness probe",
    "/health/live": "liveness probe",
    "/health/gitlab": "connectivity status only (up/down), no secrets",
    "/health/gitlab/status": "the same public connectivity report for UI polling",
    "/metrics": "scrape endpoint",
    "/dashboard/login": "the sign-in page itself",
    "/dashboard/logout": "ending a session needs no session",
    "/dashboard/language/{locale}": "sets a cookie; redirect target is guarded",
    "/csp/report": "browsers post here with no credentials; capped and rate-limited",
    "/internal/docs-authz": "IS the gate; decides for itself",
    "/internal/docs-role": "tells a reader their own role; no data",
    "/dashboard/courses/{course_id}/projects": "301 to /activity, which authenticates",
    "/privacy": "public legal page",
    "/terms": "public legal page",
    "/sw.js": "the service worker must be fetchable unauthenticated",
    "/static/offline.html": "public offline shell; adds a CSP nonce to the existing static page",
    "/favicon.ico": "static",
    "/robots.txt": "static",
    "/sitemap.xml": "static",
    "/google32f411f09f436ae2.html": "Google site-verification token",
}


def _walk(routes, prefix=""):
    for route in routes:
        original = getattr(route, "original_router", None)
        if original is not None:
            context = getattr(route, "include_context", None)
            yield from _walk(original.routes, prefix + (getattr(context, "prefix", "") or ""))
        elif isinstance(route, APIRoute):
            yield prefix + route.path, route


def _has_auth(route) -> bool:
    names: set[str] = set()

    def collect(dep, depth=0):
        if depth > 6:
            return
        call = getattr(dep, "call", None) or getattr(dep, "dependency", None) or dep
        names.add((getattr(call, "__name__", "") or str(call)).lower())
        for sub in getattr(dep, "dependencies", []) or []:
            collect(sub, depth + 1)

    for dep in getattr(route, "dependencies", []) or []:
        collect(dep)
    dependant = getattr(route, "dependant", None)
    if dependant:
        for sub in getattr(dependant, "dependencies", []) or []:
            collect(sub)

    endpoint = getattr(route, "endpoint", None)
    if endpoint:
        names.add(getattr(endpoint, "__name__", "").lower())
        try:
            for param in inspect.signature(endpoint).parameters.values():
                names.add(str(param.annotation).lower())
                names.add(param.name.lower())
        except (TypeError, ValueError):
            pass
        try:
            body = inspect.getsource(endpoint).lower()
        except (OSError, TypeError):
            body = ""
        names.update(f"src:{m}" for m in AUTH_MARKERS if m in body)

    return any(marker in name for name in names for marker in AUTH_MARKERS)


def test_no_route_is_accidentally_public() -> None:
    app = create_app()
    unguarded = []
    for path, route in _walk(app.routes):
        methods = {m for m in (route.methods or set()) if m not in ("HEAD", "OPTIONS")}
        if not methods or path in PUBLIC_BY_DESIGN:
            continue
        if not _has_auth(route):
            unguarded.append(f"{','.join(sorted(methods))} {path}")

    assert not unguarded, (
        "these routes have no authentication in their dependency chain and are "
        "not on the PUBLIC_BY_DESIGN list. If a route is meant to be public, add "
        "it there with the reason it is safe; otherwise give it an auth "
        "dependency:\n  " + "\n  ".join(sorted(unguarded))
    )


def test_the_public_list_has_no_stale_entries() -> None:
    """An entry that no longer matches a real route is dead - it can hide a
    genuinely unguarded route that happens to share the path later."""
    app = create_app()
    real = {path for path, _ in _walk(app.routes)}
    stale = [p for p in PUBLIC_BY_DESIGN if p not in real]
    assert not stale, f"PUBLIC_BY_DESIGN lists routes that do not exist: {stale}"
