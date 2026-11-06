"""An internal navigation never takes the reader's page away.

UPDATED 2026-09-03: the page-level loader is gone. Three earlier shapes were
tried and each was reported from a screenshot: blanking `#main-content` for a
centred loader (the reader lost their page and got two jumps), a toast beside
the page (a message about a transition the reader was already watching), and a
full-screen veil carrying a second copy of the brand mark in a 92px ring - which
covered the page it was reporting on, stayed brand-orange on an accented theme,
moved its own mark 13px when the slow note appeared, and stood still under
`prefers-reduced-motion`.

What is there now, after a pill was tried and dropped as one more thing saying
what the progress bar already said:

  1. the top progress bar, from the first millisecond;
  2. the CLICKED control. When it leads with an icon, that icon becomes the app's
     spinner in its own box; when it has no icon slot - a table row, a link in a
     cell, a card - the control (or its row) holds an accent tint instead, so a
     click in a table is answered where it happened. Searching a control for any
     icon at all is what put a spinner in the corner of a stat card, over that
     card's own category icon, which is why the rule is the FIRST child only;
  3. a `progress` cursor over the content region - the signal every browser and
     desktop app uses for this, and the one that covers every control with no
     icon slot to stand in.

The contract this file has always guarded is unchanged and still first: the page
underneath is never emptied. That is GitLab's model, and it holds all the way -
GitLab never replaces the page it is leaving, however long the next one takes.
Measured while chasing the "analytics takes ages" report, and worth keeping
because it says where the time was NOT going: the page issues 17 queries with no
N+1 and its four heaviest aggregates run in 5-9ms each against the production
database. The delay the reader saw was almost entirely the blanking.

Where the browser has to answer instead of the source:
tests/e2e/scenarios/test_navigation_shows_the_wait.py.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "src/app/templates/static/js/_parts/core/42-spa-navigation.js"
LOGO_CSS = REPO / "src/app/templates/static/css/logo.css"


def _nav() -> str:
    src = CORE.read_text(encoding="utf-8")
    return src.split("function _navigateNow(", 1)[1].split("\n  /* CAPTURE phase", 1)[0]


def test_the_navigation_never_replaces_the_content() -> None:
    assert "mc.innerHTML" not in _nav(), (
        "the navigation writes over #main-content again - the reader loses the "
        "page they were looking at"
    )


def test_nothing_is_drawn_over_the_page_either() -> None:
    """The veil is retired, in the builder AND in the stylesheet. A page-level
    loader is the shape that keeps coming back and keeps being reported."""
    assert "gp-nav-loader" not in CORE.read_text(encoding="utf-8"), (
        "a full-screen loader is being built again"
    )
    assert "gp-nav-loader" not in LOGO_CSS.read_text(encoding="utf-8"), (
        "the retired veil's rules are back in the stylesheet"
    )


def test_the_busy_mark_and_its_styling_travel_together() -> None:
    """Either both exist or neither does - a mark with no rules paints an
    unstyled block inside the control, which is worse than no mark at all."""
    src = CORE.read_text(encoding="utf-8")
    css = LOGO_CSS.read_text(encoding="utf-8")
    has_builder = "function _markBusy" in src
    has_css = ".nav-busy-spinner" in css
    assert has_builder == has_css, (
        f"busy-mark builder present={has_builder} but its stylesheet rules={has_css}"
    )


def test_the_mark_goes_on_a_leading_icon_or_nowhere() -> None:
    """One rule, and both halves of it. Without the first-child test a stat
    card's own corner icon is a `querySelector('svg')` hit, which is how a
    spinner ended up in the top-right of a card that leads with a heading."""
    src = CORE.read_text(encoding="utf-8")
    assert "function _leadingIcon" in src, "the placement rule is gone"
    body = src.split("function _leadingIcon", 1)[1].split("\n  }", 1)[0]
    assert "firstElementChild" in body, "any icon in the control can be taken again"
    assert "0.25" in body, "an icon its layout pushed to the right can be taken again"
    assert "is-nav-busy-tint" in src, (
        "a control with no icon slot now reports nothing at all - the click in a "
        "table is unanswered again"
    )
    tint = src.split("const icon = _leadingIcon(el);", 1)[1].split("\n    }", 1)[0]
    assert "closest('tr')" in tint, (
        "a row is tinted through the row, not through whichever cell was clicked"
    )


def test_a_control_with_no_icon_still_says_it_is_busy() -> None:
    """The cursor covers what the mark cannot: a card, a row, a bare link. On
    the SCROLLER, because the content itself is not hit-tested while stale."""
    assert ".gl-page-content:has(#main-content.is-navigating)" in LOGO_CSS.read_text(
        encoding="utf-8"
    ), "nothing at all reports a click on a control with no icon"


def test_the_clicked_control_is_what_turns() -> None:
    """The anchor travels with the navigation; a page-level indicator can never
    say WHICH of a dozen links is being answered."""
    src = CORE.read_text(encoding="utf-8")
    assert "_navigate(href, true, a)" in src, "the click no longer carries its own control"
    assert "_markBusy(origin" in _nav(), "the navigation does not mark its origin busy"


def test_no_page_level_loader_comes_back() -> None:
    """Four have been tried and reported: a blanked page, a toast, a veil, a
    pill. The bar, the icon and the cursor are the whole signal now."""
    src = CORE.read_text(encoding="utf-8")
    for gone in ("gp-nav-loader", "gp-nav-pill", "gl-nav-status"):
        assert gone not in src, f"{gone} is being built again"
    assert "showToast" not in _nav(), "the navigation reports itself in a toast again"


def test_every_signal_is_taken_back_when_the_page_lands() -> None:
    body = _nav()
    assert "_markBusy(null)" in body, "the clicked control would keep turning"
    assert "mc.classList.remove('is-navigating')" in body, "the page would stay inert"


def test_the_outgoing_page_is_still_marked_inert() -> None:
    """Keeping the page means it must not look interactive while it is stale."""
    assert "mc.classList.add('is-navigating')" in _nav()
