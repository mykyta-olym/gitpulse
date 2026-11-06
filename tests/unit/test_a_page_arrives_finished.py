"""An in-app navigation shows the incoming page once it is finished.

A full load already does: theme-bootstrap's first-frame gate keeps <body>
hidden until the deferred scripts have run. A navigation swapped the new
content in and only then loaded the page's scripts, so whatever they paint -
a table's rows, a chart, a count - landed after the content was on screen.
Measured on Admin > Events: the table showed 39px tall with every column at its
header's width for a few frames, then the rows landed and it opened out to
4191px with other column widths. Longest on the first visit, before the page
script is cached - the "the table deforms on first launch" report.

The swapped content is now `is-arriving` (visibility: hidden - laid out, so the
scripts measure real boxes, never painted) from the swap's own task until the
scripts and Alpine are done, or displays a retryable script error. A navigation
that stays on the page (a filter, a sort) keeps its controls on screen.
"""

from __future__ import annotations

import re
from pathlib import Path

_STATIC = Path(__file__).resolve().parents[2] / "src/app/templates/static"
_NAV = (_STATIC / "js/_parts/core/42-spa-navigation.js").read_text(encoding="utf-8")
_CSS = (_STATIC / "css/logo.css").read_text(encoding="utf-8")


def _after_swap() -> str:
    start = _NAV.index("document.body.addEventListener('htmx:afterSwap'")
    return _NAV[start : _NAV.index("/* -- Same-document link navigation", start)]


def test_the_swapped_content_is_hidden_until_it_is_finished() -> None:
    handler = _after_swap()
    mark = handler.index("tgt.classList.toggle('is-arriving', _gated)")
    # Set before the page scripts are even requested - in the swap's own task,
    # so no frame paints the unfinished content.
    assert mark < handler.index("_loadScriptsSeq(_pageScripts")
    assert re.search(r"#main-content\.is-arriving\s*\{\s*visibility:\s*hidden;\s*\}", _CSS)


def test_it_is_shown_once_scripts_and_alpine_are_done_or_have_failed() -> None:
    handler = _after_swap()
    loaded = handler[handler.index("_loadScriptsSeq(_pageScripts") :]
    # Both a failed read and successful subtree initialisation reveal the page.
    assert loaded.index("GP.registerPageAlpineData();") < loaded.index(
        "root.removeAttribute('x-ignore')"
    )
    assert loaded.index("window.Alpine.initTree(root)") < loaded.rindex("_arrive();")
    assert "setTimeout(_arrive" not in handler
    assert "GP.errorStateHtml" in loaded
    assert "GP.bindRetry" in loaded


def test_a_navigation_that_stays_on_the_page_keeps_its_controls() -> None:
    handler = _after_swap()
    assert "const _gated = !tgt.classList.contains('is-refining');" in handler


def test_a_stale_navigation_cannot_reveal_a_newer_one() -> None:
    handler = _after_swap()
    arrive = handler[handler.index("const _arrive = function") :]
    assert "if (_navGen === _navGeneration) tgt.classList.remove('is-arriving');" in arrive
