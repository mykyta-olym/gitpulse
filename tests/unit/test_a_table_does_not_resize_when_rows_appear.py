"""No table decides its columns from the rows that happen to be showing.

With `table-layout: auto` - which every table here uses, deliberately - the
browser sizes each column from its content. A column with no declared width is
therefore re-solved whenever the set of VISIBLE rows changes, and that changes
twice on every load. Traced on the Users page at 500 kbit/s:

    t=3322ms   62 rows parsed, all visible    table 1187px
    t=3374ms   68 rows parsed, all visible    table 1236px   <- one long bot name
    t=4758ms   ClientPaginator leaves 50      table 1187px

Eight columns laid out three times: the content slides sideways and slides back.
It was worst where rows are drawn by JavaScript - Job History paints a header
over an empty tbody, so the header alone sized the table until the rows landed
(measured 247,108,174,109,338,83 becoming 257,113,136,114,352,87).

THIS TEST DISCOVERS THE TABLES; IT DOES NOT LIST THEM.

Fixing the four tables that were noticed would leave the rule as "somewhere yes,
somewhere no", and the next table added would bring the bug back. So this walks
every `<colgroup>` in every template and requires a width for every column of
every one of them. A table that omits one fails here, before anyone sees it
slide.

`table-layout: fixed` is NOT the fix and was tried before: `#adminCoursesTable`
still carries `.tbl-fixed` with `table-layout: auto` put back, because fixed
"crams every column into an ellipsis at the narrow end".
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "src/app/templates"
CSS_DIR = TEMPLATES / "static/css"

#: Layout-only classes that never carry a width of their own.
_NOT_A_COLUMN = re.compile(r"^col-hide-|^col$")


def _rules() -> list[tuple[str, str]]:
    """(selector, body) for every rule in the hand-written stylesheets."""
    out: list[tuple[str, str]] = []
    for path in CSS_DIR.rglob("*.css"):
        if ".min." in path.name or "bundle" in path.name:
            continue
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for chunk in text.split("}"):
            if "{" in chunk:
                sel, body = chunk.rsplit("{", 1)
                out.append((sel, body))
    return out


RULES = _rules()


def _sized_classes() -> set[str]:
    """Every column class some rule gives a real width to.

    `min-width: 0` is not a width: it only permits shrinking, which is what these
    columns were already doing.
    """
    sized: set[str] = set()
    for sel, body in RULES:
        real = [
            m
            for m in re.finditer(r"(?:^|[\s;])(?:width|min-width)\s*:\s*([^;]+)", body)
            if not re.fullmatch(r"0(px|%)?", m.group(1).strip())
        ]
        if not real:
            continue
        sized.update(re.findall(r"\.(col-[\w-]+)", sel))
    return sized


SIZED = _sized_classes()


def _colgroup_columns() -> dict[str, set[str]]:
    """template -> the column classes its colgroups declare."""
    found: dict[str, set[str]] = {}
    for path in TEMPLATES.rglob("*.html"):
        src = path.read_text(encoding="utf-8")
        for group in re.findall(r"<colgroup>(.*?)</colgroup>", src, re.S):
            for attr in re.findall(r'<col[^>]*class="([^"]+)"', group):
                for klass in attr.split():
                    if klass.startswith("col-") and not _NOT_A_COLUMN.match(klass):
                        found.setdefault(path.relative_to(TEMPLATES).as_posix(), set()).add(klass)
    return found


COLUMNS = _colgroup_columns()


def test_the_search_found_the_tables() -> None:
    """If this ever finds nothing, the test below is passing vacuously."""
    assert len(COLUMNS) >= 5, (
        f"only {len(COLUMNS)} templates with a colgroup - has the markup moved?"
    )


@pytest.mark.parametrize("template", sorted(COLUMNS), ids=lambda p: p.split("/")[-1])
def test_every_column_of_every_table_declares_a_width(template: str) -> None:
    unsized = sorted(c for c in COLUMNS[template] if c not in SIZED)
    assert not unsized, (
        f"{template} has columns with no declared width: {unsized}. The browser "
        "sizes those from whichever rows are visible, and that changes twice on "
        "every load - the table slides sideways and back."
    )


def test_a_width_for_a_shared_column_class_is_scoped_to_its_table() -> None:
    """`col-actions` and `col-status` belong to several tables at different
    widths - Users' Actions settles at 84px and the Groups table's at 209px. A
    rule on the bare class would hand one of them the other's width."""
    shared = ("col-actions", "col-status")
    for sel, body in RULES:
        if not any(re.search(rf"\.{c}\b", sel) for c in shared):
            continue
        if not re.search(r"(?:^|[\s;])width\s*:", body):
            continue
        assert "#" in sel or re.search(r"\.[a-z-]+-table", sel), (
            f"a width for a shared column class is not scoped to a table: {sel.strip()[:70]}"
        )


def test_a_client_rewritten_timestamp_reserves_its_wider_form() -> None:
    """localize-time.js rewrites a stamp AFTER first paint, and the server's form
    is the wider one. Reserving the narrower width moved every column to its
    right by 6px on load."""
    import ast

    template = (TEMPLATES / "admin_system.html").read_text(encoding="utf-8")
    widths = re.search(r"id='jobsTable'.*?column_widths=(\[[^\]]+\])", template)
    assert widths, "job columns must be declared through the shared table component"
    activity_width = ast.literal_eval(widths.group(1))[3]
    assert int(activity_width.removesuffix("px")) >= 142, (
        "the Enqueued column is narrower than the server-rendered timestamp, so "
        "the column shrinks when the client rewrites it"
    )


def test_fixed_layout_was_not_reintroduced() -> None:
    """It was tried and put back - see the note on `.tbl-fixed`."""
    css = (CSS_DIR / "pages/admin.css").read_text(encoding="utf-8")
    m = re.search(r"#adminCoursesTable\.tbl-fixed\s*\{([^}]*)\}", css)
    assert m, "the tbl-fixed override is gone"
    assert "table-layout: auto" in m.group(1), (
        "adminCoursesTable is back on table-layout: fixed, which crams every "
        "column into an ellipsis at the narrow end"
    )


def test_a_table_reserves_the_room_its_scrollbar_will_take() -> None:
    """Verify table-responsive behavior.

    scrollbar-gutter: stable was removed because on short tables (e.g. 2 rows in
    Archived Courses) it reserved dead empty space on the right of the table box.
    """
    css = (CSS_DIR / "tables.css").read_text(encoding="utf-8")
    m = re.search(r"\.table-responsive\s*\{([^}]*)\}", css)
    assert m, "the table scroll viewport lost its rule"
    body = m.group(1)
    assert "scrollbar-gutter: stable" not in body, (
        "table-responsive must not reserve scrollbar gutter to prevent dead empty space "
        "on short tables"
    )
    why = (
        "the viewport is no longer a capped scroll container - if that changed "
        "on purpose, this rule and its gutter need revisiting together"
    )
    assert "overflow-y: auto" in body, why
    assert "max-height" in body, why
