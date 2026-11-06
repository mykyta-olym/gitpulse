"""Server -> client data goes through ONE pair of macros.

Fourteen templates hand-wrote their own `<script type="application/json">`
island. Three consequences, all measured on 2026-08-26:

* Booleans were hand-serialised as `{{ 'true' if x else 'false' }}` at 21 call
  sites. A JSON island is one missing comma away from taking the whole page's
  JavaScript down with a parse error, and hand-writing every separator is how
  that comma goes missing.
* The five role flags were spelled out identically in three page blocks.
* `base.html` derived two of those five DIFFERENTLY - `canEdit` as
  `is_admin or is_teacher` and `isStudent` as `user_role == 'student'`, against
  the server-computed `can_edit` / `is_student` the page blocks used. A page
  could therefore ship two contradictory answers to the same question, and
  which one a script believed depended on which island it read.

`page_config(config, nonce, id=...)` now owns the role flags and
`json_island(data, nonce, id=...)` carries a raw payload with nothing added.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
LAYOUT = TEMPLATES / "components/layout.html"

# An error page must render in the most minimal Jinja environment available:
# importing from layout.html pulls in components/buttons.html, which needs the
# app's custom `force_escape` filter, and a 503 is exactly when the app may be
# too broken to have registered it. Its island stays inline on purpose.
INLINE_ISLAND_ALLOWED = {"errors/error.html"}


def _templates() -> list[Path]:
    return sorted(TEMPLATES.rglob("*.html"))


def _rel(p: Path) -> str:
    return p.relative_to(TEMPLATES).as_posix()


def test_both_macros_exist() -> None:
    src = LAYOUT.read_text(encoding="utf-8")
    assert "{% macro page_config(" in src
    assert "{% macro json_island(" in src


def test_no_template_hand_writes_a_json_island() -> None:
    offenders = {}
    for p in _templates():
        if p == LAYOUT or _rel(p) in INLINE_ISLAND_ALLOWED:
            continue
        hits = [
            n
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if 'type="application/json"' in line
        ]
        if hits:
            offenders[_rel(p)] = hits
    assert not offenders, (
        "use page_config() or json_island() from components/layout.html instead of a "
        f'hand-written <script type="application/json">: {offenders}'
    )


def test_no_json_island_hand_serialises_a_boolean() -> None:
    """`{{ 'true' if x else 'false' }}` is what `| tojson` is for.

    Scoped to the island call sites: `aria-selected` and `data-*` attributes
    legitimately take the literal strings "true"/"false", and rewriting those
    would be a different (and wrong) change.
    """
    call = re.compile(r"\{\{\s*(?:page_config|json_island)\((?:[^{}]|\{[^{}]*\})*\}\}", re.S)
    offenders = {}
    for p in _templates():
        for m in call.finditer(p.read_text(encoding="utf-8")):
            if re.search(r"'(?:true|false)'\s+if", m.group(0)):
                offenders.setdefault(_rel(p), []).append(" ".join(m.group(0).split())[:100])
    assert not offenders, (
        f"hand-serialised booleans inside a JSON island - pass the value itself: {offenders}"
    )


def test_every_page_config_import_carries_context() -> None:
    """Without `with context` the macro cannot see `can_edit`, `is_admin` and
    the rest, so every role flag it emits silently becomes false."""
    pattern = re.compile(r"\{%\s*from \"components/layout\.html\" import [^%]*%\}")
    offenders = {}
    for p in _templates():
        for m in pattern.finditer(p.read_text(encoding="utf-8")):
            line = m.group(0)
            names = line.split("import", 1)[1]
            if "page_config" in names and "with context" not in line:
                offenders.setdefault(_rel(p), []).append(" ".join(line.split())[:100])
    assert not offenders, f"page_config imported without `with context`: {offenders}"


def test_no_template_repeats_the_whole_role_block() -> None:
    """Three pages spelled out all five flags; the macro supplies them now.

    An individual override is still allowed - the admin pages deliberately
    redefine `canEdit` as "is admin" - but restating the SET is the duplication
    that let base.html and the page blocks drift apart.
    """
    keys = ("canEdit", "isAdmin", "isTeacher", "isStudent", "userRole")
    offenders = {}
    for p in _templates():
        if p == LAYOUT:
            continue
        src = p.read_text(encoding="utf-8")
        present = [k for k in keys if re.search(rf"['\"]{k}['\"]\s*:", src)]
        if len(present) >= 4:
            offenders[_rel(p)] = present
    assert not offenders, f"these restate the role block page_config() already emits: {offenders}"


def test_layout_derives_each_role_flag_exactly_once() -> None:
    src = LAYOUT.read_text(encoding="utf-8")
    block = src.split("{%- set _roles = {", 1)
    assert len(block) == 2, "the shared role block is gone from page_config"
    body = block[1].split("} -%}", 1)[0]
    for key in ("canEdit", "isAdmin", "isTeacher", "isStudent", "userRole"):
        assert body.count(f"'{key}'") == 1, f"{key} is defined {body.count(key)} times"
