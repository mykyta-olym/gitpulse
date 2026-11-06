"""Nothing removes the focus outline without putting something back.

`outline: none` with no replacement is the one CSS line that can make a
control unusable by keyboard while looking perfectly fine with a mouse. The
markdown textarea on the support page had exactly that: it killed the outline
and stopped there, so tabbing into the only free-text field on the page gave
no signal at all.

The error page carries its own token set (it renders without the app's
stylesheet), so its ring is mixed from `--err-primary` rather than hard-coded
blue - one accent for that page instead of two.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "src/app/templates/static/css"


def _sheets() -> list[Path]:
    return [p for p in CSS.rglob("*.css") if ".min." not in p.name and "bundle" not in p.name]


def test_no_rule_removes_focus_without_replacing_it() -> None:
    offenders = []
    for p in _sheets():
        src = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"([^{}]*:focus(?:-visible)?[^{}]*)\{([^}]*)\}", src):
            body = m.group(2)
            if not re.search(r"outline\s*:\s*none", body):
                continue
            replaced = re.search(r"box-shadow\s*:\s*(?!none)", body) or re.search(
                r"outline\s*:\s*(?!none)", body
            )
            if replaced:
                continue
            selector = " ".join(m.group(1).split())
            if ":not(:focus-visible)" in selector:
                continue  # a mouse click legitimately draws nothing
            line = src[: m.start()].count("\n") + 1
            offenders.append(f"{p.name}:{line} {selector[:70]}")
    assert not offenders, (
        f"these leave a keyboard user with no focus indication at all: {offenders}"
    )


def test_focus_rings_come_from_a_token() -> None:
    """A hand-mixed rgba is how a second blue enters the system."""
    offenders = []
    for p in _sheets():
        src = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"[^{}]*:focus(?:-visible)?[^{}]*\{([^}]*)\}", src):
            for sm in re.finditer(r"box-shadow\s*:\s*([^;]+)", m.group(1)):
                value = " ".join(sm.group(1).split())
                # `none` (with or without !important) is a reset that spares
                # focus - `.x:not(:focus-visible) { box-shadow: none }` - not a ring.
                if "var(" in value or value.split(" !important")[0] == "none":
                    continue
                line = src[: m.start()].count("\n") + 1
                offenders.append(f"{p.name}:{line} {value[:60]}")
    assert not offenders, f"focus rings must come from a variable: {offenders}"
