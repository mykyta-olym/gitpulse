"""A temporary button lock releases into the current form state."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("button lock checks need a running server", allow_module_level=True)


@pytest.fixture(params=[390, 1440])
def lock_page(browser, context_for, live_server: str, request):
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
          const button = document.getElementById('preferencesSave');
          button.dataset.processLockWhen = 'sync';
          button.dataset.processLockScope = 'course:lock-probe';
          window.__initial = document.getElementById('diff_color_removed').value;
          window.__label = button.textContent.trim();
        }""")
        yield page
        assert not errors, errors


def _job(page, active: bool):
    page.evaluate(
        """active => {
          window._globalJobs = window._globalJobs || {};
          if (active) _globalJobs['sync:course:lock-probe'] = {status: 'running',
            meta: {jobKind: 'course_sync', courseId: 'lock-probe'}};
          else delete _globalJobs['sync:course:lock-probe'];
          GP.refreshProcessActionGuards();
        }""",
        active,
    )


def _assert_state(page, dirty: bool, disabled: bool):
    assert page.evaluate("() => GP.hasDirtyReason('preferences_form')") == dirty
    assert page.locator("#preferencesSave").is_disabled() == disabled
    if not disabled:
        assert page.locator("#preferencesSave").get_attribute("aria-disabled") is None
        assert not page.locator("#preferencesSave").evaluate(
            "b => b.classList.contains('is-disabled')"
            " || b.parentElement.classList.contains('gl-tip-wrap')"
        )


@pytest.mark.parametrize("initially_dirty", [False, True])
@pytest.mark.parametrize("finally_dirty", [False, True])
def test_process_completion_uses_current_edits(
    lock_page, initially_dirty: bool, finally_dirty: bool
):
    page = lock_page
    initial = page.evaluate("() => __initial")
    if initially_dirty:
        page.locator("#diff_color_removed").fill("#112233")
    _job(page, True)
    page.locator("#diff_color_removed").fill("#445566" if finally_dirty else initial)
    _assert_state(page, finally_dirty, True)
    _job(page, False)
    _assert_state(page, finally_dirty, not finally_dirty)
    if not finally_dirty:
        assert page.locator("#preferencesSave").evaluate(
            "b => !!b.parentElement.dataset.disabledReason"
        )


@pytest.mark.parametrize("order", ["process-first", "cooldown-first"])
@pytest.mark.parametrize("dirty", [False, True])
def test_process_and_cooldown_release_in_either_order(lock_page, order: str, dirty: bool):
    page = lock_page
    if dirty:
        page.locator("#diff_color_removed").fill("#112233")
    _job(page, True)
    page.evaluate("() => GP.applyCooldown(document.getElementById('preferencesSave'))")
    if order == "process-first":
        _job(page, False)
    else:
        page.evaluate("() => GP.clearCooldown(document.getElementById('preferencesSave'))")
    _assert_state(page, dirty, True)
    if order == "process-first":
        page.evaluate("() => GP.clearCooldown(document.getElementById('preferencesSave'))")
    else:
        _job(page, False)
    _assert_state(page, dirty, not dirty)
    assert page.locator("#preferencesSave").inner_text() == page.evaluate("() => __label")


@pytest.mark.parametrize("lock", ["loading", "syncLocked", "archivedLocked"])
def test_finishing_a_process_preserves_another_owner(lock_page, lock: str):
    page = lock_page
    page.locator("#diff_color_removed").fill("#112233")
    _job(page, True)
    page.evaluate(
        """lock => {
          const b = document.getElementById('preferencesSave');
          if (lock === 'loading') GP.setButtonLoading(b, true);
          else b.dataset[lock] = '1';
        }""",
        lock,
    )
    _job(page, False)
    _assert_state(page, True, True)
    if lock == "loading":
        page.wait_for_timeout(250)
        page.evaluate(
            "() => GP.setButtonLoading(document.getElementById('preferencesSave'), false)"
        )
        page.wait_for_timeout(500)
    else:
        page.evaluate(
            """lock => { const b = document.getElementById('preferencesSave');
              delete b.dataset[lock]; GP.refreshButtonDisabledState(b); }""",
            lock,
        )
    _assert_state(page, True, False)


@pytest.mark.parametrize("lock", ["syncLocked", "archivedLocked"])
def test_expired_cooldown_preserves_another_owner(lock_page, lock: str):
    page = lock_page
    page.locator("#diff_color_removed").fill("#112233")
    page.evaluate(
        """lock => { const b = document.getElementById('preferencesSave');
          GP.applyCooldown(b); b.dataset[lock] = '1'; GP.clearCooldown(b); }""",
        lock,
    )
    _assert_state(page, True, True)


def test_loading_toggle_leaves_a_cooldown_in_control(lock_page):
    page = lock_page
    page.locator("#diff_color_removed").fill("#112233")
    _job(page, True)
    page.evaluate("""() => {
      const b = document.getElementById('preferencesSave');
      GP.applyCooldown(b);
      delete _globalJobs['sync:course:lock-probe'];
      GP.setButtonLoading(b, false);
    }""")
    _assert_state(page, True, True)
    assert page.locator("#preferencesSave").get_attribute("data-cooldown-active") == "1"
    _job(page, False)
    page.evaluate("() => GP.clearCooldown(document.getElementById('preferencesSave'))")
    _assert_state(page, True, False)


def test_cooldown_expiry_does_not_enable_an_unchanged_save(lock_page):
    page = lock_page
    page.evaluate("() => GP.applyCooldown(document.getElementById('preferencesSave'))")
    page.wait_for_function(
        "() => !document.getElementById('preferencesSave').dataset.cooldownActive"
    )
    _assert_state(page, False, True)


@pytest.mark.parametrize("disabled", [False, True])
def test_process_keeps_a_plain_actions_original_availability(lock_page, disabled: bool):
    page = lock_page
    page.evaluate(
        """disabled => {
          const b = document.getElementById('preferencesSave');
          b.classList.remove('btn-save-guard'); b.disabled = disabled;
          GP.clearDisabledReason(b);
        }""",
        disabled,
    )
    _job(page, True)
    _job(page, False)
    assert page.locator("#preferencesSave").is_disabled() == disabled


def test_a_process_started_during_cooldown_does_not_remember_it_as_permanent(lock_page):
    page = lock_page
    page.evaluate("""() => {
      const b = document.getElementById('preferencesSave');
      b.classList.remove('btn-save-guard'); b.disabled = false;
      GP.clearDisabledReason(b); GP.applyCooldown(b);
    }""")
    _job(page, True)
    page.evaluate("() => GP.clearCooldown(document.getElementById('preferencesSave'))")
    assert page.locator("#preferencesSave").is_disabled()
    _job(page, False)
    assert page.locator("#preferencesSave").is_enabled()


def test_released_actions_use_the_shared_tooltip(lock_page):
    page = lock_page
    page.locator("#diff_color_removed").fill("#112233")
    page.evaluate("""() => {
      document.getElementById('preferencesSave').dataset.tippyContent = 'Save this draft';
    }""")
    _job(page, True)
    _job(page, False)
    page.locator("#preferencesSave").scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    page.locator("#preferencesSave").hover()
    page.locator('.tippy-box[data-state="visible"] .tippy-content').filter(
        has_text="Save this draft"
    ).wait_for()
    assert page.locator("#preferencesSave").evaluate(
        "b => b._tippy.props.popperOptions.modifiers.some("
        "m => m.name === 'eventListeners' && m.options.scroll === false)"
    )


@pytest.mark.parametrize("dirty", [False, True])
def test_settings_sync_poll_releases_the_save_guard(lock_page, live_server: str, dirty: bool):
    page = lock_page
    page.goto(live_server + "/dashboard/?period=all")
    course_id = page.locator("#my-courses .course-card[data-course-id]").first.get_attribute(
        "data-course-id"
    )
    page.route(
        "**/api/v1/courses/*/sync-status",
        lambda route: route.fulfill(json={"has_active_sync": True}),
    )
    page.goto(live_server + "/dashboard/courses/" + course_id + "/settings")
    button = page.locator("#btnSaveSettings")
    page.wait_for_function(
        "() => document.getElementById('btnSaveSettings')?.dataset.syncLocked === '1'"
    )
    page.wait_for_timeout(650)
    if dirty:
        page.locator("#course_name").fill("Draft made during synchronization")
    assert button.is_disabled()
    page.route(
        "**/api/v1/courses/*/sync-status",
        lambda route: route.fulfill(json={"has_active_sync": False}),
    )
    page.wait_for_function("() => !document.getElementById('btnSaveSettings').dataset.syncLocked")
    assert button.is_disabled() != dirty
    assert page.evaluate("() => GP.hasDirtyReason('settings_form')") == dirty
    if dirty:
        assert button.get_attribute("aria-disabled") is None
