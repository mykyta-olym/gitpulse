"""An error page offers only what can still work, and says each thing once.

A 503 - the app, or something it needs, is down - offered a search box and
links to Home, Support and Sign out, none of which could load while it was
down. Its heading and the paragraph under it were one sentence twice ("503:
Authentication backend temporarily unavailable..." / "Authentication backend
temporarily unavailable..."). And the pages were nine templates plus a
Python-built copy for the middleware, two of which ignored the message they
were handed, so a database outage said "cache or queue".
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.i18n import translate_text
from app.main import templates
from app.middleware.error_pages import ERROR_PAGES, error_context

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "src/app/templates"
AUTH_DOWN = "Authentication backend temporarily unavailable. Please retry shortly."


def _render(status: int, **page: object) -> str:
    return templates.get_template("errors/error.html").render(error_context(status, **page))


@pytest.mark.parametrize("status", [502, 503, 504])
def test_an_outage_offers_retry_and_nothing_that_needs_the_app(status: int) -> None:
    html = _render(status)
    assert 'data-action="reloadPage"' in html
    assert "data-countdown-seconds" in html, "it tries again by itself"
    assert 'class="error-search"' not in html
    assert 'href="/dashboard/' not in html, "Home / Support / Sign out cannot load"
    assert "historyBack" not in html


@pytest.mark.parametrize("status", [403, 404])
def test_a_page_that_is_not_there_offers_search_and_the_way_around(status: int) -> None:
    html = _render(status)
    assert 'class="error-search"' in html
    for href in ('href="/dashboard/"', 'href="/dashboard/support"', 'href="/dashboard/logout"'):
        assert href in html
    assert 'data-action="reloadPage"' not in html


def test_a_crash_offers_retry_and_the_way_around_but_no_search() -> None:
    html = _render(500, error_id="ABC123")
    assert 'data-action="reloadPage"' in html
    assert 'href="/dashboard/"' in html
    assert 'class="error-search"' not in html
    assert "ABC123" in html


def test_an_expired_session_offers_signing_in() -> None:
    html = _render(401)
    assert 'href="/dashboard/login"' in html
    assert 'class="error-search"' not in html
    assert 'href="/dashboard/support"' not in html


def test_the_detail_goes_under_the_heading_not_into_it() -> None:
    page = error_context(503, message=AUTH_DOWN)
    assert page["title"] == "Service Unavailable"
    assert page["message"] == AUTH_DOWN
    # Rendered in the default locale, and translated like the rest of the page.
    sentence = translate_text("sk", AUTH_DOWN)
    assert sentence != AUTH_DOWN
    assert _render(503, message=AUTH_DOWN).count(sentence) == 1


def test_a_detail_that_only_names_the_status_gives_way_to_the_description() -> None:
    assert error_context(404, message="Not Found")["message"] == ERROR_PAGES[404].hint
    assert error_context(503, message="Service unavailable")["message"] == ERROR_PAGES[503].hint


def test_every_error_page_is_the_one_template() -> None:
    assert sorted(p.name for p in (TEMPLATES / "errors").iterdir()) == ["error.html"]
    handlers = (ROOT / "src/app/api/exception_handlers.py").read_text(encoding="utf-8")
    assert handlers.count('template_name="errors/') == 1
    middleware = (ROOT / "src/app/middleware/error_pages.py").read_text(encoding="utf-8")
    assert "<main" not in middleware, "the middleware renders the template, not its own copy"


@pytest.mark.parametrize("name", ["base.html", "login.html", "errors/error.html"])
def test_every_page_head_has_the_standard_web_app_meta(name: str) -> None:
    """Chrome reports `apple-mobile-web-app-capable` as deprecated unless the
    standard `mobile-web-app-capable` is there too."""
    assert '<meta name="mobile-web-app-capable" content="yes">' in (TEMPLATES / name).read_text(
        encoding="utf-8"
    )
