"""A table header wraps; it never spills under its neighbour.

Two reports, one cause. `.users-table` and the Activity cards' tables are both
`table-layout: fixed`, so a column width is a hard cap - and a header wider
than its column overflows into the next cell, whose own background paints over
the spill. It reads as a hard clip mid-word: "GitLab User I", "Projec".

The wrap rule that fixes this already existed, scoped to `.tbl-fixed`;
`.users-table` carries its own class and never got it. It is scoped to
`.data-table` now, which both families share - one mechanic instead of one per
table family.

The second half is the responsive switch. It was keyed to the WINDOW (1439px),
which is the right threshold only for a full-width table: the Activity page
puts two of these tables in half-width cards, so at a 1440px window each got
~540px, kept the %-columns meant for 1180px, and clipped everything. Keyed to
the table's own container now, so a table in a card behaves like a table in a
narrow window - which is what it is.

Measured with Playwright at 1024 / 1280 / 1440 / 1920: zero cells whose
scrollWidth exceeds their clientWidth, across admin users, course overview,
activity, analytics, teachers and settings.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "src/app/templates/static/css/tables.css"
ADMIN = REPO / "src/app/templates/static/css/pages/admin.css"


def test_header_wrapping_covers_every_data_table() -> None:
    css = TABLES.read_text(encoding="utf-8")
    assert re.search(r"^\.data-table th \{[^}]*white-space: normal", css, re.M | re.S), (
        "the header-wrap rule is gone or narrowed back to one table family"
    )
    assert not re.search(r"^\.tbl-fixed th \{", css, re.M), (
        "the rule is scoped to .tbl-fixed again, so .users-table clips once more"
    )


def test_the_sort_link_stops_forcing_nowrap_in_headers() -> None:
    """`.sort-link` is `white-space: nowrap`; without this override the wrap
    above cannot take effect on a sortable column, which is most of them."""
    css = TABLES.read_text(encoding="utf-8")
    assert ".data-table th .sort-link { white-space: normal;" in css


def test_the_dense_table_switch_is_keyed_to_the_container() -> None:
    css = TABLES.read_text(encoding="utf-8")
    assert "@container (max-width: 1180px)" in css, (
        "the switch is keyed to the window again - a table in a half-width card "
        "will keep %-columns meant for a full-width one"
    )
    assert re.search(r"^\.table-scroll \{[^}]*container-type: inline-size", css, re.M | re.S), (
        "the query container is gone, so the @container rule can never match"
    )
    assert "@media (max-width: 1439px)" not in css, (
        "the viewport-keyed copy is back alongside the container one - two "
        "mechanics for the same decision"
    )


def test_the_users_table_has_one_layout_and_every_header_fits() -> None:
    """ONE opinion about the users table's widths.

    admin.css carried two: `table-layout: auto` with a 160px floor for the
    GitLab User ID column at the top, and `table-layout: fixed` with that
    column at 7% further down. The later one won, the floor was ignored (a
    fixed layout does not read cell min-widths) and the header was cut to
    "GitLab Us" in an 83px column. This test pinned the dead rule, and its
    regex never matched the `.users-table .col-x,  #usersTable .col-x` lines.

    Fixed stays so filters cannot resize columns. Both fixed pixel widths and
    percentage widths must fit the headers at the table's floor; Email takes
    the unassigned space.
    """
    css = ADMIN.read_text(encoding="utf-8")
    layouts = re.findall(r"^\.users-table \{[^}]*table-layout:\s*(\w+)", css, re.M)
    assert layouts == ["fixed"], f"the users table has {layouts} layouts outside the tablet band"
    floor = re.search(r"^\.users-table\.table-scrollable \{ min-width: (\d+)px; \}", css, re.M)
    assert floor, "the table lost its floor"
    widths = dict(re.findall(r"^\.users-table \.col-([\w-]+)\s+\{ width: ([^;]+);", css, re.M))
    assert widths.pop("email") == "auto", "Email should receive the remaining space"
    width = int(floor.group(1))
    pixels = {
        column: float(value[:-1]) * width / 100 if value.endswith("%") else float(value[:-2])
        for column, value in widths.items()
    }
    assert round(width - sum(pixels.values())) >= 189, "Email shrank at the table's floor"
    # measured header needs, in px, at the floor (max of EN / SK)
    needs = {
        "username": 157,
        "gitlabid": 149,
        "fullname": 125,
        "role": 91,
        "period": 166,
        "status": 96,
        "created": 124,
        "actions": 88,
    }
    short = {column: round(pixels[column]) for column in needs if pixels[column] < needs[column]}
    assert not short, f"columns narrower than their header or badge at {width}px: {short}"
