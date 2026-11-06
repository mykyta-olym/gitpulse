"""A table that scrolls sideways says so - and nothing paints over its rows.

The horizontal fade on `.table-scroll` marks the one edge that can hide
columns. Two things it must not do, both of which it did at one point:

* paint over a pinned actions column. The fade sat on top of the sticky
  cells and darkened them on every row, so a striped row looked cut where the
  column began and the column read as "outlined";
* have a vertical twin. A 28px gradient along the bottom edge of any table
  taller than its box read as the last visible row being cut off, not as
  "more below" - the wrapper's own scrollbar already says that.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js/table-scroll.js"
CSS = REPO / "src/app/templates/static/css/tables.css"


def test_the_horizontal_axis_gets_a_state_class() -> None:
    src = JS.read_text(encoding="utf-8")
    for cls in ("is-scrollable-x", "at-scroll-end"):
        assert f"'{cls}'" in src, f"{cls} is gone, so the axis has no state"


def test_there_is_no_vertical_fade() -> None:
    css = CSS.read_text(encoding="utf-8")
    src = JS.read_text(encoding="utf-8")
    assert ".table-scroll.is-scrollable-x:not(.at-scroll-end)::after" in css
    assert "::before" not in css.split(".table-responsive {", 1)[0], (
        "a bottom fade is back - it paints over the last visible row"
    )
    for cls in ("is-scrollable-y", "at-scroll-bottom"):
        assert cls not in src, f"{cls} is a state nothing styles any more"


def test_the_fade_stays_off_a_pinned_actions_column() -> None:
    """Off while the column is pinned; back when it unpins (`sticky-column-off`),
    because then nothing else tells the reader the table scrolls."""
    css = CSS.read_text(encoding="utf-8")
    block = re.search(
        r"^\.table-scroll:not\(\.sticky-column-off\)"
        r":has\(> \.table-responsive > \.table-sticky-actions\)::after \{(.*?)\}",
        css,
        re.S | re.M,
    )
    assert block, "the fade is drawn over the sticky actions column again"
    assert "display: none" in block.group(1)


def test_the_fade_does_not_swallow_a_click() -> None:
    css = CSS.read_text(encoding="utf-8")
    block = re.search(r"^\.table-scroll::after \{(.*?)\}", css, re.S | re.M)
    assert block, "the fade is gone"
    assert "pointer-events: none" in block.group(1), (
        "the fade would intercept clicks on the cells beneath it"
    )


def test_reduced_motion_covers_the_fade() -> None:
    css = CSS.read_text(encoding="utf-8")
    reduced = css.split("prefers-reduced-motion: reduce", 1)[1][:400]
    assert ".table-scroll::after" in reduced
