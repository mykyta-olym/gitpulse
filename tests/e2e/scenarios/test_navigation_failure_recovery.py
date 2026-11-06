"""Unsuccessful navigation preserves the rendered page and its live controls."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("navigation recovery needs a running server", allow_module_level=True)


def _ready(page):
    page.wait_for_function("""() => !!window.GP?.navigateTo
      && !document.querySelector('#main-content.is-navigating, #main-content.is-arriving')""")


@pytest.fixture(params=[1440, 390])
def recovery_page(browser, context_for, live_server, request):
    width = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        is_mobile=width < 768,
        has_touch=width < 768,
    ) as context:
        fault = {"path": "/dashboard/admin/users", "kind": None, "attempts": 0}
        pending = []

        def route_request(route):
            req = route.request
            if req.method not in {"GET", "HEAD"}:
                route.fulfill(status=204)
            elif urlsplit(req.url).path == "/dashboard/datepicker-cleanup-probe":
                route.fulfill(body="<p>Replacement</p>", content_type="text/html")
            elif (
                req.headers.get("hx-request") == "true"
                and urlsplit(req.url).path == fault["path"]
                and fault["kind"] is not None
            ):
                fault["attempts"] += 1
                if fault["kind"] == "network":
                    route.abort("internetdisconnected")
                elif fault["kind"] in {"timeout", "pending"}:
                    pending.append(route)
                else:
                    route.fulfill(status=fault["kind"], body="", content_type="text/html")
            else:
                route.continue_()

        context.route("**/*", route_request)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        _ready(page)
        yield page, fault, pending
        assert not errors, errors


@pytest.mark.parametrize("failure", [403, 429, 503, 204, "network", "timeout"])
def test_failed_navigation_keeps_url_modals_and_calendar_usable(recovery_page, failure):
    page, fault, _pending = recovery_page
    before = page.url
    page.evaluate("""() => {
      window.__createModal = document.getElementById('createCourseModal');
      window.__cleanupCalls = 0;
      const cleanup = GP.activePageCleanup;
      GP.activePageCleanup = () => { __cleanupCalls++; cleanup?.(); };
    }""")
    fault["kind"] = failure
    if failure == "timeout":
        page.evaluate("() => htmx.config.timeout = 150")
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
    page.wait_for_timeout(250)
    _ready(page)
    assert fault["attempts"] == 1
    assert page.url == before
    assert page.evaluate("__createModal === document.getElementById('createCourseModal')")
    assert page.evaluate("__cleanupCalls") == 0
    assert not page.locator("#main-content").evaluate("el => el.hasAttribute('x-ignore')")
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.locator("#courseSemesterStart").click()
    page.locator(".flatpickr-calendar.open").wait_for()
    assert page.locator("#courseSemesterStart").evaluate(
        "el => el._flatpickr.calendarContainer.isConnected"
    )


@pytest.mark.parametrize("failure", [503, 204, "network"])
def test_failed_navigation_retains_unsaved_preferences(recovery_page, live_server, failure):
    page, fault, _pending = recovery_page
    page.goto(live_server + "/dashboard/preferences")
    _ready(page)
    checkbox = page.locator('[name="keyboard_shortcuts_enabled"]')
    before = checkbox.is_checked()
    checkbox.set_checked(not before)
    assert page.locator("#preferencesSave").is_enabled()
    fault["kind"] = failure
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_timeout(250)
    _ready(page)
    assert page.url == live_server + "/dashboard/preferences"
    assert checkbox.is_checked() is not before
    assert page.locator("#preferencesSave").is_enabled()
    assert page.evaluate("() => GP.hasUnsavedState()")
    checkbox.set_checked(before)
    assert page.locator("#preferencesSave").is_disabled()
    assert not page.evaluate("() => GP.hasUnsavedState()")


@pytest.mark.parametrize("direction", ["back", "forward"])
def test_failed_history_navigation_restores_the_rendered_address(
    recovery_page, live_server, direction
):
    page, fault, _pending = recovery_page
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url("**/preferences")
    _ready(page)
    fault["path"] = "/dashboard/" if direction == "back" else "/dashboard/preferences"
    if direction == "forward":
        page.go_back()
        page.wait_for_url(live_server + "/dashboard/")
        _ready(page)
    before = page.url
    fault["kind"] = 503
    page.go_back() if direction == "back" else page.go_forward()
    page.wait_for_timeout(300)
    _ready(page)
    assert fault["attempts"] == 1
    assert page.url == before
    assert page.locator("#preferencesForm").count() == (direction == "back")


def _add_main_picker(page):
    page.evaluate("""() => {
      const fragment = document.createElement('div'); fragment.id = 'dateCleanupFixture';
      const input = document.createElement('input');
      input.id = 'cleanupDate'; input.name = 'cleanup_date';
      input.className = 'date-picker'; input.value = '2026-10-26';
      fragment.append(input); document.getElementById('main-content').append(fragment);
      GP.initDatePickers(fragment); window.__oldPicker = input._flatpickr;
    }""")
    assert page.evaluate("__oldPicker._handlers.length > 0")


def test_fragment_removal_destroys_picker_handlers_and_popup(recovery_page):
    page, _fault, _pending = recovery_page
    _add_main_picker(page)
    page.evaluate("""() => htmx.ajax('GET', '/dashboard/datepicker-cleanup-probe', {
      target: '#dateCleanupFixture', swap: 'innerHTML'
    })""")
    assert page.evaluate("__oldPicker._handlers.length") == 0
    assert page.evaluate("!__oldPicker.calendarContainer && !__oldPicker.input.isConnected")
    assert page.locator("#courseSemesterStart").evaluate(
        "el => el._flatpickr.calendarContainer.isConnected"
    )


def test_pending_navigation_preserves_controls_until_successful_swap(recovery_page):
    page, fault, pending = recovery_page
    _add_main_picker(page)
    page.evaluate("window.__oldModal = document.getElementById('createCourseModal')")
    fault["kind"] = "pending"
    page.evaluate("() => GP.navigateTo('/dashboard/admin/users')")
    page.wait_for_timeout(200)
    assert len(pending) == 1
    assert page.evaluate("__oldModal.isConnected && __oldPicker._handlers.length > 0")
    fault["kind"] = None
    response = pending[0].fetch()
    pending[0].fulfill(response=response)
    page.wait_for_url("**/admin/users")
    _ready(page)
    assert page.evaluate("!__oldModal.isConnected && __oldPicker._handlers.length === 0")
    assert not page.evaluate("() => GP.hasUnsavedState()")


def test_queued_back_navigation_fetches_the_page_already_in_the_address_bar(recovery_page):
    page, fault, pending = recovery_page
    for path in ("/dashboard/preferences", "/dashboard/admin/users"):
        page.evaluate("path => GP.navigateTo(path)", path)
        page.wait_for_url("**" + path)
        _ready(page)
    fault.update(path="/dashboard/preferences", kind="pending")
    page.go_back()
    page.wait_for_timeout(200)
    assert len(pending) == 1
    page.go_back()
    fault["kind"] = None
    response = pending[0].fetch()
    pending[0].fulfill(response=response)
    page.wait_for_function("""() => location.pathname === '/dashboard/'
      && !!document.getElementById('createCourseModal')
      && !document.querySelector('#main-content.is-navigating, #main-content.is-arriving')""")
    assert page.locator("#preferencesForm").count() == 0
