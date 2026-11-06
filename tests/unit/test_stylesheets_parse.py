"""Every stylesheet has to parse, because a broken one fails silently.

A sweep that deletes dead rules can leave a fragment behind. One did: a lone
`/` was left on line 1 of five stylesheets when the rule it opened was removed
(commit 9d0fac39, "remove 69 dead class selectors"). CSS error recovery then
hides the damage in the worst possible way - the parser does not stop, it
swallows the stray character TOGETHER WITH the next selector and carries on. So
Several selectors never applied on production, with no error anywhere and every other rule in
the file working normally.

A browser engine is the only complete judge of CSS, but the whole class of
damage a deletion leaves behind is structural - stray text between rules,
unbalanced braces, an unterminated comment - and that is checkable here, in a
test that costs milliseconds and runs on every commit.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CSS_DIR = Path(__file__).resolve().parents[2] / "src/app/templates/static/css"

SHEETS = sorted(
    p
    for p in CSS_DIR.rglob("*.css")
    if ".min." not in p.name and "bundle" not in p.name and "vendor" not in p.parts
)


def _without_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _ids(paths: list[Path]) -> list[str]:
    return [p.relative_to(CSS_DIR).as_posix() for p in paths]


def test_there_are_stylesheets_to_check() -> None:
    assert len(SHEETS) > 20, SHEETS


@pytest.mark.parametrize("sheet", SHEETS, ids=_ids(SHEETS))
def test_comments_are_closed(sheet: Path) -> None:
    text = sheet.read_text(encoding="utf-8")
    assert text.count("/*") == text.count("*/"), (
        f"{sheet.name}: {text.count('/*')} comment openers, {text.count('*/')} closers - "
        "an unterminated comment eats every rule after it"
    )


@pytest.mark.parametrize("sheet", SHEETS, ids=_ids(SHEETS))
def test_braces_are_balanced(sheet: Path) -> None:
    body = _without_comments(sheet.read_text(encoding="utf-8"))
    depth = 0
    for line_no, line in enumerate(body.split("\n"), 1):
        for ch in line:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                assert depth >= 0, f"{sheet.name}:{line_no}: a '}}' with no block open"
    assert depth == 0, f"{sheet.name}: {depth} block(s) left open at end of file"


@pytest.mark.parametrize("sheet", SHEETS, ids=_ids(SHEETS))
def test_nothing_stray_sits_between_rules(sheet: Path) -> None:
    """What is between one rule and the next must be able to BE a selector.

    This is the check that catches the lone `/`: it is not a selector, it is not
    an at-rule, and the parser resolves it by discarding the rule that follows.
    """
    body = _without_comments(sheet.read_text(encoding="utf-8"))
    # Everything a selector may contain. `/` is deliberately NOT in it: it is
    # legal nowhere in a selector, so a stray one is exactly the leftover this
    # test exists to find.
    selector_chars = re.compile(r"^[\w\s.#:,>+~*\[\]\-=\"'()%$^|&!]*$")
    offenders = []
    for match in re.finditer(r"(?:^|\})([^{}]*)(?=\{|\}|$)", body):
        fragment = match.group(1).strip()
        if not fragment or fragment.startswith("@"):
            continue
        line_no = body[: match.start(1)].count("\n") + 1
        if not re.search(r"[\w.#:\[*&]", fragment) or not selector_chars.match(fragment):
            offenders.append(f"line {line_no}: {fragment[:60]!r}")
    assert not offenders, (
        f"{sheet.name}: stray text where a selector should be - the parser "
        f"discards it AND the rule after it: {offenders}"
    )
