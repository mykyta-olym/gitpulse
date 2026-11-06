"""One pattern, one component.

The same control kept being built twice with different anatomy, and the two
copies drifted where the reader could see it:

* Two stat tiles - `stat_card` (icon floating right of a flat box) and
  `dashboard_stat` (label + icon on the shell, figure in an inset block) - plus
  a `.stat-card--centered` grid that re-created the second one's LOOK on the
  first one's markup. Three implementations of one tile; the description line
  landed inside the inset block on one and outside it on another.
* Three disclosure chevrons: the card's trailing chevron-down swinging 180deg,
  `details.details-accordion`'s LEADING caret swinging 90deg, and the LLM
  prompt toggle's leading chevron resting at -90deg. Same control, three
  anatomies, two of them on one settings page.
* One card in the app hid its header buttons' labels on a phone. "Reload" and
  "Add Configuration" became bare glyphs while all 41 other buttons on the same
  page kept their words.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TEMPLATES = _REPO / "src/app/templates"
_STATIC = _TEMPLATES / "static"
_CARDS_HTML = _TEMPLATES / "components/cards.html"


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _strip_jinja_comments(html: str) -> str:
    return re.sub(r"\{#.*?#\}", "", html, flags=re.DOTALL)


def _all_css() -> list[tuple[Path, str]]:
    """Every hand-written stylesheet, comments removed - a rule this file bans
    is often DESCRIBED in the comment that replaced it."""
    out = []
    for path in _STATIC.rglob("*.css"):
        if "vendor" in path.parts:
            continue
        out.append((path, _strip_css_comments(path.read_text(encoding="utf-8"))))
    return out


def test_one_stat_tile_macro() -> None:
    cards = _CARDS_HTML.read_text(encoding="utf-8")
    assert cards.count("{% macro stat_card(") == 1
    assert "{% macro dashboard_stat(" not in cards, (
        "the second stat tile is back - `stat_card` renders the dashboard "
        "anatomy for every page now"
    )

    for path in _TEMPLATES.rglob("*.html"):
        body = _strip_jinja_comments(path.read_text(encoding="utf-8"))
        assert "dashboard_stat(" not in body, f"{path.name} still calls dashboard_stat"
        assert "stat-card--centered" not in body, (
            f"{path.name} still asks for the re-implemented tile look; the tile IS that look now"
        )


def test_no_second_stat_tile_stylesheet() -> None:
    for path, css in _all_css():
        assert ".stat-card--centered" not in css, (
            f"{path.name} re-creates the stat tile with a grid; there is one "
            "tile component and it is `.gl-home-stat`"
        )


def test_every_disclosure_chevron_trails_and_swings_180() -> None:
    cards_css = (_STATIC / "css/cards.css").read_text(encoding="utf-8")
    navbar_css = (_STATIC / "css/navbar.css").read_text(encoding="utf-8")
    course_css = (_STATIC / "css/pages/course.css").read_text(encoding="utf-8")

    # the card's chevron is the reference: trailing, 0 -> 180deg
    assert ".card-collapse-btn--trailing" in cards_css
    assert 'card-collapse-btn[aria-expanded="true"] .card-collapse-icon' in cards_css

    # <details> accordions: ::after (trailing), not ::before (leading)
    assert "details.details-accordion > summary::after" in navbar_css
    assert "details.details-accordion > summary::before" not in navbar_css, (
        "a leading marker makes this disclosure a mirror image of the card one"
    )
    assert "details.details-accordion[open] > summary::after" in navbar_css
    assert "rotate(90deg)" not in navbar_css.split("details.details-accordion")[1][:2000], (
        "the accordion chevron must swing the same 180deg as every other one"
    )

    # the LLM prompt toggle
    assert '.llm-prompt-toggle-btn[aria-expanded="true"] .llm-prompt-chevron' in course_css
    assert "rotate(-90deg)" not in course_css, "a third resting angle for the same control"


def test_no_page_hides_a_button_label_on_a_phone() -> None:
    """A label the reader cannot see is a guess they have to press to resolve.

    A row action that should be an icon is built as one (`btn_icon_only` /
    `btn_link_icon_only`, with a tooltip) - not as a labelled button whose
    words a page rule hides: those came out 26-34px wide beside 24px squares."""
    offenders = []
    for path, css in _all_css():
        for match in re.finditer(r"([^{}]*\.btn-text)\s*\{([^}]*)\}", css):
            selector, body = match.group(1).strip(), match.group(2)
            if "display: none" not in body and "display:none" not in body:
                continue
            offenders.append(f"{path.name}: {selector}")
    assert not offenders, "these rules hide a button's words: " + "; ".join(offenders)
