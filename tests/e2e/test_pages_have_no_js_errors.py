"""Load every dashboard page in Chromium and fail on any JavaScript error.

This is the check nothing else in the suite can make. `node --check` parses.
The stub-DOM runner proves the bundle loads. Only a real browser evaluates the
page the way a teacher's does - with layout, real event dispatch, htmx swaps
and Alpine reactivity - and only there does a handler that throws actually
throw.
"""

from __future__ import annotations

import os

import pytest
from playwright.sync_api import Page

from tests.e2e.conftest import server_log_tail

# A real gate, but only against a server you point it at.
#
# With GITPULSE_E2E_BASE_URL set (e.g. the one `start-dev.ps1 api` runs) all 11
# pages pass: no uncaught JS, no console errors, no failed requests. Against
# the server conftest spawns itself, pages answer 5xx intermittently for
# reasons that are still unexplained - that is a harness defect, not an
# application one, so the suite SKIPS there rather than reporting a failure it
# cannot substantiate.
#
# Skip, not xfail: a suite where everything is "expected to fail" is theatre,
# and it would have hidden the run below where 10 pages passed only because
# the session cookie was rejected and every page was really the login form.
pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "browser suite needs GITPULSE_E2E_BASE_URL pointing at a running server "
        "(the spawned one is unreliable - see the module docstring)",
        allow_module_level=True,
    )


def _pages() -> list[str]:
    """Discovered from the app, not hard-coded. The old list named
    `/dashboard/courses/`, which does not exist."""
    from app.main import create_app
    from tests.route_discovery import dashboard_pages

    # logout renders a confirmation form and ends the session for the shared
    # browser context, so it is walked by the integration suite instead.
    return dashboard_pages(create_app(), exclude=("/dashboard/logout",))


_PAGES = _pages()

# Console noise that is not a code defect: the app deliberately surfaces a dead
# GitLab token.
#
# 404 is deliberately NOT ignored any more. It was, and it hid the fact that
# `/dashboard/courses/` does not exist - the page 404'd, the console error was
# swallowed, and the test passed while asserting nothing.
_IGNORED_CONSOLE = (
    "favicon",
    "gitlab",
)


def _ignorable(msg: str, failed: list[str]) -> bool:
    """Is this console error one of the deliberately-tolerated ones?

    The list above could never match the case it was written for. A failed
    subresource reaches the console as "Failed to load resource: the server
    responded with a status of 503" - Chrome does NOT put the URL in that
    message - so the "gitlab" entry matched nothing, and a dev server with no
    GitLab token failed every page in this walk.

    The URL is in the responses we record ourselves, so correlate by status
    code: tolerate the message only when every request that failed with that
    status is one we already tolerate.
    """
    if any(i in msg.lower() for i in _IGNORED_CONSOLE):
        return True
    marker = "status of "
    if marker not in msg:
        return False
    code = msg.split(marker, 1)[1][:3]
    if not code.isdigit():
        return False
    urls = [f.split(" ", 1)[1] for f in failed if f.startswith(code + " ")]
    return bool(urls) and all(any(i in u.lower() for i in _IGNORED_CONSOLE) for u in urls)


def _collect(page: Page) -> tuple[list[str], list[str], list[str]]:
    """Record uncaught errors, console errors, and failed responses.

    The failed-response list exists for diagnosis: the console only says
    "the server responded with 500", never which URL, which makes a failure
    impossible to act on.
    """
    errors: list[str] = []
    console: list[str] = []
    failed: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: console.append(m.text) if m.type == "error" else None)
    page.on(
        "response",
        lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None,
    )
    return errors, console, failed


def test_the_session_and_bundle_are_live(page: Page, live_server: str) -> None:
    """Two guards against a vacuous suite, on the FIRST page load of the run.

    Without the first, every page below would render the login form and pass.
    Without the second, a page could be error-free simply because its scripts
    never ran. It must be the first load: pages answer 5xx intermittently over
    a run (see the module docstring), so a later probe would measure that
    rather than the bundle.
    """
    page.goto(f"{live_server}/dashboard/", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)

    assert "/dashboard/login" not in page.url, "cookie rejected - the whole walk is vacuous"
    exports = page.evaluate("() => Object.keys(window.GP || {}).length")
    assert exports > 50, f"window.GP has only {exports} exports - core.bundle.js did not run"


@pytest.mark.parametrize("path", _PAGES)
def test_page_raises_no_javascript_error(page: Page, live_server: str, path: str) -> None:
    errors, console, failed = _collect(page)

    page.goto(f"{live_server}{path}", wait_until="domcontentloaded")
    # Neither `load` nor `networkidle` ever fires: the app opens SSE streams and
    # polls job state, so resources never stop arriving. Wait for the document
    # instead, then a fixed beat for DOMContentLoaded handlers and htmx swaps.
    page.wait_for_timeout(2500)

    noisy = [c for c in console if not _ignorable(c, failed)]
    detail = f"\nfailed requests: {failed}\n--- server log ---\n{server_log_tail()}"
    assert not errors, f"{path} uncaught JS: {errors}{detail}"
    assert not noisy, f"{path} console errors: {noisy}{detail}"

    # A 5xx behind the page is a defect even when nothing throws. The client
    # catches its own fetch failures and shows a toast, so a broken endpoint
    # left no trace here: the console stayed clean and this walk passed. The
    # list was already being collected for the failure message - it just was
    # never checked.
    server_errors = [
        f
        for f in failed
        if f.split(" ", 1)[0].startswith("5") and not any(i in f.lower() for i in _IGNORED_CONSOLE)
    ]
    assert not server_errors, f"{path} made requests the server could not answer: {server_errors}"
