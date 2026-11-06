"""Every card header is the same header: icon, title, then the rest.

"All Courses" had no icon, "Users" had one inside its title and "Archived
Courses" one beside it - three layouts of one component: the title text
started 12, 32 or 36px from the header's edge, and the settings cards drew a
20px icon where the others drew 16px (`icon('cpu')` defaults to md). The icon
is the macro's `icon_name` slot. The heading groups it with the title and count
so wrapping actions cannot strand the icon on a row of its own.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"
CALL = re.compile(r"\{%-?\s*call(?:\([^)]*\))?\s+card\((.*?)\)\s*-?%\}", re.S)


def _calls() -> list[tuple[str, int, str, str]]:
    out = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        for m in CALL.finditer(text):
            line = text[: m.start()].count("\n") + 1
            out.append(
                (path.relative_to(TEMPLATES).as_posix(), line, m.group(1), text[: m.start()])
            )
    return out


def test_a_card_with_a_title_has_an_icon() -> None:
    missing = [
        f"{rel}:{line}"
        for rel, line, args, _ in _calls()
        if "title=" in args and "icon_name=" not in args
    ]
    assert not missing, f"card headers without an icon: {missing}"


def test_a_title_is_words_not_an_icon() -> None:
    offenders = []
    for rel, line, args, before in _calls():
        var = re.search(r"title=([A-Za-z_]+)\b(?!\()", args)
        if not var:
            continue
        sets = re.findall(
            r"\{%-?\s*set\s+" + var.group(1) + r"\s*-?%\}(.*?)\{%-?\s*endset", before, re.S
        )
        if sets and "icon(" in sets[-1]:
            offenders.append(f"{rel}:{line}")
    assert not offenders, f"an icon drawn inside a card title instead of icon_name: {offenders}"


def test_the_title_icon_rule_is_gone() -> None:
    css = (TEMPLATES / "static/css/cards.css").read_text(encoding="utf-8")
    assert ".card-title .icon {" not in css, "a rule for icons nested in the heading is back"
