"""Cancel must discard a draft, while a running import remains a process."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal drafts need a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def draft_page(browser, context_for, live_server: str, request):
    mode = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": 1440 if mode == "desktop" else 390, "height": 900},
        is_mobile=mode != "desktop",
        has_touch=mode != "desktop",
        reduced_motion="reduce" if mode == "reduced" else "no-preference",
    ) as ctx:
        writes = []

        def block_writes(route):
            if route.request.method in {"GET", "HEAD"}:
                route.continue_()
            else:
                writes.append(route.request.url)
                route.fulfill(status=204)

        ctx.route("**/*", block_writes)
        if mode == "no-gsap":
            ctx.route(
                "**/gsap*.js*",
                lambda route: route.fulfill(body="", content_type="application/javascript"),
            )
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.wait_for_function("() => !!window.GP?.openModal && !!window.submitGitLabImport")
        yield page
        assert not errors, errors
        assert not [url for url in writes if "/courses/import/" in url], writes


def _open(page, modal: str = "importGitlabCourseModal") -> None:
    page.evaluate("id => GP.openModal(id)", modal)
    page.wait_for_function(
        "id => document.getElementById(id).classList.contains('active')", arg=modal
    )


def _answer(page, discard: bool) -> None:
    page.locator("#gpConfirmDialog.active").wait_for()
    page.locator(
        '#gpConfirmDialog [data-gp-confirm="ok"]'
        if discard
        else '#gpConfirmDialog [data-gp-confirm="cancel"]'
    ).last.click()
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")


@pytest.mark.parametrize("delay", [0, 700])
@pytest.mark.parametrize("close", ["cancel", "x", "escape", "backdrop"])
def test_import_close_warns_and_discard_removes_draft(draft_page, close: str, delay: int) -> None:
    page = draft_page
    _open(page)
    page.wait_for_timeout(delay)
    page.locator("#importGroupUrl").fill("221434")
    page.wait_for_timeout(750)
    assert page.evaluate("() => GP.hasUnsavedState()")
    if close == "cancel":
        page.locator("#importGitlabCourseCancelBtn").click()
    elif close == "x":
        page.locator("#importGitlabCourseModal .modal-close").click()
    elif close == "escape":
        page.keyboard.press("Escape")
    else:
        # A small backdrop corner remains outside the mobile bottom sheet.
        page.locator("#importGitlabCourseModal").click(position={"x": 2, "y": 2})
    _answer(page, False)
    assert page.locator("#importGroupUrl").input_value() == "221434"
    assert page.locator("#importGitlabCourseModal.active").count() == 1
    page.locator("#importGitlabCourseCancelBtn").click()
    _answer(page, True)
    page.wait_for_function("() => !document.querySelector('#importGitlabCourseModal.active')")
    assert not page.evaluate("() => GP.hasUnsavedState()")
    _open(page)
    assert page.locator("#importGroupUrl").input_value() == ""
    page.locator("#importGitlabCourseCancelBtn").click()
    page.wait_for_function("() => !document.querySelector('#importGitlabCourseModal.active')")
    assert page.locator("#gpConfirmDialog.active").count() == 0


def test_discard_restores_dependent_period_fields_checkbox_and_picker(draft_page) -> None:
    page = draft_page
    _open(page)
    page.wait_for_timeout(750)
    baseline = page.locator("#importGitlabCourseForm").evaluate(
        "form => [...new FormData(form).entries()]"
    )
    page.locator("#importGroupUrl").fill("group/project")
    page.locator("#importAutoSync").uncheck()
    period = page.locator("#importCoursePeriod").locator("..")
    current = page.locator("#importCoursePeriod").input_value()
    period.locator(".gl-form-dropdown-toggle").click()
    period.locator(f'.gl-dropdown-item:not([data-value="{current}"])').first.click()
    page.locator("#importCourseSemesterStart").fill("2028-01-05")
    page.locator("#importCourseSemesterStart").press("Tab")
    if page.locator(".flatpickr-calendar.open").count():
        page.keyboard.press("Escape")
    page.locator("#importGitlabCourseCancelBtn").click()
    _answer(page, True)
    page.wait_for_function("() => !document.querySelector('#importGitlabCourseModal.active')")
    _open(page)
    page.wait_for_timeout(750)
    assert (
        page.locator("#importGitlabCourseForm").evaluate(
            "form => [...new FormData(form).entries()]"
        )
        == baseline
    )
    assert page.locator("#importCourseSemesterStart").evaluate(
        "el => el._flatpickr.formatDate(el._flatpickr.selectedDates[0], 'Y-m-d') === el.value"
    )
    assert not page.evaluate("() => GP.hasUnsavedState()")


def test_create_course_discard_uses_opening_values(draft_page) -> None:
    page = draft_page
    _open(page, "createCourseModal")
    page.locator("#courseCode").fill("DISCARD-ME")
    page.locator("#courseDescription").fill("Unsubmitted description")
    page.locator("#createCourseModal [data-modal-close]").last.click()
    _answer(page, True)
    page.wait_for_function("() => !document.querySelector('#createCourseModal.active')")
    _open(page, "createCourseModal")
    assert page.locator("#courseCode").input_value() == ""
    assert page.locator("#courseDescription").input_value() == ""
    assert not page.evaluate("() => GP.hasUnsavedState()")


@pytest.mark.parametrize("keyboard", [False, True])
@pytest.mark.parametrize(
    ("modal", "field"),
    [
        ("createCourseModal", "courseSemesterStart"),
        ("importGitlabCourseModal", "importCourseSemesterStart"),
    ],
)
def test_early_calendar_edit_warns_and_discard_restores_the_date(
    draft_page, modal: str, field: str, keyboard: bool
) -> None:
    page = draft_page
    before = page.locator("#" + field).input_value()
    _open(page, modal)
    # Fast real input must work while the opening/initialisation is settling.
    page.locator("#" + field).click()
    day = page.locator(
        ".flatpickr-calendar.open .dayContainer "
        ".flatpickr-day:not(.selected):not(.prevMonthDay):not(.nextMonthDay)"
    ).first
    if keyboard:
        day.focus()
        page.keyboard.press("Enter")
    else:
        day.click()
    assert page.locator("#" + field).input_value() != before
    page.wait_for_timeout(750)
    assert page.evaluate("() => GP.hasUnsavedState()")
    cancel = page.locator(
        "#importGitlabCourseCancelBtn"
        if modal == "importGitlabCourseModal"
        else "#createCourseModal .modal-footer [data-modal-close]"
    )
    cancel.click()
    _answer(page, False)
    assert page.locator("#" + field).input_value() != before
    cancel.click()
    _answer(page, True)
    _open(page, modal)
    page.wait_for_timeout(750)
    assert page.locator("#" + field).input_value() == before
    assert page.locator("#" + field).evaluate(
        "el => el._flatpickr.formatDate(el._flatpickr.selectedDates[0], 'Y-m-d') === el.value"
    )
    assert not page.evaluate("() => GP.hasUnsavedState()")


def test_escape_dismisses_only_the_top_confirmation(draft_page) -> None:
    page = draft_page
    _open(page)
    page.locator("#importGroupUrl").fill("group/project")
    page.keyboard.press("Escape")
    page.locator("#gpConfirmDialog.active").wait_for()
    page.wait_for_timeout(750)
    assert page.locator("#gpConfirmDialog.active").count() == 1
    page.keyboard.press("Tab")
    assert page.evaluate(
        "() => document.getElementById('gpConfirmDialog').contains(document.activeElement)"
    )
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")
    assert page.locator("#importGitlabCourseModal.active").count() == 1
    assert page.locator("#importGroupUrl").input_value() == "group/project"


def test_import_uses_shared_modal_functions_and_opener(draft_page) -> None:
    page = draft_page
    assert page.evaluate("() => openModal === GP.openModal && closeModal === GP.closeModal")
    opener = page.locator('[data-modal-open="importGitlabCourseModal"]').first
    opener.click()
    assert page.locator("#importGitlabCourseModal").evaluate(
        "modal => modal._gpOpener === "
        "document.querySelector('[data-modal-open=importGitlabCourseModal]')"
    )
    assert page.evaluate("() => closeModal('importGitlabCourseModal')")
    page.wait_for_function("() => !document.querySelector('#importGitlabCourseModal.active')")


def test_import_draft_protects_internal_navigation(draft_page, live_server: str) -> None:
    page = draft_page
    _open(page)
    page.locator("#importGroupUrl").fill("group/project")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    _answer(page, False)
    assert page.url == live_server + "/dashboard/"
    assert page.locator("#importGroupUrl").input_value() == "group/project"
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    _answer(page, True)
    page.wait_for_url("**/dashboard/preferences")
    page.locator("#preferencesForm").wait_for()
    assert not page.evaluate("() => GP.hasUnsavedState()")


def test_old_discard_answer_cannot_reset_a_new_opening(draft_page) -> None:
    page = draft_page
    _open(page)
    page.locator("#importGroupUrl").fill("first/draft")
    page.locator("#importGitlabCourseCancelBtn").click()
    page.locator("#gpConfirmDialog.active").wait_for()
    page.evaluate("() => GP.forceCloseModal('importGitlabCourseModal')")
    page.wait_for_function("() => !document.querySelector('#importGitlabCourseModal.active')")
    _open(page)
    page.evaluate("() => document.getElementById('importGroupUrl').value = 'second/draft'")
    _answer(page, True)
    assert page.locator("#importGitlabCourseModal.active").count() == 1
    assert page.locator("#importGroupUrl").input_value() == "second/draft"


def test_running_import_close_keeps_process_cancel_semantics(draft_page) -> None:
    page = draft_page
    _open(page)
    page.locator("#importGroupUrl").fill("group/project")
    page.evaluate("""() => {
      const fetch = window.fetch;
      window.fetch = (url, options) => String(url).includes('/courses/check-import-duplicate')
        ? new Promise((_resolve, reject) => options.signal.addEventListener('abort', () =>
          reject(new DOMException('Import cancelled.', 'AbortError')), {once: true}))
        : fetch(url, options);
    }""")
    page.locator("#importGitlabCourseBtn").click()
    page.wait_for_function("() => document.getElementById('importGitlabCourseBtn').disabled")
    assert not page.evaluate("() => GP.hasUnsavedState()")
    page.locator("#importGitlabCourseCancelBtn").click()
    _answer(page, False)
    assert page.locator("#importGitlabCourseModal.active").count() == 1
    page.locator("#importGitlabCourseCancelBtn").click()
    _answer(page, True)
    page.wait_for_function("""() => {
      const btn = document.getElementById('importGitlabCourseCancelBtn');
      return btn.textContent.trim() === btn.dataset.idleLabel;
    }""")
    assert page.locator("#importGroupUrl").input_value() == "group/project"
