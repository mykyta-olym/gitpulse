"""Initial field population must not swallow real custom-control edits."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("form settling checks need a running server", allow_module_level=True)


@pytest.fixture(params=[1440, 390])
def settings_page(browser, context_for, live_server: str, request):
    width = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        is_mobile=width < 768,
        has_touch=width < 768,
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
        page.goto(live_server + "/dashboard/?period=all")
        course = page.locator("#my-courses .course-card[data-course-id]").first
        assert course.count(), "needs an active development course"
        page.goto(
            live_server
            + "/dashboard/courses/"
            + course.get_attribute("data-course-id")
            + "/settings"
        )
        page.wait_for_function("() => !!document.getElementById('semester_start_date')._flatpickr")
        yield page
        assert not errors, errors


def _restart_settling(page) -> None:
    # Start the guard on the already-rendered form so navigation/scroll timing
    # cannot move this interaction outside its initial 600 ms window.
    page.evaluate("() => GP.initSaveGuard('#courseSettingsForm', '#btnSaveSettings')")


def test_followup_synthetic_input_cannot_adopt_an_early_native_edit(settings_page):
    page = settings_page
    field = page.locator("#course_code")
    field.scroll_into_view_if_needed()
    before = field.input_value()
    _restart_settling(page)
    field.fill(before + "-EDIT")
    field.dispatch_event("input")
    page.wait_for_timeout(750)
    assert page.locator("#btnSaveSettings").is_enabled()
    field.fill(before)
    assert page.locator("#btnSaveSettings").is_disabled()


def test_early_calendar_selection_arms_the_standard_form_save(settings_page):
    page = settings_page
    field = page.locator("#semester_start_date")
    field.scroll_into_view_if_needed()
    _restart_settling(page)
    field.click()
    page.locator(
        ".flatpickr-calendar.open .dayContainer "
        ".flatpickr-day:not(.selected):not(.prevMonthDay):not(.nextMonthDay)"
    ).first.click()
    page.wait_for_timeout(750)
    assert page.locator("#btnSaveSettings").is_enabled()


def test_untouched_programmatic_population_remains_clean(settings_page):
    page = settings_page
    _restart_settling(page)
    page.locator("#course_code").evaluate("""el => {
      el.value += '-POPULATED';
      el.dispatchEvent(new Event('input', {bubbles: true}));
    }""")
    page.wait_for_timeout(750)
    assert page.locator("#btnSaveSettings").is_disabled()
    page.locator("#course_code").fill("USER-EDIT")
    assert page.locator("#btnSaveSettings").is_enabled()


@pytest.mark.parametrize("control", ["stepper", "dropdown"])
def test_early_modal_custom_control_arms_save_and_warns_on_cancel(settings_page, control):
    page = settings_page
    page.evaluate("() => GP.openModal('checkEditorModal')")
    if control == "stepper":
        page.locator('#checkEditorModal [data-number-step="1"]').first.click()
    else:
        dropdown = page.locator("#ceCategory").locator("..")
        dropdown.locator(".gl-form-dropdown-toggle").click()
        dropdown.locator('.gl-dropdown-item[data-value="mr"]').click()
    page.wait_for_timeout(750)
    assert page.locator("#btnSaveCheck").is_enabled()
    page.locator("#checkEditorModal .modal-close").click()
    page.locator("#gpConfirmDialog.active").wait_for()
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_function("() => !document.querySelector('#checkEditorModal.active')")
