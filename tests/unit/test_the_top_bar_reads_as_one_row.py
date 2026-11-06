"""The date and time in the header sit on the same line as everything beside them.

Every box in that row is centred by the layout engine, so nothing looked wrong
in the CSS - the misalignment was inside the boxes. `align-items: center` lines
up BOXES, and a 21px line box around 14px digits carries the font's full ascent,
room for accents and diacritics that "2026/2027" and "23.09. 14:03" never use.
The ink of those digits therefore landed about a pixel below the middle of its
own box: measured from the rendered pixels, the search button, the avatar and
the chips' own icons all had their ink centred on 23.75 and the text alone sat
at 25.0, which is the row not reading as level.

`line-height: 1` collapses the line box onto the em, so the ink lands where the
box already is - and it does that whatever font is in use, which matters here
because the web font is `font-display: optional`: a phone that does not have it
cached renders the whole page in the fallback, with different metrics.
"""

from __future__ import annotations

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css/topbar.css"
HEADER = Path(__file__).resolve().parents[2] / "src/app/templates/components/header.html"


def _rule(selector: str) -> str:
    text = CSS.read_text(encoding="utf-8")
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", text)
    assert match, f"{selector} not found in topbar.css"
    return match.group(1)


def test_the_context_chips_centre_the_glyphs_not_the_line_box() -> None:
    body = _rule(".gl-context-item")
    assert "align-items: center" in body
    assert "line-height: 1" in body, (
        "without it the digits' ink hangs ~1px below the icons and the avatar"
    )


def test_the_clock_still_reserves_its_line() -> None:
    """The clock's text arrives from JS after first paint.

    Empty, its box is 0 high, so the chip is only as tall as its icon and the
    whole right-hand cluster settles when the text lands. The reserved height
    has to follow the line-height above, not the old 1.5 line.
    """
    body = _rule("#topBarClockText")
    assert "min-height: 1em" in body
    assert "min-width" in body, "the WIDTH is reserved too, against a sideways shift"


def test_the_chip_icons_match_their_text_size() -> None:
    """16px beside 14px text - the pairing layout.css and cards.css both state."""
    html = HEADER.read_text(encoding="utf-8")
    for name in ("calendar", "clock"):
        assert f"icon('{name}', size='sm')" in html, (
            f"the {name} icon is not at the 16px step beside its 14px text"
        )
