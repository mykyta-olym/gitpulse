"""A page that says "not available" should not also say you are somewhere else.

`feature_disabled.html` set no breadcrumb, so it inherited base.html's default -
`nav_active|default('dashboard')`, which renders "Your work / Dashboard". Opening
Support with the forms
off, therefore told the reader they were on the dashboard while showing them a
page that is not the dashboard and a URL that is not either.

Its two buttons had the same problem in miniature: "Go Back" and "Dashboard" were
two labels for `/dashboard/`. `data-nav-back` makes the first mean what it says -
the core handler steps back through history when there is somewhere to step back
to, and falls through to the href when there is not.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "src/app/templates/feature_disabled.html"
CORE_JS = REPO / "src/app/templates/static/js/_parts/core/30-data-actions.js"


@pytest.fixture(scope="module")
def page() -> str:
    return PAGE.read_text(encoding="utf-8")


def test_it_names_itself_in_the_breadcrumb(page: str) -> None:
    assert "breadcrumb_items" in page, "the page inherits 'Your work / Dashboard' again"
    crumbs = page.split("breadcrumb_items = [", 1)[1].split("]", 1)[0]
    assert "Feature Not Available" in crumbs, "the last crumb does not name this page"


def test_going_back_goes_back(page: str) -> None:
    assert "'nav-back': ''" in page, "'Go Back' is a second link to the dashboard again"


def test_the_handler_behind_that_attribute_still_exists() -> None:
    """The attribute is inert without it, and the button would silently become
    a plain link to the dashboard - which is what it used to be."""
    js = CORE_JS.read_text(encoding="utf-8")
    assert "[data-nav-back]" in js
    assert "window.history.back()" in js
