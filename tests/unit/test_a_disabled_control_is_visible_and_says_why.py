"""A disabled control is visible, reads as disabled, and says why - on a phone too.

Reported on the light theme, on a phone: an archived course's check list showed
an Active column of empty boxes - a disabled checkbox was GitLab's disabled box
at 40% opacity, an outline of 1.1:1 against the page, ticked or not; the pager's
dead arrows were near-white buttons on the grey card shell; and nothing said why
anything was off. Tooltips are hover-only, and of the disabled controls that had
a reason at all, most had it on the control itself, which a disabled control
never receives an event for.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "src" / "app" / "templates" / "static"
CSS = STATIC / "css"
TEMPLATES = ROOT / "src" / "app" / "templates"


def _rule(css: str, selector: str) -> str:
    m = re.search(re.escape(selector) + r"[^{]*\{([^}]*)\}", css)
    assert m, f"no rule for {selector}"
    return m.group(1)


def test_a_disabled_checkbox_is_gitlabs_box_not_a_ghost() -> None:
    forms = (CSS / "forms.css").read_text(encoding="utf-8")
    rule = _rule(forms, ".form-check-input:disabled,\n.form-check-input:checked:disabled")
    assert "opacity" not in rule, "a disabled checkbox is faded out again"
    assert "var(--gl-control-bg-disabled)" in rule
    assert "var(--gl-control-border-disabled)" in rule
    tick = _rule(forms, ".form-check-input:disabled::after")
    assert "var(--gl-control-indicator-disabled)" in tick, "a ticked disabled box hides its tick"


def test_a_dead_pager_arrow_is_a_bare_glyph_on_the_body() -> None:
    navbar = (CSS / "navbar.css").read_text(encoding="utf-8")
    band = _rule(navbar, ".pagination-controls {")
    assert "background" not in band, "the pager is painted the card shell's grey again"
    dead = _rule(navbar, ".pagination .pagination-btn:disabled")
    assert "transparent" in dead
    assert "var(--gl-action-disabled-text)" in dead


def test_a_disabled_control_carries_a_reason_a_tap_can_reach() -> None:
    guards = (STATIC / "js" / "process-action-guards.js").read_text(encoding="utf-8")
    assert "function syncDisabledReason(" in guards, "data-disabled-reason is no longer honoured"
    assert "attributeFilter: ['disabled', 'aria-disabled', 'data-disabled-reason']" in guards
    paginator = (STATIC / "js" / "components.js").read_text(encoding="utf-8")
    assert paginator.count("data-disabled-reason=") == 2, "a pager arrow lost its reason"
    bulk = (TEMPLATES / "components" / "bulk_actions.html").read_text(encoding="utf-8")
    assert "'disabled-reason'" in bulk, "a bulk action does not say it needs a ticked row"


def test_no_text_shrinks_below_12px_on_a_phone() -> None:
    """The phone sheets set small badges to 11px and score labels to 10px,
    below the 12px GitLab uses for its smallest text."""
    tiny = re.compile(r"font-size:\s*(?:[0-9]|1[01])px")
    offenders = {
        p.name: tiny.findall(p.read_text(encoding="utf-8"))
        for p in (CSS / "_parts" / "responsive").glob("*.css")
        if tiny.search(p.read_text(encoding="utf-8"))
    }
    assert not offenders, f"text shrinks below 12px on a phone: {offenders}"
