"""The actual tour welcome yields to core confirmations, including a delayed seed."""

import os

import pytest

from tests.e2e.scenarios.conftest import COURSE

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("needs GITPULSE_E2E_BASE_URL", allow_module_level=True)


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("delayed", [False, True])
def test_confirmation_remains_operable_with_first_visit_tour(
    browser, context_for, live_server, width, delayed
):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 900},
        service_workers="block",
    ) as context:
        page = context.new_page()
        errors = []
        pending = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route(
            "**/dashboard/api/tour/seen",
            lambda route: pending.append(route) if delayed else route.fulfill(json={"keys": []}),
        )
        page.goto(live_server + "/dashboard/admin/system?lang=en")
        page.wait_for_function("() => window.GP && GP.tour")
        if not delayed:
            page.locator("#gpTourWelcome.is-visible").wait_for()
        page.evaluate("""() => {
          GP.confirmDialog({message: 'Keep this confirmation open'}).then(result => {
            window.confirmationResult = result;
          });
        }""")
        if delayed:
            page.wait_for_timeout(100)
            assert pending
            for route in pending:
                route.fulfill(json={"keys": []})
        page.wait_for_timeout(1000)
        assert page.locator("#gpTourWelcome.is-visible").count() == 0
        dialog = page.locator("#gpConfirmDialog.active")
        assert dialog.is_visible()
        dialog.locator('[data-gp-confirm="cancel"]').last.click()
        page.wait_for_function("() => window.confirmationResult === false")
        assert not errors


def _assert_delayed_prompt_yields(browser, context_for, live_server, width, control):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": width, "height": 900},
        service_workers="block",
    ) as context:
        context.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.method in {"GET", "HEAD"}
                else route.fulfill(status=204)
            ),
        )
        page = context.new_page()
        pending, errors = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/dashboard/api/tour/seen", lambda route: pending.append(route))
        path = (
            f"/dashboard/courses/{COURSE}/settings"
            if control == "calendar"
            else "/dashboard/admin/users"
        )
        page.goto(live_server + path + "?lang=en")
        page.wait_for_function(
            "() => GP.tour && document.documentElement.hasAttribute('data-gp-ready')"
        )
        if control == "calendar":
            page.locator("#semester_start_date").click()
            assert page.locator(".flatpickr-calendar.open").count() == 1
        elif control == "search":
            page.locator("#userSearch").fill("review")
        elif control == "dropdown":
            page.locator(".gl-period-selector .gl-dropdown-toggle").click()
        else:
            page.locator("#mobileMenuBtn").click()
        assert pending
        for route in pending:
            route.fulfill(json={"keys": []})
        page.wait_for_timeout(1000)
        assert page.locator("#gpTourWelcome.is-visible").count() == 0
        if control == "calendar":
            assert page.locator("#semester_start_date").evaluate("el => el._flatpickr.isOpen")
            page.locator(
                ".flatpickr-calendar.open .dayContainer "
                ".flatpickr-day:not(.selected):not(.prevMonthDay):not(.nextMonthDay)"
            ).first.click()
            page.wait_for_function("() => !document.getElementById('btnSaveSettings').disabled")
            assert page.locator("#btnSaveSettings").is_enabled()
        elif control == "search":
            assert page.locator("#userSearch").evaluate("el => el === document.activeElement")
            assert page.locator("#userSearch").input_value() == "review"
        elif control == "dropdown":
            assert (
                page.locator(".gl-period-selector .gl-dropdown-toggle").get_attribute(
                    "aria-expanded"
                )
                == "true"
            )
        else:
            assert page.locator("#appSidebar").evaluate(
                "el => el.classList.contains('mobile-open')"
            )
        assert not errors


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("control", ["calendar", "search", "dropdown"])
def test_delayed_first_visit_prompt_does_not_interrupt_a_control(
    browser, context_for, live_server, width, control
):
    _assert_delayed_prompt_yields(browser, context_for, live_server, width, control)


def test_delayed_first_visit_prompt_does_not_close_the_mobile_sidebar(
    browser, context_for, live_server
):
    _assert_delayed_prompt_yields(browser, context_for, live_server, 390, "sidebar")
