"""Contracts measured against the university's own GitLab instance.

Every assertion here corresponds to a number taken off gitlab.example.com with
a real browser, not to a preference:

* GitLab's dropdown does not animate in either direction - the panel is at
  opacity 1 on the first frame after the click and `display: none` 2ms after the
  dismiss.
* GitLab's modal dismiss is opacity-only, `0.2s cubic-bezier(0.22, 0.61, 0.36,
  1)`, with `transform: none` on the dialog throughout.
* GitLab's panel header is an opaque 36px block flush with the panel's top edge,
  rounded 8px on its top corners; content scrolls under it and is cut at 84px.

Plus the dashboard stat-card states, which have to agree with the traffic-light
bands used everywhere else.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.api.dashboard.home.stats import _apply_states, _compliance_state

TEMPLATES = Path(__file__).resolve().parents[2] / "src" / "app" / "templates"
CSS = TEMPLATES / "static" / "css"


def _read(name: str) -> str:
    return (CSS / name).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Motion
# --------------------------------------------------------------------------


def test_dropdown_animates_open_and_stays_attached() -> None:
    """The dropdown DEPARTS from GitLab here, on the author's explicit call.

    GitLab's own panel does not animate - measured on gitlab.example.com,
    `transition: all 0s` and opacity 1 on the first frame - and this file pinned
    that. The author asked for a visible open/close repeatedly and reported the
    panel reading as "not joined" to its control, so the app now opens it with a
    short downward slide. The parity note stays in the CSS so nobody re-derives
    the GitLab number and assumes it was an oversight.
    """
    css = _read("dropdowns.css")
    panel = css.split(".gl-dropdown-menu {", 1)[1].split("}", 1)[0]
    assert "margin-top: var(--gl-spacing-2)" in panel, (
        "GitLab floats the panel, it is not welded on"
    )

    opened = css.split(".gl-dropdown:not([x-data]).open .gl-dropdown-menu {", 1)[1]
    opened = opened.split("}", 1)[0]
    assert "transform: translateY(0)" in opened
    assert "opacity: 1" in opened

    closed = css.split(".gl-dropdown:not([x-data]) .gl-dropdown-menu {", 1)[1]
    closed = closed.split("}", 1)[0]
    assert "translateY(-4px)" in closed, "it slides down out of the trigger"

    # Every menu gets the motion, not just the CSS-driven ones. The form select
    # is an Alpine component whose panel used to be toggled by `x-show`, which
    # removes the element on the same tick the flag changes - so it was the one
    # panel in the app that could not have a close animation at all. It is
    # driven by GP.motion now, so the browser-dependent `@starting-style` +
    # `allow-discrete` workaround is gone with it: that mechanism silently did
    # nothing wherever it was unsupported, exactly as it did for <details> and
    # the tab panels before they were moved too.
    _bare = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    assert "@starting-style" not in _bare, (
        "the select's motion belongs to GP.motion, not to a browser-gated rule"
    )

    select_js = (TEMPLATES / "static" / "js" / "_parts" / "core" / "17-form-select.js").read_text(
        encoding="utf-8"
    )
    assert "GP.motion.popIn(menu)" in select_js
    assert "GP.motion.popOut(menu" in select_js

    forms = (TEMPLATES / "components" / "forms.html").read_text(encoding="utf-8")
    assert 'x-show="open"' not in forms, "x-show hides the panel before its exit can run"


def test_exit_easing_is_gitlabs_ease_out_not_an_invented_ease_in() -> None:
    """Exits use the same curve as entrances; cubic-bezier(0.4, 0, 1, 1) holds
    an element at full opacity for the first third of its duration, which is the
    slow fade-out GitLab does not have."""
    tokens = _read("tokens.css")
    assert "--motion-ease-exit: var(--motion-ease-standard);" in tokens
    assert "--motion-ease-standard: cubic-bezier(0.22, 0.61, 0.36, 1);" in tokens
    assert "--motion-ease-exit: cubic-bezier(0.4, 0, 1, 1)" not in tokens


def test_modal_dismiss_does_not_move_the_dialog() -> None:
    """GitLab fades the modal out; it never slides it back down."""
    assert "modalSlideDown" not in _read("modals.css")
    assert "modalSlideDown" not in _read("animations.css")


def test_panel_header_is_gitlabs_36px_block() -> None:
    css = _read("sidebar.css")
    block = re.search(r"\.gl-content-breadcrumb \{([^}]*)\}", css)
    assert block, "breadcrumb header rule missing"
    body = block.group(1)
    assert "height: 36px" in body
    assert "border-radius: var(--radius-lg) var(--radius-lg) 0 0" in body
    # Flush with the panel: GitLab's header owns the strip, margins do not.
    assert "margin: 0" in body


def test_content_panel_is_flush_with_the_sidebar() -> None:
    """GitLab measures `.paneled-view` at x=240 against a 240px sidebar."""
    css = _read("sidebar.css")
    assert "margin-left: var(--sidebar-width);" in css
    assert "margin-left: calc(var(--sidebar-width) + 8px)" not in css


# --------------------------------------------------------------------------
# Stat card states
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, "danger"),
        (49, "danger"),
        (50, "warning"),
        (74, "warning"),
        (75, "success"),
        (100, "success"),
    ],
)
def test_compliance_bands(score: int, expected: str) -> None:
    assert _compliance_state(score) == expected


def test_compliance_without_data_is_empty_not_danger() -> None:
    """No active course is 'nothing to report', not 'catastrophic'."""
    assert _compliance_state(0, has_data=False) == "empty"
    assert _compliance_state(None) == "empty"


def test_apply_states_marks_zeroes_empty_and_keeps_explicit_states() -> None:
    cards = _apply_states(
        [
            {"id": "a", "value": 0},
            {"id": "b", "value": "0%"},
            {"id": "c", "value": 7},
            {"id": "d", "value": "20%", "state": "danger"},
        ]
    )
    by_id = {c["id"]: c["state"] for c in cards}
    assert by_id == {"a": "empty", "b": "empty", "c": "", "d": "danger"}


def test_every_card_carries_a_state_key() -> None:
    """The template reads `c.state`; a card without one would silently lose its
    tone on that role's dashboard only."""
    cards = _apply_states([{"id": "x", "value": 3}, {"id": "y", "value": 0}])
    assert all("state" in c for c in cards)


# --------------------------------------------------------------------------
# Stylesheet integrity
# --------------------------------------------------------------------------


def test_every_stylesheet_has_balanced_braces() -> None:
    """One stray brace silently kills every rule after it, and nothing else
    catches it: the bundle gate only compares concatenation, and the minifier
    happily passes the damage through. Removing a keyframe left an extra `}` in
    animations.css and shipped it, disabling everything below `modalSlideUp`.
    """
    sources = [p for p in CSS.rglob("*.css") if ".min." not in p.name and "bundle" not in p.name]
    assert sources, "no source stylesheets found"
    unbalanced = {}
    for path in sources:
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        delta = text.count("{") - text.count("}")
        if delta:
            unbalanced[path.name] = delta
    assert not unbalanced, f"unbalanced braces: {unbalanced}"
