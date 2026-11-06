"""A link opens the view it is about, and every term stays reachable.

"2 archived courses, reactivate one" opened Course Management on whatever term
the reader last picked - often not the one those courses are in - and with no
way to see only the archived ones. The support ticket items linked to the
overview with ?status=open, which after it became a table of courses filtered
nothing. The Dashboard counted only ACTIVE courses when deciding whether the
reader "has courses", so once every course was archived its period selector
vanished and the archived courses could not be reached at all.

A filter a link sets is shown in its dropdown AND applied - on a full load and
after an in-page swap, which htmx's attribute settling used to undo.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src/app"
TEMPLATES = SRC / "templates"
JS = TEMPLATES / "static/js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


# -- Attention items ----------------------------------------------------------


def _archived(code: str, year: str, semester: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"id-{code}",
        is_active=False,
        code=code,
        name=code,
        academic_year=year,
        semester=semester,
        archived_at=None,
    )


def _items(courses: list[SimpleNamespace]) -> list[dict]:
    from app.api.dashboard.home.attention import _build_attention_items

    return asyncio.run(
        _build_attention_items(
            "teacher",
            [],
            {},
            AsyncMock(),
            {"user": "t", "gitlab_username": "t"},
            "en",
            active_courses=[],
            archived_courses=[],
            lifecycle_courses=courses,
        )
    )


def test_archived_courses_open_course_management_on_their_term_and_filter() -> None:
    items = _items(
        [_archived("ZSI", "2025/2026", "summer"), _archived("DEVOPS", "2025/2026", "summer")]
    )
    urls = [i["url"] for i in items if "archived" in i["title"]]
    assert urls == ["/dashboard/admin/courses?period=2025-2026-summer&status=archived"]


def test_archived_courses_of_several_terms_open_every_term() -> None:
    items = _items(
        [_archived("ZSI", "2025/2026", "summer"), _archived("ZSI", "2024/2025", "summer")]
    )
    urls = [i["url"] for i in items if "archived" in i["title"]]
    assert urls == ["/dashboard/admin/courses?period=all&status=archived"]


def test_ticket_items_open_the_courses_own_list() -> None:
    src = _read(SRC / "api/dashboard/home/attention.py")
    helper = src.split("def _tickets_url(", 1)[1].split("\n    panels = ", 1)[0]
    assert 'f"/dashboard/support/tickets?course_id={next(iter(courses))}"' in helper
    assert 'url += "&status=open"' in helper
    assert '"/dashboard/support/tickets?period=all"' in helper
    assert '"/dashboard/support/tickets?status=open"' not in src
    assert '"/dashboard/support/tickets?priority=critical"' not in src


# -- The Dashboard ------------------------------------------------------------


def test_an_archived_only_reader_keeps_the_period_selector() -> None:
    routes = _read(SRC / "api/dashboard/home/routes.py")
    assert "has_courses_elsewhere = bool(reader_courses)" in routes
    assert "any(c.is_active for c in reader_courses)" not in routes
    assert '"other_period": other_period' in routes


def test_an_empty_term_says_where_the_courses_are() -> None:
    grid = _read(TEMPLATES / "partials/dashboard/_courses_grid.html")
    assert "t('No active courses in {period}.'" in grid
    assert "t('Your newest courses are in {period}.'" in grid
    assert "action_href='?period=' ~ other_period.key" in grid


# -- Course Management ---------------------------------------------------------


def test_course_management_filters_by_status_from_the_address() -> None:
    page = _read(TEMPLATES / "admin_courses.html")
    assert "'filter-dropdowns': 'status:#courseStatusFilter@data-status'" in page
    assert "value=request.query_params.get('status', '')" in page
    assert "data-status=\"{{ 'active' if course.is_active else 'archived' }}\"" in page
    lifecycle = _read(JS / "_parts/admin-courses/10-lifecycle.js")
    assert "row.dataset.status = isActive ? 'active' : 'archived';" in lifecycle


def test_the_course_identifier_opens_the_course() -> None:
    page = _read(TEMPLATES / "admin_courses.html")
    assert '<a href="/dashboard/courses/{{ course.id }}" class="course-code">' in page


# -- Filters live in the address ------------------------------------------------


def test_a_dropdown_filter_is_written_to_the_address_and_applied_on_load() -> None:
    components = _read(JS / "components.js")
    table_filter = components.split("class TableFilter", 1)[1].split("\nclass ", 1)[0]
    assert "url.searchParams.set(name, dropdown.value)" in table_filter
    assert "const _preset = Object.values(this._activeFilters).some" in table_filter


def test_a_select_renders_its_value_before_alpine_starts() -> None:
    forms = _read(TEMPLATES / "components/forms.html")
    assert 'x-ref="input" value="{{ value }}" :value="selected">' in forms


def test_htmx_does_not_settle_attributes() -> None:
    """Settling gave swapped elements their OLD class first: a selected filter
    blinked, and a row hidden right after the swap came back."""
    progress = _read(JS / "_parts/core/41-htmx-config.js")
    assert "htmx.config.attributesToSettle = [];" in progress


def test_the_ticket_list_filters_in_the_browser_not_twice() -> None:
    support = _read(SRC / "api/dashboard/support.py")
    call = support.split("responses, total_responses = await svc.get_responses(", 1)[1].split(
        ")", 1
    )[0]
    assert "status=status" not in call
    toolbar = _read(TEMPLATES / "partials/support/_tickets_toolbar.html")
    assert "value=(filter_status | default(''))" in toolbar


# -- A disabled control's reason never wraps a hidden input ---------------------


def test_a_hidden_input_is_never_wrapped_for_a_tooltip() -> None:
    """On an archived course the period field's two hidden inputs were wrapped
    in visible boxes and took two thirds of their grid row."""
    guards = _read(JS / "process-action-guards.js")
    fn = guards.split("function showDisabledReason(el, content) {", 1)[1][:600]
    assert "el.type === 'hidden'" in fn


# -- Preferences: the Default period ---------------------------------------------


def _request(query: str = "", cookie: str = "", default: str | None = None):
    from starlette.requests import Request

    headers = [(b"cookie", f"gp_period={cookie}".encode())] if cookie else []
    req = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/dashboard/",
            "query_string": query.encode(),
            "headers": headers,
        }
    )
    if default is not None:
        req.state.default_period = default
    return req


def test_the_default_period_decides_where_a_page_opens() -> None:
    from app.services.academic_periods import ALL_PERIODS, calendar_period, requested_period

    now = calendar_period().key
    picked = f"2025-2026-summer~{now}"
    # the period picked last (the default): the remembered pick
    assert requested_period(_request(cookie=picked)) == "2025-2026-summer"
    assert requested_period(_request(cookie=picked, default="remembered")) == "2025-2026-summer"
    # the others ignore the pick
    assert requested_period(_request(cookie=picked, default="newest")) is None
    assert requested_period(_request(cookie=picked, default="current")) == now
    assert requested_period(_request(cookie=picked, default="all")) == ALL_PERIODS
    # a link that names a period always wins
    assert (
        requested_period(_request("period=2024-2025-winter", picked, "all")) == "2024-2025-winter"
    )


def test_the_default_period_is_a_preference_end_to_end() -> None:
    from app.api.dashboard._helpers import _role_context
    from app.api.dashboard.preferences import PREFERENCE_FIELDS

    field = next(f for f in PREFERENCE_FIELDS if f.name == "default_period")
    assert [c.value for c in field.choices] == ["remembered", "newest", "current", "all"]
    assert field.default == "remembered"
    assert "remember_period" not in {f.name for f in PREFERENCE_FIELDS}
    assert _role_context({})["default_period"] == "remembered"
    deps = _read(SRC / "dependencies.py")
    assert "User.default_period" in deps
    assert '("default_period", default_period)' in deps
    # every dashboard guard - plain, teacher, admin - hands it to the request
    assert deps.count("_apply_period_default(request, session_data)") == 2
    assert deps.count("_apply_account_locale(request, session_data)") == 2
    assert "data-period-default=\"{{ default_period|default('remembered') }}\"" in _read(
        TEMPLATES / "base.html"
    )
    assert "['default_period', 'data-period-default', 'remembered']" in _read(
        JS / "pages/preferences.js"
    )
    period = _read(JS / "academic-period.js")
    assert "if (memoryOff()) { forgetPeriod(); return; }" in period
    assert "'data-period-default'" in period
    prefs = _read(SRC / "api/dashboard/preferences.py")
    assert "response.delete_cookie(PERIOD_COOKIE" in prefs
    migration = _read(REPO / "alembic/versions/021_default_period.py")
    assert "SET default_period = 'newest' WHERE remember_period IS FALSE" in migration
