"""Every table in the app is the same table.

A row's padding was declared eight times. `tables.css` set 16px for every
`.data-table` cell; `pages/admin.css` made the Users table 12px; `pages/course.css`
set the Groups table twice, both `!important`, the second overriding the first;
the group- and project-member tables took a third value and the analytics trend
table a fourth. Measured at 1920px, five tables on four pages:

    users (the reference)   row 50px   padding 12/12
    team projects           row 58px   padding 16/16
    team members            row 74px   padding 16/16
    course groups           row 42px   padding  8/8
    events                  row 57px   padding 16/16

Four paddings and five row heights for one thing, which is why no two tables
lined up with each other. There is one declaration now - in the shared
stylesheet, at the value the Users page already used - and the page-level ones
are gone. Measured after: 12/12 on all five, rows 49-50px.

What is still allowed is a real variant, not a second opinion: `.table-compact`
for a denser table, and a cell that is genuinely special (an expanded detail row
at padding 0, the tree-toggle column, a heat map). Those name themselves; a rule
that simply restates the padding for one more table does not.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CSS_DIR = ROOT / "src/app/templates/static/css"
PAGES_DIR = CSS_DIR / "pages"

#: Cells that are their own thing rather than "this table, but different".
ALLOWED = (
    "tree-row-child",  # a nested row inside the groups tree
    "th-check",  # the check matrix's one-glyph columns
    "heatmap-table",  # a heat map, not a list
    "dn-code-table",  # a diff preview: code, at a code size
)

#: A rule whose subject is the CELL, not something sitting inside one.
#: `.teams-table td a.text-bold` nudges a link; it does not restate the cell.
_A_CELL = re.compile(r"(?:^|[\s>+~,])(?:[\w.#\[\]=\"'-]*\s)?(td|th)(?:[.#:\[][^\s,]*)?\s*(?:,|$)")


def _is_about_the_cell(selector: str) -> bool:
    return any(_A_CELL.search(part.strip() + ",") for part in selector.split(",") if part.strip())


def _rules(path: Path) -> list[tuple[str, str]]:
    text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    out = []
    for chunk in text.split("}"):
        if "{" in chunk:
            sel, body = chunk.rsplit("{", 1)
            out.append((" ".join(sel.split()), body))
    return out


def test_the_shared_stylesheet_declares_the_padding() -> None:
    rules = _rules(CSS_DIR / "tables.css")
    hit = [b for s, b in rules if s == ".data-table th, .data-table td" and "padding" in b]
    assert hit, "no shared padding for a table cell"
    assert "--gl-spacing-4) var(--gl-spacing-5" in hit[0], (
        "the shared cell padding is no longer the reference value (12px 16px, "
        "what the Users page shows)"
    )


@pytest.mark.parametrize(
    "sheet", sorted(p.name for p in PAGES_DIR.glob("*.css") if ".min." not in p.name)
)
def test_no_page_restates_the_cell_padding(sheet: str) -> None:
    offenders = []
    for sel, body in _rules(PAGES_DIR / sheet):
        if not re.search(r"\b(td|th)\b", sel):
            continue
        if not re.search(r"(?:^|[\s;])padding(?:-\w+)?\s*:", body):
            continue
        if any(a in sel for a in ALLOWED):
            continue
        offenders.append(sel[:70])
    assert not offenders, (
        f"pages/{sheet} sets the padding of a table cell again: {offenders}. One "
        "table then does not line up with the next; use `.table-compact` for a "
        "denser table, or name the cell that is genuinely special."
    )


def test_nobody_shouts_important_at_a_table_cell() -> None:
    """Two of the old declarations were `!important` and fought each other."""
    offenders = []
    for path in PAGES_DIR.glob("*.css"):
        if ".min." in path.name:
            continue
        for sel, body in _rules(path):
            if not re.search(r"\b(td|th)\b", sel) or any(a in sel for a in ALLOWED):
                continue
            for decl in re.finditer(r"padding(?:-\w+)?\s*:[^;]*!important", body):
                offenders.append(f"{path.name}: {sel[:50]} -> {decl.group(0)[:40]}")
    assert not offenders, f"!important on a table cell's padding: {offenders}"


# ---------------------------------------------------------------------------
# The controls band: search on the left, filters on the right, one height.
#
# The band existed and four pages did not use it. Search boxes and filter
# dropdowns were rendered into `card(header_actions=...)`, which is where a
# table's ACTIONS go - so the Groups card carried its title, its search box and
# its row count in one header row, and the tickets card carried a search, three
# dropdowns, a Reset, a bulk-delete and a purge menu in that same row and
# wrapped to three lines. Measured at 1600px, the same band on four pages:
#
#     users (the reference)   45px   search 699px   filters 495px
#     job history             57px   search   0px   filters 288px
#     system configuration    51px   search   0px   filters 336px
#     event pipeline          73px   search   0px   filters 202px
#
# Four heights for one band, because a `.form-group` wrapper kept its 16px
# bottom margin inside a flex row, dropdowns were asked for at `-sm` (28px) on
# one page and default (32px) on the next, and tab buttons arrived at 26px or
# 30px depending on which strip they came from. All four measure 45px now, with
# every control in them at 32px.
# ---------------------------------------------------------------------------

TEMPLATE_DIR = ROOT / "src/app/templates"

#: Every template that renders a table, minus the component library itself.
_PAGE_TEMPLATES = sorted(
    p
    for p in TEMPLATE_DIR.rglob("*.html")
    if "components/" not in p.relative_to(TEMPLATE_DIR).as_posix()
    and "data_table(" in p.read_text(encoding="utf-8")
)


def _tables_css() -> str:
    return (CSS_DIR / "tables.css").read_text(encoding="utf-8")


def test_the_search_runs_to_the_filters() -> None:
    """It was capped at 28rem inside a slot that stretches, so a 699px slot held
    a 261px box and the 438px between it and the filters belonged to nothing."""
    css = _tables_css()
    m = re.search(r"\.table-controls-search\s*\{([^}]*)\}", css)
    assert m, "the search slot lost its rule"
    assert "max-width" not in m.group(1), (
        "the search is capped again, so it stops short of the filters"
    )
    assert re.search(r"\.table-controls-search[^{]*input[^{]*\{[^}]*width:\s*100%", css, re.S), (
        "the slot stretches but the field inside it does not"
    )


def test_the_band_uses_the_controls_own_dimensions() -> None:
    css = _tables_css()
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if ".table-controls " not in selector:
            continue
        if re.search(r"\.(btn|gl-dropdown-toggle|form-input|form-select|tab-btn)\b", selector):
            assert not re.search(r"\b(height|min-height|padding|font-size|box-shadow)\s*:", body), (
                f"{selector.strip()} overrides a shared control"
            )
    band = re.search(r"^\.table-controls \{([^}]*)\}", css, re.M)
    assert band, "the band lost its rule"
    padding = re.search(r"padding:\s*([^;]+)", band.group(1))
    assert padding, "the band lost its padding declaration"
    assert padding.group(1).strip().startswith("0"), (
        "the band has top padding again: it is then 45px tall when it opens a "
        "card body and 57px when anything precedes it - the same band at two "
        "heights on one page"
    )


def test_the_filters_only_hug_the_right_edge_when_a_search_faces_them() -> None:
    """With no search, `margin-left: auto` pushed two dropdowns into the far
    corner of an otherwise empty 1200px band."""
    css = _tables_css()
    m = re.search(r"^\.table-controls-filters \{([^}]*)\}", css, re.M)
    assert m, "the filters slot lost its rule"
    assert "margin-left: auto" not in m.group(1), (
        "the filters are pushed right unconditionally again"
    )
    assert re.search(
        r"\.table-controls-search:not\(:empty\)\s*~\s*\.table-controls-filters\s*\{"
        r"[^}]*margin-left:\s*auto",
        css,
        re.S,
    ), "nothing puts the filters opposite a search any more"


@pytest.mark.parametrize(
    "template",
    [p.relative_to(TEMPLATE_DIR).as_posix() for p in _PAGE_TEMPLATES],
    ids=lambda p: p.split("/")[-1],
)
def test_a_search_box_is_not_a_card_header_action(template: str) -> None:
    """`header_actions` is what you can DO to a table. Narrowing it is not an
    action, and every page that put a search there had a header that wrapped."""
    src = (TEMPLATE_DIR / template).read_text(encoding="utf-8")
    names = set(re.findall(r"header_actions=([a-z_]+)", src))
    offenders = []
    for name in names:
        block = re.search(
            r"\{%-?\s*set\s+" + name + r"\s*%\}(.*?)\{%-?\s*endset\s*%\}",
            src,
            re.S,
        )
        if block and "search_input(" in block.group(1):
            offenders.append(name)
    assert not offenders, (
        f"{template} renders a search box into a card header ({offenders}). It "
        "belongs in `table_controls`, the band between the header and the rows."
    )


# ---------------------------------------------------------------------------
# A table that fills itself from JavaScript says so.
#
# Five tbodies in five templates rendered as `<tbody id="..."></tbody>` - a
# header over a void until a fetch returned. The weekly-breakdown table on the
# student page went further and stayed `display: none` until its data landed,
# so the card grew by the table's full height (measured 0 -> 1092px) the moment
# it did.
# ---------------------------------------------------------------------------

_TBODY = re.compile(r"<tbody\b([^>]*)>(.*?)</tbody>", re.S)

#: A heat map is drawn cell by cell into a panel hidden until it has data; it is
#: not a list of rows and has no row-shaped loading state.
_NOT_A_LIST = {"checkHeatmapBody"}


def _is_a_void(body: str) -> bool:
    """True when the SERVER renders nothing into this tbody."""
    includes = re.findall(r"""{%-?\s*include\s+["']([^"']+)["']""", body)
    for included in includes:
        body += (TEMPLATE_DIR / included).read_text(encoding="utf-8")
    return "{% for" not in body and "{%- for" not in body and "<tr" not in body


def _js_filled_tbodies() -> dict[str, list[str]]:
    """template -> ids of tbodies the server renders with nothing in them."""
    found: dict[str, list[str]] = {}
    for path in TEMPLATE_DIR.rglob("*.html"):
        src = path.read_text(encoding="utf-8")
        for attrs, body in _TBODY.findall(src):
            tid = re.search(r'id="([^"]+)"', attrs)
            if not tid or tid.group(1) in _NOT_A_LIST or not _is_a_void(body):
                continue
            found.setdefault(path.relative_to(TEMPLATE_DIR).as_posix(), []).append(tid.group(1))
    return found


JS_TBODIES = _js_filled_tbodies()


def test_the_search_found_the_js_filled_tables() -> None:
    """If this ever finds nothing, the test below is passing vacuously."""
    assert "admin_events.html" in JS_TBODIES, "the scan missed the live events table"
    assert "admin_system.html" not in JS_TBODIES, "server rows were mistaken for a JS-filled table"


@pytest.mark.parametrize("template", sorted(JS_TBODIES), ids=lambda p: p.split("/")[-1])
def test_a_table_filled_by_javascript_says_it_is_loading(template: str) -> None:
    src = (TEMPLATE_DIR / template).read_text(encoding="utf-8")
    silent = []
    for attrs, body in _TBODY.findall(src):
        tid = re.search(r'id="([^"]+)"', attrs)
        if not tid or tid.group(1) in _NOT_A_LIST or not _is_a_void(body):
            continue
        if "sk_table_loading" not in body:
            silent.append(tid.group(1))
    assert not silent, (
        f"{template} has tables that fill from JavaScript and show nothing while "
        f"they do: {silent}. `sk_table_loading` is the one loading state for a "
        "table body - the same box the empty state uses, so loading, empty and "
        "loaded are three states of one shape rather than three layouts."
    )


def test_the_weekly_breakdown_table_is_not_hidden_until_its_data_arrives() -> None:
    html = (TEMPLATE_DIR / "partials/student/_compliance_history.html").read_text(encoding="utf-8")
    m = re.search(r'<div id="historyTable"([^>]*)>', html)
    assert m, "the weekly breakdown table lost its wrapper"
    assert "d-none" not in m.group(1), (
        "the table is hidden until its fetch returns again - the card then grows "
        "by the table's full height the moment the data lands, and until then "
        "there is nothing on screen to say a table is coming"
    )


def test_only_the_shared_stylesheet_decides_how_a_cell_sits() -> None:
    """`pages/admin.css` carried `.data-table tbody td { vertical-align: middle }`
    - an unscoped rule for every table in the app, written in one page's
    stylesheet. A badge beside a two-line cell sat differently depending on
    which page's sheet happened to be loaded."""
    offenders = []
    for path in PAGES_DIR.glob("*.css"):
        if ".min." in path.name:
            continue
        for sel, body in _rules(path):
            if not _is_about_the_cell(sel) or any(a in sel for a in ALLOWED):
                continue
            if re.search(r"(?:^|[\s;])vertical-align\s*:", body):
                offenders.append(f"{path.name}: {sel[:60]}")
    assert not offenders, f"a page decides how a table cell sits: {offenders}. tables.css does."


def test_no_page_gives_one_table_its_own_text_size() -> None:
    """Four tables set their own: the weekly deadlines summary and the analytics
    trend table at `--font-size-sm`, the groups and member tables at
    `--font-size-xs` on a phone. Every other table reads at `--font-size-base`,
    so the same kind of list was set two steps smaller depending on the page."""
    offenders = []
    for path in PAGES_DIR.glob("*.css"):
        if ".min." in path.name:
            continue
        for sel, body in _rules(path):
            if any(a in sel for a in ALLOWED):
                continue
            if not re.search(r"(\btd\b|\bth\b|-table\b|data-table)", sel):
                continue
            if re.search(r"(?:^|[\s;])font-size\s*:", body):
                offenders.append(f"{path.name}: {sel[:60]}")
    assert not offenders, (
        f"a page sets a table's text size: {offenders}. Use `.table-compact` for "
        "a denser table, or name the cell that is genuinely special."
    )
