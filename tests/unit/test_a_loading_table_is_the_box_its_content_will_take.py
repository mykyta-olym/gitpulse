"""A table's loading state is the box its content is going to occupy, and it
says "loading" from its first frame.

Measured on the Events page with no events (production's state): the
server-rendered loading row claimed `min-height: min(78vh, 820px)` - a 700px
box at 900px viewport - and its spinner and label were held transparent for
400ms. The deferred page script painted the empty state within that window,
so the reader saw a tall BLANK box collapse to a 170px "No events received
yet" - "the table stretches to double while loading and snaps back, and there
is no spinner". Every table that renders this row has its first page inlined:
when rows are coming, `data_table(reserve_rows=...)` already reserves their
height on the scroll viewport; when the page is empty, what lands is the empty
state, which is the same box as the loading row by design. Neither case needs
a screenful.

The block loader has the same contract: it reserves the height the content
will take, and the spinner + label are visible from the first frame - the
System Health card is the reference the rest of the app is measured against.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TABLES_CSS = REPO / "src/app/templates/static/css/tables.css"
ANIM_CSS = REPO / "src/app/templates/static/css/animations.css"
EVENTS = REPO / "src/app/templates/admin_events.html"


def _rule(css: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert match, f"{selector} rule is gone"
    return match.group(1)


def test_the_loading_row_claims_no_height_of_its_own() -> None:
    body = _rule(TABLES_CSS.read_text(encoding="utf-8"), "\n.table-loading-state")
    assert "min-height" not in body, (
        "the loading row reserves a screenful again; with an empty first page "
        "the empty state that lands is 170px and the box collapses"
    )


def test_loading_and_empty_share_one_icon_slot_height() -> None:
    """The slot is 72px - the GitLab sm illustration an empty state leads with.
    The 28px spinner centres in the same slot, so the two boxes measure the
    same and loading -> empty moves nothing. Inside a reserved box the loader
    lies in one line and claims no slot height."""
    css = TABLES_CSS.read_text(encoding="utf-8")
    assert "min-height: 72px" in _rule(css, "\n.table-empty-icon")
    assert ".table-empty-message:first-child" not in css, "an empty state lost its art"
    inline = _rule(
        css,
        '.table-responsive:is([style*="min-height"], [data-reserve]) .table-loading-state '
        ".table-empty-message",
    )
    assert "min-height: 0" in inline


def test_the_reservation_lets_go_once_the_rows_are_in() -> None:
    """`reserve_rows` holds the rows' height until they land, no longer. As an
    inline min-height it outlived the rows of every table that drew them on its
    first render - the student's Issues, Weekly Breakdown, the Events table -
    and stood as blank space under the last row (41px under two issues, 47px
    under Events on a phone) until a filter switch re-rendered it, back again
    on reload. It is a CSS rule now, live only while the body is empty or holds
    nothing but the loader."""
    macro = (REPO / "src/app/templates/components/tables.html").read_text(encoding="utf-8")
    assert 'style="min-height: min(' not in macro, "the reservation is inline again"
    assert 'data-reserve style="--table-reserve:' in macro

    rule = _rule(
        TABLES_CSS.read_text(encoding="utf-8"),
        ".table-responsive[data-reserve]:not(:has(> table > tbody > tr:not(.table-loading-row)))",
    )
    assert "var(--table-reserve)" in rule

    # Both writers of the loader row mark it, or the reservation would let go
    # the moment a loader appeared - the jump it exists to prevent.
    loaders = (REPO / "src/app/templates/components/loaders.html").read_text(encoding="utf-8")
    assert '<tr class="table-empty-row table-loading-row">' in loaders
    states = (REPO / "src/app/templates/static/js/_parts/core/22-content-states.js").read_text(
        encoding="utf-8"
    )
    assert '\'<tr class="table-empty-row table-loading-row"><td colspan="\' + cols' in states


def test_the_spinner_and_label_are_legible_from_the_first_frame() -> None:
    """No loading mark is held transparent any more - not the table row, not the
    block loader."""
    css = ANIM_CSS.read_text(encoding="utf-8")
    assert "gp-loading-state-appears" not in css, "a loading mark is held transparent again"
    assert "gp-loading-clock" not in css, "a decorative clock delays ready data"


def test_ready_data_does_not_wait_for_a_loading_animation() -> None:
    """The spinner is delayed for fast reads; data is never held after a read."""
    helpers = (REPO / "src/app/templates/static/js/_parts/core/22-content-states.js").read_text(
        encoding="utf-8"
    )
    assert "_BUSY_DELAY_MS" in helpers
    assert "loadingHoldRemaining" not in helpers
    assert "afterLoadingMinimum" not in helpers
    motion = (REPO / "src/app/templates/static/js/motion.js").read_text(encoding="utf-8")
    handoff = motion.split("function loadingHandoff(", 1)[1].split("\n  /* ---", 1)[0]
    assert "setTimeout" not in handoff
    for rel in (
        "js/pages/admin-events.js",
        "js/_parts/admin-system/20-jobs.js",
        "js/_parts/course-settings/10-sections.js",
    ):
        src = (REPO / "src/app/templates/static" / rel).read_text(encoding="utf-8")
        assert "afterLoadingMinimum" not in src


def test_the_events_table_reserves_its_two_line_rows() -> None:
    src = EVENTS.read_text(encoding="utf-8")
    assert "reserve_row_px=65" in src, (
        "Where and Received wrap to two lines; the 57px default under-reserves "
        "and the card grows when the rows land"
    )
