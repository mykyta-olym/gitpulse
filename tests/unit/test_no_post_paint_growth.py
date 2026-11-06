"""Content that arrives after first paint occupies space that was already its own.

Measured with Playwright across every page (1440x900, authenticated): the
System page grew 546px after paint and the Teachers panel 37px per member row,
because three different blocks on one page had three different treatments -
one with a loader, one with none, and one drawn by Alpine from data the
server already held.

Three rules came out of it, and this pins them:

1. The shared loading hand-off takes the loader OUT OF FLOW before the
   content is revealed. It used to fade the loader while it still occupied
   its full height, so the card was loader+content tall for the length of the
   fade - 520px + 546px for ~100ms on the System page, then a collapse. Every
   loader in the app uses this one function, so the bounce was everywhere.
2. `data_table(reserve_rows=N)` holds the height of rows that paint from an
   inlined island, because the page bundle is deferred and the <tbody> is empty
   until it runs.
3. A list the server already holds is rendered by the server. The Teachers
   panel was drawn by Alpine from the inlined list and reserved its rows to
   hide the wait; it is server-rendered now, so there is no wait to hide.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MOTION = REPO / "src/app/templates/static/js/motion.js"
TABLES = REPO / "src/app/templates/components/tables.html"
SYSTEM = REPO / "src/app/templates/admin_system.html"
TEACHERS = REPO / "src/app/templates/partials/course/_teachers_content.html"
TEACHERS_JS = REPO / "src/app/templates/static/js/pages/course-teachers.js"


def test_the_loader_leaves_the_flow_before_the_content_arrives() -> None:
    src = MOTION.read_text(encoding="utf-8")
    body = src.split("function loadingHandoff(", 1)[1].split("\n  /* ---", 1)[0]
    pin = body.index("position: 'absolute'")
    reveal = body.index("contentEl.classList.remove('d-none')", pin - 4000)
    # the pin that matters is the one before the reveal inside the fade branch
    assert body.index("position: 'absolute'") < body.rindex(
        "contentEl.classList.remove('d-none')"
    ), "the loader is pinned after the content is revealed - the height still doubles"
    assert reveal > 0


def test_the_shared_table_can_reserve_its_rows() -> None:
    src = TABLES.read_text(encoding="utf-8")
    assert "reserve_rows=0" in src, "data_table lost its row reservation"
    assert re.search(r'class="table-responsive"\{% if reserve_rows %\}', src), (
        "the reservation is no longer applied to the scroll viewport"
    )


def test_the_jobs_table_renders_rows_without_a_height_reservation() -> None:
    """The server rows occupy their actual height before deferred scripts run."""
    src = SYSTEM.read_text(encoding="utf-8")
    assert "include 'partials/admin/_system_job_rows.html'" in src
    assert "reserve_rows=" not in src
    assert "gp-jobs-first-page" not in src


def test_the_teacher_list_is_in_the_first_frame() -> None:
    """The rows are the server's, so there is nothing to wait for and nothing
    to reserve: the first frame is the page (measured: 0 elements appear,
    vanish or move between the first frame and the settled page)."""
    src = TEACHERS.read_text(encoding="utf-8")
    assert "x-for=" not in src, "the teacher rows are drawn by Alpine after paint again"
    assert "{% for inst in _listed %}" in src
    assert "reserve_rows" not in src, "a reservation for rows that are already there"
    js = TEACHERS_JS.read_text(encoding="utf-8")
    assert "tableLoaded" not in js
    assert "style.minHeight" not in js


def test_the_handoff_leaves_an_already_stacked_loader_alone() -> None:
    """`.gl-chart-swap` puts the loader and the chart in the SAME grid cell,
    so they overlap by construction and pinning buys nothing. It also costs
    something: taking a grid child out of flow re-resolves its containing block,
    and the analytics checklist loader jumped 240px sideways - a 0.062 CLS on
    a page that had measured 0.000 before."""
    src = MOTION.read_text(encoding="utf-8")
    body = src.split("function loadingHandoff(", 1)[1].split("\n  /* ---", 1)[0]
    assert "_alreadyStacked" in body, (
        "the hand-off pins every loader again, including ones the layout already overlaps"
    )
    assert "gridArea" in body, "the stacking test no longer looks at the grid area"
    # the stacked branch must still fade the loader out
    stacked = body.split("_alreadyStacked", 1)[1]
    assert "opacity: 0" in stacked


def test_the_stack_container_still_overlaps_its_children() -> None:
    """The premise for the branch above."""
    css = (REPO / "src/app/templates/static/css/loaders.css").read_text(encoding="utf-8")
    assert ".gl-chart-swap { display: grid; }" in css
    assert ".gl-chart-swap > * { grid-area: 1 / 1;" in css
