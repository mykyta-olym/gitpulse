"""Saving a preference has to change the page, not just the database.

`base.html` renders nine preferences onto `<html>` (plus the two diff colours
as custom properties) so CSS can key off them before first paint. Nothing ever
updated them again: the save handler posted the form, said "Preferences saved"
and left the document exactly as it was. Accent, syntax scheme, layout width,
page size, first day of week, time format, relative times and keyboard
shortcuts therefore appeared to do nothing at all until the reader happened to
reload - and an SPA navigation does not count, because it swaps `#main-content`
and never re-renders `<html>`.

The invariant this pins: every preference `base.html` puts on the root element
must also be applied by the page's own `applySaved`, or saving it is invisible.

`theme_preference` is the documented exception - theme-bootstrap.js owns
`[data-theme-value]` and applies the mode on click, before any save.
`preferred_language` is the other: every string on the page was translated
server-side, so the client cannot apply it and the handler reloads instead.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "src/app/templates/base.html"
PAGE = REPO / "src/app/templates/static/js/pages/preferences.js"

sys.path.insert(0, str(REPO / "src"))

APPLIED_ELSEWHERE = {
    "theme_preference": "theme-bootstrap.js applies the mode on click",
    "preferred_language": "server-rendered strings - the handler reloads instead",
}


def _field_names() -> list[str]:
    from app.api.dashboard.preferences import PREFERENCE_FIELDS

    return [f.name for f in PREFERENCE_FIELDS]


def _root_element(src: str) -> str:
    """The opening <html ...> tag, where the pre-paint preferences live.

    Bounded by `<head>` rather than the first `>`: one of the comments inside
    the tag contains the literal `<html>`, and stopping there captured only
    the first two attributes - which made an earlier draft of this test pass
    against the very bug it exists to catch.
    """
    start = src.index("<html")
    return src[start : src.index("<head>", start)]


def test_every_preference_on_the_root_element_is_applied_on_save() -> None:
    root = _root_element(BASE.read_text(encoding="utf-8"))
    page = PAGE.read_text(encoding="utf-8")
    offenders = []
    for name in _field_names():
        if name not in root or name in APPLIED_ELSEWHERE:
            continue
        if name not in page:
            offenders.append(name)
    assert not offenders, (
        "base.html renders these onto <html> but the save handler never updates "
        f"them, so saving one changes nothing until a full page load: {offenders}"
    )


def test_the_exceptions_still_earn_their_exemption() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert "theme-bootstrap.js" in page, (
        "the comment naming who owns the mode is gone - re-check the exemption"
    )
    assert "reloadKeepScroll" in page, (
        "a language change no longer reloads, so the page keeps the old language"
    )


def test_the_save_handler_applies_what_it_saved() -> None:
    page = PAGE.read_text(encoding="utf-8")
    if ".then(function () {" in page:
        body = page.split(".then(function () {", 1)[1].split(".catch(", 1)[0]
    else:
        submit_block = page.split("form.addEventListener('submit'", 1)[1].split(
            "form.addEventListener('click'", 1
        )[0]
        body = submit_block.split("apiCall(", 1)[1]
    assert "applySaved(" in body, "a successful save no longer applies the values"


def test_the_diff_preview_paints_both_panes() -> None:
    """Removed and added are two tables; `querySelector` painted only the first,
    so the added colour previewed as the default no matter what was typed."""
    page = PAGE.read_text(encoding="utf-8")
    m = re.search(r"function repaintPreview\(\) \{(.*?)\n    \}", page, re.S)
    assert m, "repaintPreview is gone"
    assert "querySelectorAll('.gl-diff-preview')" in m.group(1), (
        "the preview must paint every .gl-diff-preview pane, not the first"
    )


def test_the_reset_of_the_guard_precedes_any_reload() -> None:
    """Otherwise the still-registered dirty reason fires the browser's
    "Leave site?" prompt on the way out of a save that just succeeded."""
    page = PAGE.read_text(encoding="utf-8")
    reset = page.index("resetSaveGuard('#preferencesForm', form)")
    reload_at = page.index("reloadKeepScroll")
    assert reset < reload_at, "the save guard must be cleared before the reload"


def test_the_diff_preview_table_is_still_a_table() -> None:
    """`display: block` on a <table> demotes it to a block box: the rows
    collapse into an anonymous max-content table and the row tint - the whole
    point of the preview - stops short of the pane edge. Measured at 267px of a
    667px pane before the scroll container moved to the wrapper."""
    css = (REPO / "src/app/templates/static/css/pages/preferences.css").read_text(encoding="utf-8")
    m = re.search(r"^\.gl-diff-preview \{(.*?)\}", css, re.S | re.M)
    assert m, "the preview rule is gone"
    body = m.group(1)
    assert "display: block" not in body, (
        "the table must stay a table; put the scroll on .gl-diff-preview-pane"
    )
    assert "overflow-x" not in body, "the scroll belongs to the wrapper, not the table"
    assert re.search(r"^\.gl-diff-preview-pane \{", css, re.M), (
        "the scrolling wrapper is gone, so a long line will widen the grid column"
    )
    html = (REPO / "src/app/templates/preferences.html").read_text(encoding="utf-8")
    assert html.count('class="gl-diff-preview-pane"') == 1, (
        "both panes come from one loop - the wrapper must be inside it"
    )
