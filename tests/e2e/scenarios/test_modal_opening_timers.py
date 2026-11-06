"""Delayed modal work belongs to the opening that scheduled it."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip("modal timer checks need a running server", allow_module_level=True)


@pytest.fixture(params=["desktop", "mobile", "reduced", "no-gsap"])
def timer_page(browser, context_for, live_server: str, request):
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
        page.wait_for_function("() => !!window.GP?.confirmDialog")
        yield page
        assert not errors, errors


@pytest.mark.parametrize("confirmation", [False, True])
def test_closing_dialogs_cannot_receive_delayed_focus(timer_page, confirmation: bool):
    events = timer_page.evaluate(
        """async confirmation => {
          const id = confirmation ? 'gpConfirmDialog' : 'createCourseModal';
          const events = [];
          const record = event => {
            if (event.target.closest('#' + id + '.closing')) events.push(event.target.id);
          };
          document.addEventListener('focusin', record);
          if (confirmation) GP.confirmDialog({message: 'Cancel immediately'});
          else GP.openModal(id);
          GP.forceCloseModal(id);
          await new Promise(resolve => setTimeout(resolve, 120));
          document.removeEventListener('focusin', record);
          return events;
        }""",
        confirmation,
    )
    assert events == [], "a closing dialog received focus from its opening timer"


def test_a_new_top_dialog_prevents_background_autofocus(timer_page):
    result = timer_page.evaluate("""async () => {
      const events = [];
      const record = event => {
        if (event.target.closest('#createCourseModal')) events.push(event.target.id);
      };
      document.addEventListener('focusin', record);
      GP.openModal('createCourseModal');
      GP.openModal('importConfigCourseModal');
      await new Promise(resolve => setTimeout(resolve, 120));
      document.removeEventListener('focusin', record);
      return {events, insideTop: document.getElementById('importConfigCourseModal')
        .contains(document.activeElement)};
    }""")
    assert result == {"events": [], "insideTop": True}


def test_autofocus_preserves_a_field_chosen_before_the_timer(timer_page):
    timer_page.evaluate("""() => {
      GP.openModal('createCourseModal');
      document.getElementById('courseName').focus();
    }""")
    timer_page.wait_for_timeout(120)
    assert timer_page.evaluate("() => document.activeElement.id") == "courseName"


def test_confirmation_keeps_its_safe_initial_focus(timer_page):
    result = timer_page.evaluate("""async () => {
      GP.confirmDialog({message: 'Keep the safe control focused'});
      await new Promise(resolve => requestAnimationFrame(resolve));
      const root = document.getElementById('gpConfirmDialog');
      const safe = root.querySelector('[data-gp-confirm="cancel"]');
      const startedSafe = document.activeElement === safe;
      await new Promise(resolve => setTimeout(resolve, 120));
      return {startedSafe, stayedSafe: document.activeElement === safe};
    }""")
    assert result == {"startedSafe": True, "stayedSafe": True}


def test_superseded_confirmation_frame_cannot_choose_its_old_control(timer_page):
    result = timer_page.evaluate("""async () => {
      const events = [];
      GP.confirmDialog({message: 'First confirmation'});
      GP.confirmDialog({message: 'Replacement', requireTyping: true, expectedValue: 'KEEP'});
      const root = document.getElementById('gpConfirmDialog');
      const input = root.querySelector('input');
      const record = event => {
        if (root.contains(event.target) && event.target !== input) {
          events.push(event.target.tagName);
        }
      };
      document.addEventListener('focusin', record);
      await new Promise(resolve => setTimeout(resolve, 120));
      document.removeEventListener('focusin', record);
      return {events, inputFocused: document.activeElement === input};
    }""")
    assert result == {"events": [], "inputFocused": True}


def test_an_old_opening_cannot_end_the_reopened_animation(timer_page):
    states = timer_page.evaluate("""async () => {
      const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
      const root = document.getElementById('createCourseModal');
      GP.openModal(root.id);
      await wait(120);
      GP.forceCloseModal(root.id);
      await wait(30);
      GP.openModal(root.id);
      await wait(280);
      const stillAnimating = root.classList.contains('modal-animating');
      const pointerBlocked = getComputedStyle(root.querySelector('input')).pointerEvents === 'none';
      await wait(200);
      return {stillAnimating, finished: !root.classList.contains('modal-animating'),
        pointerBlocked, pointerRestored: getComputedStyle(root.querySelector('input'))
          .pointerEvents !== 'none',
        active: root.classList.contains('active'), closing: root.classList.contains('closing')};
    }""")
    assert states == {
        "stillAnimating": True,
        "finished": True,
        "pointerBlocked": True,
        "pointerRestored": True,
        "active": True,
        "closing": False,
    }
