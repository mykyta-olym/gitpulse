"""The JavaScript the app ships follows one standard, and the audit's bugs stay fixed.

An ESLint pass over every shipped unit - the core as build_bundle.py
concatenates it, each page bundle inside its IIFE, every standalone script -
found, besides 146 `var` declarations and 75 bindings that were never
reassigned, four real defects:

- a raw backspace byte (0x08) in a regex where `\\b` was meant: an edit script
  wrote "\\b" without a raw string. The Dashboard's refresh key never
  normalised <time>, so every tab return rebuilt the attention list and feed;
- ClientPaginator declared register() twice; the second, poorer copy won;
- the course page's fallback sync poll counted errors in two names nothing
  declared, so in strict mode its first assignment threw;
- "passive controls are excluded" went through a helper private to another
  script's closure, so the guard was always false.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js"
TEMPLATES = REPO / "src/app/templates"


def _sources() -> list[Path]:
    """Every hand-written script: no vendor code (build outputs live in dist/)."""
    return [p for p in JS.rglob("*.js") if "vendor" not in p.parts]


def _code(text: str) -> str:
    """The script without its comments, so prose that says "var x" does not count."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", text)


def test_no_var_declarations() -> None:
    offenders = [
        p.relative_to(JS).as_posix()
        for p in _sources()
        if re.search(r"(?<![\w$.'\"`])var\s+[A-Za-z_$]", _code(p.read_text(encoding="utf-8")))
    ]
    assert not offenders, f"`var` is back (use const, or let when reassigned): {offenders}"


def test_no_raw_control_characters_in_sources() -> None:
    """A control byte in a source file is an escape that went through a
    non-raw string on its way in - invisible in review, wrong at run time."""
    bad = re.compile(rb"[\x00-\x08\x0b\x0c\x0e-\x1f]")
    offenders = []
    for root, pattern in ((JS, "*.js"), (TEMPLATES, "*.html"), (TEMPLATES / "static/css", "*.css")):
        for p in root.rglob(pattern):
            if p.name.endswith((".min.js", ".min.css")) or "vendor" in p.parts:
                continue
            if bad.search(p.read_bytes()):
                offenders.append(p.relative_to(REPO).as_posix())
    assert not offenders, offenders


def test_the_refresh_key_normalises_time_elements() -> None:
    src = (JS / "_parts/dashboard/20-live-updates.js").read_text(encoding="utf-8")
    assert r".replace(/<time\b[^>]*>[^<]*<\/time>/g, '<time>')" in src


def test_client_paginator_registers_once() -> None:
    src = (JS / "components.js").read_text(encoding="utf-8")
    paginator = src.split("class ClientPaginator {", 1)[1].split("\nclass ", 1)[0]
    assert paginator.count("  register(id) {") == 1


def test_the_fallback_poll_declares_its_error_count() -> None:
    src = (JS / "_parts/course-detail/00-sync-stream.js").read_text(encoding="utf-8")
    assert "let _pollErrorCount = 0;" in src
    assert "const _POLL_MAX_ERRORS = 10;" in src


def test_passive_controls_are_really_excluded() -> None:
    guards = (JS / "process-action-guards.js").read_text(encoding="utf-8")
    assert "GP.isPassiveUiControl = isPassiveUiControl;" in guards
    helpers = (JS / "_parts/core/21-buttons.js").read_text(encoding="utf-8")
    assert "GP.isPassiveUiControl(el)" in helpers
    assert "typeof isPassiveUiControl" not in helpers
