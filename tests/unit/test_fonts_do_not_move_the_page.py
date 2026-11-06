"""A web font must not rewrite every width after the page is already readable.

`font-display: swap` paints the fallback first and then replaces it. The two
faces have different metrics, so the swap changes every text width on the page
at once - and a table sized to its content is then re-laid out under the
reader. Measured on User Management with the font delayed: the columns went
[162, 95, 232, 298, 85, 92, 104, 84] to [174, 97, 250, 318, 88, 95, 115, 84]
and the table grew 68px, 179ms after it was already readable.

`optional` gives the face a short block period and then commits to whatever it
has for that page load. It never swaps, so the layout cannot move; the main
face is preloaded so it usually wins anyway, and once cached it is used from
the first frame.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_FONTS = _REPO / "src" / "app" / "templates" / "static" / "css" / "fonts.css"
_BASE = _REPO / "src" / "app" / "templates" / "base.html"


def test_no_face_swaps_after_first_paint() -> None:
    text = _FONTS.read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    offenders = re.findall(r"font-display:\s*(swap|fallback|auto)\s*;", code)
    assert not offenders, (
        f"a face is set to {offenders} - it will repaint every width once it "
        "arrives, moving the tables under the reader"
    )


def test_every_face_states_its_display_policy() -> None:
    """A face with no `font-display` gets `auto`, which behaves like block then
    swap - the same reflow by omission."""
    code = re.sub(r"/\*.*?\*/", "", _FONTS.read_text(encoding="utf-8"), flags=re.S)
    faces = code.count("@font-face")
    declared = len(re.findall(r"font-display:\s*optional\s*;", code))
    assert faces > 0, "fonts.css declares no faces"
    assert declared == faces, f"{faces} faces but {declared} say `font-display: optional`"


def test_the_ui_face_is_preloaded() -> None:
    """`optional` only keeps the brand face if it arrives inside the block
    period, and a preload is what gets it there on a first visit."""
    assert 'rel="preload"' in _BASE.read_text(encoding="utf-8")
    assert "GitLabSans.woff2" in _BASE.read_text(encoding="utf-8")
