"""A toast is the last word on screen, so nothing may be painted over it.

The toast carries confirmations and failures - including ones raised from
inside a modal. If any overlay in the app outranks it, that message is fired,
counted as "shown", and never seen. The absolute numbers are ours (GitLab's
1100 sits on Bootstrap's scale, where the modal is 1050); the ordering is the
part that has to hold.

The toast's geometry is measured against @gitlab/ui 136.3.0 `toast.scss`:
16px/24px padding, an 8px feedback radius, a 12px stack gap, 24px off the
bottom. Its colours deliberately diverge - this app carries a light toast in
its light theme, on repeated request - and that divergence is not pinned here.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOKENS = REPO / "src/app/templates/static/css/tokens.css"
TOASTS = REPO / "src/app/templates/static/css/toasts.css"

_Z = re.compile(r"--z-([a-z-]+):\s*(\d+)")


def _z_scale() -> dict[str, int]:
    return {m.group(1): int(m.group(2)) for m in _Z.finditer(TOKENS.read_text(encoding="utf-8"))}


def test_the_toast_outranks_every_other_layer() -> None:
    scale = _z_scale()
    toast = scale.pop("toast")
    above = {name: z for name, z in scale.items() if z >= toast}
    assert not above, f"painted over the toast: {above}"


def test_the_toast_keeps_gitlabs_geometry() -> None:
    src = TOASTS.read_text(encoding="utf-8")
    chip = src.split("\n.toast {", 1)[1].split("\n}", 1)[0]
    # gl-py-5 / gl-px-6, and --gl-feedback-border-radius (= border-radius-lg, 8px)
    assert "padding: var(--gl-spacing-5) var(--gl-spacing-6)" in chip
    assert "border-radius: var(--gl-feedback-border-radius)" in chip
    slot = src.split("\n.toast-container {", 1)[1].split("\n}", 1)[0]
    # .b-toaster-slot: gl-gap-4 between toasts, spacing-6 off the bottom edge
    assert "gap: var(--gl-spacing-4)" in slot
    assert "bottom: var(--gl-spacing-6)" in slot
