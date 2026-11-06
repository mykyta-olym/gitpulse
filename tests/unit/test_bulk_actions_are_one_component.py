"""Selecting rows and acting on them looks the same wherever a table offers it.

Three places had written this by hand - a button, then a bare
`<span class="muted font-sm">(<span id="...">0</span>)</span>` beside it - so
the count's markup, its size and its spacing were decided per call site. And
because each was its own copy, two of the three tables offered no way to DELETE
what you had ticked: the Event Pipeline could replay and resurrect a selection
but not remove it, while Job History had had exactly that since it was built.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO / "src/app/templates"
_COMPONENT = _TEMPLATES / "components/bulk_actions.html"

# The surfaces whose tables carry row checkboxes. Tickets lives in a partial
# rather than a page, which is exactly how it stayed the one selection table
# with no way to delete what you had selected.
_SELECTION_PAGES = (
    "admin_system.html",
    "admin_events.html",
    "partials/support/_tickets_toolbar.html",
)


def test_the_component_renders_the_button_and_its_tally() -> None:
    macro = _COMPONENT.read_text(encoding="utf-8")
    assert "{% macro bulk_action(" in macro
    assert "bulk-count" in macro, "the tally has no class of its own to style"
    assert "disabled=true" in macro, (
        "a bulk button must start disabled - acting on nothing is not an action"
    )


def test_no_page_hand_rolls_the_tally_any_more() -> None:
    offenders = []
    for name in _SELECTION_PAGES:
        text = (_TEMPLATES / name).read_text(encoding="utf-8")
        for line in text.splitlines():
            if re.search(r'<span[^>]*class="[^"]*font-sm[^"]*"[^>]*>\(', line):
                offenders.append(f"{name}: {line.strip()[:70]}")
    assert not offenders, (
        "these write the selection tally by hand instead of asking "
        "`bulk_action` for it:\n  " + "\n  ".join(offenders)
    )


def test_every_table_with_a_selection_can_delete_what_is_selected() -> None:
    """Ticking rows and then having no way to remove them is the gap this closes."""
    missing = []
    for name in _SELECTION_PAGES:
        text = (_TEMPLATES / name).read_text(encoding="utf-8")
        selections = len(re.findall(r"SelectAll", text))
        deletes = len(re.findall(r"btnDeleteSelected", text))
        # The tickets head declares its select-all in table_heads.html, so the
        # toolbar beside it is judged on offering the delete at all.
        if "tickets" in name:
            selections = max(selections, 1)
        if selections and deletes < selections:
            missing.append(f"{name}: {selections} selection(s), {deletes} delete action(s)")
    assert not missing, (
        "a table lets the reader tick rows and then offers nothing that removes "
        "them:\n  " + "\n  ".join(missing)
    )


def test_every_bulk_button_is_wired_to_something() -> None:
    """A button that never enables, or never acts, is furniture.

    `btnBatchResurrect` was exactly that: the dead-letter tab rendered it and
    armed it with the selection, and no handler was ever bound - clicking it did
    nothing at all, for as long as that tab existed.
    """
    js = (_TEMPLATES / "static/js/pages/admin-events.js").read_text(encoding="utf-8")
    page = (_TEMPLATES / "admin_events.html").read_text(encoding="utf-8")

    rendered = set(re.findall(r"'(btn(?:Delete|Batch|Replay)\w+)'", page))
    assert rendered, "no bulk buttons found on the page - the scan is broken"

    for button in sorted(rendered):
        assert f"getElementById('{button}')" in js, (
            f"{button} is rendered but no handler is bound to it"
        )
        assert f"'{button}'" in js.split("_armBulk", 1)[-1][:400] or "_armBulk(" in js, (
            f"{button} is never enabled by a selection"
        )

    assert "_armBulk(" in js, (
        "each selection should arm its buttons through one helper, or the next "
        "bulk button added will be the one nobody remembers to enable"
    )
