"""There is one focus ring in this app, and every control paints it.

The app had two: twenty-seven selectors drew the two-layer `--focus-ring`
(GitLab's shape - a 1px against the surface, a 3px outside it) and six drew a
flat `outline: 2px solid var(--primary)`. The six were the BASELINE rules - bare
`button`, bare `a`, `summary`, table rows, the back link, the tab - so which
ring a control got depended on whether anyone had styled it. That is the same
drift that gave three collapsible card headers three different rings, one level
further out, and it is invisible until two of them are on screen together.

A control whose ring must sit inside its own box uses `--focus-ring-inset`;
that is still the one ring, drawn inward.
"""

from __future__ import annotations

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"

# Deliberate exceptions, each with a reason:
#   .gl-sidebar-item - already on --focus-ring-inset
# (none currently need a bespoke ring; add one here WITH its reason if it does)
ALLOWED_BESPOKE: set[str] = set()


def _sources() -> list[Path]:
    return sorted(p for p in CSS.rglob("*.css") if ".min." not in p.name and "bundle" not in p.name)


def test_no_rule_paints_its_own_focus_ring() -> None:
    """`outline: <width> solid <colour>` on :focus-visible is a second ring."""
    offenders: list[str] = []
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        # rule blocks whose selector mentions :focus-visible
        for match in re.finditer(r"([^{}]*:focus-visible[^{}]*)\{([^{}]*)\}", text):
            selector = " ".join(match.group(1).split())
            body = match.group(2)
            if selector in ALLOWED_BESPOKE:
                continue
            # A system-colour outline is the High Contrast pairing, not a ring.
            if re.search(r"outline:\s*\d+px\s+solid\s+(?!LinkText)", body):
                offenders.append(f"{path.name}: {selector[:70]}")
    assert not offenders, (
        "these paint their own focus ring instead of --focus-ring / "
        "--focus-ring-inset: " + "; ".join(offenders)
    )


def test_the_ring_survives_high_contrast() -> None:
    """A box-shadow ring is dropped in Windows High Contrast, so every focusable
    element needs a real outline in that mode - the pairing GitLab uses."""
    text = (CSS / "utilities.css").read_text(encoding="utf-8")
    block = re.search(r"@media \(forced-colors: active\)\s*\{(.+?)\n\}", text, re.S)
    assert block, "utilities.css has no forced-colors block"
    body = block.group(1)
    assert "LinkText" in body, "the High Contrast ring must use a system colour"
    for element in ("a", "button", "summary", "input", "select", "textarea"):
        assert re.search(rf"\b{element}\b", body), f"{element} is not covered"
