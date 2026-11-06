"""Slow saves acknowledge submitted values and preserve later edits."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("form save checks need a running server", allow_module_level=True)


@pytest.fixture(params=[390, 1440])
def save_page(browser, context_for, live_server: str, request):
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        service_workers="block",
        viewport={"width": request.param, "height": 900},
        has_touch=request.param == 390,
        is_mobile=request.param == 390,
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
        page.goto(live_server + "/dashboard/preferences")
        page.wait_for_function(
            "() => document.getElementById('preferencesForm')?.dataset.preferencesBound === '1'"
        )
        page.wait_for_timeout(650)
        page.evaluate("""() => {
          const fetch = window.fetch;
          window.__saves = []; window.__reloads = 0;
          GP.reloadKeepScroll = window.reloadKeepScroll = () => { __reloads++; };
          window.fetch = (url, options) => {
            if (options?.method === 'POST' && String(url).includes('/api/preferences')) {
              return new Promise(resolve => __saves.push({body: JSON.parse(options.body),
                respond(status = 200) {
                  const body = status === 200 ? {} : {detail: 'Save refused'};
                  resolve(new Response(JSON.stringify(body),
                    {status, headers: {'Content-Type': 'application/json'}}));
                }
              }));
            }
            return fetch(url, options);
          };
        }""")
        yield page
        assert not errors, errors


def _submit(page, color: str = "#112233", count: int = 1):
    page.locator("#diff_color_removed").fill(color)
    page.locator("#preferencesSave").click()
    page.wait_for_function("count => __saves.length === count", arg=count)


def _respond(page, index: int = 0, status: int = 200):
    page.evaluate("([index, status]) => __saves[index].respond(status)", [index, status])
    page.wait_for_function("""() => {
      const button = document.getElementById('preferencesSave');
      return button && !button._loadingArmed && !button.classList.contains('loading')
        && (!button._gpClickLockUntil || Date.now() >= button._gpClickLockUntil);
    }""")
    page.wait_for_timeout(100)


def _dirty(page):
    return page.evaluate("() => GP.hasDirtyReason('preferences_form') && GP.hasUnsavedState()")


def _dismiss_toasts(page):
    for button in page.locator(".toast .toast-close").all():
        button.click()


def _leave(page, live_server: str, path: str = "/dashboard/"):
    page.evaluate("path => GP.navigateTo(path)", path)
    page.locator("#gpConfirmDialog.active").wait_for()
    page.locator('#gpConfirmDialog .modal-footer [data-gp-confirm="ok"]').click()
    page.wait_for_url(live_server + path)
    page.wait_for_function(
        "() => !document.querySelector('#main-content.is-navigating,#main-content.is-arriving')"
    )


def test_edits_keep_save_disabled_while_pending_then_remain_unsaved(save_page):
    page = save_page
    _submit(page)
    page.locator("#diff_color_removed").fill("#445566")
    assert page.locator("#preferencesSave").is_disabled()
    assert _dirty(page)
    _respond(page)
    assert page.locator("#diff_color_removed").input_value() == "#445566"
    assert page.locator("#preferencesSave").is_enabled()
    assert _dirty(page)
    page.locator("#diff_color_removed").fill("#112233")
    assert page.locator("#preferencesSave").is_disabled()
    assert not _dirty(page)


@pytest.mark.parametrize("status", [200, 409])
def test_another_save_submits_the_remaining_draft(save_page, status: int):
    page = save_page
    _submit(page)
    page.locator("#diff_color_removed").fill("#445566")
    _respond(page, status=status)
    assert _dirty(page)
    _dismiss_toasts(page)
    page.locator("#preferencesSave").click()
    page.wait_for_function("() => __saves.length === 2")
    assert page.evaluate("() => __saves.map(s => s.body.diff_color_removed)") == [
        "#112233",
        "#445566",
    ]
    _respond(page, index=1)
    assert not _dirty(page)
    assert page.locator("#preferencesSave").is_disabled()


def test_leaving_discards_only_the_unsaved_preview(save_page, live_server: str):
    page = save_page
    _submit(page)
    page.locator("#diff_color_removed").fill("#445566")
    _respond(page)
    _leave(page, live_server)
    assert (
        page.evaluate(
            "() => document.documentElement.style"
            ".getPropertyValue('--gl-diff-color-removed').trim()"
        )
        == "#112233"
    )


@pytest.mark.parametrize("status", [200, 409])
def test_a_late_response_cannot_reset_a_replacement_form(save_page, live_server: str, status: int):
    page = save_page
    _submit(page)
    _leave(page, live_server)
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url(live_server + "/dashboard/preferences")
    page.wait_for_timeout(700)
    page.locator("#diff_color_removed").fill("#778899")
    page.locator("#diff_color_removed").press("Tab")
    toasts = page.locator(".toast").count()
    page.evaluate("status => __saves[0].respond(status)", status)
    page.wait_for_timeout(900)
    assert page.locator("#diff_color_removed").input_value() == "#778899"
    assert _dirty(page)
    assert page.locator("#preferencesSave").is_enabled()
    assert page.locator(".toast").count() == toasts
    assert page.evaluate("() => __reloads") == 0


def test_language_reload_waits_until_later_edits_are_saved(save_page):
    page = save_page
    page.locator('[name="preferred_language"]').evaluate("""el => {
      el.value = el.value === 'sk' ? 'en' : 'sk';
      el.dispatchEvent(new Event('change', {bubbles: true}));
    }""")
    _submit(page)
    page.locator("#diff_color_removed").fill("#445566")
    _respond(page)
    assert _dirty(page)
    assert page.evaluate("() => __reloads") == 0
    _dismiss_toasts(page)
    page.locator("#preferencesSave").click()
    page.wait_for_function("() => __saves.length === 2")
    _respond(page, index=1)
    assert not _dirty(page)
    assert page.evaluate("() => __reloads") == 1


@pytest.mark.parametrize(
    "lock", ["archivedLocked", "processLocked", "syncLocked", "cooldownActive"]
)
def test_edits_respect_existing_button_locks(save_page, lock: str):
    page = save_page
    page.locator("#preferencesSave").evaluate("(button, key) => {button.dataset[key] = '1';}", lock)
    page.locator("#diff_color_removed").fill("#112233")
    assert page.locator("#preferencesSave").is_disabled()
    assert _dirty(page)
    page.locator("#preferencesSave").evaluate(
        "(button, key) => {delete button.dataset[key];}", lock
    )
    page.evaluate("() => GP.recheckSaveGuardFor(document.getElementById('preferencesSave'))")
    assert page.locator("#preferencesSave").is_enabled()


def test_owner_reference_cannot_reset_another_forms_guard(save_page, live_server: str):
    page = save_page
    page.evaluate("() => { window.__oldForm = document.getElementById('preferencesForm'); }")
    page.evaluate("() => GP.navigateTo('/dashboard/')")
    page.wait_for_url(live_server + "/dashboard/")
    page.evaluate("() => GP.navigateTo('/dashboard/preferences')")
    page.wait_for_url(live_server + "/dashboard/preferences")
    page.wait_for_timeout(700)
    page.locator("#diff_color_removed").fill("#778899")
    page.evaluate("() => GP.resetSaveGuard('#preferencesForm', __oldForm)")
    assert _dirty(page)


@pytest.fixture(params=["settings", "assistant"])
def course_save(save_page, live_server: str, request):
    page = save_page
    page.goto(live_server + "/dashboard/?period=all")
    course = page.locator("#my-courses .course-card[data-course-id]").first
    assert course.count(), "needs an active development course"
    path = "/dashboard/courses/" + course.get_attribute("data-course-id") + "/" + request.param
    page.goto(live_server + path)
    settings = request.param == "settings"
    field = "#course_name" if settings else "#conflict_file_path"
    button = "#btnSaveSettings" if settings else "#btnSaveAssistantTools"
    dirty_key = "settings_form" if settings else "assistant_tools"
    page.locator(field).wait_for()
    page.wait_for_timeout(700)
    page.evaluate("""() => {
      const fetch = window.fetch; window.__courseSaves = []; window.__reloads = 0;
      GP.reloadKeepScroll = window.reloadKeepScroll = () => { __reloads++; };
      window.fetch = (url, options) => {
        if ((options?.method === 'POST' && String(url).includes('/dashboard/courses/')
              && String(url).endsWith('/settings'))
            || (options?.method === 'POST' && String(url).endsWith('/assistant/tools'))) {
          return new Promise(resolve => __courseSaves.push({url: String(url),
            body: options.body instanceof FormData
              ? Object.fromEntries(options.body) : JSON.parse(options.body),
            respond() { resolve(new Response(JSON.stringify({ok: true}),
              {status: 200, headers: {'Content-Type': 'application/json'}})); }
          }));
        }
        return fetch(url, options);
      };
    }""")
    return page, path, field, button, dirty_key, settings


def _complete_course_save(page):
    page.evaluate("() => __courseSaves[0].respond()")
    page.wait_for_timeout(1200)


def test_course_saves_keep_later_edits_and_do_not_interrupt_with_a_reload(course_save):
    page, _path, field, button, key, settings = course_save
    saved = "Course saved name" if settings else "saved.txt"
    draft = "Course later draft" if settings else "later.txt"
    page.locator(field).fill(saved)
    page.locator(button).click()
    page.wait_for_function("() => __courseSaves.length === 1")
    page.locator(field).fill(draft)
    assert page.locator(button).is_disabled()
    _complete_course_save(page)
    assert page.locator(field).input_value() == draft
    assert page.locator(button).is_enabled()
    assert page.evaluate("key => GP.hasDirtyReason(key)", key)
    assert page.evaluate("() => __reloads") == 0
    assert page.locator("#gpConfirmDialog.active").count() == 0
    page.locator(field).fill(saved)
    assert page.locator(button).is_disabled()
    assert not page.evaluate("key => GP.hasDirtyReason(key)", key)


def test_course_save_response_does_not_touch_a_replacement_page(course_save, live_server: str):
    page, path, field, button, key, settings = course_save
    page.locator(field).fill("Saved course" if settings else "saved.txt")
    page.locator(button).click()
    page.wait_for_function("() => __courseSaves.length === 1")
    _leave(page, live_server)
    page.evaluate("path => GP.navigateTo(path)", path)
    page.wait_for_url(live_server + path)
    page.wait_for_timeout(800)
    page.locator(field).fill("New page draft" if settings else "new.txt")
    _complete_course_save(page)
    assert page.evaluate("key => GP.hasDirtyReason(key)", key)
    assert page.locator(button).is_enabled()
    assert page.evaluate("() => __reloads") == 0
    assert page.locator("#gpConfirmDialog.active").count() == 0


def test_assistant_reload_does_not_discard_edits_made_after_the_save(save_page, live_server: str):
    page = save_page
    page.goto(live_server + "/dashboard/?period=all")
    course_id = page.locator("#my-courses .course-card[data-course-id]").first.get_attribute(
        "data-course-id"
    )
    page.goto(live_server + "/dashboard/courses/" + course_id + "/assistant")
    page.wait_for_timeout(700)
    page.evaluate("""() => {
      const fetch = window.fetch; window.__toolResponse = null; window.__reloads = 0;
      GP.reloadKeepScroll = window.reloadKeepScroll = () => { __reloads++; };
      window.fetch = (url, options) => options?.method === 'POST'
        && String(url).endsWith('/assistant/tools')
        ? new Promise(resolve => { __toolResponse = () => resolve(
          new Response('{"ok":true}', {status: 200,
            headers: {'Content-Type': 'application/json'}})); }) : fetch(url, options);
    }""")
    page.locator("#conflict_file_path").fill("saved.txt")
    page.locator("#btnSaveAssistantTools").click()
    page.wait_for_function("() => !!__toolResponse")
    page.evaluate("() => __toolResponse()")
    page.wait_for_function("() => !GP.hasDirtyReason('assistant_tools')")
    page.locator("#conflict_file_path").fill("after-save.txt")
    page.wait_for_timeout(1000)
    assert page.evaluate("() => __reloads") == 0
    assert page.evaluate("() => GP.hasDirtyReason('assistant_tools')")
