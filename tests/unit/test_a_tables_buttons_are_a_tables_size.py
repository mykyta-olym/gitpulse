"""A button over a table is small; a button over a page is not.

Two sizes, two places. The buttons that act on a table live in that card's
header - Delete selected, Purge Old, Refresh, Check Now, Export, Add Check -
and they are `btn-sm` (24px), the size the row actions beside them already use.
The buttons that act on the whole page live in the page header - Clear Cache,
Refresh Stats - and they are the default 32px (GlButton medium).

They drifted: a pass that componentised the bulk actions dropped `size='sm'`
from the card headers too, so "Delete selected / Purge Old / Refresh" rendered
at page-header height and towered over the table they belong to. This pins the
rule per header block rather than per button, so the next button added to one
of these cards inherits the answer instead of picking one.
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"

_CALL = re.compile(
    r"\{\{-?\s*(btn_icon_only|btn_icon|btn_link_icon|btn|bulk_action)\((.*?)\)\s*-?\}\}", re.S
)


def _header_blocks() -> dict[str, str]:
    """Every `{% set X %}...{% endset %}` that a card is given as header_actions."""
    blocks: dict[str, str] = {}
    for path in sorted(_TEMPLATES.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        for name in set(re.findall(r"header_actions=(\w+)", text)):
            if name == "none":
                continue
            match = re.search(
                r"\{%-?\s*set\s+" + name + r"\s*%\}(.*?)\{%-?\s*endset\s*%\}", text, re.S
            )
            if match:
                blocks[f"{path.relative_to(_TEMPLATES)}:{name}"] = match.group(1)
    return blocks


def test_the_scan_finds_the_header_blocks() -> None:
    blocks = _header_blocks()
    assert len(blocks) >= 10, f"only found {len(blocks)} - the scan is broken, not the templates"


def test_every_button_over_a_table_is_a_table_button() -> None:
    offenders = []
    for where, block in _header_blocks().items():
        for macro, args in _CALL.findall(block):
            # bulk_action already defaults to sm (pinned below), so silence is
            # the right answer there; every other macro defaults to page size.
            if "size=" not in args and macro != "bulk_action":
                label = re.search(r"t\('([^']+)'\)", args)
                offenders.append(f"{where}: {macro}({label.group(1) if label else '?'})")
            elif re.search(r"size='(?!sm')", args):
                size = re.search(r"size='(\w*)'", args)
                offenders.append(f"{where}: {macro} is size='{size.group(1) if size else '?'}'")
    assert not offenders, (
        "these sit in a card header, over a table, at page-header height:\n  "
        + "\n  ".join(offenders)
    )


def test_a_bulk_action_is_small_without_being_asked() -> None:
    """It is always a table's action - there is nowhere else to put one."""
    macro = (_TEMPLATES / "components/bulk_actions.html").read_text(encoding="utf-8")
    assert "size='sm') %}" in macro, "bulk_action defaults to the page-header size again"


def test_the_page_header_keeps_the_page_size() -> None:
    """The other half of the rule: these are not table buttons and are not small."""
    system = (_TEMPLATES / "admin_system.html").read_text(encoding="utf-8")
    header = system.split("page_header(t('System Settings')", 1)[1].split("{% endcall %}", 1)[0]
    assert "btnClearCache" in header
    assert "size='sm'" not in header, (
        "the page's own actions shrank to table size - the reader asked for these "
        "to be the big ones"
    )
