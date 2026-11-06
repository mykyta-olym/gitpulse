"""A data table scrolls; it does not squeeze its columns.

`data_table` wraps every table in `.table-scroll > .table-responsive`, but the
wrapper only has something to scroll when the table itself carries a min-width -
which is what `.table-scrollable` supplies (tables.css). Without it the columns
absorb the squeeze instead: the narrow ones ellipsise and the wide one wraps its
text over several lines, which is the "some tables have no scroll and wrap the
text in the columns" report.

Two of the twenty-odd calls had drifted out of the contract - the System page's
Parameter / Value / Env tables - and nothing said so.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"

# The macro's own definition and the usage example in its docstring are not
# call sites.
_MACRO_FILE = "tables.html"
_CALL = re.compile(r"\{%\s*call\s+data_table\((?P<args>[^%]*?)\)\s*%\}", re.DOTALL)


def _call_sites() -> list[tuple[Path, str]]:
    sites: list[tuple[Path, str]] = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        if path.name == _MACRO_FILE:
            continue
        for match in _CALL.finditer(path.read_text(encoding="utf-8")):
            sites.append((path, match.group("args")))
    return sites


def test_there_are_call_sites_to_check() -> None:
    """A regex that silently matches nothing would make every test below pass."""
    assert len(_call_sites()) > 10


def test_every_data_table_carries_the_scroll_contract() -> None:
    offenders = [
        f"{path.relative_to(TEMPLATES).as_posix()}: {args.strip()[:80]}"
        for path, args in _call_sites()
        if "table-scrollable" not in args
    ]
    assert not offenders, (
        "these tables have the scroll WRAPPER but no min-width to scroll, so "
        f"their columns squeeze and wrap instead: {offenders}"
    )


def test_no_table_opts_out_of_the_wrapper() -> None:
    """`responsive=false` drops `.table-scroll`/`.table-responsive` entirely,
    leaving a table that can only overflow its card."""
    offenders = [
        path.relative_to(TEMPLATES).as_posix()
        for path, args in _call_sites()
        if re.search(r"responsive\s*=\s*false", args)
    ]
    assert not offenders, f"tables rendered without a scroll wrapper: {offenders}"
