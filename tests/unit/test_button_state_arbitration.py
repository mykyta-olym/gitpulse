"""Loading and done are two states competing for one button's innerHTML.

Production symptom that produced these tests: the admin System Health button
froze on "Checking..." forever. The health check succeeded, its toast handed the
button a done state, and 1.6s later the done state restored what it had
snapshotted - which was the loading label, because at snapshot time the resting
label lived in `dataset.originalText`, not in `innerHTML`.

So the two states need an explicit hand-off, in both directions.
"""

from __future__ import annotations

import re
from pathlib import Path

CORE_JS = Path(__file__).resolve().parents[2] / "src/app/templates/static/js/_parts/core"


def _helpers() -> str:
    return (CORE_JS / "21-buttons.js").read_text(encoding="utf-8")


def _fn(src: str, opening: str) -> str:
    """The body of a function, from its opening line to the next top-level one."""
    body = src.split(opening, 1)[1]
    end = body.find("\nfunction ")
    return body if end == -1 else body[:end]


def test_done_state_resets_loading_before_snapshotting_the_label() -> None:
    """setButtonDone must clear the loading chrome before it snapshots.

    A loading button carries a spinner element inside it, so snapshotting the
    live `innerHTML` would capture the spinner and paint it back when the done
    state ends. Clearing the loading chrome first makes the snapshot correct by
    construction.
    """
    body = _fn(_helpers(), "function _setButtonOutcome(btn, kind, label) {")
    reset_at = body.index("_applyButtonLoadingReset(btn)")
    snapshot_at = body.index("btn.dataset.outcomeRestore = btn.innerHTML")
    assert reset_at < snapshot_at, "the loading reset must run BEFORE the snapshot"
    assert "_applyButtonLoadingReset(btn);" in body


def test_done_state_cancels_the_pending_spinner() -> None:
    """Completion cancels an unpainted spinner before it snapshots the label."""
    body = _fn(_helpers(), "function clearButtonLoadingChrome(btn) {")
    assert "clearTimeout(btn._loadingArmed)" in body
    assert "btn._loadingArmed = 0" in body


def test_loading_reset_defers_to_an_active_done_state() -> None:
    """setButtonLoading(btn, false) must not wipe a done state already showing.

    The done state consumed the loading state when it took over and holds the
    label to restore; letting the reset run would blank the green "Done" one
    frame after it appeared.
    """
    # The arbitration lives in _setButtonLoadingState now: setButtonLoading
    # only ARMS the state, so that work finishing in a few milliseconds paints
    # nothing at all. The ordering it guards is unchanged.
    body = _fn(_helpers(), "function _setButtonLoadingState(btn, loading) {")
    assert "if (!btn._outcomeTimer) _applyButtonLoadingReset(btn);" in body


def test_a_new_click_supersedes_a_showing_done_state() -> None:
    """Loading must tear the done state down before it paints its own state.

    The loading state adds a spinner to whatever the button currently holds. If
    the done state were still up, the spinner would land next to the green tick
    and the label the done state restores afterwards would be the wrong one.
    """
    body = _fn(_helpers(), "function _setButtonLoadingState(btn, loading) {")
    clear_at = body.index("_clearButtonOutcome(btn)")
    paint_at = body.index("GP.renderSpinnerHtml")
    assert clear_at < paint_at


def test_the_loading_state_never_rewrites_the_label() -> None:
    """It inserts a spinner and leaves the label alone.

    Replacing `innerHTML` with a loading label - or letting CSS blank the button
    with `color: transparent` - is what made a working control deform into an
    empty box, and it is why there used to be two loading mechanisms.
    """
    body = _fn(_helpers(), "function _setButtonLoadingState(btn, loading) {")
    assert "innerHTML" not in body
    src = _helpers()
    # One mechanism, so neither the second signature nor its class survives.
    assert "function setButtonLoading(btn, loading = true)" in src
    assert "btn-loading-text" not in src.replace("`.btn-loading-text`", "")


def test_done_teardown_is_one_shared_function() -> None:
    """Ending a done state happens two ways - the timer, and a new click.

    Both go through `_clearButtonOutcome`; a second inline copy is exactly the
    duplicate-pattern drift this codebase keeps paying for.
    """
    src = _helpers()
    assert "function _clearButtonOutcome(btn) {" in src
    assert src.count("delete btn.dataset.outcomeRestore") == 1


def test_a_button_can_report_a_failure_and_not_only_a_success() -> None:
    """The app shipped a done state and no error state at all for a long time.

    A button whose action failed returned to its resting label as though nothing
    had been asked of it, and the only evidence was a toast in the corner. Both
    answers are the same state now, so the failing one cannot go missing again
    without this failing too.
    """
    src = _helpers()
    assert "function setButtonError(btn, label) {" in src
    assert "GP.setButtonError = setButtonError" in src
    # Two answers, one mechanism: neither is allowed its own private routine.
    for outcome in ("setButtonDone", "setButtonError"):
        line = next(ln for ln in src.splitlines() if ln.startswith(f"function {outcome}("))
        assert "_setButtonOutcome(btn, " in line, (
            f"{outcome} grew a body of its own; that asymmetry is how the error "
            "state came to be missing in the first place"
        )


def test_a_failure_releases_the_button_it_was_paired_with() -> None:
    """The pairing must be consumed by EITHER answer, not only by success.

    While only a success released it, a failed action stayed armed for 30s and
    the next success toast from anywhere painted a green tick on the control
    that had just failed.
    """
    src = _helpers()
    base = (CORE_JS / "09-toasts.js").read_text(encoding="utf-8")
    assert "GP._markActiveActionFailed" in src
    assert "GP._markActiveActionFailed()" in base, (
        "showToast never forwards a failure, so nothing releases the pairing"
    )
    # The release happens before the outcome is painted, so an expired pairing
    # still clears rather than lingering to be collected later.
    body = _fn(src, "function _markActiveActionOutcome(kind) {")
    assert body.index("_activeActionButton = null") < body.index("startedAt > 30000")


def test_the_loading_reset_defers_to_the_read_only_guard_on_an_archived_course() -> None:
    """Only a button the guard locked stays disabled after loading.

    The reset used to lock every button under `.is-course-archived` unless it
    carried `data-readonly-ok`, so a Reload the guard had left live worked once
    and then sat greyed out on every archived course where the tag was missed.
    The guard marks what it locks (`data-archived-locked`); the reset reads
    that mark and nothing else.
    """
    body = _fn(_helpers(), "function refreshButtonDisabledState(btn, wasDisabled = false) {")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", body, flags=re.DOTALL)
    assert "'archivedLocked'" in code
    assert ".is-course-archived" not in code
    assert "data-readonly-ok" not in code
    reset = _fn(_helpers(), "function _applyButtonLoadingReset(btn) {")
    assert "refreshButtonDisabledState(btn)" in reset


STATIC_JS = CORE_JS.parents[1]


def _guards() -> str:
    return (STATIC_JS / "process-action-guards.js").read_text(encoding="utf-8")


def test_the_cooldown_retires_an_outcome_before_it_snapshots_the_label() -> None:
    """A failed Sync came back from its 5s countdown reading "Failed" for good.

    The toast that announces the failure paints the red outcome before the
    handler applies the cooldown, so the cooldown's snapshot was the outcome
    markup and that is what the countdown restored: "Failed" in an icon-only
    control, its icon gone. The cooldown must retire the outcome first, and
    give back the aria-label and tooltip it borrows for "Wait Ns".
    """
    body = _guards().split("function _applyCooldown(el) {", 1)[1].split("\n  function ", 1)[0]
    retire_at = body.index("GP.clearButtonOutcome(el)")
    assert retire_at < body.index("el.dataset.cooldownLabel = savedLabel")
    assert "GP.clearButtonOutcome = _clearButtonOutcome" in _helpers()
    clear = _guards().split("function _clearCooldown(el) {", 1)[1].split("\n  function ", 1)[0]
    assert "el.setAttribute('aria-label', el.dataset.cooldownAria)" in clear
    assert "el.dataset.tippyContent = el.dataset.cooldownTip" in clear


def test_server_verification_keeps_process_locks_until_confirmed() -> None:
    """Finishing now means pending server verification, never a cosmetic hold."""
    active = _guards().split("function isJobActive(job) {", 1)[1].split("}", 1)[0]
    assert "job.status !== 'finishing'" not in active
    assert "job.status !== 'done'" in active
    assert "job.status !== 'error'" in active
    bar = (STATIC_JS / "_parts/global-job-bar/10-sse-render.js").read_text(encoding="utf-8")
    running = bar.split("function isGlobalJobRunning(jobType) {", 1)[1].split("}", 1)[0]
    assert "job.status !== 'finishing'" not in running


def test_an_icon_only_button_keeps_the_outcome_word_out_of_sight() -> None:
    """In a 24px square the word has no room: it shrank to a 2px sliver of its
    first letter beside the mark and pushed the mark off centre (the "strip on
    the right" of the green tick). A control whose resting label has no text
    gets the word as accessible name only, at every width."""
    body = _fn(_helpers(), "function _setButtonOutcome(btn, kind, label) {")
    assert "_probe.innerHTML = btn.dataset.outcomeRestore" in body
    assert "'btn-outcome-label sr-only'" in body
    assert "'btn-outcome-label sr-only-sm'" in body
