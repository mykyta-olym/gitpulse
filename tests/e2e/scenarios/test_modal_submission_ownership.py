"""A delayed modal write must not act on a later interaction or another page."""

from __future__ import annotations

import json
import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal submission races need a running server", allow_module_level=True)


@pytest.fixture(params=[1440, 390])
def edit_page(browser, context_for, live_server: str, request):
    width = request.param
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": width, "height": 900},
        has_touch=width == 390,
        is_mobile=width == 390,
    ) as ctx:
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.bring_to_front()
        # Also protect against accidental real writes if the injected fetch
        # fails to catch one. All reads still use the real development server.
        ctx.route(
            "**/api/v1/**",
            lambda route: (
                route.continue_() if route.request.method in {"GET", "HEAD"} else route.abort()
            ),
        )
        page.goto(live_server + "/dashboard/admin/users")
        page.wait_for_function("() => !!window.submitModalForm && !!window.updateUser")
        page.evaluate("""() => {
          const fetch = window.fetch;
          window.__writes = [];
          window.__finished = [];
          window.fetch = (url, options) => {
            if ((options?.method === 'PUT' && String(url).includes('/api/v1/users/'))
                || (options?.method === 'POST' && String(url).endsWith('/api/v1/courses/'))) {
              return new Promise(resolve => __writes.push({
                url: String(url), body: JSON.parse(options.body),
                respond(status) {
                  resolve(new Response(JSON.stringify(status === 200
                    ? {...this.body, id: 'stale-created-course'}
                    : {detail: 'Submission rejected for testing'}),
                    {status, headers: {'Content-Type': 'application/json'}}));
                }
              }));
            }
            return fetch(url, options);
          };
          const submit = window.submitModalForm;
          let count = 0;
          window.submitModalForm = (...args) => {
            const id = count++;
            const pending = submit(...args);
            pending.then(() => __finished.push(id), () => __finished.push(id));
            return pending;
          };
        }""")
        yield page
        assert not errors, errors


def _open(page, index: int):
    row = page.locator('.users-table tr[data-bot="0"]').nth(index)
    opener = row.locator('[data-action="openEditUserModal"]')
    args = json.loads(opener.get_attribute("data-action-args"))
    opener.click()
    return row, args


def _save_changed_status(page, active: bool, count: int) -> None:
    page.locator("#editIsActive").set_checked(not active)
    page.locator("#editUserBtn").click()
    page.wait_for_function("count => __writes.length === count", arg=count)


def _discard(page, modal: str = "editUserModal") -> None:
    page.locator(f"#{modal} .modal-close").click()
    page.wait_for_function("() => !!document.querySelector('#gpConfirmDialog.active')")
    page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
    page.wait_for_function(
        "id => !document.getElementById(id).classList.contains('active')", arg=modal
    )


def _respond(page, index: int, status: int = 200) -> None:
    page.evaluate("([index, status]) => __writes[index].respond(status)", [index, status])
    page.wait_for_function("index => __finished.includes(index)", arg=index)


@pytest.mark.parametrize("status", [200, 409])
def test_old_save_cannot_close_edit_or_change_another_users_row(edit_page, status: int) -> None:
    page = edit_page
    first_row, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    _discard(page)
    second_row, second = _open(page, 1)
    page.locator("#editIsActive").set_checked(not second[3])
    toasts = page.locator(".toast").count()
    _respond(page, 0, status)
    page.wait_for_timeout(700)
    assert page.locator("#editUserModal.active:not(.closing)").count() == 1
    assert page.locator("#editUsername").input_value() == second[1]
    assert page.locator("#editIsActive").is_checked() is not second[3]
    assert page.locator("#editUserBtn").is_enabled()
    assert first_row.evaluate("row => !row.classList.contains('row-inactive')") is first[3]
    assert second_row.evaluate("row => !row.classList.contains('row-inactive')") is second[3]
    assert page.locator(".toast").count() == toasts


@pytest.mark.parametrize("first_to_finish", [0, 1])
def test_new_interaction_can_save_while_the_old_write_is_pending(
    edit_page, first_to_finish: int
) -> None:
    page = edit_page
    _, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    _discard(page)
    second_row, second = _open(page, 1)
    _save_changed_status(page, second[3], 2)
    page.wait_for_function(
        "() => document.getElementById('editUserBtn').classList.contains('loading')"
    )
    _respond(page, first_to_finish)
    if first_to_finish == 0:
        page.wait_for_timeout(500)
        assert page.locator("#editUserModal.active:not(.closing)").count() == 1
        assert page.locator("#editUserBtn.loading").count() == 1
        assert page.locator("#editUserBtn").is_disabled()
        assert page.locator("#editIsActive").is_disabled()
        assert page.locator("#editRole_toggle").is_disabled()
        _respond(page, 1)
        page.wait_for_function(
            "() => !document.getElementById('editUserModal').classList.contains('active')"
        )
    else:
        page.wait_for_function(
            "() => !document.getElementById('editUserModal').classList.contains('active')"
        )
        _open(page, 1)
        _respond(page, 0)
        page.wait_for_timeout(500)
        assert page.locator("#editUserModal.active:not(.closing)").count() == 1
        assert page.locator("#editIsActive").is_checked() is not second[3]
        assert page.locator("#editUserBtn").is_disabled()
    assert second_row.evaluate("row => !row.classList.contains('row-inactive')") is not second[3]
    assert page.evaluate("() => __writes.map(write => write.url.split('/').pop())") == [
        first[0],
        second[0],
    ]


@pytest.mark.parametrize("status", [200, 409])
def test_reopening_clears_previous_button_feedback_and_keeps_pristine_save_disabled(
    edit_page, status: int
) -> None:
    page = edit_page
    row, first = _open(page, 0)
    original_label = page.locator("#editUserBtn").inner_text()
    _save_changed_status(page, first[3], 1)
    _respond(page, 0, status)
    if status == 200:
        page.wait_for_function(
            "() => !document.getElementById('editUserModal').classList.contains('active')"
        )
        assert row.evaluate("row => !row.classList.contains('row-inactive')") is not first[3]
    else:
        assert "Submission rejected for testing" in page.locator(".toast").last.inner_text()
        page.wait_for_function("() => !document.getElementById('editUserBtn').disabled")
        _discard(page)
    _open(page, 1)
    page.wait_for_timeout(700)
    button = page.locator("#editUserBtn")
    assert button.is_disabled()
    assert button.evaluate(
        "btn => !btn.matches('.loading, .btn-done, .btn-error') && !btn.querySelector('.spinner')"
    )
    assert button.inner_text() == original_label


@pytest.mark.parametrize("status", [200, 409])
def test_a_late_save_cannot_reload_or_show_feedback_on_a_new_page(
    edit_page, live_server: str, status: int
) -> None:
    page = edit_page
    _, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    _discard(page)
    page.evaluate("() => { GP.navigateTo('/dashboard/preferences'); }")
    page.wait_for_url("**/dashboard/preferences")
    page.wait_for_function("() => !!document.getElementById('preferencesForm')")
    toasts = page.locator(".toast").count()
    _respond(page, 0, status)
    page.wait_for_timeout(700)
    assert page.url == live_server + "/dashboard/preferences"
    assert page.locator("#preferencesForm").is_visible()
    assert page.locator(".toast").count() == toasts


@pytest.mark.parametrize("action", ["reopen", "navigate"])
def test_a_late_course_creation_cannot_redirect_the_next_interaction(
    edit_page, live_server: str, action: str
) -> None:
    page = edit_page
    page.evaluate("() => { GP.navigateTo('/dashboard/'); }")
    page.wait_for_url("**/dashboard/")
    page.wait_for_function("() => !!document.getElementById('createCourseForm')")
    page.evaluate("() => openModal('createCourseModal')")
    page.locator("#courseCode").fill("RACE-QA")
    page.locator("#courseName").fill("Delayed course creation")
    page.locator("#createCourseBtn").click()
    page.wait_for_function("() => __writes.length === 1")
    _discard(page, "createCourseModal")
    if action == "navigate":
        page.evaluate("() => { GP.navigateTo('/dashboard/preferences'); }")
        page.wait_for_url("**/dashboard/preferences")
        page.wait_for_function("() => !!document.getElementById('preferencesForm')")
    else:
        page.evaluate("() => openModal('createCourseModal')")
        page.locator("#courseName").fill("Keep this draft")
    url = page.url
    _respond(page, 0)
    page.wait_for_timeout(700)
    assert page.url == url
    assert not page.locator(".toast").count()
    if action == "reopen":
        assert page.locator("#createCourseModal.active:not(.closing)").count() == 1
        assert page.locator("#courseName").input_value() == "Keep this draft"
    else:
        assert page.url == live_server + "/dashboard/preferences"


def test_dialog_opened_during_arrival_still_protects_edits(edit_page) -> None:
    page = edit_page
    scripts = []
    page.route("**/js/pages/dashboard.*.js", lambda route: scripts.append(route))
    page.evaluate("() => GP.navigateTo('/dashboard/')")
    page.wait_for_function(
        "() => document.querySelector('#main-content.is-arriving #createCourseForm')"
    )
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.wait_for_function("() => document.querySelector('#createCourseModal.active')")
    assert scripts, "the incoming page script was not held"
    scripts.pop().continue_()
    page.wait_for_function("() => !document.querySelector('#main-content.is-arriving')")
    page.locator("#courseName").fill("Keep this unsaved draft")
    _discard(page, "createCourseModal")
    page.evaluate("() => GP.openModal('createCourseModal')")
    assert page.locator("#courseName").input_value() == ""


def test_returning_to_the_page_can_submit_while_its_old_write_is_pending(edit_page) -> None:
    page = edit_page
    _, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    _discard(page)
    page.evaluate("() => { GP.navigateTo('/dashboard/'); }")
    page.wait_for_url("**/dashboard/")
    page.wait_for_function("() => !!document.getElementById('createCourseForm')")
    page.evaluate("() => { GP.navigateTo('/dashboard/admin/users'); }")
    page.wait_for_url("**/dashboard/admin/users")
    page.wait_for_function("() => !!window.updateUser")
    _, second = _open(page, 1)
    _save_changed_status(page, second[3], 2)
    _respond(page, 0)
    page.wait_for_timeout(500)
    assert page.locator("#editUserModal.active:not(.closing)").count() == 1
    assert page.locator("#editUserBtn").is_disabled()
    _respond(page, 1)
    page.wait_for_function(
        "() => !document.getElementById('editUserModal').classList.contains('active')"
    )


def test_pending_save_freezes_fields_and_the_row_matches_what_was_sent(edit_page) -> None:
    page = edit_page
    row, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    for selector in ["#editIsActive", "#editIsBot", "#editRole_toggle"]:
        field = page.locator(selector)
        assert field.is_disabled()
        box = field.bounding_box()
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        if page.viewport_size["width"] == 390:
            page.touchscreen.tap(x, y)
        else:
            page.mouse.click(x, y)
    assert page.locator("#editIsActive").is_checked() is not first[3]
    assert page.locator("#editRole_toggle").get_attribute("aria-expanded") == "false"
    assert page.locator(
        '#editUserModal .modal-footer [data-modal-close="editUserModal"]'
    ).is_enabled()
    assert page.locator("#editUserModal .modal-close").is_enabled()
    assert page.evaluate("() => __writes[0].body") == {
        "role": first[2],
        "is_active": not first[3],
        "is_bot": False,
    }
    _respond(page, 0)
    page.wait_for_function(
        "() => !document.getElementById('editUserModal').classList.contains('active')"
    )
    assert row.evaluate("row => !row.classList.contains('row-inactive')") is not first[3]


def test_failed_save_restores_editing_and_can_be_retried(edit_page) -> None:
    page = edit_page
    row, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    page.wait_for_function(
        "() => document.getElementById('editUserBtn').classList.contains('loading')"
    )
    _respond(page, 0, 409)
    assert page.locator("#editIsActive").is_enabled()
    assert page.locator("#editRole_toggle").is_enabled()
    # A field disabled before submission must stay disabled after it.
    assert page.locator("#editUsername").is_disabled()
    role = "teacher" if first[2] != "teacher" else "student"
    page.locator("#editRole_toggle").click()
    page.locator(f'#editRole_options [data-value="{role}"]').click()
    page.locator("#editUserBtn").click()
    page.wait_for_function("() => __writes.length === 2")
    assert page.locator("#editIsActive").is_disabled()
    _respond(page, 1)
    page.wait_for_function(
        "() => !document.getElementById('editUserModal').classList.contains('active')"
    )
    assert row.get_attribute("data-role") == role
    assert row.evaluate("row => !row.classList.contains('row-inactive')") is not first[3]


def test_new_opening_unlocks_fields_without_waiting_for_the_previous_write(edit_page) -> None:
    page = edit_page
    _, first = _open(page, 0)
    _save_changed_status(page, first[3], 1)
    assert page.locator("#editIsActive").is_disabled()
    _discard(page)
    _, second = _open(page, 1)
    assert page.locator("#editIsActive").is_enabled()
    assert page.locator("#editRole_toggle").is_enabled()
    assert page.locator("#editUsername").is_disabled()
    page.locator("#editIsActive").set_checked(not second[3])
    _respond(page, 0)
    assert page.locator("#editIsActive").is_enabled()
    assert page.locator("#editIsActive").is_checked() is not second[3]
