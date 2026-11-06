"""The Actions column's label sits at the end, with its buttons.

`.table-sticky-actions` pins the last column to the right edge, and its buttons
are drawn there - but the header said "Actions" at the LEFT of that column, so
on a wide table the word floated in the middle of empty space while the buttons
it named were 100px away against the edge.

Five tables had answered this in their own markup - three `text-right`, one
`text-center`, one nothing at all - for a question the class already decides.
"""

from __future__ import annotations

from pathlib import Path

_CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css/tables.css"


def _rule_for(selector_fragment: str) -> str:
    css = _CSS.read_text(encoding="utf-8")
    blocks = css.split("}")
    for block in blocks:
        if selector_fragment in block and "{" in block:
            head, body = block.split("{", 1)
            if selector_fragment in head:
                return body
    return ""


def test_the_class_that_pins_the_column_also_aligns_it() -> None:
    css = _CSS.read_text(encoding="utf-8")
    aligned = [
        block
        for block in css.split("}")
        if "table-sticky-actions" in block.split("{")[0] and "text-align: right" in block
    ]
    assert aligned, (
        "the sticky actions column no longer aligns its own header and cells, so "
        "every table decides again and they disagree"
    )
    rule = aligned[0].split("{")[0]
    moved_together = "th:last-child" in rule and "td:last-child" in rule
    assert moved_together, (
        "the label and the buttons have to move together - aligning one leaves "
        "the other where it was"
    )
