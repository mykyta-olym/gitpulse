"""No stylesheet may re-implement a button on top of the button system.

Found by measuring the same component across every page: the tour's welcome
dialog rendered `.btn .btn-primary .btn-sm` markup, and then `tour.css` restyled
it from scratch with rem values that silently won:

    font-size  13.76px (0.86rem)   vs the token's 14px
    padding    7.2 x 15.2px        vs 0 12px on a fixed height
    radius     4px                 vs 8px

Fractional pixel values are the tell - nothing in the design system produces
them, so they only appear where somebody sized a control in `rem`/`em` instead
of using the shared classes.
"""

from __future__ import annotations

import re
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"

# The one legitimate bare-`button` rule: a font-family/size normalise that makes
# form controls inherit the page font instead of the browser's default.
ALLOWED = {("navbar.css", "input, button, select, textarea, optgroup")}

SIZING = ("font-size", "padding", "border-radius", "height")


def _rules(css: str):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        yield m.group(1).strip(), m.group(2)


def test_no_stylesheet_sizes_a_bare_button_element() -> None:
    """Sizing a bare `button` overrides `.btn` wherever the two meet.

    `.btn` and a bare `button` selector have different specificity but the same
    origin, so whichever comes later wins - which makes this a silent, ordering
    dependent override rather than an obvious one.
    """
    offenders = []
    for path in sorted(CSS_DIR.rglob("*.css")):
        if ".min." in path.name:
            continue
        for selector, body in _rules(path.read_text(encoding="utf-8")):
            if not re.search(r"(^|[\s,>])button\s*(,|$)", selector):
                continue
            props = [p for p in SIZING if re.search(rf"(^|;|\s){p}\s*:", body)]
            if not props:
                continue
            key = (path.name, " ".join(selector.split()))
            if key in ALLOWED:
                continue
            offenders.append(f"{path.name}: {key[1][:70]} sets {props}")

    assert not offenders, (
        "these rules size a bare <button> and will override the .btn system:\n  "
        + "\n  ".join(offenders)
    )


def test_tour_welcome_buttons_use_the_shared_button_classes() -> None:
    """The markup must keep carrying `.btn`, or removing the override strands it."""
    render = (CSS_DIR.parents[0] / "js/_parts/tours/10-render.js").read_text(encoding="utf-8")
    assert "btn btn-primary btn-sm gp-tour-welcome-start" in render
    assert "btn btn-secondary btn-sm gp-tour-welcome-skip" in render

    tour = re.sub(
        r"/\*.*?\*/", "", (CSS_DIR / "tour.css").read_text(encoding="utf-8"), flags=re.DOTALL
    )
    for selector, body in _rules(tour):
        if "gp-tour-welcome-start" in selector or "gp-tour-welcome-skip" in selector:
            for prop in ("font-size", "padding", "border-radius", "background", "color"):
                assert not re.search(rf"(^|;|\s){prop}\s*:", body), (
                    f"{selector.strip()} re-styles {prop}; the .btn classes own that"
                )


def _all_rules():
    for path in sorted(CSS_DIR.rglob("*.css")):
        for selector, body in _rules(path.read_text(encoding="utf-8")):
            yield path.name, selector, body


def test_a_button_icon_is_16px_at_every_button_size() -> None:
    """GlButton draws its icon at 16px whatever the button's size; a small
    button is a shorter box around the same glyph. The app had a ladder of
    14px (.btn-sm), 13px (card-header actions) and 14px (phones) steps, which
    read as "the icons are too small" and made a small button change width
    while loading, because the spinner that replaces the icon is 16px.
    `.btn-xs` is no exception any more: it is GlButton small too."""
    offenders = []
    for name, selector, body in _all_rules():
        if ".icon" not in selector or ".btn" not in selector:
            continue
        m = re.search(r"width:\s*(\d+)px", body)
        if m and m.group(1) != "16":
            offenders.append((name, selector, m.group(1)))
    assert not offenders, offenders


def test_card_headers_use_the_buttons_own_sizing() -> None:
    """Header placement must not override shared button dimensions or padding."""
    for selector, body in _rules((CSS_DIR / "cards.css").read_text(encoding="utf-8")):
        if ".card-actions" in selector and re.search(r"\.btn(?:[\s.:#-]|$)", selector):
            assert not any(re.search(rf"\b{prop}\s*:", body) for prop in SIZING), selector
