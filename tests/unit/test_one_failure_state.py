"""'This did not load' looks the same wherever it appears, and is said once.

Empty states already went through one helper (`GP.emptyStateHtml`). Their
failure twin did not: a table row in the Events list, a differently-worded
table row in the DLQ, a bare `<p class="text-danger p-4">` in the project
history, and red text written into a button on admin users - four shapes, four
sets of words, none of them offering a retry.

`GP.errorStateHtml` / `GP.errorStateRow` are that twin. They reuse the empty
state's layout on purpose, so a table does not change shape between "nothing
here" and "this did not load"; only the mark's colour and the `role="alert"`
distinguish them.

The admin-users case was a different bug wearing the same clothes: it showed
the failure in a toast AND wrote it into the button, then undid the button
after 3s. That says it twice and races anything else touching the button in
between - exactly what the refresh contract in core/22-content-states.js exists to
prevent ("the outcome is reported, and reported ONCE").
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js"
HELPERS = JS / "_parts/core/22-content-states.js"


def _sources() -> list[Path]:
    return [
        p
        for p in JS.rglob("*.js")
        if ".min." not in p.name and "bundle" not in p.name and "vendor" not in p.parts
    ]


def test_the_shared_failure_state_exists_next_to_its_twin() -> None:
    src = HELPERS.read_text(encoding="utf-8")
    for name in ("emptyStateHtml", "emptyStateRow", "errorStateHtml", "errorStateRow"):
        assert f"GP.{name} = {name};" in src, f"GP.{name} is gone"


def test_nothing_hand_writes_a_failure_row_any_more() -> None:
    offenders = {}
    for p in _sources():
        src = p.read_text(encoding="utf-8")
        hits = [
            src[: m.start()].count("\n") + 1
            for m in re.finditer(r"text-danger[^\n]{0,80}(?:Could not|Failed|Error)", src)
        ]
        if hits:
            offenders[p.relative_to(JS).as_posix()] = hits
    assert not offenders, (
        f"use GP.errorStateHtml / GP.errorStateRow instead of hand-built markup: {offenders}"
    )


def test_a_failure_is_not_reported_twice() -> None:
    """A toast AND a button label saying the same thing, with a timer undoing
    the label, is both duplicate feedback and a race."""
    src = (JS / "pages/admin-users.js").read_text(encoding="utf-8")
    assert 'btn.innerHTML = \'<span class="text-danger">' not in src


def test_only_the_dialog_itself_falls_back_to_the_browser_confirm() -> None:
    """`GP.confirmDialog` already degrades to `window.confirm` when no dialog
    element is in the DOM, so a caller re-declaring that fallback is a second
    copy of the same decision."""
    offenders = {}
    for p in _sources():
        src = p.read_text(encoding="utf-8")
        for m in re.finditer(r"window\.confirm\s*\(", src):
            line_no = src[: m.start()].count("\n") + 1
            line = src.splitlines()[line_no - 1]
            if line.lstrip().startswith(("//", "*", "/*")):
                continue
            if p.name == "19-confirm-dialog.js":
                continue  # the one documented fallback, inside confirmDialog
            offenders.setdefault(p.relative_to(JS).as_posix(), []).append(line_no)
    assert not offenders, f"call GP.confirmDialog and let it decide: {offenders}"
