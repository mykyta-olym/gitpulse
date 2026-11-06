"""The logo hover has to end as smoothly as it starts.

Two separate defects produced the same visible jerk on mouse-out, and both are
easy to reintroduce:

1. Writing the effect straight into `filter` / `stroke-dashoffset`. You cannot
   transition OUT of a removed animation - the spec does not treat animation
   output as a transition's before-change style - so the value drops in one
   frame. Measured in a browser: brightness 1.66 -> 1.00 between two samples.
2. A later rule re-declaring `transition` on the same shapes. The `transition`
   shorthand REPLACES the whole declaration, so a stray `transition: filter 0.8s`
   silently dropped `--gp-amp` from it and the snap came back even with (1) fixed.
"""

from __future__ import annotations

import re
from pathlib import Path

LOGO_CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css/logo.css"


def _css() -> str:
    """Stylesheet with /* comments */ stripped, so prose cannot satisfy a rule."""
    return re.sub(r"/\*.*?\*/", "", LOGO_CSS.read_text(encoding="utf-8"), flags=re.DOTALL)


def _base_css() -> str:
    """Comment-free CSS with every @media block removed.

    `prefers-reduced-motion` legitimately re-declares these selectors to switch
    the motion off; that is not the drift these tests look for.
    """
    css = _css()
    out, i = [], 0
    while True:
        m = css.find("@media", i)
        if m == -1:
            out.append(css[i:])
            return "".join(out)
        out.append(css[i:m])
        depth = 0
        cursor = css.index("{", m)
        for pos in range(cursor, len(css)):
            if css[pos] == "{":
                depth += 1
            elif css[pos] == "}":
                depth -= 1
                if depth == 0:
                    cursor = pos
                    break
        i = cursor + 1


def _block(css: str, selector: str) -> str:
    """Body of the LAST rule whose selector is EXACTLY `selector`.

    Anchored at line start so `.gp-ecg-trace-pulse` does not match the long
    `:is(... ) .gp-ecg-trace-pulse` hover selector that ends with the same text.
    """
    hits = list(re.finditer(r"^" + re.escape(selector) + r"\s*\{", css, re.MULTILINE))
    assert hits, f"no rule for {selector!r}"
    i = hits[-1].end()
    return css[i : css.index("}", i)]


def test_phase_and_amplitude_are_registered_properties() -> None:
    """Unregistered custom properties swap discretely - they cannot ease."""
    css = _css()
    for prop in ("--gp-wave", "--gp-amp", "--gp-dash"):
        assert f"@property {prop}" in css, f"{prop} must be registered to interpolate"


def test_keyframes_drive_the_phase_never_the_painted_property() -> None:
    """If a keyframe sets `filter` directly, the exit snaps again."""
    css = _css()
    for name in ("gp-pulse-flare", "gp-pulse-sweep"):
        body = css.split(f"@keyframes {name}", 1)[1]
        body = body[: body.index("\n}")]
        assert "filter:" not in body, f"{name} must animate the phase, not filter"
        assert "stroke-dashoffset:" not in body, f"{name} must animate the phase"


def test_the_animation_is_never_removed_only_paused() -> None:
    """The wave stays applied and paused at rest; hover flips play-state.

    Removing the animation is what makes the value snap. Toggling play-state
    freezes it instead, and the amplitude transition carries the exit.
    """
    css = _base_css()
    part = _block(css, ".gp-part")
    assert "paused" in part, "the flare animation must rest paused, not absent"
    assert "transition: --gp-amp" in part

    trace = _block(css, ".gp-ecg-trace-pulse")
    assert "paused" in trace, "the sweep must rest paused, not absent"

    hover = css[css.rindex(") .gp-part {") :]
    hover = hover[: hover.index("}")]
    assert "animation-play-state: running" in hover
    assert "--gp-amp:" in hover, "hover must raise the amplitude, not restart the animation"


def test_no_second_transition_declaration_on_the_logo_shapes() -> None:
    """Exactly one rule may declare `transition` for the mark's shapes.

    A second one replaces the first wholesale. This is the bug that survived the
    first fix: a leftover `transition: filter 0.8s ease` later in the file.
    """
    css = _base_css()
    shapes = (".gp-center", ".gp-left-ear", ".gp-right-ear", ".gp-left-cheek", ".gp-right-cheek")
    offenders = []
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        selector, body = m.group(1).strip(), m.group(2)
        if "transition" not in body or ":hover" in selector:
            continue
        if any(s in selector for s in shapes):
            offenders.append(selector.replace("\n", " ")[:80])
    assert not offenders, (
        "these rules also declare `transition` for the logo shapes and will "
        f"clobber `.gp-part`'s: {offenders}"
    )


def test_the_pulse_layer_is_invisible_at_rest() -> None:
    """A paused sweep freezes mid-trace; at rest that must not be visible.

    The halo, guard and core layers draw the ECG when the cursor is away, so the
    wave layer can sit at opacity 0 with a frozen dash parked anywhere.
    """
    trace = _block(_base_css(), ".gp-ecg-trace-pulse")
    assert re.search(r"opacity:\s*0\s*;", trace), "the wave layer must rest invisible"
