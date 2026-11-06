"""Picking a filter changes the rows, not the filter.

Every in-app navigation stepped the whole content back to 75% until the next
page landed - including a navigation that only changes the query (the period,
a server-side sort, a page of the same list). The controls band faded with it,
so the filter just picked went out and came back: "the selected filter blinks
while it loads", on every page with a period selector. The period box also kept
the OLD term until then, and the swap dropped the focus to <body>.

Now a navigation within the same page marks the content `is-refining`: the
controls keep full strength, only the rows step back, the box says the pick at
once, and the focus comes back to the box when the page lands. A navigation to
another page still steps the whole page back - that page IS stale.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATIC = REPO / "src/app/templates/static"
PROGRESS = STATIC / "js/_parts/core/42-spa-navigation.js"
LOGO_CSS = STATIC / "css/logo.css"
PERIOD_JS = STATIC / "js/academic-period.js"


def _navigate_now() -> str:
    src = PROGRESS.read_text(encoding="utf-8")
    return src.split("function _navigateNow(", 1)[1].split("\n  function ", 1)[0]


def test_a_same_page_navigation_is_marked_refining() -> None:
    body = _navigate_now()
    assert ".pathname === window.location.pathname" in body
    assert "mc.classList.toggle('is-refining', inPlace)" in body
    # still inert and still the progress cursor
    assert "mc.classList.add('is-navigating')" in body
    assert "mc.classList.remove('is-refining')" in body


def test_only_the_rows_step_back_when_the_page_stays() -> None:
    css = LOGO_CSS.read_text(encoding="utf-8")
    assert "#main-content.is-navigating.is-refining {\n  opacity: 1;\n}" in css.replace(
        "\r\n", "\n"
    )
    assert "#main-content.is-refining tbody {" in css
    # another page still steps back as a whole
    assert "#main-content.is-navigating {" in css


def test_the_focus_comes_back_to_the_control_after_the_swap() -> None:
    src = PROGRESS.read_text(encoding="utf-8")
    key = src.split("function _focusKeyOf(", 1)[1].split("\n  }\n", 1)[0]
    assert "el.closest('[data-period-selector]')" in key, "a click in the period menu"
    assert "CSS.escape(el.id)" in key
    body = _navigate_now()
    assert "inPlace && mc ? _focusKeyOf(document.activeElement, mc)" in body
    release = body.index("_clear();", body.index(".finally("))
    focus = body.index("mc.querySelector(refocus)?.focus({ preventScroll: true })")
    assert focus > release, "focus must return after the page leaves its inert state"
    assert "if (refocus && !_navigating)" in body


def test_the_period_box_says_the_pick_at_once() -> None:
    src = PERIOD_JS.read_text(encoding="utf-8")
    click = src.split(
        "const link = target.closest('[data-period-selector] a[data-period-key]');", 1
    )[1]
    click = click.split("\n    const toggle", 1)[0]
    assert "text.textContent = title.textContent.trim()" in click
    assert "link.setAttribute('aria-selected', 'true')" in click
    # a click that opens a new tab leaves this page as it is
    assert "!e.ctrlKey && !e.metaKey" in click
