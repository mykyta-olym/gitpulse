"""A list of people reads as columns, not as three ragged rows.

Every row in the teachers list carries the control that changes what the person
is. It was sized to its own label, so the rows did not line up: a row reading
"Course Owner" was 42px wider than one reading "Teacher" and shoved that row's
badges left by exactly that much.

Measured in a browser against the real stylesheet, every row now starts its
control at the same x. This pins the declaration that makes that true - and the
narrow-screen exemption, where a grid track does the aligning and a fixed width
would push the name out of its own cell.

(The badge column that sat beside it, `.member-badges`, is gone: the badges
moved into the table's Account column, and its rules were removed as dead CSS.)
"""

from __future__ import annotations

import re
from pathlib import Path

_ADMIN_CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css/pages/admin.css"


def _rule(css: str, selector: str, *, inside_media: bool) -> str | None:
    """The body of the first `selector { ... }` block, inside a media query or not."""
    depth_media = False
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    for match in re.finditer(r"(@media[^{]*\{)|([^{}]+)\{([^{}]*)\}|(\})", css):
        if match.group(1):
            depth_media = True
        elif match.group(4):
            depth_media = False
        elif match.group(2):
            name = " ".join(match.group(2).split())
            if name == selector and depth_media == inside_media:
                return match.group(3)
    return None


def test_the_role_control_is_a_column_too() -> None:
    css = _ADMIN_CSS.read_text(encoding="utf-8")
    body = _rule(css, ".member-role", inside_media=False)
    assert body, ".member-role lost its base rule"
    assert re.search(r"width:\s*[\d.]+rem", body), (
        '"Course Owner" is wider than "Teacher", so a content-sized control '
        "drags that row's badges left with it"
    )


def test_the_narrow_layout_keeps_its_grid() -> None:
    """There the track aligns them; a fixed width would squeeze the name."""
    css = _ADMIN_CSS.read_text(encoding="utf-8")
    body = _rule(css, ".member-role", inside_media=True)
    assert body, ".member-role lost its responsive rule"
    assert "width: auto" in body, (
        ".member-role carries the desktop column width into the narrow grid"
    )
