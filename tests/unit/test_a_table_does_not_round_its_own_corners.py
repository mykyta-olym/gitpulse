"""The scroll viewport owns a table's corners. The table has no say.

`data_table(class='... table-scrollable')` puts that class on the `<table>`
element, and `.table-scrollable:first-child` - written for the wrapper - matched
it too, because a table is always the first child of its viewport. So every such
table rounded its own top corners at 12px while the rules that decide whether
the block should round at all were being applied to the wrapper around it.

Invisible while both round. A 12px notch of card ground the moment the wrapper
is squared by a header, a toolbar or a tab strip above it - which is the unlit
corner that gets reported from a screenshot, and it was live on six of the nine
tables walked at 1440x900: the Users table, Job History, Feature Flags, Recent
Events, the student page's issue tables and Group Members.

The browser settles cascade questions and `tests/e2e/scenarios/
test_tables_meet_the_block_above_them.py` asks it there. What is pinned here is
the part that can be read from the source: the rule exists, and it is written at
a specificity that beats the rule it has to override - which is the thing that
went wrong twice before in this same file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css/tables.css"


@pytest.fixture(scope="module")
def css() -> str:
    return CSS.read_text(encoding="utf-8")


def _specificity(selector: str) -> tuple[int, int, int]:
    """(ids, classes+attributes+pseudo-classes, elements+pseudo-elements)."""
    ids = len(re.findall(r"#[\w-]+", selector))
    classes = len(re.findall(r"\.[\w-]+|\[[^\]]+\]|:(?!:)[\w-]+", selector))
    elements = len(re.findall(r"(?:^|[\s>+~])([a-z][\w-]*)", selector))
    return ids, classes, elements


def test_the_table_takes_its_corners_from_its_wrapper(css: str) -> None:
    assert ".table-responsive > table.table-scrollable" in css, (
        "nothing stops a table from rounding its own corners inside a square wrapper"
    )
    block = css.split(".table-responsive > table.table-scrollable", 1)[1].split("}", 1)[0]
    assert "border-radius: inherit" in block, (
        "the table should take the wrapper's radius, not a fixed one - the wrapper's "
        "changes with what sits above it"
    )


def test_it_outranks_the_rule_it_has_to_beat(css: str) -> None:
    """`.table-scrollable:first-child` is what gives the table its 12px. A fix
    that reads correctly and loses the cascade is how this bug survived twice."""
    assert _specificity(".table-responsive > table.table-scrollable") > _specificity(
        ".table-scrollable:first-child"
    )


def test_a_tab_panel_squares_the_table_under_its_strip(css: str) -> None:
    """The tab strip is the panel's sibling, not the table's, so none of the
    "is anything above me" rules could see it."""
    assert "[data-tab-panel] > .table-scroll > :is(.table-responsive, .table-scrollable)" in css
    block = css.split("[data-tab-panel] > :is(.table-responsive", 1)[1].split("}", 1)[0]
    assert "border-start-start-radius: 0" in block
    assert "border-start-end-radius: 0" in block
