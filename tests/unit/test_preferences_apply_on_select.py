"""Picking a theme repaints the page immediately - Save only persists it.

GitLab's preferences page applies an accent or a scheme the moment you pick it.
Ours waited for Save, so choosing a theme looked like it did nothing at all:
the reported "half the settings do not work". The dirty guard still owns
PERSISTENCE - Save writes, and leaving with unsaved changes still asks - but it
no longer gates the preview.

The undo matters as much as the preview: an SPA navigation swaps
`#main-content` and never re-renders `<html>` (see the note in
tests/unit/test_preferences_apply_on_save.py), so an accent that was tried and
not saved would otherwise follow the reader onto every other page for the rest
of the session and misrepresent what the account holds.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "src/app/templates/static/js/pages/preferences.js"


def _src() -> str:
    return PAGE.read_text(encoding="utf-8")


def test_a_change_repaints_without_waiting_for_save() -> None:
    src = _src()
    assert "form.addEventListener('change', function () {" in src, (
        "nothing previews a preference on selection any more"
    )
    change = src.split("form.addEventListener('change', function () {", 1)[1].split("});", 1)[0]
    assert "applySaved(readForm(form))" in change, (
        "the change handler no longer applies the picked values"
    )


def test_the_preview_is_undone_when_the_page_is_left() -> None:
    src = _src()
    cleanup = src.split("GP.preferencesCleanup = function () {", 1)[1].split("};", 1)[0]
    assert "applySaved(_savedValues)" in cleanup, (
        "an unsaved preview would survive the content swap and follow the "
        "reader onto every other page"
    )


def test_the_baseline_follows_what_was_actually_saved() -> None:
    """Otherwise the cleanup reverts to a stale value and undoes a real save."""
    src = _src()
    if ".then(function () {" in src:
        then = src.split(".then(function () {", 1)[1].split(".catch(", 1)[0]
    else:
        submit_block = src.split("form.addEventListener('submit'", 1)[1].split(
            "form.addEventListener('click'", 1
        )[0]
        then = submit_block.split("apiCall(", 1)[1]
    assert "_savedValues = saved" in then


def test_save_still_owns_persistence() -> None:
    """The preview must not turn into an autosave."""
    src = _src()
    change = src.split("form.addEventListener('change', function () {", 1)[1].split("});", 1)[0]
    for forbidden in ("apiCall", "fetch(", "submit("):
        assert forbidden not in change, (
            f"selecting an option must not write to the server ({forbidden})"
        )


def test_every_syntax_scheme_carries_its_own_ground() -> None:
    """A scheme is a background as much as a palette.

    Only `solarized-light` used to set one, so four of the five previews
    rendered on the same dark block and read as one scheme with the tokens
    slightly recoloured - the reported "syntax highlighting is broken". GitLab
    gives each scheme its own ground, which is what makes them tellable apart.
    """
    css = (REPO / "src/app/templates/static/css/cards.css").read_text(encoding="utf-8")
    schemes = ("default", "monokai", "solarized-dark", "solarized-light", "none")
    missing = []
    grounds = {}
    for name in schemes:
        block = css.split(f".gl-syntax-preview--{name} {{", 1)
        assert len(block) == 2, f"the {name} scheme is gone"
        body = block[1].split("}", 1)[0]
        if "--syn-bg:" not in body or "--syn-fg:" not in body:
            missing.append(name)
        else:
            grounds[name] = body.split("--syn-bg:", 1)[1].split(";", 1)[0].strip()
    assert not missing, f"these schemes set no background of their own: {missing}"
    dark_schemes = {k: v for k, v in grounds.items() if k != "none"}
    assert len(set(dark_schemes.values())) >= 4, (
        f"the schemes must not share one ground, or they look identical: {grounds}"
    )


def test_the_block_reads_the_scheme_ground() -> None:
    css = (REPO / "src/app/templates/static/css/cards.css").read_text(encoding="utf-8")
    block = css.split(".gl-desc-pre.highlight {", 1)
    assert len(block) == 2, "nothing applies the scheme's ground to a code block"
    body = block[1].split("}", 1)[0]
    assert "var(--syn-bg" in body
    assert "var(--syn-fg" in body
