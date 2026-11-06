"""If a row has buttons, the reader has to be able to reach them.

A wide table scrolls sideways. `.table-sticky-actions` pins the last column
against the right edge so the row's buttons stay in view while the rest slides
under them - Users, Job History, Admin Courses and the group list all use it.

The project Members table did not, and it is the widest table in the app: a
16-column check matrix. Its View buttons scrolled off the right, and the class
it DID carry - `table-sticky-first` - had done nothing since 84c8ac3b removed
the rule behind it, while the comments around it still described a pinned first
column. Two of the four tables whose last column is Actions were missing the
one class that does something.

This scans the source rather than the browser: a table with no rows in the
seeded database renders no cells to measure, and that is exactly the case a
browser walk misses.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO / "src/app/templates"
_HEADS = _TEMPLATES / "components/table_heads.html"


def _macros_ending_in_actions() -> set[str]:
    """Head macros whose LAST column is Actions."""
    src = _HEADS.read_text(encoding="utf-8")
    out: set[str] = set()
    for m in re.finditer(r"\{%\s*macro\s+(\w+)\(", src):
        body = src[m.end() :]
        body = body[: body.find("{% endmacro %}")]
        columns = re.findall(r"(<th[^>]*>.*?</th>|sortable_header\([^)]*\))", body, re.S)
        if columns and "Actions" in columns[-1]:
            out.add(m.group(1))
    return out


def _tables_using(macro: str) -> list[tuple[Path, str]]:
    """Every `data_table` call whose body invokes this head macro."""
    found = []
    for path in _TEMPLATES.rglob("*.html"):
        if path == _HEADS:
            continue
        text = path.read_text(encoding="utf-8")
        if macro + "(" not in text:
            continue
        for call in re.finditer(r"\{%\s*call\s+data_table\((.*?)\)\s*%\}", text, re.S):
            after = text[call.end() : call.end() + 700]
            if macro + "(" in after:
                found.append((path, call.group(1)))
    return found


def test_every_table_whose_last_column_is_actions_pins_it() -> None:
    macros = _macros_ending_in_actions()
    assert macros, "no head macro ends in an Actions column - the scan is broken"

    offenders = []
    for macro in sorted(macros):
        for path, args in _tables_using(macro):
            if "table-sticky-actions" not in args:
                offenders.append(f"{path.relative_to(_TEMPLATES)} ({macro})")

    assert not offenders, (
        "these tables put buttons in the last column and let it scroll out of "
        "reach; add `table-sticky-actions` to the class list:\n  " + "\n  ".join(offenders)
    )


def test_the_class_that_does_nothing_is_not_used() -> None:
    """`table-sticky-first` has had no rule behind it since 84c8ac3b.

    It stayed on seventeen call sites and in four comments, which is how it came
    to be trusted: the members table carried it, so its first column looked like
    it was handled, and the column that actually needed pinning had nothing.
    """
    users = [
        str(p.relative_to(_TEMPLATES))
        for p in _TEMPLATES.rglob("*.html")
        if "table-sticky-first" in p.read_text(encoding="utf-8")
    ]
    assert not users, (
        "a template asks for a pinned first column, but no stylesheet defines "
        f"one, so nothing happens: {users}"
    )

    css = (_TEMPLATES / "static/css").rglob("*.css")
    defined = [
        str(p)
        for p in css
        if ".min." not in p.name and "table-sticky-first" in p.read_text(encoding="utf-8")
    ]
    assert not defined, f"the class is back in CSS without its templates: {defined}"


def test_a_pinned_cell_wears_its_rows_tint() -> None:
    """Every cell inherits the same opaque row state, including pinned actions.
    A separate pinned-cell background used to drift from the other cells."""
    css = (_REPO / "src/app/templates/static/css/tables.css").read_text(encoding="utf-8")
    assert re.search(
        r"tr:where\([^{}]*\.member-excluded[^{}]*\)\s*\{\s*"
        r"--table-row-bg: var\(--gl-background-color-subtle\)",
        css,
    )
    assert "background: var(--table-row-bg)" in css
    assert "background: var(--gl-table-row-selected-bg) !important" not in css
