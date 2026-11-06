"""A course's academic period and its semester dates are one fact, told once.

The period (``academic_year`` + ``semester``) and the window
(``semester_start_date`` / ``semester_end_date``) used to be asked for by five
surfaces - Create, Import, Edit, Transfer and the settings page - each with its
own year list, semester list and "Quick preset" list, three of them wired in
different code, and every API accepted any string for either. These tests pin
the one rule each piece now follows, and that every surface uses the one
component that follows it.
"""

from __future__ import annotations

import asyncio
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.schemas.courses import (
    CourseCreate,
    CourseTransferRequest,
    CourseUpdate,
    GitLabGroupImportRequest,
)
from app.services.academic_periods import (
    NO_PERIOD,
    PERIOD_COOKIE,
    count_students,
    requested_period,
    resolve_period,
)
from app.utils.academic_period import (
    AcademicPeriod,
    calendar_period,
    calendar_periods,
    dialog_periods,
    in_session,
    normalize_academic_year,
    normalize_semester,
    parse_key,
    period_of_date,
)
from app.utils.semester import SemesterDateError, validate_semester_window
from app.utils.semester_presets import current_semester, running_preset

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
JS = TEMPLATES / "static/js"
SRC = REPO / "src/app"


# -- one answer to "which term is this day in" -----------------------------


def test_the_winter_exams_and_the_first_summer_week_overlap_and_summer_wins() -> None:
    """2027-02-08 .. 2027-02-12 is inside both terms of the TUKE table.

    Winter came first in the table, so every caller said "winter" in the week
    summer teaching had started - and a course created that week went into the
    finished term. The later-starting term wins, in every caller.
    """
    day = date(2027, 2, 10)
    summer = AcademicPeriod("2026/2027", "summer")
    assert in_session(day) == summer
    assert period_of_date(day) == summer
    assert calendar_period(day) == summer
    preset = current_semester(day)
    assert preset is not None
    assert (preset.academic_year, preset.semester) == ("2026/2027", "summer")
    assert running_preset(day) == preset


def test_a_day_in_a_gap_belongs_to_the_term_about_to_start() -> None:
    assert period_of_date(date(2026, 8, 20)) == AcademicPeriod("2026/2027", "winter")
    assert period_of_date(date(2026, 2, 14)) == AcademicPeriod("2025/2026", "summer")


def test_a_day_before_the_table_is_not_pulled_into_its_first_term() -> None:
    """The old rule took "the next preset" however far away it was, so
    1 October 2024 answered winter 2025/2026 - a year out."""
    assert period_of_date(date(2024, 10, 1)) == AcademicPeriod("2024/2025", "winter")
    assert period_of_date(date(2025, 3, 3)) == AcademicPeriod("2024/2025", "summer")


def test_the_browser_asks_the_same_question_the_same_way() -> None:
    """academic-period.js mirrors period_of_date: same look-ahead, same steps."""
    from app.utils import academic_period as module

    js = (JS / "academic-period.js").read_text(encoding="utf-8")
    assert f"GAP_LOOKAHEAD_DAYS = {module._GAP_LOOKAHEAD_DAYS}" in js
    body = js.split("function periodOfDate(", 1)[1].split("\n  }\n", 1)[0]
    # containing (later start wins) -> upcoming within the horizon -> derived
    assert body.index("containing") < body.index("upcoming") < body.index("m === 7 || m === 8")
    assert "b.start > a.start" in body


# -- one spelling of a period ----------------------------------------------


@pytest.mark.parametrize(
    ("raw", "stored"),
    [("2026/2027", "2026/2027"), (" 2026-2027 ", "2026/2027"), ("2026 / 2027", "2026/2027")],
)
def test_an_academic_year_is_two_consecutive_years(raw: str, stored: str) -> None:
    assert normalize_academic_year(raw) == stored


@pytest.mark.parametrize("raw", ["", "2026", "26/27", "2026/2028", "2027/2026", "abcd/efgh", None])
def test_anything_else_is_refused(raw: str | None) -> None:
    with pytest.raises(ValueError, match="consecutive"):
        normalize_academic_year(raw)


def test_a_semester_is_winter_or_summer_whatever_its_case() -> None:
    assert normalize_semester(" Winter ") == "winter"
    with pytest.raises(ValueError, match="winter"):
        normalize_semester("fall")


def test_a_url_key_with_a_year_that_is_not_one_is_refused() -> None:
    assert parse_key("2026-2028-winter") is None
    assert parse_key("2026-2027-winter") == AcademicPeriod("2026/2027", "winter")


# -- every way in accepts the same periods ----------------------------------


def test_create_refuses_a_period_no_page_could_show() -> None:
    with pytest.raises(ValidationError):
        CourseCreate(code="ZSI", name="ZSI", academic_year="2026/2028")
    with pytest.raises(ValidationError):
        CourseCreate(code="ZSI", name="ZSI", academic_year="2026/2027", semester="autumn")
    ok = CourseCreate(code="ZSI", name="ZSI", academic_year="2026-2027", semester="Summer")
    assert (ok.academic_year, ok.semester) == ("2026/2027", "summer")


def test_create_refuses_a_window_the_settings_page_would_refuse() -> None:
    today = date.today()  # noqa: DTZ011 - a calendar day, inside the accepted range
    with pytest.raises(ValidationError, match="strictly after"):
        CourseCreate(
            code="ZSI",
            name="ZSI",
            academic_year="2026/2027",
            semester_start_date=today,
            semester_end_date=today,
        )


def test_a_request_that_names_no_semester_gets_the_calendars() -> None:
    """Create defaulted to "winter", Import to "summer" 2025/2026 - forever."""
    now = calendar_period()
    assert CourseCreate(code="ZSI", name="ZSI", academic_year=now.academic_year).semester == (
        now.semester
    )
    imp = GitLabGroupImportRequest(group_url="https://x/g", course_code="ZSI", course_name="ZSI")
    assert (imp.academic_year, imp.semester) == (now.academic_year, now.semester)


def test_update_and_transfer_refuse_the_same_periods() -> None:
    with pytest.raises(ValidationError):
        CourseUpdate(academic_year="26/27")
    with pytest.raises(ValidationError):
        CourseTransferRequest(academic_year="2026/2027", semester="spring")
    assert CourseUpdate(semester="SUMMER").semester == "summer"


def test_the_json_config_import_uses_the_same_rule() -> None:
    text = (SRC / "api/dashboard/courses/settings_config.py").read_text(encoding="utf-8")
    assert "normalize_academic_year(" in text
    assert "normalize_semester(" in text
    assert "_VALID_SEMESTERS" not in text


# -- a stored date is not re-judged by a moving floor -----------------------


def test_an_unchanged_old_start_date_does_not_block_saving_the_course() -> None:
    """The floor is 1 January two years back: a course's own, correct start
    date sinks below it later, and every save of any setting failed."""
    old = date(2023, 9, 18)
    validate_semester_window(old, date(2024, 2, 9), stored_start=old, stored_end=date(2024, 2, 9))
    with pytest.raises(SemesterDateError):
        validate_semester_window(old, date(2024, 2, 9))


# -- which terms a dialog offers --------------------------------------------


def test_a_dialog_offers_this_term_and_the_next_not_a_six_year_span() -> None:
    offered = dialog_periods(date(2026, 9, 25))
    keys = [p.key for p, _ in offered]
    assert keys == ["2027-2028-summer", "2027-2028-winter", "2026-2027-summer", "2026-2027-winter"]
    assert {p.key: s for p, s in offered}["2026-2027-winter"] == "current"


def test_between_terms_the_coming_one_is_upcoming_not_current() -> None:
    states = {p.key: s for p, s in dialog_periods(date(2026, 7, 10))}
    assert states["2026-2027-winter"] == "upcoming"


def test_import_alone_reaches_back_and_says_the_term_is_over() -> None:
    states = {p.key: s for p, s in dialog_periods(date(2026, 9, 25), past_terms=2)}
    assert states["2025-2026-summer"] == "ended"
    assert states["2025-2026-winter"] == "ended"


def test_a_course_in_an_old_term_still_shows_where_it_is() -> None:
    old = AcademicPeriod("2021/2022", "summer")
    assert old in [p for p, _ in dialog_periods(date(2026, 9, 25), include=old)]


def test_the_scope_selector_drops_finished_empty_terms() -> None:
    """Every term of the preset table was listed; the list grew by two a year
    and the stale ones were empty. Terms with courses are merged back in."""
    keys = [p.key for p in calendar_periods(date(2026, 9, 25))]
    assert "2025-2026-winter" not in keys
    assert keys == ["2026-2027-summer", "2026-2027-winter"]


# -- a remembered pick -------------------------------------------------------


def _request(query: dict[str, str] | None = None, cookie: str | None = None) -> Any:
    # `state` as a real request has it: the dashboard auth puts the account's
    # Default period there (absent = "the period I picked last").
    return SimpleNamespace(
        query_params=query or {},
        cookies={PERIOD_COOKIE: cookie} if cookie else {},
        state=SimpleNamespace(),
    )


def test_the_address_wins_over_a_remembered_pick() -> None:
    now = calendar_period().key
    req = _request({"period": "all"}, f"2025-2026-summer~{now}")
    assert requested_period(req) == "all"  # type: ignore[arg-type]


def test_a_pick_is_remembered_while_its_term_runs() -> None:
    now = calendar_period().key
    assert requested_period(_request(cookie=f"2025-2026-summer~{now}")) == "2025-2026-summer"  # type: ignore[arg-type]


def test_a_pick_from_an_earlier_term_has_lapsed() -> None:
    assert requested_period(_request(cookie="2025-2026-summer~2000-2001-winter")) is None  # type: ignore[arg-type]


def test_no_period_carried_to_a_page_of_courses_means_no_choice() -> None:
    result = MagicMock()
    result.all.return_value = [("2025/2026", "summer")]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    key, period, _ = asyncio.run(resolve_period(db, NO_PERIOD, include_none=False))
    assert key != NO_PERIOD
    assert period is not None


# -- the dashboard counts what it shows -------------------------------------


def test_the_students_card_counts_the_students_of_the_courses_on_screen() -> None:
    captured: list[Any] = []

    async def _execute(stmt: Any) -> Any:
        captured.append(stmt)
        res = MagicMock()
        res.scalar.return_value = 3
        return res

    db = AsyncMock()
    db.execute = _execute
    import uuid

    assert asyncio.run(count_students(db, [uuid.uuid4()])) == 3
    sql = str(captured[0].compile(dialect=postgresql.dialect())).lower()
    assert "team_members" in sql
    assert "teams.course_id in" in sql
    assert asyncio.run(count_students(db, [])) == 0


def test_every_scoped_card_names_its_period_and_links_to_the_same_view() -> None:
    from app.api.dashboard.home.stats import _build_stat_cards

    db = AsyncMock()
    res = MagicMock()
    res.scalar.return_value = 10
    db.execute = AsyncMock(return_value=res)
    cards = asyncio.run(_build_stat_cards("admin", [], [], db, {}, period_key="2026-2027-winter"))
    by_id = {c["id"]: c for c in cards}
    assert by_id["statTotalUsers"]["link"].endswith("period=all")
    assert by_id["statTotalStudents"]["link"].endswith("period=2026-2027-winter")
    assert by_id["statTotalStudents"]["scoped"]
    assert by_id["statGroups"]["scoped"]
    content = (TEMPLATES / "partials/dashboard/_content.html").read_text(encoding="utf-8")
    assert "c.scoped and _scope_sel" in content


# -- one component, everywhere a course's period is asked for ---------------


SURFACES = {
    "Create": ("partials/dashboard/_modals.html", "'period': 'createCoursePeriod'"),
    "Import": ("partials/dashboard/_modals.html", "'period': 'importCoursePeriod'"),
    "Edit": ("partials/dashboard/_modals.html", "'period': 'editCoursePeriod'"),
    "Transfer": ("partials/course_settings/_modals.html", "'period': 'transferPeriod'"),
    "Settings": ("course_settings.html", "'period': 'course_period'"),
}


@pytest.mark.parametrize("surface", list(SURFACES))
def test_every_surface_uses_the_period_fields_component(surface: str) -> None:
    rel, marker = SURFACES[surface]
    assert marker in (TEMPLATES / rel).read_text(encoding="utf-8"), surface


def test_no_surface_keeps_a_year_list_a_semester_list_or_a_preset_list() -> None:
    offenders = []
    for path in TEMPLATES.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for bad in ("academic_year_options(", "semester_presets", "'_preset'", "Quick preset"):
            if bad in text and path.name != "academic_period.html":
                offenders.append(f"{path.relative_to(TEMPLATES)}: {bad}")
    assert not offenders, offenders
    comp = (TEMPLATES / "components/academic_period.html").read_text(encoding="utf-8")
    assert "select_field('_period'" in comp
    assert 'name="{{ year_name }}"' in comp
    assert 'name="{{ semester_name }}"' in comp


def test_the_old_private_copies_of_the_rule_are_gone() -> None:
    crud = (JS / "_parts/dashboard/10-course-crud.js").read_text(encoding="utf-8")
    assert "_wireSemesterPresetPickers" not in crud
    assert "_wireAcademicYearAutofill" not in crud
    core = (JS / "_parts/course-settings/00-core.js").read_text(encoding="utf-8")
    assert "initSemesterPreset" not in core
    helpers = (SRC / "api/dashboard/_helpers.py").read_text(encoding="utf-8")
    assert "_suggest_academic_year" not in helpers
    assert "_academic_year_options" not in helpers
    assert not (SRC / "api/dashboard/home/semester.py").exists()


def test_the_period_module_is_in_the_core_bundle_before_its_callers() -> None:
    build = (REPO / "scripts/build_bundle.py").read_text(encoding="utf-8")
    assert build.index('"academic-period.js"') < build.index('"import-stream.js"')
    assert build.index('"academic-period.js"') < build.index('"search-palette.js"')


def test_no_script_builds_a_period_label_by_hand() -> None:
    """Six did - "2026/2027 / winter", English and lowercase on Slovak pages."""
    pattern = re.compile(r"academic_year[^;\n]{0,40}' / '[^;\n]{0,40}semester")
    offenders = []
    for path in JS.rglob("*.js"):
        if ".min." in path.name or "bundle" in path.name or path.parent.name == "pages":
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(JS)))
    assert not offenders, offenders


# -- the selector is a filter like the others ------------------------------


def test_the_selector_wears_the_filter_control() -> None:
    comp = (TEMPLATES / "components/academic_period.html").read_text(encoding="utf-8")
    body = comp.split("{% macro period_selector(", 1)[1].split("{% endmacro %}", 1)[0]
    assert "gl-form-dropdown gl-period-selector" in body
    assert "gl-dropdown-toggle gl-form-dropdown-toggle" in body
    assert "btn btn-secondary" not in body
    assert "data-period-current" in body
    # what "All periods" and "No period" mean is said where they are picked
    assert body.count("data-tippy-content") >= 4


def test_the_users_table_gives_the_period_its_own_column() -> None:
    """In the Role cell, which does not wrap, the badge ran over Status."""
    head = (TEMPLATES / "components/table_heads.html").read_text(encoding="utf-8")
    assert '<col class="col-period' in head
    table = (TEMPLATES / "partials/admin/_users_table.html").read_text(encoding="utf-8")
    role_cell = table.split('<td class="col-role">', 1)[1].split("</td>", 1)[0]
    assert "period_badge" not in role_cell
    assert 'class="col-period' in table
    js = (JS / "pages/admin-users.js").read_text(encoding="utf-8")
    assert "cells[5]" not in js, "the status cell is found by position again"


# -- the attention card is about the reader's courses, not the term shown ---


def test_an_empty_term_does_not_tell_a_student_they_are_not_enrolled() -> None:
    from app.api.dashboard.home.attention import _build_attention_items

    course = SimpleNamespace(id=1, is_active=True, code="ZSI", name="ZSI")
    items = asyncio.run(
        _build_attention_items(
            "student",
            [],
            {},
            AsyncMock(),
            {"user": "s", "gitlab_username": "s"},
            "en",
            active_courses=[],
            archived_courses=[],
            lifecycle_courses=[course],
        )
    )
    assert not any("Not enrolled" in i["title"] for i in items)


def test_a_new_year_suggests_a_transfer_not_a_reactivation() -> None:
    """Reactivating last year's course keeps its old period, so this year's
    students would be filed under last year."""
    text = (SRC / "api/dashboard/home/attention.py").read_text(encoding="utf-8")
    assert "Transfer this course to {period}" in text
    assert "#transfer" in text
    assert "Reactivate and reconfigure this course for {year}" not in text
