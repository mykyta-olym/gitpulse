"""A dropdown menu clips its items to its own corner radius.

An item's highlight is a 4px-rounded fill spanning the full width; the menu's
corner is 8px. With nothing clipping, highlighting the FIRST or LAST item drew
a hard square edge across the rounded corner - measured on every menu in the
app, on four different pages.

Clipping also gives the menu the behaviour it was missing: a long list scrolls
inside itself instead of growing off the screen, which is what GitLab's
listbox does.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "src/app/templates/static/css/dropdowns.css"


def _menu_rule() -> str:
    src = CSS.read_text(encoding="utf-8")
    return src.split(".gl-dropdown-menu {", 1)[1].split("\n}", 1)[0]


def test_the_menu_clips_its_items() -> None:
    body = _menu_rule()
    assert "overflow-x: hidden" in body
    assert "overflow-y: auto" in body, (
        "a menu that clips both axes cannot scroll, so a long list would be cut off"
    )


def test_a_long_menu_scrolls_rather_than_growing() -> None:
    body = _menu_rule()
    assert "max-height" in body, "without a max height the menu can still run off screen"


def test_the_radius_it_clips_to_is_still_there() -> None:
    body = _menu_rule()
    assert "border-radius: var(--gl-dropdown-border-radius)" in body
