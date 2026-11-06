"""First-paint cookie data contains public preferences and preserves HTML boundaries."""

import html
import json
import re

from starlette.requests import Request

from app.main import templates


def test_preference_cookie_data_excludes_session_and_escapes_values() -> None:
    request = Request(
        {
            "type": "http",
            "headers": [
                (
                    b"cookie",
                    b"gitpulse_color_mode=dark; gp_lang=en; gp_period=2026-2027-winter~now; "
                    b"session=private; gp_cookie_consent=accepted",
                )
            ],
        }
    )
    source = (
        '{% from "components/preference_cookies.html" import preference_cookie_data %}'
        "{{ preference_cookie_data(request) }}"
    )
    rendered = templates.env.from_string(source).render(request=request)
    match = re.search(r'data-preference-cookies="([^"]*)"', rendered)
    assert match is not None
    data = json.loads(html.unescape(match[1]))
    assert data == {
        "gitpulse_color_mode": "dark",
        "gp_lang": "en",
        "gp_period": "2026-2027-winter~now",
        "gp_cookie_consent": "accepted",
    }
    assert "private" not in rendered
