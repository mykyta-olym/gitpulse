"""Hover answers in colour, the way GitLab's does.

@gitlab/ui 136.3.0's complete transition inventory carries no transform outside
animated icons - no lift, no nudge, no grow. This app had eighteen hover states
that moved something: cards lifting 2px, arrows sliding in from a 4px offset,
sidebar and avatar icons growing, a health bar stretching 1.75x. The lift had
already been removed from the course cards once, which is what made the rest
read as inconsistent rather than as a style.

Three transforms are left and none of them is motion:

* two in `loaders.css` CENTRE a tooltip pseudo-element (`translateX(-50%)`) in
  the no-JS fallback path;
* nothing else. A third exemption used to be listed here - a reduced-motion
  rule setting a table row's left indicator to `scaleY(1)` - but that indicator
  was removed in b1eae61e and the override outlived it by three weeks,
  describing a pseudo-element that no longer exists. The row still highlights;
  it does it with `--gl-table-row-hover-bg`, which is colour, which is the
  point.

Rotations are exempt: a chevron turning is an animated icon, which GitLab does
do, and so are the checkbox tick, the toggle knob and the progress bar.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "src/app/templates/static/css"

ALLOWED = {
    # file, declaration -> why it is not motion
    ("loaders.css", "transform: translateX(-50%)"): "centres the no-JS tooltip",
}


def _sheets() -> list[Path]:
    return [p for p in CSS.rglob("*.css") if ".min." not in p.name and "bundle" not in p.name]


def test_no_hover_state_moves_its_element() -> None:
    offenders = []
    for p in _sheets():
        src = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"([^{}]*:hover[^{}]*)\{([^}]*)\}", src):
            body = m.group(2)
            tm = re.search(r"(?:^|\s|;)(transform|translate|scale)\s*:\s*([^;]+)", body)
            if not tm:
                continue
            value = " ".join(tm.group(2).split())
            if "rotate" in value or value == "none":
                continue  # an icon turning is an animated icon
            decl = f"{tm.group(1)}: {value}"
            if (p.name, decl) in ALLOWED:
                continue
            line = src[: m.start()].count("\n") + 1
            selector = " ".join(m.group(1).split())[:60]
            offenders.append(f"{p.name}:{line} {selector} -> {decl}")
    assert not offenders, (
        "hover must answer in colour, border or shadow - GitLab's transition "
        f"inventory has no transform outside animated icons: {offenders}"
    )


def test_the_three_exemptions_still_earn_it() -> None:
    """If one of them disappears, the allowlist above is stale."""
    loaders = (CSS / "loaders.css").read_text(encoding="utf-8")
    assert loaders.count("transform: translateX(-50%)") >= 2, (
        "the no-JS tooltip centring is gone - drop it from ALLOWED"
    )
    tables = (CSS / "tables.css").read_text(encoding="utf-8")
    assert "--table-row-bg: var(--gl-table-row-hover-bg);" in tables, (
        "a table row no longer highlights on hover at all - the colour answer "
        "that replaced the indicator bar is gone too"
    )
    assert "background: var(--table-row-bg);" in tables
