"""`{% call page_header(...) %}{% endcall %}` renders a box with nothing in it.

The macro's caller block exists to hold a page's own actions, and it emits
`<div class="page-header-actions">` whenever it is called as a block - whether
or not anything was put inside. Two pages called it with an empty body: the
System page, which kept its actions in a card of their own below (a header, a
border and 133px of chrome around two buttons), and Preferences, whose actions
live in the sticky footer where GitLab keeps them.

Neither is a render error and neither shows up as a broken page - an empty flex
box takes no height. It is the kind of thing that stays for a year, and it is
cheap to ask about here rather than in a browser.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src" / "app" / "templates"

#: `{% call <macro>(...) %}` ... `{% endcall %}` with nothing but whitespace and
#: comments between them.
_CALL_BLOCK = re.compile(
    r"\{%-?\s*call\s+(?P<macro>[a-z_][\w.]*)\([^%]*?%\}(?P<body>.*?)\{%-?\s*endcall\s*-?%\}",
    re.S,
)
_COMMENT = re.compile(r"\{#.*?#\}", re.S)


def test_no_template_calls_a_macro_as_a_block_and_gives_it_nothing() -> None:
    empty: list[str] = []
    for path in sorted(TEMPLATES.rglob("*.html")):
        if "static" in path.parts:
            continue
        for match in _CALL_BLOCK.finditer(path.read_text(encoding="utf-8")):
            body = _COMMENT.sub("", match.group("body")).strip()
            if not body:
                rel = path.relative_to(TEMPLATES).as_posix()
                empty.append(f"{rel}: {match.group('macro')}() is called as a block with no body")
    assert not empty, (
        "a macro called as a block renders its caller wrapper - an empty one here:\n  "
        + "\n  ".join(empty)
        + "\ncall it as `{{ macro(...) }}` instead, or put the content in."
    )
