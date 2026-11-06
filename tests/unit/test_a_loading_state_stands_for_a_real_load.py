"""A loading state stands for a load that is actually happening.

"Check that every loading mark is real and not decorative - it is odd to see
a spinner when there is no data." Audited every mark in the app against the
path its data takes:

* the five tables whose first page is INLINED as an island (events, jobs,
  compliance checks, webhook configurations, the student's history) rendered a
  "Loading..." row anyway and then HELD it for the 800ms minimum - a spinner
  for a load that never happened, on every page load. The row is rendered
  only when the island is absent and the script has to fetch;
* the pagination bar opened with "Loading pagination..." under tables whose
  rows are in the page from the first byte - every one of them. The bar is
  born empty and keeps its height;
* cache hits and ready data never wait for a cosmetic loading minimum.

Real pending requests use shared loading states. Table spinners wait briefly
to avoid flashing on fast responses, while aria-busy and inert apply at once.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"


def test_a_loading_row_is_rendered_only_when_the_first_page_has_to_be_fetched() -> None:
    offenders: list[str] = []
    for path in TEMPLATES.rglob("*.html"):
        if path.name == "loaders.html":
            continue
        src = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\{\{\s*sk_table_loading\(", src):
            # the guard must be the last statement before the call
            tail = src[max(0, match.start() - 400) : match.start()].rstrip()
            if not re.search(r"\{%\s*if not \w+_json\s*%\}$", tail):
                offenders.append(str(path.relative_to(TEMPLATES)))
    assert not offenders, "a loading row that shows even when the rows are inlined: " + ", ".join(
        offenders
    )


def test_the_pagination_bar_is_born_empty() -> None:
    tables = (TEMPLATES / "components/tables.html").read_text(encoding="utf-8")
    macro = tables.split("{% macro pagination_controls(", 1)[1].split("{% endmacro %}", 1)[0]
    assert "gp-pagination-placeholder" in macro
    assert "spinner(" not in macro
    assert "Loading pagination" not in macro
    css = (TEMPLATES / "static/css/animations.css").read_text(encoding="utf-8")
    assert "gp-pagination-loading" not in css
    helpers = (TEMPLATES / "static/js/_parts/core/22-content-states.js").read_text(encoding="utf-8")
    assert "gp-pagination-loading" not in helpers


def test_table_busy_state_starts_before_the_visual_indicator() -> None:
    helpers = (TEMPLATES / "static/js/_parts/core/22-content-states.js").read_text(encoding="utf-8")
    body = helpers.split("function tableLoading(", 1)[1].split("\n}", 1)[0]
    assert body.index("tbody.setAttribute('aria-busy', 'true')") < body.index("setTimeout(show")
    assert "loadingHoldRemaining" not in helpers


def test_a_block_loader_is_rendered_only_when_its_data_has_to_be_fetched() -> None:
    """Jobs use real server rows; the heatmap still inlines its initial data."""
    system = (TEMPLATES / "admin_system.html").read_text(encoding="utf-8")
    assert "include 'partials/admin/_system_job_rows.html'" in system
    assert "gp-jobs-first-page" not in system
    assert "Loading jobs..." not in system
    student = (TEMPLATES / "partials/student/_compliance_history.html").read_text(encoding="utf-8")
    before = student.split("Loading check progress...", 1)[0][-400:]
    assert "{% if not history_first_json %}" in before
    routes = (REPO / "src/app/api/dashboard/admin/system.py").read_text(encoding="utf-8")
    assert "**_jobs_table_context(request, jobs_first_page)" in routes


def test_vendor_libraries_load_before_the_page_bundles() -> None:
    """Deferred scripts execute in document order and the in-app navigation
    loader keeps that order, so Chart.js (`extra_head`) must come before the
    page bundles (`extra_scripts`). It sat at the end of <head>: every chart's
    init found `Chart` undefined and waited for `load`, which an in-app
    navigation never fires - the User Role Breakdown, the score trend, the
    skill profile and the checklist stayed empty until a hard refresh."""
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert base.index("{% block extra_head %}") < base.index("{% block extra_scripts %}")
    assert base.index("{% block vendor_head %}") < base.index("{% block extra_scripts %}")
    assert base.index("js/core.bundle.js") < base.index("{% block extra_head %}")
