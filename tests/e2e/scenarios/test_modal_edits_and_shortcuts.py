"""Unsaved edits and keyboard actions survive modal transitions."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal interactions need a running server", allow_module_level=True)


@pytest.mark.parametrize(("delay", "width"), [(0, 1440), (120, 1440), (450, 1440), (120, 390)])
def test_edits_during_entrance_still_require_discard_confirmation(
    context_for, live_server: str, delay: int, width: int
) -> None:
    page = context_for("admin", width, 900).new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.openModal")
    page.evaluate("() => GP.openModal('createCourseModal')")
    page.wait_for_timeout(delay)
    page.locator("#createCourseModal input[type=text]").first.fill("AUDIT-UNSAVED")
    page.wait_for_timeout(750)

    assert page.evaluate("() => GP.hasUnsavedState()")
    page.locator("#createCourseModal .modal-close").click()
    page.wait_for_function("() => document.querySelector('#gpConfirmDialog.active')")
    page.locator("#gpConfirmDialog .btn-secondary").click()
    page.keyboard.press("Tab")
    assert page.evaluate(
        "() => document.getElementById('createCourseModal').contains(document.activeElement)"
    )
    page.wait_for_timeout(250)
    assert page.locator("#createCourseModal.active").count() == 1
    assert (
        page.locator("#createCourseModal input[type=text]").first.input_value() == "AUDIT-UNSAVED"
    )


@pytest.mark.parametrize("key", ["?", "Shift+?"])
def test_question_mark_opens_shortcut_help(context_for, live_server: str, key: str) -> None:
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.showToast")
    # The saved developer account may have disabled shortcuts. This scenario
    # explicitly exercises the enabled state, without changing saved settings.
    page.evaluate("() => document.documentElement.removeAttribute('data-no-shortcuts')")
    page.keyboard.press(key)
    page.wait_for_function(
        "() => [...document.querySelectorAll('.toast')].some(t => t.textContent.includes('Ctrl+K'))"
    )
    count = page.locator(".toast").count()
    page.evaluate("() => document.documentElement.setAttribute('data-no-shortcuts', '1')")
    page.keyboard.press(key)
    assert page.locator(".toast").count() == count


def test_save_shortcut_uses_preferences_and_leaves_the_background_form_alone(
    context_for, live_server: str
) -> None:
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/preferences")
    page.wait_for_timeout(750)
    # Count real submits while keeping the test from persisting preferences.
    page.evaluate("""() => {
      window.__saves = 0;
      document.getElementById('preferencesForm').addEventListener('submit', event => {
        event.preventDefault(); event.stopImmediatePropagation(); window.__saves++;
      }, true);
    }""")
    page.locator("#preferencesForm input[name=keyboard_shortcuts_enabled]").check()
    page.locator("#preferencesForm input[name=use_relative_times]").click()
    assert not page.evaluate("() => document.documentElement.hasAttribute('data-no-shortcuts')")
    page.keyboard.press("Control+s")
    assert page.evaluate("() => window.__saves") == 1
    page.evaluate("() => { GP.confirmDialog({message: 'Keep editing?'}); }")
    page.wait_for_timeout(250)
    page.keyboard.press("Control+s")
    assert page.evaluate("() => window.__saves") == 1


@pytest.mark.parametrize("mode", ["normal", "reduced", "no-gsap"])
def test_confirmation_resolves_on_programmatic_close_and_confirm(
    context_for, live_server: str, mode: str
) -> None:
    page = context_for("admin").new_page()
    page.bring_to_front()
    if mode == "reduced":
        page.emulate_media(reduced_motion="reduce")
    if mode == "no-gsap":
        page.route(
            "**/gsap-3.15.0.min.js*",
            lambda route: route.fulfill(body="", content_type="application/javascript"),
        )
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.confirmDialog")
    assert page.evaluate("() => !!window.gsap") is (mode != "no-gsap")
    for confirm in (False, True):
        page.evaluate("""() => {
          window.__answer = 'pending';
          GP.confirmDialog({message: 'Continue?'}).then(value => window.__answer = value);
        }""")
        page.wait_for_timeout(250)
        if confirm:
            page.locator('#gpConfirmDialog [data-gp-confirm="ok"]').click()
        else:
            page.evaluate("() => GP.closeModal('gpConfirmDialog')")
        page.wait_for_function("value => window.__answer === value", arg=confirm)
        page.wait_for_function("() => !document.querySelector('#gpConfirmDialog.active')")


def test_tab_stays_inside_a_dialog_that_initially_focuses_its_container(
    context_for, live_server: str
) -> None:
    page = context_for("admin").new_page()
    page.bring_to_front()
    page.goto(live_server + "/dashboard/")
    page.wait_for_function("() => !!window.GP?.confirmDialog")
    page.evaluate("() => { GP.confirmDialog({message: 'Keyboard focus'}); }")
    page.wait_for_timeout(350)
    page.keyboard.press("Shift+Tab")
    assert page.evaluate(
        "() => document.getElementById('gpConfirmDialog').contains(document.activeElement)"
    )
    page.keyboard.press("Tab")
    assert page.evaluate(
        "() => document.getElementById('gpConfirmDialog').contains(document.activeElement)"
    )


def test_swiping_dirty_form_and_confirmation_targets_the_touched_dialog(
    browser, context_for, live_server: str
) -> None:
    with browser.new_context(
        storage_state=context_for("admin").storage_state(),
        viewport={"width": 390, "height": 844},
        is_mobile=True,
        has_touch=True,
    ) as ctx:
        page = ctx.new_page()
        page.bring_to_front()
        page.goto(live_server + "/dashboard/")
        page.wait_for_function("() => !!window.GP?.openModal")
        page.evaluate("() => GP.openModal('createCourseModal')")
        page.wait_for_timeout(750)
        page.locator("#createCourseModal input[type=text]").first.fill("AUDIT-UNSAVED")
        cdp = ctx.new_cdp_session(page)

        def drag_header(selector: str) -> None:
            header = page.locator(selector + " .modal-header").bounding_box()
            assert header
            x, y = header["x"] + 90, header["y"] + 25
            cdp.send(
                "Input.dispatchTouchEvent",
                {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]},
            )
            for offset in (20, 50, 90, 150):
                cdp.send(
                    "Input.dispatchTouchEvent",
                    {"type": "touchMove", "touchPoints": [{"x": x, "y": y + offset}]},
                )
                page.wait_for_timeout(35)

        drag_header("#createCourseModal")
        page.evaluate("""() => {
          window.__positions = [];
          const start = performance.now();
          (function sample() {
            const box = document.querySelector('#createCourseModal .modal').getBoundingClientRect();
            window.__positions.push(box.top);
            if (performance.now() - start < 400) requestAnimationFrame(sample);
          })();
        }""")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(500)
        positions = page.evaluate("() => window.__positions")
        assert max(positions) <= positions[0] + 2, "a vetoed close still threw the form off-screen"
        assert page.locator("#gpConfirmDialog.active").count() == 1

        # Capture the cancellation promise as well as which sheet moves.
        page.evaluate("""() => {
          window.__answer = 'pending';
          GP.confirmDialog({message: 'Swipe to cancel'}).then(value => window.__answer = value);
        }""")
        page.wait_for_timeout(300)
        drag_header("#gpConfirmDialog")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_function("() => window.__answer === false")
        assert page.locator("#createCourseModal.active").count() == 1
        assert page.locator("#gpConfirmDialog.active").count() == 0
