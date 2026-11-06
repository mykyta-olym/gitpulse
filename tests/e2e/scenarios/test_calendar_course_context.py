"""Calendar weeks follow the incoming course and the date pair being edited."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("calendar context checks need a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def context_page(browser, context_for, live_server: str, request):
    mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 900},
        has_touch=mode != "desktop",
        is_mobile=mode != "desktop",
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
    ) as ctx:
        ctx.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.method in {"GET", "HEAD"}
                else route.fulfill(status=204)
            ),
        )
        if mode == "no-gsap":
            ctx.route(
                "**/gsap*.js*", lambda r: r.fulfill(body="", content_type="application/javascript")
            )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda msg: errors.append(msg.text) if "Flatpickr init failed" in msg.text else None,
        )
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.wait_for_function("() => !!window.GP?.navigateTo")
        yield page
        assert not errors, errors


def _navigate(page, live_server: str, name: str, start: str, body: str = "") -> None:
    url = live_server + "/dashboard/calendar-context-" + name
    meta = f'<meta name="semester-start" content="{start}">' if start else ""
    body = (
        body
        or """
      <input type="date" id="contextDate" name="context_date" value="2026-09-21" aria-label="Date">
      <input type="datetime-local" id="contextTime" name="context_time" aria-label="Deadline">
      <div class="modal-backdrop" id="contextModal" aria-hidden="true">
        <div class="modal"><div class="modal-body">
          <input class="datetime-picker" id="contextModalTime" name="context_modal_time"
            aria-label="Modal deadline">
        </div></div>
      </div>
    """
    )
    html = (
        "<!doctype html><html><head><title>Calendar context</title>"
        + meta
        + '</head><body><main id="main-content">'
        + body
        + '</main><div id="gp-modals"></div></body></html>'
    )
    page.route(url, lambda route: route.fulfill(body=html, content_type="text/html"))
    page.evaluate("url => GP.navigateTo(url)", url)
    page.wait_for_url(url)
    page.wait_for_function(
        "() => !document.querySelector('#main-content.is-navigating, #main-content.is-arriving')"
    )


def _weeks(page):
    return page.evaluate("""() => ['contextDate', 'contextTime', 'contextModalTime'].map(id => {
      const picker = document.getElementById(id)._flatpickr;
      return {weeks: picker.config.weekNumbers,
        label: picker.config.getWeek(new Date(2026, 8, 21))};
    })""")


def test_initial_navigation_uses_the_incoming_course_for_every_calendar(
    context_page, live_server: str
):
    page = context_page
    page.evaluate("() => document.querySelector('meta[name=\"semester-start\"]')?.remove()")
    _navigate(page, live_server, "initial", "2026-09-21")
    assert _weeks(page) == [{"weeks": True, "label": "1"}] * 3
    assert page.locator("body > #contextModal[data-gp-page-modal]").count() == 1
    # Check the rendered week column as well as the vendor configuration.
    page.locator("#contextDate").click()
    calendar = page.locator(".flatpickr-calendar.open")
    assert calendar.locator(".flatpickr-weekwrapper").is_visible()
    assert "1" in calendar.locator(".flatpickr-weeks .flatpickr-day").all_text_contents()


def test_switching_courses_and_leaving_a_course_replaces_the_week_context(
    context_page, live_server: str
):
    page = context_page
    for name, start, weeks, label in [
        ("winter", "2026-09-21", True, "1"),
        ("summer", "2026-02-16", True, "S19"),
        ("neutral", "", False, "39"),
        ("winter-return", "2026-09-21", True, "1"),
    ]:
        _navigate(page, live_server, name, start)
        assert _weeks(page) == [{"weeks": weeks, "label": label}] * 3


@pytest.mark.parametrize("wrapped_in_form", [False, True])
def test_each_period_end_uses_its_own_start_and_updates_live(
    context_page, live_server: str, wrapped_in_form: bool
):
    page = context_page
    body = """
      <div data-period-fields data-period-roles='{"start":"firstStart","end":"firstEnd"}'>
        <input class="date-picker" id="firstStart" name="semester_start_date" value="2026-09-21">
        <input class="date-picker" id="firstEnd" name="semester_end_date" value="2027-02-12">
      </div>
      <div data-period-fields data-period-roles='{"start":"transferStart","end":"transferEnd"}'>
        <input class="date-picker" id="transferStart" name="semester_start_date" value="2027-02-08">
        <input class="date-picker" id="transferEnd" name="semester_end_date" value="2027-06-25">
      </div>
    """
    if wrapped_in_form:
        body = "<form>" + body + "</form>"
    _navigate(page, live_server, "pairs", "2026-02-16", body)
    labels = page.evaluate("""() => ['first', 'transfer'].map(prefix => {
      const start = document.getElementById(prefix + 'Start');
      return document.getElementById(prefix + 'End')._flatpickr.config
        .getWeek(start._flatpickr.selectedDates[0]);
    })""")
    assert labels == ["1", "1"]
    label_after_edit = page.evaluate("""() => {
      const start = document.getElementById('transferStart');
      start._flatpickr.setDate('2027-02-15', true);
      return document.getElementById('transferEnd')._flatpickr.config
        .getWeek(start._flatpickr.selectedDates[0]);
    }""")
    assert label_after_edit == "1"


def test_late_fragment_uses_the_current_course_without_reinitialising_existing_pickers(
    context_page, live_server: str
):
    page = context_page
    _navigate(page, live_server, "fragment-host", "2026-02-16")
    page.evaluate("""() => {
      window.__contextPicker = document.getElementById('contextDate')._flatpickr;
      const host = document.createElement('div'); host.id = 'contextFragment';
      document.getElementById('main-content').append(host);
    }""")
    url = live_server + "/dashboard/calendar-context-late-fragment"
    page.route(
        url,
        lambda route: route.fulfill(
            body='<input id="fragmentDate" name="fragment_date" type="date" value="2026-09-21">',
            content_type="text/html",
        ),
    )
    page.evaluate(
        "url => htmx.ajax('GET', url, {target: '#contextFragment', swap: 'innerHTML'})", url
    )
    assert page.locator("#fragmentDate").evaluate("""el => el._flatpickr.config.weekNumbers
      && el._flatpickr.config.getWeek(new Date(2026, 8, 21)) === 'S19'""")
    assert page.evaluate(
        "() => __contextPicker === document.getElementById('contextDate')._flatpickr"
    )
