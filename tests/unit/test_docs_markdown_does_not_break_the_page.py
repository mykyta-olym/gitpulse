"""A bare HTML tag in a docs page can swallow the rest of the page.

The changelog carried the line "use <template> components". Hugo passes raw
HTML through, so the browser opened a real `<template>` - and everything after
it, including the whole right-hand rail, went into that element's content
fragment, which is not part of the document. The page rendered with no "Edit
this page", no "Copy for LLM", no table of contents and no back-to-top button,
and nothing in the HTML looked wrong: the markup was well-formed, it just was
not where the parser put it.

`<select>` does the same to its following siblings, and the others listed here
each change how the rest of the document parses. When a page is TALKING about
a tag, it belongs in a code span - which is also what it means.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_CONTENT_DIRS = (
    _REPO / "docs-site" / "content",
    _REPO / "docs-site" / "content-en",
)

# Elements whose content model changes what the parser does with everything
# after them: a fragment (`template`), raw text (`script`, `style`, `title`,
# `textarea`, `xmp`, `plaintext`), or a restricted child list (`table`,
# `select`, `option`, `svg`, `math`).
_BREAKING = (
    "template",
    "script",
    "style",
    "textarea",
    "title",
    "xmp",
    "plaintext",
    "iframe",
    "noscript",
    "table",
    "select",
    "option",
    "svg",
    "math",
    "pre",
)
_BARE_TAG = re.compile(r"</?(" + "|".join(_BREAKING) + r")\b[^>]*>", re.IGNORECASE)


def _outside_code_spans(line: str) -> str:
    """The line with inline code removed - a tag in backticks is just text."""
    return re.sub(r"`[^`]*`", "", line)


def _markdown_files() -> list[Path]:
    return sorted(p for d in _CONTENT_DIRS for p in d.rglob("*.md"))


@pytest.mark.parametrize("path", _markdown_files(), ids=lambda p: str(p.name))
def test_no_page_writes_a_parser_breaking_tag_as_prose(path: Path) -> None:
    offenders: list[str] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in _BARE_TAG.finditer(_outside_code_spans(line)):
            offenders.append(f"{path.name}:{number} {match.group(0)}")
    assert not offenders, (
        "a bare tag in prose changes how the rest of the page parses - put it "
        f"in a code span: {offenders[:8]}"
    )
