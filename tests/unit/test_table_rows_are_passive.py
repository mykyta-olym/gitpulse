"""Table navigation belongs to native links and explicit action controls."""

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates"


def test_templates_do_not_attach_actions_or_navigation_to_table_rows():
    offenders = []
    forbidden = re.compile(
        r"\b(?:onclick|data-navigate|data-action|data-href)\s*=|@click|x-on:click"
        r"|cursor-pointer|\brole\s*=\s*['\"](?:button|link)['\"]"
    )
    for path in TEMPLATES.rglob("*.html"):
        source = re.sub(r"\{#.*?#\}", "", path.read_text(encoding="utf-8"), flags=re.S)
        for row in re.finditer(r"<tr\b[^>]*>", source, flags=re.S):
            if forbidden.search(row.group()):
                offenders.append(str(path.relative_to(TEMPLATES)))
    assert not offenders, f"Use links or shared action buttons instead of row handlers: {offenders}"
