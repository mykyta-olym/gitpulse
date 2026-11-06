"""Shared filtering owns its page, URL and row selection across updates."""

from __future__ import annotations

import os
import re
from urllib.parse import parse_qs, urlsplit

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("filter lifecycle races need a running server", allow_module_level=True)


@pytest.fixture(params=[(1440, "normal"), (390, "normal"), (390, "reduced"), (390, "no-gsap")])
def filter_page(browser, context_for, live_server, request):
    width, mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 1000},
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
        is_mobile=width == 390,
        has_touch=width == 390,
    ) as context:
        context.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        if mode == "no-gsap":
            context.route("**/gsap*.js*", lambda route: route.fulfill(body=""))
        page = context.new_page()
        page.bring_to_front()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server + "/dashboard/")
        course = page.locator('a[href^="/dashboard/courses/"]').first.get_attribute("href")
        assert course, "needs a course in the development database"
        yield page, course.split("?")[0]
        assert not errors


def _visit(page, course, base, kind):
    paths = {
        "users": "/dashboard/admin/users",
        "teachers": course + "/teachers",
        "assistant": course + "/assistant",
        "groups": course,
    }
    inputs = {
        "users": "#userSearch",
        "teachers": "#teacherSearch",
        "assistant": "#assistantSearch",
        "groups": "#teamSearchInput",
    }
    page.goto(base + paths[kind])
    page.locator(inputs[kind]).wait_for()
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    return paths[kind], inputs[kind]


@pytest.mark.parametrize("kind", ["users", "teachers", "assistant", "groups"])
def test_fast_navigation_does_not_copy_outgoing_search_into_destination(
    filter_page, live_server, kind
):
    page, course = filter_page
    _, field = _visit(page, course, live_server, kind)
    cached = page.request.get(live_server + "/dashboard/preferences")
    assert cached.ok
    page.route("**/dashboard/preferences", lambda route: route.fulfill(response=cached))
    page.locator(field).fill("obsolete-search")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url("**/dashboard/preferences*")
    page.wait_for_timeout(180)
    assert page.locator("#main-content").first.locator(field).count() == 0
    assert "q" not in parse_qs(urlsplit(page.url).query)


@pytest.mark.parametrize("kind", ["teachers", "assistant", "groups"])
def test_search_timer_does_not_apply_while_outgoing_dom_stays_visible(
    filter_page, live_server, kind
):
    page, course = filter_page
    _, field = _visit(page, course, live_server, kind)
    cached = page.request.get(live_server + "/dashboard/preferences")
    held = []
    page.route("**/dashboard/preferences", lambda route: held.append(route))
    page.locator(field).fill("obsolete-search")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_selector("#main-content.is-navigating")
    page.wait_for_timeout(180)
    assert page.locator(field).count() == 1
    assert "q" not in parse_qs(urlsplit(page.url).query)
    assert len(held) == 1
    held[0].fulfill(response=cached)
    page.wait_for_url("**/dashboard/preferences")


def _activity_fixture(page, base, course):
    response = page.request.get(base + course + "/assistant/activity")
    assert response.ok
    html = page.evaluate(
        """html => {
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const body = doc.querySelector('#assistantActivityTable tbody');
      body.innerHTML = ['push_review','conflict','mr_review','push_review'].map((tool,i) =>
        '<tr data-search="student-' + i + ' group-' + i + ' project-' + i
          + '" data-tool="' + tool + '"><td>Student ' + i + '</td><td>Group ' + i
          + '</td><td>' + tool + '</td><td>Project ' + i
          + '</td><td>Completed</td><td>Reviewed</td><td>2026-10-01</td></tr>').join('');
      return doc.querySelector('#assistantActivityCard').outerHTML;
    }""",
        response.text(),
    )
    page.route(
        "**/assistant/activity*", lambda route: route.fulfill(body=html, content_type="text/html")
    )
    page.locator("#btnRefreshAssistantActivity").click()
    page.wait_for_selector('#assistantActivityTable tr[data-search^="student-0"]')


@pytest.mark.parametrize("kind", ["users", "teachers", "assistant"])
def test_role_or_tool_and_search_use_the_shared_filter(filter_page, live_server, kind):
    page, course = filter_page
    _, field = _visit(page, course, live_server, kind)
    if kind == "assistant":
        _activity_fixture(page, live_server, course)
    tables = {
        "users": ".users-table",
        "teachers": "#courseTeachersTable",
        "assistant": "#assistantActivityTable",
    }
    strips = {
        "users": ".users-role-filter",
        "teachers": ".teachers-role-filter",
        "assistant": ".assistant-tool-filter",
    }
    table = tables[kind]
    rows = page.locator(table + " tbody tr[data-search]").evaluate_all("""rows => rows.map(row => ({
      search:row.dataset.search, role:row.dataset.role, account:row.dataset.account,
      bot:row.dataset.bot === '1', tool:row.dataset.tool
    }))""")
    assert rows
    query = rows[0]["search"].split()[0].upper()
    tabs = page.locator(strips[kind] + " .tab-btn")
    for index in range(tabs.count()):
        value = tabs.nth(index).get_attribute("data-value")
        tabs.nth(index).click()
        for raw_query in ("", query, "no-match-at-all-749"):
            page.locator(field).fill(raw_query)
            page.wait_for_timeout(140)
            expected = []
            for row in rows:
                if kind == "users":
                    matches = (
                        row["bot"]
                        if value == "bot"
                        else (not row["bot"] and (value == "all" or row["role"] == value))
                    )
                elif kind == "teachers":
                    matches = value == "all" or (
                        row["role"] == "owner" if value == "owner" else row["account"] == value
                    )
                else:
                    matches = value == "all" or row["tool"] == value
                if matches and raw_query.lower() in row["search"].lower():
                    expected.append(row["search"])
            result = page.locator(table + " tbody").evaluate("""body => ({
              rows:body._clientPaginator.filteredRows.map(row => row.dataset.search),
              visible:[...body.querySelectorAll('tr[data-search]:not(.d-none)')]
                .map(row => row.dataset.search),size:body._clientPaginator.pageSize
            })""")
            assert result["rows"] == expected
            assert result["visible"] == (
                expected if result["size"] == "all" else expected[: result["size"]]
            )
            params = parse_qs(urlsplit(page.url).query)
            assert params.get("q", [""])[0] == raw_query
            param = "tool" if kind == "assistant" else "role"
            assert params.get(param, ["all"])[0] == value
            if not expected:
                assert page.locator(table).is_hidden()
                assert (
                    page.locator(table + " + .table-filter-empty .table-empty-icon svg").count()
                    == 1
                )


@pytest.mark.parametrize("kind", ["users", "teachers", "assistant", "groups"])
def test_filter_preserves_fragment_history_and_other_parameters(filter_page, live_server, kind):
    page, course = filter_page
    path, field = _visit(page, course, live_server, kind)
    page.evaluate("""() => history.replaceState({spa:1,keep:'filter-state'}, '',
      location.pathname + '?keep=parameter#main-content')""")
    page.locator(field).fill("retained-query")
    page.wait_for_function(
        "() => new URL(location.href).searchParams.get('q') === 'retained-query'"
    )
    assert urlsplit(page.url).fragment == "main-content"
    assert parse_qs(urlsplit(page.url).query)["keep"] == ["parameter"]
    assert page.evaluate("history.state.keep") == "filter-state"
    page.reload()
    page.locator(field).wait_for()
    assert page.locator(field).input_value() == "retained-query"
    assert urlsplit(page.url).path == path
    assert urlsplit(page.url).fragment == "main-content"


def test_group_search_does_not_filter_the_global_search_field(filter_page, live_server):
    page, course = filter_page
    _, field = _visit(page, course, live_server, "groups")
    group = page.locator("#teamsTable tbody tr[data-team-id]").first
    query = group.get_attribute("data-search").split()[0]
    page.locator(field).fill(query)
    page.wait_for_function(
        "query => new URL(location.href).searchParams.get('q') === query", arg=query
    )
    assert page.locator("#searchModalInput").input_value() == ""
    assert page.locator("#teamsTable tbody").evaluate(
        "body => body._clientPaginator.filteredRows.length > 0 && "
        "body._clientPaginator.filteredRows.every(row => "
        "row.dataset.search.includes(document.getElementById('teamSearchInput').value.toLowerCase()))"
    )


@pytest.mark.parametrize("can_edit", [False, True])
@pytest.mark.parametrize("kind", ["course", "team"])
def test_sync_tracking_respects_staff_rights_after_recovery(
    filter_page, live_server, can_edit, kind
):
    page, course = filter_page
    path = course if kind == "course" else "/dashboard/teams/" + os.environ["GITPULSE_E2E_TEAM_ID"]
    response = page.request.get(live_server + path)
    assert response.ok
    html, changes = re.subn(
        rf'(<script\b[^>]*id="gp-{kind}-detail-config"[^>]*>.*?"canEdit":\s*)(true|false)',
        r"\g<1>" + ("true" if can_edit else "false"),
        response.text(),
        flags=re.S,
    )
    assert changes == 1
    page.route(live_server + path, lambda route: route.fulfill(body=html, content_type="text/html"))
    reads = []

    def snapshot(route):
        reads.append(route.request.url)
        data = '{"has_active_sync":false,"teams":[]}'
        if route.request.url.endswith("/sync-stream"):
            route.fulfill(
                content_type="text/event-stream", body="event: complete\ndata: " + data + "\n\n"
            )
        else:
            route.fulfill(content_type="application/json", body=data)

    page.route("**/api/v1/courses/*/sync-stream", snapshot)
    page.route("**/api/v1/courses/*/sync-status", snapshot)
    page.goto(live_server + path)
    page.wait_for_function("() => document.documentElement.hasAttribute('data-gp-ready')")
    if can_edit:
        endpoint = "sync-stream" if kind == "course" else "sync-status"
        page.wait_for_function(
            "endpoint => performance.getEntriesByType('resource')"
            ".some(r => r.name.endsWith('/' + endpoint))",
            arg=endpoint,
        )
    page.evaluate("""() => {
      let hidden = true;
      Object.defineProperty(document, 'hidden', {configurable:true,get:()=>hidden});
      Object.defineProperty(document, 'visibilityState', {
        configurable:true,get:()=>hidden?'hidden':'visible'
      });
      document.dispatchEvent(new Event('visibilitychange'));
      hidden = false;
      document.dispatchEvent(new Event('visibilitychange'));
      document.dispatchEvent(new CustomEvent('gp-health-change',{detail:{current:'down'}}));
      document.dispatchEvent(new CustomEvent('gp-health-change',{detail:{current:'ok'}}));
    }""")
    page.wait_for_timeout(200)
    assert bool(reads) is can_edit


def test_dropdown_filter_preserves_history_and_applies_its_initial_value(filter_page, live_server):
    page, _ = filter_page
    page.goto(live_server + "/dashboard/admin/courses?status=archived")
    page.wait_for_function("() => !!document.querySelector('#courseSearch')._tableFilter")
    rows = "#adminCoursesTable tbody tr[data-search]:not(.d-none)"
    assert page.locator(rows).evaluate_all(
        "rows => rows.every(row => row.dataset.status === 'archived')"
    )
    page.evaluate("""() => {
      history.replaceState({spa:1,keep:'dropdown-state'},'',
        location.pathname+'?status=archived&keep=parameter#main-content');
      document.querySelector('#courseStatusFilter').value = 'active';
    }""")
    page.wait_for_function("() => new URL(location.href).searchParams.get('status') === 'active'")
    assert page.locator(rows).evaluate_all(
        "rows => rows.every(row => row.dataset.status === 'active')"
    )
    assert urlsplit(page.url).fragment == "main-content"
    assert page.evaluate("history.state.keep") == "dropdown-state"


@pytest.mark.parametrize("kind", ["users", "teachers", "assistant", "groups"])
def test_finishing_search_commits_before_the_typing_timer(filter_page, live_server, kind):
    page, course = filter_page
    _, field = _visit(page, course, live_server, kind)
    page.evaluate("""() => history.replaceState({keep:'search-state'}, '',
      location.pathname + '?keep=parameter#main-content')""")
    for query in ("latest query", ""):
        page.locator(field).fill(query)
        page.locator(field).press("Tab")
        assert parse_qs(urlsplit(page.url).query).get("q", [""])[0] == query
        assert parse_qs(urlsplit(page.url).query)["keep"] == ["parameter"]
        assert urlsplit(page.url).fragment == "main-content"
        assert page.evaluate("history.state.keep") == "search-state"


@pytest.mark.parametrize("settled", [False, True])
def test_finishing_search_does_not_reset_a_later_page_selection(filter_page, live_server, settled):
    page, course = filter_page
    _, field = _visit(page, course, live_server, "users")
    page.locator(field).fill(" ")
    if settled:
        page.wait_for_timeout(150)
    page.locator(field).press("Tab")
    page.evaluate("""() => {
      const tbody = document.querySelector('.users-table tbody');
      if (tbody._clientPaginator.totalPages < 2) throw new Error('Needs two pages of users');
      document.querySelector('#paginationControls [data-page="2"]').click();
    }""")
    page.wait_for_timeout(200)
    assert page.locator(".users-table tbody").evaluate("el => el._clientPaginator.currentPage") == 2


def test_activity_refresh_commits_search_and_retires_the_old_timer(filter_page, live_server):
    page, course = filter_page
    _, field = _visit(page, course, live_server, "assistant")
    cached = page.request.get(live_server + course + "/assistant/activity")
    page.route("**/assistant/activity*", lambda route: route.fulfill(response=cached))
    previous = page.locator(field).element_handle()
    page.locator(field).fill("latest search")
    page.evaluate("""() => {
      const button = document.querySelector('#btnRefreshAssistantActivity');
      button.focus(); button.click();
    }""")
    page.wait_for_function("el => !el.isConnected", arg=previous)
    assert previous.evaluate("el => !el.isConnected")
    assert page.locator(field).input_value() == "latest search"
    assert parse_qs(urlsplit(page.url).query)["q"] == ["latest search"]
    page.locator(field).evaluate("""el => {
      el.value = 'replacement search';
      el.dispatchEvent(new Event('input', {bubbles:true}));
      el.dispatchEvent(new Event('change', {bubbles:true}));
    }""")
    previous.evaluate("el => el.dispatchEvent(new Event('change', {bubbles:true}))")
    page.wait_for_timeout(200)
    assert page.locator(field).input_value() == "replacement search"
    assert parse_qs(urlsplit(page.url).query)["q"] == ["replacement search"]


@pytest.mark.parametrize("cancel", [False, True])
def test_pending_search_does_not_remove_a_pressed_pagination_button(
    filter_page, live_server, cancel
):
    page, course = filter_page
    _, field = _visit(page, course, live_server, "users")
    page.locator(field).focus()
    # Hold pointerdown while change commits the search. Rendering here used to
    # remove the pressed arrow, leaving no click when the pointer was released.
    button = page.locator("#paginationControls .pagination-next")
    assert button.is_enabled()
    button.scroll_into_view_if_needed()
    previous = button.element_handle()
    button.evaluate("""el => el.addEventListener('pointerdown', () => {
      window.__pressStarted = true;
      const input = document.getElementById('userSearch');
      input.value = '    ';
      input.dispatchEvent(new Event('input', {bubbles:true}));
      input.dispatchEvent(new Event('change', {bubbles:true}));
    }, {once:true})""")
    button.hover()
    page.mouse.down()
    assert page.evaluate("window.__pressStarted === true")
    page.wait_for_timeout(180)
    assert previous.evaluate("el => el.isConnected")
    if cancel:
        page.mouse.move(0, 0)
    page.mouse.up()
    page.wait_for_timeout(220)
    assert page.locator(".users-table tbody").evaluate("el => el._clientPaginator.currentPage") == (
        1 if cancel else 2
    )
