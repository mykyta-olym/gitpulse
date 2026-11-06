"""Shared form selects retain focus and selection across keyboard and API updates."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("select interactions need a running server", allow_module_level=True)


@pytest.mark.parametrize(
    ("width", "mode"), [(1440, "normal"), (390, "normal"), (390, "reduced"), (390, "no-gsap")]
)
def test_keyboard_selection_and_escape_leave_the_parent_dialog_open(
    context_for, live_server: str, width: int, mode: str
) -> None:
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    if mode == "reduced":
        page.emulate_media(reduced_motion="reduce")
    if mode == "no-gsap":
        page.route(
            "**/gsap-3.15.0.min.js*",
            lambda route: route.fulfill(body="", content_type="application/javascript"),
        )
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.openModal")
    assert page.evaluate("() => !!window.gsap") is (mode != "no-gsap")
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.wait_for_timeout(500)
    toggle = page.locator("#createCoursePeriod_toggle")
    root = page.locator("#createCoursePeriod_options")
    selected = page.locator("#createCoursePeriod").input_value()

    toggle.focus()
    page.keyboard.press("ArrowDown")
    page.wait_for_function("() => document.activeElement.matches('.gl-dropdown-item')")
    assert page.evaluate("() => document.activeElement.dataset.value") == selected
    page.keyboard.press("End")
    page.wait_for_function(
        "() => document.activeElement === "
        "document.querySelector('#createCoursePeriod_options li:last-child button')"
    )
    page.keyboard.press("ArrowDown")
    page.wait_for_function(
        "() => document.activeElement === "
        "document.querySelector('#createCoursePeriod_options button')"
    )
    page.keyboard.press("ArrowUp")
    page.keyboard.press("Home")
    page.wait_for_function(
        "() => document.activeElement === "
        "document.querySelector('#createCoursePeriod_options button')"
    )
    page.keyboard.press("Escape")
    page.wait_for_function(
        "() => document.activeElement === document.getElementById('createCoursePeriod_toggle')"
    )
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.locator("#createCourseModal.active").count() == 1
    assert page.locator("#createCoursePeriod").input_value() == selected
    assert root.evaluate("el => el.inert")

    # A second Escape now belongs to the parent, since the list is closed.
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#createCourseModal.active')")
    assert not errors


@pytest.mark.parametrize("width", [1440, 390])
def test_late_options_track_selection_and_hidden_options_cannot_keep_focus(
    context_for, live_server: str, width: int
) -> None:
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.openModal")
    page.evaluate("() => GP.openModal('importGitlabCourseModal')")
    page.wait_for_timeout(500)
    field = page.locator("#importTargetCourseId")
    toggle = page.locator("#importTargetCourseId_toggle")
    menu = page.locator("#importTargetCourseId_options")
    page.evaluate("""() => {
      const field = document.getElementById('importTargetCourseId');
      window.__selectChanges = 0;
      field.addEventListener('change', () => window.__selectChanges++);
      field.addOptions([[42, 'Late course'], ['43', 'Other late course']]);
      field.addOptions([['44', 'A very long imported course name ' + 'branch_'.repeat(15)]]);
    }""")
    toggle.click()
    menu.locator('button[data-value="42"]').click()
    page.wait_for_timeout(250)
    assert field.input_value() == "42"
    assert menu.locator('button[data-value="42"]').evaluate("el => el.classList.contains('active')")
    assert (
        menu.locator('button[data-value="42"]').locator("..").get_attribute("aria-selected")
        == "true"
    )
    assert toggle.evaluate("el => el === document.activeElement")
    assert page.evaluate("() => window.__selectChanges") == 1

    toggle.click()
    menu.wait_for(state="visible")
    assert menu.locator('button[data-value="44"]').evaluate(
        "el => el.clientWidth > 0 && el.scrollWidth <= el.clientWidth + 1"
    ), "a long option label extends beyond the menu instead of wrapping"
    page.keyboard.press("Escape")

    # External writes use the same state and create a visible option if needed.
    field.evaluate("el => { el.value = 'archived-course'; }")
    page.wait_for_timeout(50)
    assert (
        menu.locator('button[data-value="42"]').locator("..").get_attribute("aria-selected")
        == "false"
    )
    assert (
        menu.locator('button[data-value="archived-course"]')
        .locator("..")
        .get_attribute("aria-selected")
        == "true"
    )
    toggle.focus()
    page.keyboard.press("ArrowUp")
    page.wait_for_function("() => document.activeElement.dataset.value === 'archived-course'")
    page.keyboard.press("Tab")
    page.wait_for_timeout(250)
    assert toggle.get_attribute("aria-expanded") == "false"
    assert menu.evaluate("el => el.inert && !el.contains(document.activeElement)")
    assert page.locator("#importGitlabCourseModal.active").count() == 1


def test_reopening_a_dialog_does_not_reopen_its_last_dropdown(
    context_for, live_server: str
) -> None:
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.openModal")
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.wait_for_timeout(500)
    toggle = page.locator("#createCoursePeriod_toggle")
    toggle.click()
    page.evaluate("() => GP.closeModal('createCourseModal')")
    page.wait_for_function("() => !document.querySelector('#createCourseModal.active')")
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.wait_for_timeout(500)
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.locator("#createCoursePeriod_options").evaluate("el => el.inert")


@pytest.mark.parametrize("width", [1440, 390])
def test_early_select_choice_does_not_become_the_saved_baseline(
    context_for, live_server: str, width: int
) -> None:
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.openModal")
    initial = page.locator("#createCoursePeriod").input_value()
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.wait_for_timeout(110)
    page.locator("#createCoursePeriod_toggle").focus()
    page.keyboard.press("ArrowDown")
    page.wait_for_function("() => document.activeElement.matches('.gl-dropdown-item')")
    page.keyboard.press("ArrowDown")
    page.wait_for_function("value => document.activeElement.dataset.value !== value", arg=initial)
    page.keyboard.press("Enter")
    page.wait_for_function(
        "value => document.getElementById('createCoursePeriod').value !== value", arg=initial
    )
    page.wait_for_timeout(800)
    assert page.evaluate("() => GP.hasUnsavedState()")
    page.locator("#createCourseModal .modal-close").click()
    page.wait_for_function("() => document.querySelector('#gpConfirmDialog.active')")


@pytest.fixture(params=[(1440, "normal"), (390, "normal"), (390, "reduced"), (390, "no-gsap")])
def table_select_page(context_for, live_server: str, request):
    width, mode = request.param
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    if mode == "reduced":
        page.emulate_media(reduced_motion="reduce")
    if mode == "no-gsap":
        page.route(
            "**/gsap-3.15.0.min.js*",
            lambda route: route.fulfill(body="", content_type="application/javascript"),
        )
    page.goto(live_server + "/dashboard/admin/users")
    page.wait_for_function("() => !!document.querySelector('.users-table')?._clientPaginator")
    page.locator(".gl-page-size-dropdown .gl-dropdown-toggle").first.scroll_into_view_if_needed()
    yield page
    assert not errors, errors


def test_table_select_keyboard_wraps_selects_and_restores_focus_after_render(
    table_select_page,
) -> None:
    page = table_select_page
    toggle = page.locator(".gl-page-size-dropdown .gl-dropdown-toggle").first
    selected = str(
        page.locator(".users-table").evaluate("table => table._clientPaginator.pageSize")
    )
    toggle.focus()
    page.keyboard.press("ArrowDown")
    page.wait_for_function("value => document.activeElement.dataset.size === value", arg=selected)
    assert toggle.get_attribute("aria-expanded") == "true"
    assert page.locator("[data-gl-portal]").count() == 1
    page.keyboard.press("End")
    assert page.evaluate("() => document.activeElement.dataset.size") == "all"
    page.keyboard.press("ArrowDown")
    assert page.evaluate("() => document.activeElement.dataset.size") == "25"
    page.keyboard.press("ArrowUp")
    assert page.evaluate("() => document.activeElement.dataset.size") == "all"
    page.keyboard.press("Enter")
    page.wait_for_function(
        "() => document.querySelector('.users-table')._clientPaginator.pageSize === 'all'"
    )
    assert toggle.evaluate("el => el === document.activeElement")
    assert page.locator("[data-gl-portal]").count() == 0
    assert toggle.evaluate(
        "el => { const r = el.getBoundingClientRect(); "
        "return r.top >= 0 && r.bottom <= innerHeight; }"
    )
    toggle.press("ArrowUp")
    page.wait_for_function("() => document.activeElement.dataset.size === 'all'")
    page.keyboard.press("Home")
    assert page.evaluate("() => document.activeElement.dataset.size") == "25"
    page.keyboard.press("Enter")
    page.wait_for_function(
        "() => document.querySelector('.users-table')._clientPaginator.pageSize === 25"
    )
    assert toggle.evaluate("el => el === document.activeElement")
    assert page.locator("[data-gl-portal]").count() == 0


def test_table_select_tab_and_escape_dismiss_the_correct_menu(table_select_page) -> None:
    page = table_select_page
    toggle = page.locator(".gl-page-size-dropdown .gl-dropdown-toggle").first
    toggle.focus()
    page.keyboard.press("ArrowDown")
    page.wait_for_function("() => document.activeElement.matches('.gl-dropdown-item')")
    page.keyboard.press("Tab")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.locator("[data-gl-portal]").count() == 0
    toggle.focus()
    page.keyboard.press("ArrowUp")
    page.wait_for_function("() => document.activeElement.matches('.gl-dropdown-item')")
    page.keyboard.press("Shift+Tab")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert page.locator("[data-gl-portal]").count() == 0
    toggle.click()
    # Keyboard focus can move independently of a pointer click (shortcuts,
    # accessibility navigation). Escape must find the actual open root.
    page.locator('#main-content input:not([type="hidden"])').first.evaluate(
        "el => el.focus({preventScroll: true})"
    )
    page.keyboard.press("Escape")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert toggle.evaluate("el => el === document.activeElement")
    assert page.locator("[data-gl-portal]").count() == 0


def test_table_select_keyboard_skips_disabled_options(table_select_page) -> None:
    page = table_select_page
    toggle = page.locator(".gl-page-size-dropdown .gl-dropdown-toggle").first
    toggle.click()
    page.locator('[data-gl-portal] [data-size="25"]').evaluate("el => { el.disabled = true; }")
    toggle.focus()
    page.keyboard.press("Home")
    assert page.evaluate("() => document.activeElement.dataset.size") == "50"
    page.keyboard.press("End")
    assert page.evaluate("() => document.activeElement.dataset.size") == "all"
    page.keyboard.press("ArrowDown")
    assert page.evaluate("() => document.activeElement.dataset.size") == "50"
    page.keyboard.press("Escape")
    assert toggle.get_attribute("aria-expanded") == "false"
    assert toggle.evaluate("el => el === document.activeElement")
