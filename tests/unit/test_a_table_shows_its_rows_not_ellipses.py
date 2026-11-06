"""A data table shows its rows; it does not cut them to "..." in a card too
narrow for them.

Measured on the course Activity tab at 1366px and again at 1600px: Group
Activity and Recent Merge Requests shared one row as two half-width cards, and
a fixed-layout data table in a 540px card cut 39 cells - group names, MR
titles, project names, dates, even the State badge - to "..." with the rest
behind a horizontal scroll. The webhook configurations table did the same to
its Scope and Status cells.

The cure is the layout every other table in the app already has: one table
under the other at full width, auto layout so a column takes the width its
content needs. And the pagination bar under them is the shared component - a
bare empty `<div class="pagination-controls">` is `:empty`, display:none, so
the card grew 57px when the paginator drew the bar after the script ran.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
ACTIVITY = TEMPLATES / "partials/course/_activity_content.html"
WEBHOOKS = TEMPLATES / "partials/course_settings/_webhook_settings.html"
COURSE_CSS = REPO / "src/app/templates/static/css/pages/course.css"


def test_the_activity_tables_are_auto_layout_full_width() -> None:
    src = ACTIVITY.read_text(encoding="utf-8")
    for table_id in ("groupActivityTable", "recentMrsTable"):
        call = re.search(r"data_table\([^)]*id='" + table_id + r"'\)", src)
        assert call, f"{table_id} is no longer a data_table"
        assert "tbl-fixed" not in call.group(0), (
            f"{table_id} is fixed-layout again: cells will be cut to '...'"
        )
    css = COURSE_CSS.read_text(encoding="utf-8")
    assert ".activity-grid" not in css, "the two tables are side by side again"
    assert (
        "text-overflow: ellipsis"
        not in css.split("/* -- Activity card")[1].split("/* -- Pipeline health cell")[0]
    )
    # ONE card, two views on one strip - the way Configuration on System
    # Settings and the student's Issues card switch views - not two cards
    # stacked, each with its own header, help tip and pagination bar.
    assert src.count("{% call card(") == 2, (
        "the Activity tab has more than the CI/CD card and the Activity card"
    )
    assert 'data-tabs id="activityViews"' in src
    assert 'data-tab-panel="groups"' in src
    assert 'data-tab-panel="mrs"' in src
    assert "panels=true" in src, "the view strip filters rows instead of switching panels"


def test_the_webhook_table_is_auto_layout() -> None:
    src = WEBHOOKS.read_text(encoding="utf-8")
    call = re.search(r"data_table\(id='webhookConfigsTable'[^)]*\)", src).group(0)
    assert "tbl-fixed" not in call
    css = COURSE_CSS.read_text(encoding="utf-8")
    block = css[css.index("#webhookConfigsTable {") :]
    assert "table-layout: fixed" not in block.split("}", 1)[0]


def test_every_pagination_bar_is_the_component() -> None:
    """The component reserves the bar's height from the first frame; a bare div
    is hidden while empty and the card grows when the bar lands."""
    for path in TEMPLATES.rglob("*.html"):
        if path.name == "tables.html" and path.parent.name == "components":
            continue
        assert 'class="pagination-controls"' not in path.read_text(encoding="utf-8"), (
            f"{path.relative_to(TEMPLATES)} writes its own pagination bar; "
            "use pagination_controls()"
        )


def test_a_card_explains_itself_in_its_body_not_its_header() -> None:
    """One card put its explanatory line in the header through a `subtitle=`
    parameter no other caller used, so it laid out differently from every
    other card. The line goes first in the body, like User Role Breakdown."""
    cards = (TEMPLATES / "components/cards.html").read_text(encoding="utf-8")
    assert "subtitle" not in cards.split("{% macro card(")[1].split("%}")[0]
    for path in TEMPLATES.rglob("*.html"):
        src = path.read_text(encoding="utf-8")
        assert not re.search(r"call card\([^%]*subtitle=", src), (
            f"{path.relative_to(TEMPLATES)} passes subtitle= to card()"
        )
    diag = (TEMPLATES / "partials/student/_diagnostics.html").read_text(encoding="utf-8")
    body = diag.split("{% call card(title=ct, icon_name='message-square') %}", 1)[1]
    assert (
        body.lstrip().startswith("{#")
        or '<p class="muted text-sm">' in body.split("{% if indicators %}")[0]
    )
