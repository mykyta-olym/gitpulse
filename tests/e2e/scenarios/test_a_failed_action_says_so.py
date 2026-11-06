"""An action that failed has to say so on the control that started it.

The app had a done state and no error state at all: a button whose action
succeeded turned green and said "Done", and a button whose action FAILED came
back to its resting label as if nothing had been asked of it. The only evidence
was a toast in the corner, away from where the reader was looking.

Worse, the pairing that hands a control its outcome was armed by a click and
disarmed only by a SUCCESS. A failed action therefore stayed on the hook, and
the next success toast from anywhere - a poll, a background sync, another
widget - handed the button that had just failed a green tick.

Everything here is measured on a real page with the server forced to refuse,
and the button is WATCHED rather than sampled: the outcome is time-boxed, so a
single late read cannot tell "it never appeared" from "it has already gone".
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.e2e

if not os.getenv("GITPULSE_E2E_BASE_URL"):
    pytest.skip(
        "scenario walks need GITPULSE_E2E_BASE_URL pointing at a running server",
        allow_module_level=True,
    )

_SAVE = "#preferencesSave"

# Record every distinct state the button passes through, on every frame.
_WATCH = """
() => {
  window.__states = [];
  (function tick() {
    const b = document.querySelector('__SAVE__');
    if (b) {
      const s = {
        t: Math.round(performance.now()),
        done: b.classList.contains('btn-done'),
        error: b.classList.contains('btn-error'),
        disabled: b.disabled === true,
        live: b.getAttribute('aria-live'),
        text: (b.textContent || '').trim(),
      };
      const last = window.__states[window.__states.length - 1];
      if (!last || last.done !== s.done || last.error !== s.error
          || last.disabled !== s.disabled || last.text !== s.text) {
        window.__states.push(s);
      }
    }
    requestAnimationFrame(tick);
  })();
}
""".replace("__SAVE__", _SAVE)


def _open_preferences(page, live_server: str, *, refuse: bool) -> None:
    if refuse:
        page.route(
            "**/dashboard/api/preferences",
            lambda route: (
                route.fulfill(
                    status=500,
                    content_type="application/json",
                    body='{"detail":"forced by the test"}',
                )
                if route.request.method != "GET"
                else route.continue_()
            ),
        )
    page.goto(f"{live_server}/dashboard/preferences", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    page.evaluate(_WATCH)


def _edit_and_save(page) -> None:
    """Change one setting and press Save, the way a reader does."""
    changed = page.evaluate(
        """() => {
          const cb = document.querySelector('#preferencesForm input[type=checkbox][name]');
          if (!cb) return false;
          cb.click();
          return true;
        }"""
    )
    assert changed, "the preferences form has no checkbox to change"
    page.wait_for_timeout(400)
    assert not page.eval_on_selector(_SAVE, "b => b.disabled"), (
        "Save stayed disabled after a real edit - the guard never armed it, so "
        "the rest of this test would be measuring nothing"
    )
    page.evaluate(f"() => document.querySelector('{_SAVE}').click()")


def test_a_failed_save_reports_the_failure_on_its_own_button(context_for, live_server: str) -> None:
    page = context_for("admin").new_page()
    _open_preferences(page, live_server, refuse=True)
    _edit_and_save(page)
    page.wait_for_timeout(2000)

    states = page.evaluate("() => window.__states")
    failed = [s for s in states if s["error"]]
    assert failed, (
        "the save failed and the button said nothing about it; it went through "
        f"{[s['text'] for s in states]}"
    )
    assert not any(s["done"] for s in states), (
        "the button that FAILED showed the done state at some point"
    )
    assert failed[0]["live"] == "assertive", (
        "a failure has to interrupt a screen reader, not wait its turn; "
        f"aria-live was {failed[0]['live']!r}"
    )


def test_a_failure_cannot_be_overwritten_by_an_unrelated_success(
    context_for, live_server: str
) -> None:
    page = context_for("admin").new_page()
    _open_preferences(page, live_server, refuse=True)
    _edit_and_save(page)
    page.wait_for_timeout(1600)

    # Anything else in the app now succeeds - a poll, a sync, another widget.
    page.evaluate("() => showToast('Something unrelated worked', 'success')")
    page.wait_for_timeout(700)

    assert not page.eval_on_selector(_SAVE, "b => b.classList.contains('btn-done')"), (
        "an unrelated success toast painted the done state on the button whose "
        "own action had just failed"
    )
    assert page.eval_on_selector(_SAVE, "b => b.classList.contains('btn-error')"), (
        "the failure was evicted by an unrelated success"
    )


def test_a_failed_save_can_be_tried_again(context_for, live_server: str) -> None:
    """The changes are still unsaved, so the button has to stay pressable.

    A guarded Save is the one control a loading reset will not re-enable - the
    guard owns that state. Nothing asked the guard again after a failure, so the
    button that had just refused to save was disabled for good and the reader's
    edits were stranded on the page with no way to retry.
    """
    page = context_for("admin").new_page()
    _open_preferences(page, live_server, refuse=True)
    _edit_and_save(page)
    page.wait_for_timeout(4200)  # past the error state, back at rest

    assert not page.eval_on_selector(_SAVE, "b => b.disabled"), (
        "the save failed and left its own button disabled - the edits are still "
        "pending and there is now no way to save them"
    )
    assert page.eval_on_selector(
        _SAVE, "b => !b.classList.contains('btn-error') && !b.classList.contains('btn-done')"
    ), "the outcome never retired"


def test_a_save_that_worked_still_disarms_the_button(context_for, live_server: str) -> None:
    """The other half of the contract, which the failure path must not break.

    A save that SUCCEEDED leaves nothing to save, so Save goes quiet and stays
    quiet - it must not re-arm itself a second later as though the reader had
    changed something else.
    """
    page = context_for("admin").new_page()
    _open_preferences(page, live_server, refuse=False)
    _edit_and_save(page)
    page.wait_for_timeout(6000)

    states = page.evaluate("() => window.__states")
    assert any(s["done"] for s in states), "a successful save never reported itself"
    assert not any(s["error"] for s in states), "a successful save reported a failure"

    settled = states[-1]
    assert settled["disabled"], (
        "Save is armed again after a successful save, with nothing left to save; "
        f"it ended on {settled['text']!r}"
    )
