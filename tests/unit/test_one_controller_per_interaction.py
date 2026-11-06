"""One interaction, one controller.

Every time this codebase grew a second controller for something it already
handled, the two drifted and the drift shipped as a bug:

* Two click rate guards - a silent per-element debounce in core and a "3 clicks
  in 2s -> visible cooldown" pass in process-action-guards.js. They disagreed
  about disclosure controls, so a tree toggle survived one and died on the
  other, with the third click producing no click event at all.
* Two dropdown controllers - class-based `.gl-dropdown` in core and
  attribute-based `[data-dropdown]` in dropdowns.js. Each had to know about the
  other to keep `.open` in sync, and when that broke the menu opened once and
  then reported itself permanently closed.

Both are merged. These assertions are cheap; re-introducing a parallel
controller is not.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATIC = _REPO / "src/app/templates/static"
_GUARDS_JS = _STATIC / "js/process-action-guards.js"
_CORE_JS = _STATIC / "js/_parts/core"
_LOCK_JS = _CORE_JS / "33-anti-spam.js"
_DROPDOWNS_JS = _STATIC / "js/dropdowns.js"


def test_one_click_rate_guard() -> None:
    guards = _GUARDS_JS.read_text(encoding="utf-8")
    lock = _LOCK_JS.read_text(encoding="utf-8")

    assert "interceptSpamClicks" not in guards, (
        "the second click rate guard is back - rate-limiting belongs to "
        "_antiSpamClickLock in core/33-anti-spam.js alone"
    )
    assert "_antiSpamClickLock" in lock, "the surviving click lock disappeared"
    assert "_applyCooldown" in guards, (
        "the cooldown itself must stay: page-level error handlers call "
        "GP.applyCooldown after a failed action"
    )
    for attr in ("aria-expanded", "aria-pressed"):
        assert f"hasAttribute('{attr}')" in lock, (
            f"the click lock must exempt {attr} controls - they flip local state "
            "and issue no request, so a cooldown only freezes the widget"
        )


def test_one_dropdown_controller() -> None:
    core = "".join(p.read_text(encoding="utf-8") for p in sorted(_CORE_JS.glob("*.js")))
    dropdowns = _DROPDOWNS_JS.read_text(encoding="utf-8")

    assert "_initGlobalDropdowns" not in core, (
        "the class-based dropdown handler is back in core - dropdowns.js owns "
        "every dropdown now, through both selector conventions"
    )
    # It owns both conventions, so no markup had to change when they merged.
    assert "'[data-dropdown], .gl-dropdown'" in dropdowns
    assert "'[data-dropdown-toggle], .gl-dropdown-toggle'" in dropdowns
    assert "'[data-dropdown-menu], .gl-dropdown-menu'" in dropdowns
    # Behaviours that only ever lived in the deleted handler.
    assert "data-gl-portal" in dropdowns, (
        "a menu portaled to <body> must not count as an outside click"
    )
    assert "ITEM_SELECTOR" in dropdowns, "choosing an item must close its menu"
    # Alpine still owns its own dropdowns; a second writer fights its :class.
    assert "isAlpineManaged" in dropdowns


def test_only_the_shared_controller_toggles_dropdowns() -> None:
    """No second handler may answer a click on `.gl-dropdown-toggle`.

    The pagination page-size menu had its own: it caught the toggle click,
    called stopPropagation() so the shared controller never saw it, and
    re-implemented open/close to add portaling. The menu then stopped opening
    at all, because the markup is injected by innerHTML and nothing
    initialised it. Portaling is an option of the shared controller now
    (`data-dropdown-portal`), so a second handler has nothing left to add.
    """
    js_dir = _STATIC / "js"
    owners = []
    for path in sorted(js_dir.rglob("*.js")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        # A handler that reacts to a toggle click, in any quoting style.
        if re.search(r"closest\(\s*['\"][^'\"]*gl-dropdown-toggle", text):
            owners.append(path.relative_to(js_dir).as_posix())

    allowed = {"dropdowns.js", "_parts/core/33-anti-spam.js", "_parts/core/35-dropdown-menu.js"}
    unexpected = sorted(set(owners) - allowed)
    assert not unexpected, (
        f"these also answer a dropdown-toggle click: {unexpected}. "
        f"Opening and closing a dropdown belongs to dropdowns.js; if a menu needs "
        f"to escape `overflow: hidden`, mark its root with data-dropdown-portal."
    )
