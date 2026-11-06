"""A course configuration import reads the body the page posts.

The page posts the configuration as JSON with the CSRF token in the
X-CSRF-Token header. The CSRF check reads no body in that case, and the import
into an existing course looked only for a body that check had cached - so
every "Import full configuration" from the Settings page answered 400 "No
configuration provided". Both imports read through one helper now.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from starlette.requests import Request

from app.api.dashboard.courses.settings_config import read_config_text

REPO = Path(__file__).resolve().parents[2]


def _request(body: bytes, content_type: str) -> Request:
    sent = False

    async def receive() -> dict[str, object]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(b"content-type", content_type.encode())],
    }
    return Request(scope, receive)


async def test_a_json_body_nobody_read_before() -> None:
    """The page's own request: JSON, token in the header, body unread."""
    config = {"settings": {"green_threshold": 0.75}}
    text = await read_config_text(_request(json.dumps(config).encode(), "application/json"))
    assert json.loads(text) == config


async def test_a_form_upload() -> None:
    raw = json.dumps({"course": {"code": "X"}})
    body = urlencode({"config_json": raw, "csrf_token": "t"}).encode()
    text = await read_config_text(_request(body, "application/x-www-form-urlencoded"))
    assert text == raw


def test_both_imports_read_through_it() -> None:
    settings = (REPO / "src/app/api/dashboard/courses/settings.py").read_text(encoding="utf-8")
    config = (REPO / "src/app/api/dashboard/courses/settings_config.py").read_text(encoding="utf-8")
    assert 'getattr(request, "_body"' not in settings, "the import reads a cache again"
    assert "await read_config_text(request)" in settings
    assert "await read_config_text(request)" in config
