"""A cell wraps between words, and breaks inside one only as a last resort.

`word-break: break-word` breaks INSIDE a word the moment the line is full, so
`mykyta.olym` came out as "mykyta.oly / m" in a 114px column it would otherwise
have fitted in, and "Mykyta Ol / ym" before that.

The app already knew this: two rules carry the correction and explain it. Both
missed the cells of `.tbl-fixed`, because the correction was written on the
TABLE - `word-break` inherits, but a declaration on the cell itself out-ranks
anything inherited from its table, and `.tbl-fixed td` declared `break-word`
directly. So the rule meant to stop the shredding sat one level above the rule
doing it, on the widest tables in the app: Events, Job History, Admin Courses,
Support Tickets, Activity.
"""

from __future__ import annotations

import re
from pathlib import Path

_CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"


def _blocks(css: str):
    """(selector, body) for every rule, comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        yield " ".join(block.group(1).split()), block.group(2)


def test_no_rule_pairs_a_shredding_break_with_a_wrap_that_already_works() -> None:
    """`overflow-wrap` beside `word-break: break-word` is the bug's signature.

    `overflow-wrap` breaks a word that cannot fit its column; `word-break:
    break-word` also breaks words that CAN. Written together, the second adds
    nothing except the shredding - which is how it read as harmless and survived
    in three separate rules: the fixed-layout cells, inline `code` in a cell,
    and an ID-scoped `#webhookConfigsTable th:first-child` that out-ranked
    `.data-table th` and split that one header as "Me / no".
    """
    offenders = []
    for path in sorted(_CSS.rglob("*.css")):
        if ".min." in path.name or "bundle" in path.name:
            continue
        for selector, body in _blocks(path.read_text(encoding="utf-8")):
            breaks = re.search(r"(?:^|;)\s*word-break\s*:\s*(break-word|break-all)", body)
            wraps = re.search(r"(?:^|;)\s*overflow-wrap\s*:", body)
            if breaks and wraps:
                offenders.append(
                    f"{path.name}: {selector[:60]} ({breaks.group(1)} + overflow-wrap)"
                )
    assert not offenders, (
        "these break words that fit, on top of a wrap that already handles the "
        "ones that do not; drop the `word-break`:\n  " + "\n  ".join(offenders)
    )


def _declarations(css: str, prop: str) -> list[tuple[str, str]]:
    """(selector, value) for every declaration of `prop`, comments stripped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for block in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, body = block.group(1).strip(), block.group(2)
        for decl in re.finditer(rf"(?:^|;)\s*{prop}\s*:\s*([^;]+)", body):
            out.append((" ".join(selector.split()), decl.group(1).strip()))
    return out


def test_no_table_rule_breaks_inside_a_word() -> None:
    tables = (_CSS / "tables.css").read_text(encoding="utf-8")
    offenders = [
        f"{sel} {{ word-break: {value} }}"
        for sel, value in _declarations(tables, "word-break")
        if value in ("break-word", "break-all")
    ]
    assert not offenders, (
        "these break a word in half as soon as the line is full; use "
        "`overflow-wrap: break-word`, which only breaks a word that cannot fit "
        "its column on its own:\n  " + "\n  ".join(offenders)
    )


def test_the_fixed_layout_cells_carry_the_correction_themselves() -> None:
    """Not on the table, where the cell's own declaration out-ranks it."""
    tables = (_CSS / "tables.css").read_text(encoding="utf-8")
    cell_rules = [
        (sel, value) for sel, value in _declarations(tables, "word-break") if ".tbl-fixed td" in sel
    ]
    assert cell_rules, ".tbl-fixed cells no longer say how they wrap"
    for sel, value in cell_rules:
        assert value == "normal", f"{sel} sets word-break: {value}"

    wraps = [
        value for sel, value in _declarations(tables, "overflow-wrap") if ".tbl-fixed td" in sel
    ]
    assert "break-word" in wraps, (
        ".tbl-fixed cells must still wrap a word that genuinely does not fit"
    )
