"""The explanatory line a card body opens with keeps one step between itself
and what it explains - as the component's own spacing, not a utility each
template picks for itself.

Measured before: Compliance Progress 8px (mb-3), the webhook card 4px (mb-2),
Communication Indicators and User Role Breakdown 0px - the stat cards and the
chart sat on the line. "Add a bit of space between the text and the cards, the
way Compliance Progress has it - everywhere." After: 8px on all ten cards that
open with a line.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CARDS_CSS = (REPO / "src/app/templates/static/css/cards.css").read_text(encoding="utf-8")
TEMPLATES = REPO / "src/app/templates"


def test_the_gap_is_the_card_components() -> None:
    rule = re.search(
        r"\.card-body > p\.muted:first-child:not\(:last-child\)\s*\{([^}]*)\}", CARDS_CSS
    )
    assert rule, "the card-body lead line lost its spacing rule"
    assert "margin-bottom: var(--gl-spacing-3)" in rule.group(1)


def test_no_template_picks_its_own_gap() -> None:
    """A lead line that carries mb-N again is a page override of the component."""
    offenders: list[str] = []
    for path in TEMPLATES.rglob("*.html"):
        src = path.read_text(encoding="utf-8")
        for match in re.finditer(
            r"\{% call card\((?:.|\n){0,600}?<p class=\"([^\"]*muted[^\"]*)\"", src
        ):
            classes = match.group(1).split()
            if any(c.startswith("mb-") and c != "mb-0" for c in classes):
                offenders.append(f"{path.relative_to(TEMPLATES)}: {match.group(1)}")
    assert not offenders, "\n".join(offenders)
