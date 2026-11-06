"""Chart.js loads on the five pages that draw charts, not on all eighteen.

It is 73kB over the wire after compression, and thirteen of the eighteen pages
never draw a chart - the dashboard, admin users, teams, tickets and the rest
were paying for it on every first visit. Removing the global tag took the
dashboard's first-load payload from 2044kB to 1843kB uncompressed.

It was made global with a reason that no longer holds: "with hx-boost the
<head> is NOT re-parsed, so a per-page chart lib would never load when
boosting". `_loadScriptsSeq` collects the incoming page's head scripts, skips
the ones already present, and runs what is left IN ORDER before the page
bundle - so a page that declares Chart.js gets it loaded and parsed before its
own code runs, on a boosted navigation exactly as on a cold load. Verified in
Chromium: navigating from the course page (no Chart) into Analytics loads the
library and the charts draw.

The list below is derived from `<canvas>`, which is what a Chart needs.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
LIB = "chart-4.4.7.min.js"


def _pages_with_a_canvas() -> set[str]:
    """Page templates that own a canvas, directly or through a partial."""
    partial_owners = {
        "partials/course/_activity_content.html": "course_activity.html",
        "partials/course/_analytics_content.html": "course_analytics.html",
        "partials/project/_issues_to_address.html": "project_detail.html",
        "partials/student/_compliance_history.html": "student_detail.html",
    }
    pages = set()
    for p in TEMPLATES.rglob("*.html"):
        if "<canvas" not in p.read_text(encoding="utf-8"):
            continue
        rel = p.relative_to(TEMPLATES).as_posix()
        pages.add(partial_owners.get(rel, rel))
    return pages


def test_the_library_is_not_loaded_globally() -> None:
    base = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assert LIB not in base, (
        "Chart.js is global again - thirteen pages that never draw a chart pay "
        "73kB for it on first load"
    )


def test_every_page_that_draws_a_chart_declares_it() -> None:
    missing = [
        page
        for page in _pages_with_a_canvas()
        if LIB not in (TEMPLATES / page).read_text(encoding="utf-8")
    ]
    assert not missing, f"these pages hold a canvas but never load Chart.js: {missing}"


def test_it_is_declared_inside_the_head_block() -> None:
    """Outside `{% block extra_head %}` a child template's markup is simply
    dropped - which is exactly how the first attempt at this failed silently."""
    for page in _pages_with_a_canvas():
        src = (TEMPLATES / page).read_text(encoding="utf-8")
        head = src.split("{% block extra_head %}", 1)[1].split("{% endblock %}", 1)[0]
        assert LIB in head, f"{page} declares Chart.js outside extra_head, so it never renders"


def test_the_spa_still_sequences_head_scripts() -> None:
    """The whole arrangement rests on this: the sequencer must load the
    incoming page's head scripts before its bundle."""
    core = (REPO / "src/app/templates/static/js/_parts/core/42-spa-navigation.js").read_text(
        encoding="utf-8"
    )
    assert "_loadScriptsSeq" in core
    assert "_headHasSrc" in core, (
        "the swap no longer skips already-loaded head scripts, so it will "
        "re-fetch shared vendor libraries on every navigation"
    )
