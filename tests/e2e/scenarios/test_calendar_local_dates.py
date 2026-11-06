"""Semester dates retain their calendar day in every browser time zone."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("calendar date checks need a running server", allow_module_level=True)


@pytest.fixture(
    params=["Europe/Bratislava", "America/New_York", "Pacific/Honolulu", "Pacific/Kiritimati"]
)
def date_page(browser, context_for, live_server: str, request, viewport_width):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        timezone_id=request.param,
        viewport={"width": viewport_width, "height": 900},
        has_touch=viewport_width < 768,
        is_mobile=viewport_width < 768,
    ) as ctx:
        ctx.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.method in {"GET", "HEAD"}
                else route.fulfill(status=204)
            ),
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
        url = live_server + "/dashboard/calendar-local-dates"
        page.route(
            url,
            lambda route: route.fulfill(
                content_type="text/html",
                body="""<!doctype html><html><head><title>Local dates</title>
                  <meta name="semester-start" content="2032-03-01"></head><body>
                  <main id="main-content"><form>
                    <div data-period-fields>
                      <label for="semesterStart">Start</label>
                      <input class="date-picker" id="semesterStart" name="semester_start_date"
                        value="2032-03-01">
                      <label for="semesterEnd">End</label>
                      <input class="date-picker" id="semesterEnd" name="semester_end_date">
                    </div>
                    <label for="deadline">Deadline</label>
                    <input class="datetime-picker" id="deadline" name="deadline">
                  </form></main><div id="gp-modals"></div></body></html>""",
            ),
        )
        page.evaluate("url => GP.navigateTo(url)", url)
        page.wait_for_url(url)
        page.wait_for_function(
            "() => !document.querySelector("
            "'#main-content.is-navigating, #main-content.is-arriving')"
        )
        yield page
        assert not errors, errors


@pytest.fixture(params=[390, 1440])
def viewport_width(request):
    return request.param


def test_teaching_and_exam_weeks_use_local_days_across_daylight_saving(date_page):
    labels = date_page.evaluate("""() => {
      const start = document.getElementById('semesterStart')._flatpickr;
      const end = document.getElementById('semesterEnd')._flatpickr;
      const deadline = document.getElementById('deadline')._flatpickr;
      return ['2032-02-23', '2032-03-01', '2032-03-07', '2032-03-08',
        '2032-03-14', '2032-03-15', '2032-03-28', '2032-03-29',
        '2032-05-30', '2032-05-31'].map(value => {
          const date = flatpickr.parseDate(value, 'Y-m-d');
          return [start, end, deadline].map(picker => picker.config.getWeek(date));
        });
    }""")
    assert labels == [[label] * 3 for label in ["9", "1", "1", "2", "2", "3", "4", "5", "13", "S1"]]


def test_empty_deadline_opens_in_the_future_semester_month_without_changing_value(date_page):
    date_page.locator("#deadline").click()
    result = date_page.locator("#deadline").evaluate("""input => {
      const picker = input._flatpickr;
      return {year: picker.currentYear, month: picker.currentMonth, value: input.value,
        weeks: [...picker.calendarContainer.querySelectorAll('.flatpickr-weeks .flatpickr-day')]
          .map(el => el.textContent)};
    }""")
    assert result == {
        "year": 2032,
        "month": 2,
        "value": "",
        "weeks": ["1", "2", "3", "4", "5", "6"],
    }
    assert date_page.locator(".flatpickr-calendar.open .flatpickr-weekwrapper").is_visible()


def test_editing_the_start_renumbers_its_pair_without_a_time_zone_shift(date_page):
    date_page.locator("#semesterStart").click()
    date_page.locator('.flatpickr-calendar.open .flatpickr-day[aria-label="March 8, 2032"]').click()
    date_page.locator("#semesterEnd").click()
    result = date_page.locator("#semesterEnd").evaluate("""input => {
      const picker = input._flatpickr;
      picker.jumpToDate('2032-03-08');
      return {start: document.getElementById('semesterStart').value,
        label: picker.config.getWeek(flatpickr.parseDate('2032-03-08', 'Y-m-d')),
        weeks: [...picker.calendarContainer.querySelectorAll('.flatpickr-weeks .flatpickr-day')]
          .map(el => el.textContent)};
    }""")
    assert result == {"start": "2032-03-08", "label": "1", "weeks": ["10", "1", "2", "3", "4", "5"]}
