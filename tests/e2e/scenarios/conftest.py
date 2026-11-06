"""Role-scoped browser contexts for the scenario walks.

The unit suite parses the bundle and the page-error walk loads pages as an
admin. Neither can answer "does this page hold together for a STUDENT", which
is where most of the layout reports come from - a role sees a different set of
columns, banners and actions, and it is the narrow variants that break.

Sessions are minted with `create_session_cookie`, the same function login
calls, so a role here cannot drift from a real one.
"""

from __future__ import annotations

import os
import sys
import uuid
from contextlib import suppress
from pathlib import Path
from urllib.parse import urlsplit

import pytest

pytest.importorskip("playwright", reason="playwright is not installed")

from playwright.sync_api import BrowserContext

_REPO = Path(__file__).resolve().parents[3]

# Every role the dashboard renders for. `student` is deliberately included even
# though most admin pages 403 for it: a 403 that renders a broken page is still
# a broken page, and the walker records the status alongside the findings.
ROLES = ("admin", "teacher", "student")

# Existing development data used by check, process and tooltip scenarios.
COURSE = os.getenv("GITPULSE_E2E_COURSE_ID", "dc611a9a-ef71-425f-b9e3-2fb660edce69")
TEAM = os.getenv("GITPULSE_E2E_TEAM_ID", "3c464ea7-0cc4-44f0-8041-44ab8d2e8d94")
PROJECT = os.getenv("GITPULSE_E2E_PROJECT_ID", "c16895ce-15f4-4f2a-8857-9eeca5e6e3f3")


def _session_token(role: str) -> str:
    sys.path.insert(0, str(_REPO / "src"))
    from starlette.responses import Response

    from app.config import get_settings
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie
    from tests.conftest import _TEST_ENV_DEFAULTS
    from tests.e2e.conftest import _secret_from_env_file

    secret = get_settings().secret_key
    secret = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    if os.getenv("GITPULSE_E2E_BASE_URL") and secret == _TEST_ENV_DEFAULTS["SECRET_KEY"]:
        secret = _secret_from_env_file() or secret

    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user=f"e2e-{role}",
        role=role,
        user_id=str(uuid.uuid4()),
        gitlab_username=f"e2e-{role}",
        allow_stateless_fallback=True,
    )
    raw = carrier.headers.get("set-cookie", "")
    token = raw.split(f"{SESSION_COOKIE_NAME}=", 1)[-1].split(";", 1)[0]
    assert token, f"could not mint a {role} session cookie"
    return token


@pytest.fixture
def context_for(browser, live_server):
    """`context_for(role)` -> a context already carrying that role's session."""
    from app.security.session_auth import SESSION_COOKIE_NAME

    made: list[BrowserContext] = []
    host = urlsplit(live_server).hostname or "127.0.0.1"

    def _make(role: str, width: int = 1440, height: int = 900) -> BrowserContext:
        ctx = browser.new_context(viewport={"width": width, "height": height})
        ctx.add_cookies(
            [
                {
                    "name": SESSION_COOKIE_NAME,
                    "value": _session_token(role),
                    "domain": host,
                    "path": "/",
                }
            ]
        )
        made.append(ctx)
        return ctx

    try:
        yield _make
    finally:
        for ctx in made:
            with suppress(Exception):
                ctx.close()
