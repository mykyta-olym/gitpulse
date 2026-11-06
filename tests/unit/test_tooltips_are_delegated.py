"""Tooltips are ONE delegated instance per document, created per element on
first hover - never one instance per element at boot.

Profiled on User Management with 574 rows (production's size): 822ms in
initTippy plus 524ms in localizeTimes (which re-ran initTippy over the whole
document after tagging the <time> cells) - 1.4s of a 1.5s main-thread block on
load, i.e. the page "hangs" - to instantiate 3 404 tooltips of which a reader
can hover one. With `tippy.delegate` on <body>: 1 instance at boot, 345ms of
long tasks on the same page, and every `initTippy(scope)` call after a swap is
free. `el._tippy` still exists for anything that HAS been hovered, so callers
that `setContent` a live tooltip keep working, and content is re-read from the
attribute at every show.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATIC = REPO / "src/app/templates/static"
HELPERS = STATIC / "js/_parts/core/26-tooltips.js"
LOCALIZE = STATIC / "js/localize-time.js"


def _init_tippy() -> str:
    src = HELPERS.read_text(encoding="utf-8")
    start = src.index("function initTippy(")
    return src[start : src.index("function initTooltips(", start)]


def test_init_tippy_delegates_instead_of_instantiating() -> None:
    body = _init_tippy()
    assert "window.tippy.delegate(document.body" in body, (
        "tooltips are instantiated per element again"
    )
    walks = "initTippy walks the scope's elements again - that walk cost 822ms on 574 rows"
    assert "elements.forEach" not in body, walks
    assert "querySelectorAll" not in body, walks
    assert "_tippyDelegate" in body, "the delegate is not memoised; every swap would add another"


def test_the_delegate_keeps_the_show_rules() -> None:
    body = _init_tippy()
    assert "_scrollingUntil" in body, "tooltips open again while the wheel is moving"
    assert ":focus-visible" in body, "a programmatic focus (modal focus-trap) pops a tooltip again"
    assert "removeAttribute('title')" in body, (
        "native title survives beside the tippy - a double tooltip"
    )
    prepare = (
        HELPERS.read_text(encoding="utf-8")
        .split("function _prepareTooltip(", 1)[1]
        .split("function initCardInfoTips(", 1)[0]
    )
    assert "_prepareTooltip(instance)" in body, "the delegate bypasses the shared show rules"
    assert "setContent(live)" in prepare, (
        "content is not re-read at show time; a rewritten label stays stale"
    )


def test_localize_times_does_not_rebind_every_tooltip() -> None:
    src = LOCALIZE.read_text(encoding="utf-8")
    body = src[
        src.index("function localizeTimes(") : src.index("window.localizeTimes = localizeTimes")
    ]
    rebinds = "localizeTimes re-walks every tooltip after each pass - 524ms on the Users page"
    assert "initTippy?.(" not in body, rebinds
    assert "initTippy(" not in body, rebinds


def test_a_default_sort_that_changes_nothing_touches_no_dom() -> None:
    """115ms of the same load was SortableTable moving 574 already-sorted rows
    through a fragment to put them back where they were."""
    src = (STATIC / "js/sortable-table.js").read_text(encoding="utf-8")
    body = src[
        src.index("SortableTable.prototype._doSort") : src.index(
            "SortableTable.prototype._updateUI"
        )
    ]
    assert "if (inOrder) return;" in body
    assert body.index("if (inOrder) return;") < body.index("createDocumentFragment")
