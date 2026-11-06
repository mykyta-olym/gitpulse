"""Shared calendars fit narrow screens and follow their scrolling input."""

from __future__ import annotations

import itertools
import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("calendar geometry checks need a running server", allow_module_level=True)


@pytest.fixture(params=list(itertools.product([320, 360, 390, 1440], ["light", "dark"])))
def calendar_page(browser, context_for, live_server: str, request):
    width, theme = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 700},
        has_touch=width < 768,
        is_mobile=width < 768,
        reduced_motion="reduce" if theme == "dark" else "no-preference",
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
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        page.evaluate("() => GP.openModal('createCourseModal')")
        page.wait_for_timeout(450)
        page.locator("#courseSemesterStart").click()
        page.locator(".flatpickr-calendar.open").wait_for()
        page.wait_for_timeout(220)
        yield page, width
        assert not errors, errors


def _assert_grid_fits(page, width: int) -> None:
    bounds = page.locator(".flatpickr-calendar.open").evaluate("""el => {
      const box = el.getBoundingClientRect();
      return {left: box.left, right: box.right, width: box.width, viewport: innerWidth,
        week: el.querySelector('.flatpickr-weekwrapper').getBoundingClientRect().width,
        days: Array.from(el.querySelectorAll('.dayContainer .flatpickr-day')).slice(0, 7)
          .map(day => { const r = day.getBoundingClientRect();
            return {left: r.left, right: r.right, top: r.top, width: r.width}; })};
    }""")
    assert bounds["viewport"] <= width + 1, "the popup enlarged the mobile layout viewport"
    assert bounds["left"] >= -1
    assert bounds["right"] <= width + 1
    assert bounds["width"] <= width - 15
    if width >= 768:
        assert bounds["width"] > 330, "desktop calendars must retain their normal width"
    assert bounds["week"] > 20, "semester weeks must remain visible"
    assert len(bounds["days"]) == 7
    for day in bounds["days"]:
        assert day["left"] >= bounds["left"]
        assert day["right"] <= bounds["right"] + 1
        assert day["width"] > 25
        assert abs(day["top"] - bounds["days"][0]["top"]) < 1


def test_all_weekdays_fit_and_the_last_column_is_selectable(calendar_page):
    page, width = calendar_page
    _assert_grid_fits(page, width)
    before = page.locator("#courseSemesterStart").input_value()
    page.locator(".flatpickr-calendar.open .dayContainer .flatpickr-day").nth(6).click()
    field = page.locator("#courseSemesterStart")
    assert field.input_value() != before
    assert field.evaluate(
        "el => el._flatpickr.formatDate(el._flatpickr.selectedDates[0], 'Y-m-d') === el.value"
    )


def test_calendar_tracks_modal_scroll_without_losing_selection(calendar_page):
    page, width = calendar_page
    before = page.locator("#courseSemesterStart").evaluate(
        "el => ({top: el.getBoundingClientRect().top, value: el.value})"
    )
    page.locator("#createCourseModal .modal-body").evaluate("""el => {
      el.scrollTop = el.scrollTop > 40 ? el.scrollTop - 40 : el.scrollTop + 40;
    }""")
    page.wait_for_timeout(120)
    after = page.locator("#courseSemesterStart").evaluate("""el => {
      const input = el.getBoundingClientRect(), calendar = el._flatpickr.calendarContainer
        .getBoundingClientRect();
      return {top: input.top, value: el.value, open: el._flatpickr.isOpen,
        gap: Math.min(Math.abs(calendar.bottom - input.top + 2),
          Math.abs(calendar.top - input.bottom - 2))};
    }""")
    assert abs(after["top"] - before["top"]) >= 10, "the modal body must actually scroll"
    assert after["gap"] < 2, "the calendar detached from its field"
    assert after["value"] == before["value"]
    assert after["open"]
    _assert_grid_fits(page, width)
    page.keyboard.press("Escape")
    assert page.locator("#courseSemesterStart").evaluate("el => !el._flatpickr.isOpen")
    assert page.locator("#createCourseModal.active").count() == 1


def test_calendar_recovers_its_standard_width_after_resize(calendar_page):
    page, width = calendar_page
    value = page.locator("#courseSemesterStart").input_value()
    previous_width = width
    for next_width in (1440, 320, width):
        page.locator(".flatpickr-calendar.open input.cur-year").focus()
        page.set_viewport_size({"width": next_width, "height": 700})
        page.wait_for_timeout(280)
        if next_width != previous_width:
            assert page.locator("#courseSemesterStart").evaluate("el => !el._flatpickr.isOpen")
            assert page.locator("#courseSemesterStart").evaluate(
                "el => el === document.activeElement"
            )
        page.locator("#courseSemesterStart").evaluate("el => el._flatpickr.close()")
        page.locator("#courseSemesterStart").click()
        page.wait_for_timeout(220)
        _assert_grid_fits(page, next_width)
        assert page.locator("#courseSemesterStart").input_value() == value
        previous_width = next_width


def test_height_only_resize_keeps_the_calendar_and_year_focus(calendar_page):
    page, width = calendar_page
    year = page.locator(".flatpickr-calendar.open input.cur-year")
    year.focus()
    value = page.locator("#courseSemesterStart").input_value()
    page.set_viewport_size({"width": width, "height": 600})
    page.wait_for_timeout(280)
    assert page.locator("#courseSemesterStart").evaluate("el => el._flatpickr.isOpen")
    assert year.evaluate("el => el === document.activeElement")
    assert page.locator("#courseSemesterStart").input_value() == value
    _assert_grid_fits(page, width)


@pytest.mark.parametrize("platform", ["Android", "iPhone"])
def test_native_mobile_date_input_keeps_the_unsaved_edit_guard(
    browser, context_for, live_server: str, platform: str
):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 390, "height": 900},
        is_mobile=True,
        has_touch=True,
        user_agent=f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 Mobile Safari/537.36",
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
        page.evaluate("""() => {
          // Plain date fields without semester weeks use Flatpickr's native
          // mobile branch; it has no body-mounted calendar container.
          document.querySelector('meta[name="semester-start"]')?.remove();
          const input = document.createElement('input');
          input.id = 'nativeDateProbe'; input.name = 'native_date';
          input.type = 'date'; input.value = '2026-10-26';
          document.getElementById('createCourseForm').prepend(input);
          GP.initDatePickers(document);
          GP.openModal('createCourseModal');
        }""")
        assert page.locator("#nativeDateProbe").evaluate(
            "el => el._flatpickr.isMobile && !el._flatpickr.calendarContainer"
        )
        # Playwright fill() assigns native date values with synthetic events.
        # Use a real key so the browser itself emits the date-change events.
        native = page.locator(".flatpickr-mobile")
        native.press("ArrowUp")
        assert native.input_value() != "2026-10-26"
        page.wait_for_timeout(750)
        assert page.evaluate("() => GP.hasUnsavedState()")
        page.locator("#createCourseModal .modal-footer [data-modal-close]").tap()
        page.locator("#gpConfirmDialog.active").wait_for()
        assert not errors, errors
