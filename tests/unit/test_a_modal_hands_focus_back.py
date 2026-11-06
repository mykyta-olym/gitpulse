"""A modal puts focus where the reader will type and gives it back when it
closes.

It used to focus the first focusable element in DOM order - the "x" in the
header - so every modal opened with its close button highlighted, one Enter
from closing; and on close it blurred whatever was focused and stopped, so a
keyboard user was dropped at the top of the document after every modal.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODAL_JS = (REPO / "src/app/templates/static/js/_parts/core/10-modals.js").read_text(
    encoding="utf-8"
)


def test_focus_lands_on_the_first_field_not_the_close_button() -> None:
    body = MODAL_JS.split("function _focusFirstModalField(", 1)[1].split("\n}", 1)[0]
    assert "[data-modal-close], .modal-close, a[href]" in body
    assert "querySelector('.modal-body')" in body
    assert "target.focus({ preventScroll: true })" in body


def test_focus_returns_to_the_opener_on_close() -> None:
    assert "modal._gpOpener = (opener && opener !== document.body" in MODAL_JS
    cleanup = MODAL_JS.split("function _cleanup() {", 1)[1].split("\n  }", 1)[0]
    assert "back.focus({ preventScroll: true })" in cleanup
    assert "!_modalState.openStack.length" in cleanup, "a confirm over a form must not steal focus"


def test_a_phone_does_not_get_the_keyboard_with_the_modal() -> None:
    """Autofocus into a text field is a hardware-keyboard affordance.

    On touch it raised the on-screen keyboard over half the dialog before the
    reader had decided to type anything - on EVERY modal, including the ones
    with nothing to type into (Run Checks is tick-the-boxes-and-press-Run, and
    it opened with its list of checks hidden behind the keyboard). A focused
    field then collects whatever the keyboard emits, so closing the modal
    asked "You have unsaved changes. Discard?" for something never typed.
    """
    body = MODAL_JS.split("function _focusFirstModalField(", 1)[1].split("\n}", 1)[0]
    assert "_isTouchPointer()" in body
    assert "_isTypable(target)" in body
    assert "target = modal" in body, "touch must fall back to the dialog, not skip focus"
    # the dialog still takes focus, so Escape and the announcement keep working
    assert "modal.setAttribute('tabindex', '-1')" in body
    assert "'(pointer: coarse)'" in MODAL_JS
