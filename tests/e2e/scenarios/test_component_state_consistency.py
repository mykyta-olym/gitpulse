"""Shared controls retain their appearance and data across editing and outages."""

from __future__ import annotations

import json
import re

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture
def consistency_context(browser, admin_context, live_server):
    with browser.new_context(
        storage_state=admin_context.storage_state(), service_workers="block"
    ) as context:
        context.add_cookies([{"name": "gp_lang", "value": "en", "url": live_server}])
        yield context


def _course(page, base):
    page.goto(base + "/dashboard/?period=all")
    card = page.locator("#my-courses .course-card[data-course-id]").first
    if not card.count():
        pytest.skip("needs an active course")
    return "/dashboard/courses/" + card.get_attribute("data-course-id")


@pytest.mark.parametrize(("width", "theme"), [(1440, "light"), (390, "dark")])
def test_member_actions_and_priority_badges_inherit_shared_styles(
    consistency_context, live_server, width, theme
):
    page = consistency_context.new_page()
    page.set_viewport_size({"width": width, "height": 1000})
    page.bring_to_front()
    course = _course(page, live_server)
    page.goto(live_server + course)
    team = page.locator('#teamsTable a[href^="/dashboard/teams/"]').first.get_attribute("href")
    page.goto(live_server + team)
    project = page.locator('#projectsTable a[href^="/dashboard/projects/"]').first
    page.goto(live_server + project.get_attribute("href"))
    page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
    page.locator(".project-members-table").scroll_into_view_if_needed()
    groups = page.locator(".project-members-table .gl-row-actions:visible")
    assert groups.count() > 0
    assert groups.evaluate_all("""groups => groups.every(group => {
      const buttons = [...group.querySelectorAll('.btn')].map(b => b.getBoundingClientRect());
      return buttons.slice(1).every((button, i) =>
        Math.abs(button.left - buttons[i].right - 4) < 1);
    })""")
    badges = page.locator(".issues-summary-badges .badge")
    assert badges.count() > 0
    assert badges.evaluate_all("""badges => badges.every(badge => {
      const reference = badge.cloneNode(true);
      document.body.append(reference);
      const read = el => {
        const css = getComputedStyle(el);
        return [css.fontSize, css.fontWeight, css.padding, css.borderWidth,
          css.borderStyle, css.boxShadow].join('|');
      };
      const same = read(badge) === read(reference);
      reference.remove();
      return same;
    })""")


@pytest.mark.parametrize("width", [1440, 390])
def test_week_deadlines_restore_calendar_state_and_clear_the_next_entry(
    consistency_context, live_server, width
):
    page = consistency_context.new_page()
    page.set_viewport_size({"width": width, "height": 1000})
    page.bring_to_front()
    course = _course(page, live_server)
    page.goto(live_server + course + "/settings")
    weeks = [
        {
            "week": 1,
            "label": "First",
            "mr_deadline": "2026-11-02T10:15",
            "expected_checks": ["R01"],
        },
        {"week": 2, "label": "Second", "mr_deadline": "2026-12-16T19:30", "expected_checks": []},
        {"week": 3, "label": "Empty", "expected_checks": []},
    ]
    page.locator('textarea[name="weekly_deadlines"]').evaluate(
        """(el, weeks) => {
          el.value = JSON.stringify(weeks);
          el.dispatchEvent(new Event('change', {bubbles: true}));
        }""",
        weeks,
    )
    rows = page.locator("#weeklyDeadlinesBody tr")
    assert rows.count() == 3
    assert rows.first.locator(".gl-row-actions .btn-secondary").count() == 1
    assert rows.first.locator(".gl-row-actions .btn-danger").count() == 1
    assert (
        rows.first.locator(".badge-sm").evaluate("el => getComputedStyle(el).padding") == "2px 6px"
    )
    for index, expected in [(0, "2026-11-02 10:15"), (1, "2026-12-16 19:30"), (2, "")]:
        rows.nth(index).locator('[data-action="editWeek"]').click()
        field = page.locator("#wdMrDeadline")
        assert field.input_value() == expected
        assert field.evaluate("""el => el._flatpickr.selectedDates.map(date =>
          el._flatpickr.formatDate(date, 'Y-m-d H:i'))""") == ([expected] if expected else [])
        field.click()
        if expected:
            assert field.evaluate("""el => {
              const picker = el._flatpickr;
              return picker.currentMonth === picker.selectedDates[0].getMonth();
            }""")
        if index == 1:
            field.evaluate("el => el._flatpickr.hourElement.focus()")
        page.keyboard.press("Escape")
        assert field.evaluate("el => !el._flatpickr.isOpen")
        assert not page.locator("#weeklyDeadlineModal").evaluate(
            "el => el.classList.contains('closing')"
        )
        if index == 0:
            page.locator("#btnSaveWeeklyDeadline").click()
            saved = json.loads(page.locator('textarea[name="weekly_deadlines"]').input_value())
            assert saved[0]["mr_deadline"] == expected
        else:
            page.evaluate("() => GP.closeModal('weeklyDeadlineModal')")
        page.wait_for_function(
            "() => !document.getElementById('weeklyDeadlineModal').classList.contains('active')"
        )
    page.locator("#btnAddWeeklyDeadline").click()
    assert page.locator("#wdMrDeadline").input_value() == ""
    assert page.locator("#wdWeek").input_value() == "4"
    page.evaluate("() => GP.closeModal('weeklyDeadlineModal')")


@pytest.mark.parametrize("width", [1440, 390])
def test_archived_deadlines_are_locked_in_html_and_after_rendering(
    consistency_context, live_server, width
):
    page = consistency_context.new_page()
    page.set_viewport_size({"width": width, "height": 1000})
    page.bring_to_front()
    page.goto(live_server + "/dashboard/?period=all")
    archived = page.locator('.gl-home-archived a[href^="/dashboard/courses/"]').first
    if not archived.count():
        pytest.skip("needs an archived course")
    url = live_server + archived.get_attribute("href") + "/settings"
    response = page.request.get(url)
    assert response.status == 200
    button = re.search(r'<button\b[^>]*\bid="btnAddWeeklyDeadline"[^>]*>', response.text())
    assert button is not None
    assert re.search(r"\sdisabled(?:\s|=|>)", button.group())
    assert 'data-archived-locked="1"' in button.group()
    page.goto(url)
    assert page.locator("#btnAddWeeklyDeadline").is_disabled()
    assert page.locator('textarea[name="weekly_deadlines"]').evaluate("""el => {
      el.value = JSON.stringify([{week:1, label:'Unsaved test', expected_checks:['R01']}]);
      el.dispatchEvent(new Event('change', {bubbles:true}));
      const buttons = [...document.querySelectorAll('#weeklyDeadlinesBody .btn')];
      return buttons.length === 2 && buttons.every(b =>
        b.disabled && b.dataset.archivedLocked === '1');
    }""")


def test_gitlab_outage_report_keeps_the_banner_without_failed_poll_requests(
    consistency_context, live_server
):
    page = consistency_context.new_page()
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    report = {"status": "ok"}
    calls = []

    def respond(route):
        calls.append(report["status"])
        route.fulfill(content_type="application/json", body=json.dumps(report))

    page.route("**/health/gitlab/status", respond)
    page.route(
        "**/api/v1/observability/status",
        lambda route: route.fulfill(json={"state": "ok", "notices": []}),
    )
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.health")
    page.wait_for_timeout(1700)
    assert calls == ["ok"]
    report["status"] = "unreachable"
    for _ in range(3):
        with page.expect_response("**/health/gitlab/status"):
            page.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(50)
    page.wait_for_function("() => GP.health.isGitLabDown")
    assert page.locator("#healthGlobalBanner").is_visible()
    assert (
        "GitLab server is currently unreachable" in page.locator("#healthBannerText").inner_text()
    )
    report["status"] = "ok"
    page.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))")
    page.wait_for_function("() => !GP.health.isGitLabDown")
    assert page.locator("#healthGlobalBanner").is_hidden()
    assert errors == []
