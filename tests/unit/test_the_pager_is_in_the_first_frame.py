"""The bar under a table is in the first frame, and so is the first page of rows.

Measured with the deferred scripts held back (what a reader sees before they
run) against the settled page: on every paginated list the bar was born empty
and ClientPaginator filled it a moment later - "Showing 1-25 of 54", the page
buttons, the arrows and the per-page menu all popped in under the table. And a
CSS rule hid rows past a fixed 50 (25 on the Users page) until the paginator
ran, whatever the reader's Rows per page: the Users page opened with 25 rows
and grew to 50, 1265px, when the script ran.

Now `pagination_controls(total=, page_size=)` renders page 1 itself - the
markup the paginator writes - and the rows past the first page are hidden at
the reader's own page size (html[data-page-size]).
"""

from __future__ import annotations

import re
from pathlib import Path

from app.main import templates

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "src/app/templates"
JS = (T / "static/js/components.js").read_text(encoding="utf-8")


def _bar(**kw: object) -> str:
    src = (
        "{% from 'components/tables.html' import pagination_controls %}"
        "{{ pagination_controls(**kw) }}"
    )
    return templates.env.from_string(src).render(kw=kw)


def _range(html: str) -> list[str]:
    info = html.split('class="gl-pagination-info">', 1)[1].split("</span>", 1)[0]
    return re.findall(r"<strong>(\d+)</strong>", info)


def test_page_one_is_rendered_by_the_server() -> None:
    html = _bar(total=54, page_size="50")
    assert _range(html) == ["1", "50", "54"]
    assert 'class="pagination-page pagination-current" data-page="1" aria-current="page">1<' in html
    assert 'data-page="2">2<' in html
    prev = html.split("pagination-prev", 1)[1].split(">", 1)[0]
    nxt = html.split("pagination-next", 1)[1].split(">", 1)[0]
    assert " disabled" in prev
    assert " disabled" not in nxt
    assert re.search(r'class="gl-dropdown-item active" data-size="50"', html)


def test_the_edges() -> None:
    assert _range(_bar(total=0, page_size="50")) == ["0", "0", "0"]
    many = _bar(total=1000, page_size="25")  # 40 pages: 1, 2, ..., 40
    assert '<span class="pagination-ellipsis">...</span>' in many
    assert 'data-page="40">40<' in many
    assert 'class="pagination d-none"' in _bar(total=10, page_size="all")
    assert "gp-pagination-placeholder" in _bar(), "a table fed by fetch keeps the empty bar"


def test_it_is_the_markup_the_paginator_writes() -> None:
    """Same classes and attributes as _paintControls, so the paginator's first
    render replaces the bar with an identical one."""
    html = _bar(total=54, page_size="50")
    for piece in (
        'class="gl-pagination-info"',
        '<nav class="pagination" aria-label="Pagination">',
        "btn btn-secondary btn-icon-only pagination-btn pagination-prev",
        "btn btn-secondary btn-icon-only pagination-btn pagination-next",
        'class="pagination-pages"',
        'class="gl-pagination-size"',
        'class="gl-dropdown gl-page-size-dropdown" data-dropdown-portal',
    ):
        assert piece in html, f"the server bar lost {piece}"
        assert piece in JS, f"the paginator no longer writes {piece}"


def test_rows_past_page_one_wait_at_the_readers_page_size() -> None:
    css = (T / "static/css/tables.css").read_text(encoding="utf-8")
    for size, nth in (("25", r"n\+26"), ("100", r"n\+101")):
        assert re.search(rf'html\[data-page-size="{size}"\][^{{]*nth-child\({nth}\)', css), size
    assert "nth-child(n+51)" in css
    admin = (T / "static/css/pages/admin.css").read_text(encoding="utf-8")
    assert "nth-child(n+26)" not in admin, "the Users page's fixed 25 is back"


def test_only_tables_the_paginator_works_wait() -> None:
    """A pager fed by fetch never marks its table ready: scoped to any card
    with a pager, the rule hid every Job History row past the 50th for good."""
    css = (T / "static/css/tables.css").read_text(encoding="utf-8")
    assert ":is([data-paginator] table, table[data-paginated]):not(.paginator-ready)" in css
    assert ".card-body:has(.pagination-controls)) table:not(.paginator-ready)" not in css
    for rel in (
        "partials/admin/_users_table.html",
        "partials/course/_teachers_content.html",
        "partials/team/_detail_content.html",
        "partials/course/_detail_content.html",
    ):
        assert "paginated=true" in (T / rel).read_text(encoding="utf-8"), rel
    system = (T / "admin_system.html").read_text(encoding="utf-8")
    assert "paginated=true" not in system, "Job History's pager is fed by fetch"


def test_every_server_rendered_list_passes_its_total() -> None:
    fed_by_fetch = {"admin_system.html", "admin_events.html", "_ai_analysis.html", "tables.html"}
    for p in T.rglob("*.html"):
        if p.name in fed_by_fetch:
            continue
        for m in re.finditer(r"pagination_controls\((.*?)\)\s*\}\}", p.read_text(encoding="utf-8")):
            args = m.group(1)
            assert "total=" in args, f"{p.name}: the pager under server-rendered rows is born empty"
            assert "page_size=default_page_size | default('50')" in args, p.name
