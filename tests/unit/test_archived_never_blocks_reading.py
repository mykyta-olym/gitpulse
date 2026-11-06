"""An archived course is read-ONLY, not unreadable.

The guard locks every control inside a settings form, which is right for the
things that write and wrong for the things that only look. Audited across the
five archived-course pages, three components were being locked that cannot
change anything:

* every collapsible card header - so a reader could not fold a section to get
  through a long settings page;
* the "Admins (N)" disclosure - so an archived course hid its own admin list
  behind a greyed-out button;
* the Copy Token button - so a secret they were allowed to SEE could not be
  copied.

They are named in the guard's own allowlist rather than tagged one template at
a time, because the rule is about the component: these are read-only by
construction, wherever they appear. `input[readonly]` is there for the same
reason from the other side - the browser already refuses to edit it, so
disabling it protects nothing and only stops the reader selecting the text.

What stays locked is everything that writes: 130 controls on the archived
settings page and 54 on teachers, including every form dropdown, checkbox and
role picker.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GUARD = REPO / "src/app/templates/static/js/_parts/core/48-archived-course.js"


def _allowlist() -> str:
    src = GUARD.read_text(encoding="utf-8")
    start = src.index("const _READONLY_OK = ")
    return src[start : src.index(";", start)]


def test_the_read_only_components_are_named_centrally() -> None:
    allow = _allowlist()
    for selector in (
        "[data-readonly-ok]",
        ".card-collapse-btn",
        ".tree-toggle-btn",
        ".admin-toggle-btn",
        "input[readonly]",
    ):
        assert selector in allow, (
            f"{selector} is locked on an archived course again, which stops the "
            "reader looking at something they are allowed to see"
        )


def test_the_copy_action_is_allowed() -> None:
    assert "copyRevealedSecret" in _allowlist()


def test_the_guard_still_locks_by_default() -> None:
    """The allowlist is an exception list; anything not on it must still lock."""
    src = GUARD.read_text(encoding="utf-8")
    body = src.split("function _lockControls()", 1)[1].split("\n  }", 1)[0]
    assert "el.matches(_READONLY_OK)" in body, "the allowlist is no longer consulted"
    assert "form.is-course-archived" in body, (
        "the guard no longer walks the archived form, so nothing is locked at all"
    )


def test_a_disclosure_is_never_locked() -> None:
    """ "Edit JSON Configuration" on the settings page only reveals the schedule
    editor that is already on the page - and answered "this course is
    read-only" to a click that changed nothing. Anything with `aria-expanded`
    that is not a listbox toggle is a disclosure, whoever renders it; the
    textarea behind it stays disabled by the same pass. Listbox toggles carry
    `aria-haspopup` and stay locked: opening one is the first half of a change."""
    allow = _allowlist()
    assert "'[aria-expanded]:not([aria-haspopup])'" in allow
    # Alpine writes `aria-expanded` at init; a lock pass that runs first sees
    # only the raw binding, so that is matched too.
    assert "'[\\\\:aria-expanded]:not([aria-haspopup])'" in allow
    assert "'[data-modal-close]'" in allow


def test_every_listbox_toggle_says_it_is_one() -> None:
    """The disclosure rule above is only safe while every dropdown toggle carries
    `aria-haspopup` - that attribute is what keeps the role and form selects
    locked on an archived course."""
    import re

    comps = REPO / "src/app/templates/components"
    for name in ("dropdown.html", "forms.html"):
        src = (comps / name).read_text(encoding="utf-8")
        for tag in re.findall(r"<button[^>]*:aria-expanded[^>]*>", src, flags=re.S):
            if "gl-dropdown-toggle" in tag:
                assert "aria-haspopup" in tag, (
                    f"{name}: a listbox toggle without aria-haspopup "
                    "would be treated as a disclosure"
                )


def test_a_disabled_dropdown_toggle_looks_disabled_on_its_first_frame() -> None:
    """The role selects on an archived Teachers page are rendered `disabled`,
    and there was no `:disabled` rule for the toggle at all - so every filter
    switch painted a row of white, available-looking selects until the guard's
    observer marked them a frame later and the colour transition greyed them:
    "what is locked lights up when I switch filters". The state is the
    element's own; nothing may have to catch up to it."""
    css = (REPO / "src/app/templates/static/css/dropdowns.css").read_text(encoding="utf-8")
    start = css.index(".gl-dropdown-toggle:disabled")
    rule = css[start : css.index("}", start)]
    assert "var(--gl-btn-disabled-bg)" in rule
    assert "transition: none" in rule
