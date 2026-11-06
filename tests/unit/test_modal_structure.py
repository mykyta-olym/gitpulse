"""Structural invariants shared by every modal.

Modal bodies are hand-written per page, so the footer convention drifts easily:
`transferCourseModal` had grown a lone full-width submit dropped in the body,
and `eventDetailModal` offered no Close at all. Both read as "this dialog is
built differently from the others".
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATES = Path("src/app/templates")

_CALL_MODAL = re.compile(r"\{%-?\s*call\s+modal\(\s*'([^']+)'")
_ENDCALL = re.compile(r"\{%-?\s*endcall\s*-?%\}")
_ANY_CALL = re.compile(r"\{%-?\s*call\s")

# Modals that legitimately have no footer.
_FOOTERLESS = {
    # A context menu: every row is itself the action.
    "courseMenuModal",
}
# Footers that come from a shared macro rather than literal markup.
_MACRO_FOOTERS = ("config_import_body(", "import_modal_footer(", "rcm-footer")


def _modal_bodies() -> list[tuple[str, str, str]]:
    """Return ``(template, modal_id, body)`` for every ``{% call modal(...) %}``."""
    found: list[tuple[str, str, str]] = []
    for path in sorted(_TEMPLATES.rglob("*.html")):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        i = 0
        while i < len(lines):
            match = _CALL_MODAL.search(lines[i])
            if not match:
                i += 1
                continue
            depth = 0
            body: list[str] = []
            j = i
            for j in range(i, len(lines)):
                if _ANY_CALL.search(lines[j]):
                    depth += 1
                if _ENDCALL.search(lines[j]):
                    depth -= 1
                    if depth == 0:
                        break
                body.append(lines[j])
            found.append((path.relative_to(_TEMPLATES).as_posix(), match.group(1), "\n".join(body)))
            i = j + 1
    return found


def test_the_scan_finds_the_known_modals() -> None:
    """Guard the parser itself - a silent zero would make the rest vacuous."""
    modals = _modal_bodies()

    assert len(modals) > 15
    assert "checkEditorModal" in {mid for _, mid, _ in modals}


def test_every_modal_puts_its_actions_in_a_footer() -> None:
    offenders = []
    for template, modal_id, body in _modal_bodies():
        if modal_id in _FOOTERLESS:
            continue
        if "modal-footer" in body or any(m in body for m in _MACRO_FOOTERS):
            continue
        offenders.append(f"{modal_id} ({template})")

    assert not offenders, "modals without a footer: " + ", ".join(offenders)
