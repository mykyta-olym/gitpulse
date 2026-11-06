"""The academic period scope across the pages that list more than one course.

`test_academic_period.py` covers naming and ordering a period. This covers what
the pages DO with one: who survives a scope, what a scoped page defaults to,
and the interconnections - a page and its live refresh, and the dialogs that
create a course - that must all agree on the same term.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.models.user import User
from app.services.academic_periods import (
    ALL_PERIODS,
    NO_PERIOD,
    courses_in_scope,
    period_scope_context,
    periods_of,
    scope_students_to_period,
)
from app.utils.academic_period import AcademicPeriod

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
JS = TEMPLATES / "static/js"

SUMMER_25 = AcademicPeriod("2025/2026", "summer")
WINTER_26 = AcademicPeriod("2026/2027", "winter")


def _course(year: str, semester: str, *, active: bool = True) -> Any:
    return SimpleNamespace(academic_year=year, semester=semester, is_active=active)


def _sql(stmt: Any) -> str:
    return str(stmt.compile(dialect=postgresql.dialect())).lower()


def _db_with_courses(*periods: tuple[str, str]) -> Any:
    """A session whose ``SELECT DISTINCT year, semester`` returns ``periods``."""
    result = MagicMock()
    result.all.return_value = list(periods)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    return db


# -- who survives a scope ---------------------------------------------------


def test_all_periods_does_not_touch_the_query() -> None:
    base = select(User)
    assert scope_students_to_period(base, None, scope=ALL_PERIODS) is base


def test_a_period_narrows_students_only() -> None:
    """Admins and teachers are not cohort-bound.

    An admin belongs to no course at all, and a teacher who teaches nothing
    this term is still who you open User Management to find - so the scope is
    "not a student, OR a student who reaches this term".
    """
    sql = _sql(scope_students_to_period(select(User), WINTER_26, scope=WINTER_26.key))
    assert "users.role != " in sql, "non-students must pass through untouched"
    assert sql.count("exists") >= 2, "both routes into a course are checked"


def test_the_team_route_is_how_a_student_actually_reaches_a_course() -> None:
    """``course_memberships`` holds owners and teachers; students come in via teams.

    Measured on the dev data: 0 of the membership rows had role 'student', and
    every student reached their course through Team -> TeamMember -> Student.
    A scope built on memberships alone would have hidden every student.
    """
    sql = _sql(scope_students_to_period(select(User), WINTER_26, scope=WINTER_26.key))
    for table in ("team_members", "students", "teams", "course_memberships"):
        assert table in sql, table
    assert "team_members.is_active" in sql, "a student who left the group is not in its cohort"


def test_a_student_is_matched_by_username_like_the_rest_of_the_app() -> None:
    """Not by ``gitlab_user_id``: the two tables fill it from different sources.

    On the dev data the id join matched 0 rows. The User Info modal, the student
    page and the enrichment pass all match by username - so does this, or the
    table and the modal would disagree about who belongs where.
    """
    sql = _sql(scope_students_to_period(select(User), WINTER_26, scope=WINTER_26.key))
    assert "students.gitlab_username = users.gitlab_username" in sql
    assert "students.gitlab_username = users.username" in sql
    assert "students.gitlab_user_id = users.gitlab_user_id" not in sql


def test_no_period_is_students_who_reach_no_course_at_all() -> None:
    """The one who signed in through GitLab and is not synced into a group yet.

    Invisible in every period otherwise - which is exactly when an admin needs
    to find them.
    """
    sql = _sql(scope_students_to_period(select(User), None, scope=NO_PERIOD))
    assert "users.role = " in sql
    # NOT ((EXISTS membership) OR (EXISTS team)) - the negation covers BOTH
    # routes, so a student reachable by either one is not "unassigned".
    assert "not ((exists" in sql


# -- what a page shows -----------------------------------------------------


def test_courses_in_scope_keeps_the_chosen_term_only() -> None:
    courses = [_course("2025/2026", "summer"), _course("2026/2027", "winter")]
    scope = {
        "selected_key": WINTER_26.key,
        "selected": {"academic_year": "2026/2027", "semester": "winter"},
    }
    assert [c.academic_year for c in courses_in_scope(courses, scope)] == ["2026/2027"]


def test_courses_in_scope_all_keeps_everything() -> None:
    courses = [_course("2025/2026", "summer"), _course("2026/2027", "winter")]
    assert courses_in_scope(courses, {"selected_key": ALL_PERIODS, "selected": None}) == courses


def test_periods_of_skips_a_course_with_a_bad_semester_rather_than_failing() -> None:
    """One hand-edited row must not take the whole page down."""
    periods = periods_of([_course("2026/2027", "winter"), _course("2026/2027", "autumn")])
    assert periods == [WINTER_26]


# -- the default a page opens on --------------------------------------------


def test_the_default_is_the_newest_term_that_has_courses() -> None:
    """Not the calendar's current term - a summer-only deployment is in winter
    for half the year, and every page would open on an empty table."""
    db = _db_with_courses(("2025/2026", "summer"))
    scope = asyncio.run(period_scope_context(db, None))
    assert scope["selected_key"] == SUMMER_25.key


def test_a_reader_opens_on_the_newest_term_they_can_see() -> None:
    """A student whose only course is last summer's must land on last summer.

    Resolved from the whole database, the default would be whichever newer term
    somebody else's course is in, and the student would see an empty dashboard.
    """
    db = _db_with_courses(("2026/2027", "winter"), ("2025/2026", "summer"))
    theirs = [_course("2025/2026", "summer")]
    scope = asyncio.run(period_scope_context(db, None, visible_courses=theirs))
    assert scope["selected_key"] == SUMMER_25.key
    marks = {o["key"]: o["has_courses"] for o in scope["options"]}  # type: ignore[union-attr]
    assert marks[SUMMER_25.key] is True
    assert marks[WINTER_26.key] is False, "another reader's term is empty for this one"


def test_a_page_listing_courses_offers_no_no_period_option() -> None:
    """Every course has a period, so "no period" could never match anything."""
    db = _db_with_courses(("2026/2027", "winter"))
    scope = asyncio.run(period_scope_context(db, None, include_none=False))
    assert scope["include_none"] is False


def test_junk_in_the_url_falls_back_to_the_default() -> None:
    db = _db_with_courses(("2026/2027", "winter"))
    scope = asyncio.run(period_scope_context(db, "../../etc/passwd"))
    assert scope["selected_key"] == WINTER_26.key


def test_a_deep_link_to_an_old_term_is_honoured_and_listed() -> None:
    """A link to a cohort from years ago still opens that cohort."""
    db = _db_with_courses(("2026/2027", "winter"))
    scope = asyncio.run(period_scope_context(db, "2019-2020-summer"))
    assert scope["selected_key"] == "2019-2020-summer"
    assert "2019-2020-summer" in [o["key"] for o in scope["options"]]  # type: ignore[union-attr]


# -- the dialogs that make a course -----------------------------------------


def test_transfer_proposes_the_same_term_next_year() -> None:
    """The source course's OWN term is where it already is.

    That was the old default before the August rollover, and the create API
    refuses a second course with the same code in the same term.
    """
    assert SUMMER_25.next_year() == AcademicPeriod("2026/2027", "summer")
    assert WINTER_26.next_year() == AcademicPeriod("2027/2028", "winter")


def test_every_new_course_dialog_defaults_from_one_place() -> None:
    """Import defaulted to "summer" and Create to "winter" - on the same page.

    Both now take `_np`: the term the reader PICKED, else the calendar's - not
    the term the page merely opened on (its newest term with data, often last
    summer), which pre-filled new courses into a finished term.
    """
    modals = (TEMPLATES / "partials/dashboard/_modals.html").read_text(encoding="utf-8")
    assert "period_scope.explicit and period_scope.selected" in modals
    assert modals.count("_np.academic_year, _np.semester") == 2
    assert "value='summer'" not in modals, "a hard-coded semester default is back"
    assert "suggested_academic_year" not in modals, "the boot-frozen year is back"


def test_the_transfer_dialog_uses_the_next_year_default() -> None:
    modals = (TEMPLATES / "partials/course_settings/_modals.html").read_text(encoding="utf-8")
    assert "next_course_period(course.academic_year, course.semester)" in modals
    assert "value=course.semester" not in modals


def test_the_template_globals_are_computed_per_render() -> None:
    """A string captured at import time freezes at server boot."""
    from app.main import templates

    for name in ("new_course_period", "next_course_period"):
        assert callable(templates.env.globals[name]), name
    nxt = templates.env.globals["next_course_period"]("2025/2026", "summer")
    assert nxt == {"academic_year": "2026/2027", "semester": "summer"}


# -- one wording, everywhere -------------------------------------------------


def test_no_template_builds_a_period_string_by_hand() -> None:
    """Nine did, with two different separators ("/" and "·")."""
    offenders = []
    for path in TEMPLATES.rglob("*.html"):
        if path.name == "academic_period.html":
            continue
        text = path.read_text(encoding="utf-8")
        for bad in ("academic_year ~ ' / '", "academic_year }} / {{", "academic_year }} · {{"):
            if bad in text:
                offenders.append(f"{path.relative_to(TEMPLATES)}: {bad}")
    assert not offenders, offenders


def test_the_user_info_card_translates_the_semester() -> None:
    """It printed the raw column: "2026/2027 · winter", English on a Slovak page."""
    js = (JS / "user-info-modal.js").read_text(encoding="utf-8")
    assert "function periodLabel(" in js
    assert "esc(c.semester" not in js
    assert "esc(dc.semester" not in js


# -- the page and its live refresh agree ------------------------------------


def test_every_live_refresh_asks_for_the_page_period() -> None:
    """The cards, the attention list and the feed are re-fetched on every tab
    focus and sync completion.

    A refresh that scoped differently from the page load changed them under the
    reader: the stats and the feed used to ask for every term at once beside a
    grid of one.
    """
    js = (JS / "_parts/dashboard/20-live-updates.js").read_text(encoding="utf-8")
    for url in ("'/dashboard/stats'", "'/dashboard/attention-items'", "'/dashboard/activity'"):
        assert f"GP.withPagePeriod({url})" in js, url


def test_page_and_every_refresh_scope_with_the_same_function() -> None:
    """The page, the stats, the attention list and the feed: one scoping call."""
    routes = (REPO / "src/app/api/dashboard/home/routes.py").read_text(encoding="utf-8")
    assert routes.count("await _scoped_courses(request, db, reader_courses)") == 4
    assert routes.count("courses_in_scope(") == 1, "a handler scopes on its own again"


def test_the_scope_selector_is_on_every_multi_course_page() -> None:
    for rel in (
        "partials/admin/_users_table.html",
        "admin_courses.html",
        "partials/dashboard/_courses_grid.html",
    ):
        text = (TEMPLATES / rel).read_text(encoding="utf-8")
        assert "period_selector(period_scope)" in text, rel


def test_an_empty_term_keeps_the_selector_on_the_dashboard() -> None:
    """Otherwise the reader is stranded on the empty term with no control to leave it."""
    grid = (TEMPLATES / "partials/dashboard/_courses_grid.html").read_text(encoding="utf-8")
    assert "{% if active_courses or has_courses_elsewhere %}" in grid


# -- on a phone ----------------------------------------------------------------


def test_the_users_selector_sits_beside_search_not_in_the_scrolling_tabs() -> None:
    """At the end of the role tabs it was at x=365 of a 390px screen.

    That row scrolls sideways on a phone, so the control was off-screen - and
    a scrolling container clips a dropdown opened inside it.
    """
    text = (TEMPLATES / "partials/admin/_users_table.html").read_text(encoding="utf-8")
    search = text.split("{% set users_search %}", 1)[1].split("{% endset %}", 1)[0]
    views = text.split("{% set users_views %}", 1)[1].split("{% endset %}", 1)[0]
    assert "period_selector(period_scope)" in search
    assert "period_selector" not in views


def test_every_dropdown_menu_is_kept_inside_the_screen_horizontally() -> None:
    """Menus were anchored to one edge of the toggle and never asked if they fit.

    A toggle at the left of a phone opened its menu 34-51px past the left edge.
    The clamp moves ``left``/``right``, never ``transform`` - the open animation
    owns that, and an inline transform would kill it.
    """
    helpers = (JS / "_parts/core/35-dropdown-menu.js").read_text(encoding="utf-8")
    body = helpers.split("function positionDropdownMenu(menu)", 1)[1].split(
        "\nGP.positionDropdownMenu", 1
    )[0]
    assert "window.innerWidth" in body
    assert "menu.style.left" in body
    assert "style.transform" not in body
    # a leftover clamp is cleared before each measurement
    assert body.index("delete menu.dataset.clampedX") < body.index("getBoundingClientRect")
    # an ancestor that clips its overflow cuts a menu off like the screen does
    assert "overflowX" in body
    # out on one side, it flips to the toggle's other edge before clamping
    assert "toggleRect.left + rect.width <= maxX" in body
    # portaled menus are placed by their own positioner, which clamps too
    assert "data-gl-portal" in body
    portal = (JS / "dropdowns.js").read_text(encoding="utf-8")
    placed = portal.split("function positionMenu(menu, toggle)", 1)[1].split("\n  }", 1)[0]
    assert "window.innerWidth - EDGE - menuW" in placed
