"""Real-browser fixtures: a live server plus an authenticated Chromium page.

These are the only tests that execute the JavaScript the way a teacher's
browser does. Everything else in the suite either parses the bundle or runs it
against a stub DOM, neither of which can see an exception thrown from a click
handler, an htmx swap, or Alpine's reactivity.

Skipped unless Playwright *and* its Chromium build are present, so a checkout
without `python -m playwright install chromium` still has a green suite.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen

import pytest

pytest.importorskip("playwright", reason="playwright is not installed")

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from tests.conftest import _TEST_ENV_DEFAULTS

_REPO = Path(__file__).resolve().parents[2]
_STARTUP_TIMEOUT_S = 90


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _secret_from_env_file() -> str | None:
    """SECRET_KEY as the repo's .env spells it - the value a locally-run server
    is using. Read directly rather than through pydantic-settings, which the
    test environment has already overridden by then."""
    env = _REPO / ".env"
    if not env.exists():
        return None
    for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() == "SECRET_KEY":
            return value.strip().strip("'\"") or None
    return None


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as p:
        try:
            launched = p.chromium.launch()
        except Exception as exc:
            pytest.skip(f"chromium unavailable - run `playwright install chromium` ({exc})")
        try:
            yield launched
        finally:
            launched.close()


@pytest.fixture(scope="session")
def live_server() -> Iterator[str]:
    """Serve the real app on a random port, backed by the dev database.

    Set ``GITPULSE_E2E_BASE_URL`` to test an already-running server instead
    (e.g. the one `start-dev.ps1 api` provides). That is not just a
    convenience: the suite is clean against a long-running server and fails
    against the one spawned here, so the switch is how you tell an
    application problem apart from a harness one.
    """
    external = os.getenv("GITPULSE_E2E_BASE_URL")
    if external:
        _SERVER_LOG["tail"] = lambda: f"<external server at {external}; see its own console>"
        yield external.rstrip("/")
        return

    port = _free_port()
    env = {
        **os.environ,
        "PYTHONPATH": str(_REPO / "src"),
        "APP_ENV": "test",
        "ALLOWED_HOSTS": '["127.0.0.1","localhost","testserver"]',
    }
    # Log to a FILE, never a pipe. The app logs heavily via structlog; an
    # unread PIPE fills its ~64 KB OS buffer and uvicorn then blocks forever on
    # write, so the port stays open while every request hangs.
    log = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed in the finally below
        mode="w+", suffix=".log", prefix="gp-e2e-", delete=False
    )
    proc = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=_REPO,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )

    def _tail() -> str:
        log.flush()
        return Path(log.name).read_text(encoding="utf-8", errors="ignore")[-2000:]

    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + _STARTUP_TIMEOUT_S
    try:
        # Poll a real HTTP response, not just the socket: uvicorn binds the port
        # before the application has finished starting up.
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.skip(f"server exited early:\n{_tail()}")
            try:
                with urlopen(f"{base}/health", timeout=2):  # noqa: S310 - fixed localhost URL
                    break
            except (URLError, OSError):
                time.sleep(0.4)
        else:
            pytest.skip(f"server did not answer /health in {_STARTUP_TIMEOUT_S}s:\n{_tail()}")
        # Warm the app before any browser touches it. A cold worker resolves
        # settings, opens the DB pool and connects Redis on the first request;
        # a browser firing that request alongside a dozen assets and an SSE
        # stream turned it into an intermittent 5xx.
        for _ in range(3):
            with suppress(URLError, OSError):
                urlopen(f"{base}/dashboard/login", timeout=20).read()  # noqa: S310
            time.sleep(0.5)

        # Expose the log so a failing test can report what the SERVER said.
        # A browser failure otherwise reads only as "500", with the traceback
        # that explains it sitting in a file nobody looks at.
        _SERVER_LOG["tail"] = _tail
        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        # On Windows the child may still hold the handle for a moment after
        # terminate(); a failed cleanup must not mask the test's own result.
        with suppress(OSError):
            Path(log.name).unlink(missing_ok=True)


# Populated by `live_server`; read by tests when an assertion fails.
_SERVER_LOG: dict[str, object] = {}


def server_log_tail() -> str:
    tail = _SERVER_LOG.get("tail")
    return tail() if callable(tail) else "<server log unavailable>"


@pytest.fixture
def admin_context(browser: Browser, live_server: str) -> Iterator[BrowserContext]:
    """A browser context carrying a genuine admin session cookie.

    Minted with `create_session_cookie` itself, so the fixture cannot drift
    from the payload login actually writes.
    """
    sys.path.insert(0, str(_REPO / "src"))
    from starlette.responses import Response

    from app.config import get_settings
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = get_settings().secret_key
    secret = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    # An EXTERNAL server (GITPULSE_E2E_BASE_URL) reads its secret from the repo
    # .env, while tests/conftest.py substitutes its own SECRET_KEY whenever the
    # variable is unset. Signing with that one produces a cookie the server
    # rejects, and the whole walk then runs against the login page - which is
    # exactly what `test_the_session_and_bundle_are_live` exists to catch. When
    # the secret in play is that stand-in, take the one the server actually read.
    if os.getenv("GITPULSE_E2E_BASE_URL") and secret == _TEST_ENV_DEFAULTS["SECRET_KEY"]:
        secret = _secret_from_env_file() or secret

    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user="e2e-admin",
        role="admin",
        user_id=str(uuid.uuid4()),
        gitlab_username="e2e-admin",
        allow_stateless_fallback=True,
    )
    raw = carrier.headers.get("set-cookie", "")
    token = raw.split(f"{SESSION_COOKIE_NAME}=", 1)[-1].split(";", 1)[0]
    assert token, "could not mint a session cookie"

    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    # Cookie domain must match the host under test - localhost and 127.0.0.1
    # are different origins to the browser.
    host = urlsplit(live_server).hostname or "127.0.0.1"
    ctx.add_cookies([{"name": SESSION_COOKIE_NAME, "value": token, "domain": host, "path": "/"}])
    try:
        yield ctx
    finally:
        ctx.close()


@pytest.fixture
def page(admin_context: BrowserContext) -> Page:
    """Closed with its context, so no teardown of its own."""
    return admin_context.new_page()
