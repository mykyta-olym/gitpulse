"""Modal focus follows the usable controls, including during state changes."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal focus checks need a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced"])
def focus_page(browser, context_for, live_server: str, request):
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
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.wait_for_function("() => !!window.GP?.openModal")
        yield page
        assert not errors, errors


def test_transfer_starts_on_the_visible_period_control(focus_page, live_server: str):
    page = focus_page
    page.goto(live_server + "/dashboard/admin/courses?period=all")
    rows = page.locator('#adminCoursesTable tr[data-is-active="true"]')
    if not rows.count():
        pytest.skip("an active development course is required")
    course_id = rows.first.get_attribute("data-course-id")
    page.goto(live_server + f"/dashboard/courses/{course_id}/settings")
    page.locator("#btnTransferCourse").click()
    page.wait_for_function("() => document.activeElement.id === 'transferPeriod_toggle'")
    # The 4px required-field validator must never receive initial focus.
    page.keyboard.press("ArrowDown")
    page.wait_for_function("() => document.activeElement.matches('.gl-dropdown-item')")
    page.keyboard.press("Escape")
    page.wait_for_function("() => document.activeElement.id === 'transferPeriod_toggle'")
    assert page.locator("#transferCourseModal.active").count() == 1

    page.locator("#transferCourseModal .modal-close").focus()
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("() => document.activeElement.id") == "btnSubmitTransfer"
    page.keyboard.press("Tab")
    assert page.locator("#transferCourseModal .modal-close").evaluate(
        "el => el === document.activeElement"
    )
    page.keyboard.press("Escape")
    page.wait_for_function("() => document.activeElement.id === 'btnTransferCourse'")


@pytest.mark.parametrize("state", ["negative", "disabled", "fieldset", "inert"])
def test_inactive_controls_cannot_take_autofocus_or_break_tab_wrap(focus_page, state: str):
    page = focus_page
    # Exercise the shared dialog with controls becoming unavailable at either
    # boundary, as happens while a form or its dropdown is closing/loading.
    page.evaluate(
        """state => {
          const body = document.querySelector('#courseMenuModal .modal-body');
          for (const position of ['prepend', 'append']) {
            const control = document.createElement('button');
            control.type = 'button';
            control.tabIndex = state === 'negative' ? -1 : 0;
            control.textContent = 'Unavailable';
            let wrapper = control;
            if (state === 'disabled') control.disabled = true;
            if (state === 'fieldset' || state === 'inert') {
              wrapper = document.createElement(state === 'fieldset' ? 'fieldset' : 'div');
              if (state === 'fieldset') wrapper.disabled = true;
              else wrapper.inert = true;
              wrapper.append(control);
            }
            body[position](wrapper);
          }
          GP.openModal('courseMenuModal');
        }""",
        state,
    )
    first = page.locator("#courseMenuModal .ctx-item-start").first
    page.wait_for_function(
        "() => document.activeElement === "
        "document.querySelector('#courseMenuModal .ctx-item-start')"
    )
    assert first.evaluate("el => el === document.activeElement")
    close = page.locator("#courseMenuModal .modal-close")
    last = page.locator("#courseMenuModal .ctx-item-danger").last
    close.focus()
    page.keyboard.press("Shift+Tab")
    assert last.evaluate("el => el === document.activeElement")
    page.keyboard.press("Tab")
    assert close.evaluate("el => el === document.activeElement")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#courseMenuModal.active')")


def test_file_picker_remains_in_the_keyboard_order(focus_page):
    page = focus_page
    page.evaluate("() => GP.openModal('importConfigCourseModal')")
    page.wait_for_timeout(450)
    page.locator("#import_config_paste_input").focus()
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("() => document.activeElement.id") == "import_config_paste_input_file"
    page.keyboard.press("Tab")
    assert page.evaluate("() => document.activeElement.id") == "import_config_paste_input"
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#importConfigCourseModal.active')")
