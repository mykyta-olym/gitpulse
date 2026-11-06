"""The frame round a table is the same on every side.

A card body padded 24px, but the pagination bar under its table restated the
padding as 16px: it sat 8px inside the body's left, right and bottom edges and
12px under the last row - against 24px between the body's top edge and the
table's controls. Every paginated table in the app had a thick top and a thin
bottom, and each breakpoint carried its own stale copy of the bar's margins.

The card body now publishes its padding (--card-body-pad-y / -x); breakpoints
change those properties, and the bar takes its margins from them.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "src/app/templates/static/css"


def _read(rel: str) -> str:
    return (CSS / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def _sources() -> list[tuple[str, str]]:
    return [(str(p.relative_to(CSS)), p.read_text(encoding="utf-8")) for p in CSS.rglob("*.css")]


def test_the_card_body_publishes_its_padding() -> None:
    cards = _read("cards.css")
    rule = cards.split("\n.card-body {", 1)[1].split("\n}", 1)[0]
    assert "--card-body-pad-y: var(--gl-spacing-6);" in rule
    assert "--card-body-pad-x: var(--gl-spacing-6);" in rule
    assert "padding: var(--card-body-pad-y) var(--card-body-pad-x);" in rule


def test_no_breakpoint_sets_the_card_body_padding_directly() -> None:
    offenders = []
    for name, css in _sources():
        for m in re.finditer(r"(^|[\s,}])\.card-body\s*\{([^}]*)\}", css):
            if re.search(r"(^|;|\s)padding\s*:", m.group(2)) and "--card-body-pad" not in m.group(
                2
            ):
                offenders.append(name)
    assert not offenders, (
        f"a breakpoint restates the padding instead of the properties: {offenders}"
    )


def test_the_pagination_bar_takes_its_margins_from_the_body() -> None:
    navbar = _read("navbar.css")
    for block in navbar.split("> .pagination-controls {")[1:3]:
        margin = block.split("\n}", 1)[0]
        assert "var(--card-body-pad-y" in margin
        assert "var(--card-body-pad-x" in margin
        assert "var(--gl-spacing-4) calc(-1 * var(--gl-spacing-5))" not in margin


def test_no_breakpoint_restates_the_bars_margins() -> None:
    for name in ("_parts/responsive/00-mobile.css", "_parts/responsive/10-tablet.css"):
        css = _read(name)
        for block in css.split(".card-body:not(.p-0) > .pagination-controls {")[1:]:
            assert "margin" not in block.split("}", 1)[0], name


def test_every_controls_band_is_the_users_band() -> None:
    """One band, whatever it holds. A band with tabs dropped its padding and
    aligned to its line (`.table-controls--tabs` and two `:has()` copies) while
    a band with a search or dropdowns kept 16px under them - Job History's
    controls sat 16px from the body's top and 17px over the line, Users' 22px
    and 7px. Every band is Users' now: a 44px row, controls centred, the line
    under it; a tab strip alone rests on the line."""
    cards = _read("cards.css")
    body = cards.split("\n.card-body {", 1)[1].split("\n}", 1)[0]
    assert "--table-band-room: min(var(--card-body-pad-y), var(--gl-spacing-5));" in body
    tables = _read("tables.css")
    band = tables.split("\n.table-controls {", 1)[1].split("\n}", 1)[0]
    assert "padding: 0;" in band
    assert "align-items: center;" in band
    for group in (".table-controls-search {", ".table-controls-filters {"):
        rule = tables.split("\n" + group, 1)[1].split("\n}", 1)[0]
        assert "min-height: 43px;" in rule, f"{group} lost the band's row height"
    opener = tables.split("\n.card-body:has(> .table-controls:first-child),", 1)[1]
    assert opener.startswith(
        "\n.card-body:has(> [data-tabs]:first-child > .table-controls:first-child) {"
    ), "a band that opens its body inside a tabs wrapper sits lower again"
    assert "padding-top: var(--table-band-room);" in opener.split("\n}", 1)[0]
    assert "table-controls--tabs" not in tables
    assert ".table-controls:has(" not in tables, "a band lays itself out by its content again"
    macro = (CSS.parents[1] / "components/tables.html").read_text(encoding="utf-8")
    assert "table-controls--tabs" not in macro
    mobile = _read("_parts/responsive/00-mobile.css")
    for block in mobile.split("  .table-controls {")[1:]:
        assert "padding" not in block.split("}", 1)[0], "a breakpoint restates the band's room"
