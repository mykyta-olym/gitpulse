"""The "are you sure?" is on top of the thing that asked.

Every dialog in the app is `.modal-backdrop` at `--z-modal-backdrop` (1000), and
a page modal is moved to the end of `<body>` when it opens. At equal z-index the
last element in the document wins - so the modal that raised the question
covered the question.

Found by clicking through the course page: "Run selected checks" inside the Run
Compliance Checks modal calls `confirmDangerousAction`, the confirmation opened
*behind* the modal, and `document.elementFromPoint` at the Confirm button's
centre returned `#runChecksGrid`. The screenshot showed no dialog at all. The
button could not be clicked by anyone, which made the course-wide Run Checks -
the grading action on that page - impossible to complete.

1005 puts the dialog above `--z-modal` (1001) and below `--z-popover` (1010), so
a tooltip or dropdown opened from inside the dialog still paints over it.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODALS_CSS = REPO / "src/app/templates/static/css/modals.css"
TOKENS_CSS = REPO / "src/app/templates/static/css/tokens.css"


def _token(name: str) -> int:
    m = re.search(rf"--{name}:\s*(\d+)", TOKENS_CSS.read_text(encoding="utf-8"))
    assert m, f"--{name} is not defined any more"
    return int(m.group(1))


def test_the_confirm_dialog_has_its_own_layer() -> None:
    css = MODALS_CSS.read_text(encoding="utf-8")
    assert "#gpConfirmDialog {" in css, "the confirmation dialog has no z-index of its own"
    block = css.split("#gpConfirmDialog {", 1)[1].split("}", 1)[0]
    m = re.search(r"z-index:\s*(\d+)", block)
    assert m, "#gpConfirmDialog does not set a z-index"
    z = int(m.group(1))
    assert z > _token("z-modal"), (
        f"the confirmation sits at {z}, at or below the modals it is asked from "
        f"({_token('z-modal')}) - it will be covered by whichever opened last"
    )
    assert z < _token("z-popover"), (
        "the confirmation is above popovers and tooltips, so anything opened from "
        "inside it would be hidden behind it"
    )
