"""Wherever a course is listed, its academic term is listed with it.

"ZSI" is every year's ZSI. User Info printed a course's term as plain grey
text and a group's course with no term at all; the Events table's Where column,
the search palette's team results, the support ticket and form headers, the Run
Checks dialog and the dashboard's lifecycle items ("ZSI - archived over 2 years
ago") named the course alone.

Lists drawn on the server use period_badge(); lists drawn in the browser use
GP.periodBadgeHtml(), which returns the same markup and highlights the running
term the same way, read from <meta name="gp-current-period">.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src/app"
TEMPLATES = SRC / "templates"
JS = TEMPLATES / "static/js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# -- The badge drawn in the browser is the badge drawn on the server ---------


def _node(script: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "harness.js"
        path.write_text(script, encoding="utf-8")
        result = subprocess.run(  # noqa: S603
            ["node", str(path)],  # noqa: S607
            capture_output=True,
            text=True,
            encoding="utf-8",  # the label's "·"; Windows would decode cp1252
            timeout=60,
            cwd=str(REPO),
        )
    assert result.returncode == 0, result.stderr[:400]
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def _core_function(file: str, name: str) -> str:
    """The source of one top-level function in a core part, as the bundle has it."""
    src = _read(JS / "_parts/core" / file)
    body = src.split(f"function {name}(", 1)[1].split("\n}\n", 1)[0]
    return f"function {name}({body}\n}}\n"


def test_the_browser_badge_matches_the_server_badge() -> None:
    src = json.dumps(str(JS / "academic-period.js"))
    # The period badge is the app's badge (GP.badgeHtml, core) and its label
    # the app's translation (GP.t) - give the harness the real ones, as the
    # bundle does before academic-period.js.
    core = (
        _core_function("00-namespace.js", "_translateUiText")
        + _core_function("06-utilities.js", "escapeHtml")
        + _core_function("22-content-states.js", "badgeHtml")
    )
    out = _node(
        textwrap.dedent(
            """
            const fs = require('fs');
            const meta = { content: '2025-2026-summer' };
            global.window = { GP: {} };
            global.document = {
              readyState: 'loading',
              addEventListener() {},
              querySelector(sel) { return sel.includes('gp-current-period') ? meta : null; },
              querySelectorAll() { return []; },
            };
            const GP = window.GP;
            __CORE__
            GP.t = _translateUiText;
            GP.escapeHtml = escapeHtml;
            GP.badgeHtml = badgeHtml;
            eval(fs.readFileSync(__SRC__, 'utf8'));
            console.log(JSON.stringify({
              current: GP.periodBadgeHtml('2025/2026', 'summer'),
              past: GP.periodBadgeHtml('2024/2025', 'winter'),
              none: GP.periodBadgeHtml('', ''),
            }));
            """
        )
        .replace("__SRC__", src)
        .replace("__CORE__", core)
    )
    span = '<span class="badge badge-{} badge-sm gl-period-badge">{}</span>'
    assert out["current"] == span.format("info", "2025/2026 · Summer")
    assert out["past"] == span.format("gray", "2024/2025 · Winter")
    assert out["none"] == ""


def test_the_server_badge_has_the_same_classes() -> None:
    macro = _read(TEMPLATES / "components/academic_period.html")
    body = macro.split("{% macro period_badge(", 1)[1].split("{%- endmacro %}", 1)[0]
    assert "variant='info' if current else 'gray'" in body
    assert "size='sm'" in body
    assert "class='gl-period-badge '" in body


def test_every_page_says_which_term_is_running() -> None:
    base = _read(TEMPLATES / "base.html")
    assert '<meta name="gp-current-period" content="{{ current_period().key' in base


# -- Browser-drawn lists -----------------------------------------------------


def test_user_info_badges_every_course_and_every_groups_course() -> None:
    modal = _read(JS / "user-info-modal.js")
    assert modal.count("GP.periodBadgeHtml(") >= 3
    assert "GP.periodBadgeHtml(m.academic_year, m.semester)" in modal


def test_the_events_where_column_names_the_term() -> None:
    page = _read(JS / "pages/admin-events.js")
    assert "GP.periodBadgeHtml(ev.course_academic_year, ev.course_semester)" in page
    schema = _read(SRC / "schemas/events.py")
    assert "course_academic_year: str | None = None" in schema
    assert "course_semester: str | None = None" in schema
    assert '"course_academic_year": year' in _read(SRC / "api/events.py")


def test_search_team_results_name_the_term() -> None:
    routes = _read(SRC / "api/dashboard/home/routes.py")
    assert '"course_year": t.course.academic_year if t.course else ""' in routes
    palette = _read(JS / "search-palette.js")
    assert "GP.periodLabel(t.course_year, t.course_semester)" in palette


# -- Server-drawn headers ----------------------------------------------------


@pytest.mark.parametrize(
    "template",
    [
        "support_tickets.html",
        "support_form.html",
        "partials/support/_form_content.html",
        "partials/support/_ticket_detail_content.html",
    ],
)
def test_a_support_page_about_one_course_badges_its_term(template: str) -> None:
    text = _read(TEMPLATES / template)
    # A course's term uses the shared badge, whether in the page header or the
    # ticket's metadata row. Its position does not change the component contract.
    assert any(
        f"period_badge({course}.academic_year, {course}.semester" in text
        for course in ("course", "selected_course")
    )


def test_run_checks_names_the_term_it_runs_in() -> None:
    modal = _read(TEMPLATES / "partials/_run_checks_modal.html")
    assert "period_label(course.academic_year, course.semester)" in modal


# -- Dashboard lifecycle items -----------------------------------------------


def test_a_lifecycle_item_names_the_course_with_its_term() -> None:
    from app.api.dashboard.home.attention import _build_attention_items

    course = SimpleNamespace(
        id="c1",
        is_active=False,
        code="ZSI",
        name="ZSI",
        academic_year="2024/2025",
        semester="summer",
        archived_at=None,
    )
    items = asyncio.run(
        _build_attention_items(
            "teacher",
            [],
            {},
            AsyncMock(),
            {"user": "t", "gitlab_username": "t"},
            "en",
            active_courses=[],
            archived_courses=[],
            lifecycle_courses=[course],
        )
    )
    titles = [i["title"] for i in items]
    assert any(title.startswith("ZSI (2024/2025 · Summer) — ") for title in titles), titles


# -- Before something is destroyed -------------------------------------------


def test_a_course_confirmation_names_the_term() -> None:
    """ "Archive ZSI?" / "Delete ZSI?" named every year's ZSI."""
    components = _read(JS / "components.js")
    lifecycle = components.split("function courseLifecycle(", 1)[1].split(
        "\nconst courseActions", 1
    )[0]
    assert "_coursePeriodOf(courseId, btn)" in lifecycle
    assert "GP.t('Period') + ': ' + period" in lifecycle
    for template, marker in (
        ("admin_courses.html", 'data-course-period="{{ period_label(course.academic_year'),
        ("partials/dashboard/_content.html", 'data-course-period="{{ period_label(c.academic_year'),
        ("components/cards.html", 'data-course-period="{{ period_label(course.academic_year'),
    ):
        assert marker in _read(TEMPLATES / template), template


def test_settings_delete_asks_for_the_course_code_not_its_uuid() -> None:
    """The button carried no course code, so the dialog fell back to the id
    and asked the reader to type a UUID."""
    zone = _read(TEMPLATES / "partials/course_settings/_danger_zone.html")
    enabled = zone.split("id='btnDeleteCoursePermanent', data_attrs=")[1]
    assert "'course-code': course.code" in enabled.split("}) }}", 1)[0]
    assert zone.count("'course-period': period_label(") == 3


def test_a_ticket_purge_clears_only_the_course_on_screen() -> None:
    page = _read(JS / "pages/support-tickets.js")
    assert "course_id: _purgeCfg.courseId || null" in page
    assert "{course}" in page.split("async function purgeTickets(", 1)[1].split("\n  }\n", 1)[0]
    content = _read(TEMPLATES / "partials/support/_tickets_content.html")
    assert "'courseLabel':" in content
    route = _read(SRC / "api/support.py")
    purge = route.split("async def purge_support_tickets(", 1)[1].split("\n@router", 1)[0]
    assert "where.append(SupportTicket.course_id == course_id)" in purge


# -- Support about an archived course -----------------------------------------


@pytest.mark.parametrize(
    "template", ["support_form.html", "support_tickets.html", "support_ticket_detail.html"]
)
def test_support_says_when_the_course_is_archived(template: str) -> None:
    """Not "read-only" - Support takes requests for it and they reach its
    teachers - but the reader should know it is last term's course."""
    text = _read(TEMPLATES / template)
    block = text.split("{% block top_banners %}", 1)[1].split("{% endblock %}", 1)[0]
    assert '{% include "partials/course/_archived_banner.html" %}' in block
    assert "archived_note = t('support requests still reach its teachers')" in block


def test_the_archived_banner_says_read_only_by_default() -> None:
    banner = _read(TEMPLATES / "partials/course/_archived_banner.html")
    assert "{{ archived_note | default(t('read-only')) }}" in banner
