"""Fast reads cancel the delayed spinner; completed work is never held.

Each assertion below is a bug that shipped:

* An armed spinner must not appear after a request has completed.
* The checkmark inside a checkbox is an absolutely-positioned `::after`, so the
  box must stay its own containing block. A mobile rule set `position: static`
  and the tick anchored to `.modal-body` instead: measured 970px away from its
  checkbox, which is why a checked box on a phone showed no checkmark at all.
* A tooltip left mounted during a scroll makes Popper recompute its position
  every frame. Profiled at 4x CPU throttle on System Health: 12 long tasks and
  ~960ms of blocked main thread across one 2.5s scroll.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATIC = _REPO / "src/app/templates/static"
_CORE_JS = _STATIC / "js/_parts/core"
_BUTTONS_JS = _CORE_JS / "21-buttons.js"
_STATES_JS = _CORE_JS / "22-content-states.js"
_TOOLTIPS_JS = _CORE_JS / "26-tooltips.js"
_MODALS_CSS = _STATIC / "css/modals.css"
_FORMS_CSS = _STATIC / "css/forms.css"


def test_done_state_retires_the_loading_state_without_a_delay() -> None:
    src = _BUTTONS_JS.read_text(encoding="utf-8")
    body = src[src.index("function _setButtonOutcome(") : src.index("function setButtonDone(")]

    assert "_applyButtonLoadingReset(btn)" in body
    assert "_MIN_LOADING_MS" not in src
    assert "_outcomeDeferred" not in src
    clear = src.split("function clearButtonLoadingChrome(btn)", 1)[1].split("\n}", 1)[0]
    assert "clearTimeout(btn._loadingArmed)" in clear


def test_busy_state_thresholds_are_declared_once() -> None:
    src = _BUTTONS_JS.read_text(encoding="utf-8") + _STATES_JS.read_text(encoding="utf-8")
    declarations = re.findall(r"^const _BUSY_DELAY_MS = (\d+);", src, re.MULTILINE)
    assert len(declarations) == 1
    assert 0 < int(declarations[0]) <= 200


def _no_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def test_checkbox_stays_its_own_containing_block() -> None:
    """The tick is `position: absolute` inside the box - never `static`."""
    forms = _no_comments(_FORMS_CSS.read_text(encoding="utf-8"))
    assert "position: relative" in forms[forms.index(".form-check-input {") :][:600], (
        ".form-check-input must be positioned - its ::after checkmark is placed against it"
    )

    modals = _no_comments(_MODALS_CSS.read_text(encoding="utf-8"))
    blocks = re.findall(r"\.modal-body \.form-check-input \{[^}]*\}", modals, re.DOTALL)
    assert blocks, "the mobile checkbox rule vanished - this test guards nothing"
    for block in blocks:
        assert "position: static" not in block, (
            "position: static hands the ::after checkmark to .modal-body, which "
            "paints it hundreds of pixels away from its checkbox"
        )


def test_tooltips_do_not_survive_a_scroll() -> None:
    src = _TOOLTIPS_JS.read_text(encoding="utf-8")
    assert "_hideTippyOnScroll" in src, "the scroll handler that hides tooltips is gone"
    assert "hideAll" in src, "hiding on scroll must actually hide them"
    assert "_scrollingUntil" in src, (
        "a scroll drags elements under a stationary cursor and every mouseenter "
        "opens a tooltip; showing has to be suppressed while scrolling"
    )
    assert "scroll: false" in src, (
        "Popper's scroll listener must be off - the tooltip hides on scroll, so "
        "it has nothing to follow"
    )
