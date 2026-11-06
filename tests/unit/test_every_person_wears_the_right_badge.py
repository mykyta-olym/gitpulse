"""Every person the app lists says what kind of person they are, and a course
list says which courses are over.

User Management's Period column printed a dash for every teacher, admin and
service account - a reader could not tell "no term" from "every term" - and a
service account's Role cell said "Student", the role GitLab sync happened to
store. The support tickets named people as bare usernames. The Support course
picker put archived courses among the running ones.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
CSS = TEMPLATES / "static/css"


def _read(rel: str) -> str:
    return (TEMPLATES / rel).read_text(encoding="utf-8")


# -- User Management ---------------------------------------------------------


def test_the_period_cell_has_a_badge_for_every_kind_of_person() -> None:
    table = _read("partials/admin/_users_table.html")
    cell = table.split('<td class="col-period', 1)[1].split("</td>", 1)[0]
    # administrators and service accounts are in every term
    assert "_every_term" in cell
    assert "t('All periods')" in cell
    # a teacher's own terms, or "No courses"
    assert "user.role in ('student', 'teacher')" in table
    assert "t('No courses')" in cell
    # a student with no group yet: the selector's own "No period"
    assert "t('No period')" in cell
    assert '<span class="muted">-</span>' not in cell, "the dash is back"


def test_a_service_account_is_not_shown_as_a_student() -> None:
    table = _read("partials/admin/_users_table.html")
    role_cell = table.split('<td class="col-role">', 1)[1].split("</td>", 1)[0]
    assert "user.is_bot" in role_cell
    assert "t('Bot')" in role_cell


# -- Support -----------------------------------------------------------------


def test_both_support_pages_list_courses_with_one_component() -> None:
    """Support's first step and the Support Tickets overview are the same list
    - the same table, archived courses after the active ones, each marked."""
    table = _read("partials/support/_course_table.html")
    assert (
        "(courses | selectattr('is_active') | list) + (courses | rejectattr('is_active') | list)"
        in table
    )
    assert "status_indicator('muted', t('Archived'))" in table
    form = _read("support_form.html")
    tickets = _read("support_tickets.html")
    assert "support_course_table('supportCoursesTable'" in form
    assert "mine=true" in form
    assert "support_course_table('ticketCoursesTable'" in tickets
    assert not (TEMPLATES / "partials/support/_course_picker.html").exists()


def test_tickets_say_what_kind_of_person_each_name_is() -> None:
    listing = _read("partials/support/_tickets_content.html")
    detail = _read("partials/support/_ticket_detail_content.html")
    assert listing.count("person_badge(") == 2
    # The submitter's header and the shared comment macro. The former duplicate
    # participant strip no longer repeats these people above the request.
    assert detail.count("person_badge(") == 2
    assert "gh-role-" not in detail
    badges = _read("components/badges.html")
    macro = badges.split("{% macro person_badge(", 1)[1].split("{%- endmacro %}", 1)[0]
    assert "info.is_bot" in macro
    assert "role_badge(info.role" in macro


def test_people_are_looked_up_by_either_username_in_one_query() -> None:
    from app.api.dashboard._helpers import people_by_name

    result = MagicMock()
    result.all.return_value = [
        ("demo.ucitel", "demo.ucitel", "teacher", False, "https://gl/a.png"),
        ("x", "project_991_bot", "student", True, None),
    ]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    found: dict[str, Any] = asyncio.run(
        people_by_name(db, ["demo.ucitel", "project_991_bot", None, "ghost"])
    )
    assert found["demo.ucitel"] == {
        "role": "teacher",
        "is_bot": False,
        "avatar_url": "https://gl/a.png",
    }
    assert found["project_991_bot"]["avatar_url"] == ""
    assert found["project_991_bot"]["is_bot"] is True
    assert "ghost" not in found
    assert db.execute.await_count == 1
    assert asyncio.run(people_by_name(db, [None, ""])) == {}


# -- the card component --------------------------------------------------------


def test_a_card_header_does_not_spread_its_own_items_apart() -> None:
    """With `space-between`, a header with no right-hand part put the icon at
    the left, the title in the middle and the count at the far right."""
    cards = (CSS / "cards.css").read_text(encoding="utf-8")
    header = cards.split(".card-header {", 1)[1].split("}", 1)[0]
    assert "justify-content: flex-start" in header
    assert "space-between" not in header.split("justify-content", 1)[1].split(";", 1)[0]


def test_a_collapsed_disclosure_has_no_dead_strip_under_its_header() -> None:
    """A closed <details> keeps its content slot as a flex item, so the shell's
    gap sat under the header: 9px below "Raw Check Details", 5px above."""
    cards = (CSS / "cards.css").read_text(encoding="utf-8")
    assert "details.card {\n  row-gap: 0;" in cards.replace("\r\n", "\n")
    assert "details.card > summary + * {" in cards
