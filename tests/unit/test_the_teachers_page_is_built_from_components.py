"""The Teachers page is a list page like every other one.

It had a private copy of the component set (`.invite-bar`, `.members-panel`,
`.empty-state-compact`, `.text-btn` and twenty rules for them), and after those
went it was still a page of its own: an Alpine app that drew the rows from an
inlined list after first paint, sorted, filtered and counted them itself, had
no search and no pagination, and drafted changes behind a Save bar no other
list has. Reported as "this page differs from the others, things are missing,
and it blinks": the first frame was a header over an empty table, then the
rows, the count, the sort arrow, the active tab and the Remove all button all
changed.

Now it is the Users page's shape: the server renders the rows, the shared
ClientPaginator / TableFilter / FilterPills / sortable-table.js work them, the
card header holds the actions, the controls band the search and the tabs, and
a change applies when it is made, as on GitLab's members page.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "src/app/templates/partials/course/_teachers_content.html"
JS = ROOT / "src/app/templates/static/js/pages/course-teachers.js"
CSS = ROOT / "src/app/templates/static/css/pages"
TOUR = ROOT / "src/app/templates/static/js/_parts/tours/20-courses.js"

#: Private markup that a shared component already draws.
RETIRED = (
    "invite-bar",
    "invite-bar-inner",
    "invite-search-box",
    "invite-hint",
    "members-panel",
    "members-panel-header",
    "empty-state-compact",
    "text-btn",
)


@pytest.fixture(scope="module")
def page() -> str:
    src = PAGE.read_text(encoding="utf-8")
    return re.sub(r"\{#.*?#\}", "", src, flags=re.S)  # the notes name what is gone


def test_the_page_calls_the_components(page: str) -> None:
    for macro in (
        "card(",
        "table_controls(",
        "search_input(",
        "filter_tabs(",
        "data_table(",
        "sortable_header(",
        "pagination_controls(",
        "empty_state(",
        "person_typeahead(",
        "modal(",
    ):
        assert macro in page, f"the page stopped using {macro.rstrip('(')}"


def test_the_rows_are_the_servers(page: str) -> None:
    """Alpine is left only where it is a component's own: the typeahead in the
    Add teacher dialog. The card - header, controls, table - has none."""
    assert "{% for inst in _listed %}" in page
    card = page.split("{% call card(", 1)[1].split("{% endcall %}\n\n", 1)[0]
    for alpine in ("x-for=", "x-data", "x-show", "x_click=", "x_class=", "x_bind"):
        assert alpine not in card, f"{alpine} - the table is drawn or worked by Alpine again"
    assert "teacherManager" not in page
    table = page.split("{% call data_table(", 1)[1].split(")", 1)[0]
    assert "sortable=true" in table, "the shared sorter no longer works the table"


def test_each_control_sits_with_its_own_kind(page: str) -> None:
    """The card header carries what you DO (add, remove all); the controls band
    carries how you NARROW (search, tabs); the bar under the table the count."""
    actions = page.split("{% set teachers_actions %}", 1)[1].split("{% endset %}", 1)[0]
    assert "btnAddTeacher" in actions
    assert "Remove all restrictions" in actions
    assert "search_input(" not in actions
    assert "filter_tabs(" not in actions
    assert "table_controls(search=teachers_search, filters=teachers_views)" in page
    assert "table_count(" not in page, (
        "a header count next to a pager that already says Showing X-Y of Z"
    )


def test_the_shared_components_work_the_table() -> None:
    js = JS.read_text(encoding="utf-8")
    for component in ("new ClientPaginator(", "new TableFilter(", "new FilterPills("):
        assert component in js, f"the page no longer uses {component}"
    for private in ("sortTeachers", "filterTeachers", "updateCount", "isDirty"):
        assert private not in js, f"{private} - a private copy of what a component does"


def test_a_change_applies_when_it_is_made() -> None:
    """No draft and no Save bar: the list goes to the endpoint the form always
    posted to, asking for the outcome as JSON, and the page comes back."""
    page = PAGE.read_text(encoding="utf-8")
    assert "settings-sticky-footer" not in page
    assert "btnSaveTeachers" not in page
    js = JS.read_text(encoding="utf-8")
    assert "headers: { Accept: 'application/json' }" in js
    assert "GP.reloadKeepScroll()" in js
    route = (ROOT / "src/app/api/dashboard/admin/course_teachers.py").read_text(encoding="utf-8")
    assert 'JSONResponse({"error": "conflict"}, status_code=409)' in route
    assert 'JSONResponse({"error": "no_owner"}, status_code=422)' in route
    assert 'JSONResponse({"ok": True})' in route


def test_the_role_badge_leads_its_column(page: str) -> None:
    """ "you" written first pushed the reader's own Admin badge out of line."""
    cell = page.split('<td class="col-teacher-account"', 1)[1].split("</td>", 1)[0]
    assert cell.find("role_badge(") < cell.find("current_username"), (
        "the 'you' marker is written before the role badge again"
    )


def test_the_first_frame_is_already_filtered(page: str) -> None:
    """A link to ?role=owner or ?q= opens on that view, not on All switching
    after paint - as on the Users page."""
    assert "request.query_params.get('role')" in page
    assert "request.query_params.get('q')" in page
    assert "active=_initial_role" in page
    assert "pagination_controls(total=_shown.n" in page


@pytest.mark.parametrize("klass", RETIRED)
def test_no_private_copy_of_a_component(page: str, klass: str) -> None:
    assert klass not in page, (
        f"`{klass}` is back in the markup - a second drawing of something the "
        "component set already provides"
    )


@pytest.mark.parametrize("klass", RETIRED)
def test_the_rules_went_with_the_markup(klass: str) -> None:
    """Orphaned CSS outlives the HTML that justified it and nothing removes it."""
    admin = (CSS / "admin.css").read_text(encoding="utf-8")
    live = [ln for ln in admin.splitlines() if re.match(rf"\s*\.{klass}\b", ln)]
    assert not live, f"pages/admin.css still styles .{klass}: {live[:2]}"


def test_what_the_page_still_owns_is_only_its_columns() -> None:
    """The typeahead and the identity cell are components; what is this page's
    own is what its columns need."""
    course = (CSS / "course.css").read_text(encoding="utf-8")
    shared = CSS.parent
    forms = (shared / "forms.css").read_text(encoding="utf-8")
    tables = (shared / "tables.css").read_text(encoding="utf-8")
    for gone in ("invite-dropdown", "invite-search-wrap", "teacher-identity", "teacher-add-row"):
        assert not re.search(rf"^\.{gone}", course, re.M), (
            f".{gone} is back in the page's own stylesheet"
        )
    typeahead = (ROOT / "src/app/templates/components/typeahead.html").read_text(encoding="utf-8")
    assert 'class="gl-dropdown-menu"' in typeahead, (
        "the typeahead's menu is not the shared dropdown"
    )
    assert 'class="gl-dropdown-item"' in typeahead
    assert not re.search(r"^\.typeahead-(menu|item|empty|more)", forms, re.M), (
        "the typeahead draws its own menu again"
    )
    assert re.search(r"^\.table-identity", tables, re.M), "the identity cell is page-private again"
    assert re.search(r"^\.col-teacher", course, re.M), ".col-teacher should stay with the page"


def test_the_tour_can_still_find_its_steps(page: str) -> None:
    assert "id='btnAddTeacher'" in page
    assert "'tour': 'add-teacher'" in page
    assert 'data-tour="teacher-row"' in page
    tour = TOUR.read_text(encoding="utf-8")
    assert "add-teacher" in tour
    assert "teacher-row" in tour
