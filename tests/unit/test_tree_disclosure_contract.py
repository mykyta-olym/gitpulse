"""The group tree caps its children behind "View all".

This is easy to break silently and nothing else would notice: an expanded
group renders only the first `tree_child_limit` projects and a
"View all" row - a group with 15 projects otherwise pushes every row below it
off the screen. The cap lives in the TEMPLATE (which stamps `tree-row-extra`);
the client paints by class and holds no copy of the number, so template and
script cannot drift apart - but only as long as those class names stay in sync.

The click guard that used to freeze this toggle on the third rapid click is
covered by test_one_controller_per_interaction.py.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATIC = _REPO / "src/app/templates/static"
_DETAIL = _REPO / "src/app/templates/partials/course/_detail_content.html"
_TREE_JS = _STATIC / "js/_parts/course-detail/30-course-data.js"
_GUARDS_JS = _STATIC / "js/process-action-guards.js"


def test_template_caps_children_and_renders_view_all() -> None:
    html = _DETAIL.read_text(encoding="utf-8")

    assert re.search(r"\{%\s*set\s+tree_child_limit\s*=\s*\d+\s*%\}", html), (
        "tree_child_limit must be set in the template - it is the single source "
        "of truth for the cap"
    )
    assert "loop.index0 >= tree_child_limit" in html, (
        "child rows past the limit must be stamped .tree-row-extra"
    )
    assert "projects|length > tree_child_limit" in html, (
        "the 'View all' row must only render when there are hidden children"
    )
    assert 'class="tree-row-child tree-row-more' in html
    assert "View all (%s more items)" in html, (
        "one translation key with a placeholder - splitting the count off the "
        "noun cannot be translated into Slovak, which inflects it"
    )


def test_client_paints_the_cap_by_class() -> None:
    js = _TREE_JS.read_text(encoding="utf-8")

    # No numeric limit on the client: it must read the classes the server set.
    assert "tree-row-extra" in js
    assert "tree-row-more" in js
    assert "tree-row-show-all" in js
    assert re.search(r"(LIMIT|limit)\s*=\s*\d+", js) is None, (
        "the client must not carry its own copy of the cap - it paints from "
        ".tree-row-extra, which the template stamps"
    )
    # Collapsing has to reset the disclosure, or re-expanding dumps everything.
    assert "classList.remove('tree-row-show-all')" in js
