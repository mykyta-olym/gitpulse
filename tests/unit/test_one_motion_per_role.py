"""Alike elements move alike: one timing per role, GitLab's for that role.

Measured before this was pinned: a disclosure chevron turned in 100ms on one
page and 200ms on the next; a close button eased at 100ms beside a 200ms
button; a press scaled a button by 0.97, a close button by 0.94, a card by
0.995, a tile by 0.98, a badge by 0.95, an info tip by 0.92 and the exclusion
toggle by 0.88; live dots pulsed at 1.5s or 2s (and one keyframe did not
exist); fills ran at 300, 500 or 600ms. The roles and their tokens are written
down in tokens.css next to --transition-control.
"""

from __future__ import annotations

import re
from pathlib import Path

CSS = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"


def _rules() -> list[tuple[str, str, str]]:
    out = []
    for path in sorted(CSS.rglob("*.css")):
        if ".min." in path.name or "bundle" in path.name:
            continue
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
            out.append((path.name, " ".join(sel.split()), body))
    return out


def test_a_press_moves_nothing() -> None:
    """GlButton's :active is a colour. No control scales or shifts under the press."""
    offenders = [
        f"{name}: {sel}"
        for name, sel, body in _rules()
        if ":active" in sel and re.search(r"transform:\s*(scale|translate)", body)
    ]
    assert not offenders, offenders


def test_controls_ease_at_the_control_speed() -> None:
    """A close / dismiss / icon button, a badge and a tab are controls: 200ms."""
    offenders = [
        f"{name}: {sel}"
        for name, sel, body in _rules()
        if re.search(r"close|dismiss|btn|badge|tab-", sel)
        and not re.search(r"dropdown-item|list-item|result-item|typeahead|-option", sel)
        and "transition" in body
        and "--transition-fast" in body
    ]
    assert not offenders, offenders


def test_every_live_mark_pulses_on_one_clock() -> None:
    pulses = [
        (name, sel, body)
        for name, sel, body in _rules()
        if re.search(r"animation:\s*pulse\b", body)
    ]
    assert pulses
    for name, sel, body in pulses:
        assert "pulse var(--gl-anim-loop) var(--motion-ease-loop) infinite" in body, (
            f"{name}: {sel}"
        )
    tokens = (CSS / "tokens.css").read_text(encoding="utf-8")
    assert "--gl-anim-loop-slow" not in tokens


def test_every_fill_runs_six_hundred_milliseconds() -> None:
    """GlProgressBar: transform 0.6s out-cubic. Every meter, bar and ring fill."""
    offenders = []
    for name, sel, body in _rules():
        if not re.search(r"fill|progress|bar\b|contrib", sel) or "gl-sidebar" in sel:
            continue
        for decl in re.findall(r"transition:\s*([^;]+)", body):
            if (
                re.search(r"\b(width|stroke-dashoffset)\s", decl)
                and "--gl-anim-progress" not in decl
            ):
                offenders.append(f"{name}: {sel}: {decl.strip()}")
    assert not offenders, offenders


def test_form_fields_ease_as_gitlab_fields() -> None:
    """$input-transition / $custom-control-transition: .15s ease-in-out."""
    tokens = (CSS / "tokens.css").read_text(encoding="utf-8")
    assert "--transition-control: 150ms ease-in-out;" in tokens


def test_every_collapse_opens_on_the_disclosure_clock() -> None:
    animations = (CSS / "animations.css").read_text(encoding="utf-8")
    rule = re.search(r"div\[x-collapse\]\s*\{([^}]*)\}", animations)
    assert rule, "Alpine's own 250ms collapse is back"
    assert "var(--motion-duration-normal)" in rule.group(1)
    assert "var(--motion-ease-standard)" in rule.group(1)


def test_a_tab_switch_swaps_the_panel_without_a_fade() -> None:
    """GlTabs renders its panels with `:no-fade="true"`. Ours faded the incoming
    panel up from opacity 0, so what both panels share - Quick access's
    empty-state illustration - vanished and came back on every switch."""
    helpers = (CSS.parent / "js/_parts/core/39-tabs-and-toggles.js").read_text(encoding="utf-8")
    body = helpers.split("function _activateTab(", 1)[1].split("\n}\n", 1)[0]
    assert "GP.motion.inkTo(b)" in body, "the underline no longer travels"
    assert "panelIn" not in body, "a tab switch fades its panel again"
