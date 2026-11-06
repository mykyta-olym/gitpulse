"""A settings form's save bar is ONE component, and it is GitLab's.

Two forms carry a dirty guard - course settings and preferences - and each had
written its own bar. Course settings' was sticky under a course-specific name
(`.save-button-container`); the preferences row was static, so the Save button
the guard arms scrolled off the page at exactly the moment it became useful.

Both are now `.settings-sticky-footer`, the name and the rule GitLab uses in
app/assets/stylesheets/pages/settings.scss.

The `pointer-events` check is the other half of the same copy. GitLab's
disabled button (@gitlab/ui 136.3.0, button.scss) sets `cursor: not-allowed`
and deliberately does NOT set `pointer-events: none`: an element that is not a
hit target shows no cursor at all, so a disabled control silently lost the
`not-allowed` affordance. An <a> is the exception - `btn_link` marks a disabled
link with a class because an anchor has no native `disabled` attribute, so
nothing else stops the navigation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "src/app/templates/static/css"
TEMPLATES = REPO / "src/app/templates"

BAR = "settings-sticky-footer"


def _sources(root: Path, suffix: str) -> list[Path]:
    return list(root.rglob(f"*{suffix}"))


def test_the_bar_is_declared_once_and_in_a_shared_stylesheet() -> None:
    """A page bundle would scope it to that page and invite the second copy."""
    declarations = {
        p.relative_to(CSS).as_posix()
        for p in _sources(CSS, ".css")
        if re.search(rf"^\.{BAR} \{{", p.read_text(encoding="utf-8"), re.M)
    }
    assert declarations == {"forms.css"}, (
        f"the shared save bar must be declared once, in forms.css: {declarations}"
    )


def test_it_is_gitlabs_bar_flush_with_the_content() -> None:
    """GitLab's bar is the page's own background under a top border, inside the
    content. Ours added a shadow and pulled the bar 16px out into the
    container's padding on each side: on the light theme a white box floating
    over the page, wider than the cards above it (reported on Preferences and
    course Settings)."""
    rule = re.search(
        rf"^\.{BAR} \{{(.*?)^\}}", (CSS / "forms.css").read_text(encoding="utf-8"), re.S | re.M
    )
    assert rule, "the save bar rule is gone"
    body = rule.group(1)
    assert "box-shadow" not in body, "GitLab's save bar has no shadow"
    assert not re.search(r"margin-(left|right)", body), "the bar is pulled out of the content again"
    assert "border-top: 1px solid var(--gl-border-color-default)" in body
    assert "background: var(--gl-background-color-default)" in body
    restyled = {
        p.relative_to(CSS).as_posix()
        for p in _sources(CSS, ".css")
        if p.name != "forms.css"
        for sel, decls in re.findall(r"([^{}]*)\{([^{}]*)\}", p.read_text(encoding="utf-8"))
        if BAR in sel and re.search(r"margin|box-shadow|padding", decls)
    }
    assert not restyled, f"the bar's box is restyled outside forms.css: {restyled}"


def test_both_guarded_forms_use_it() -> None:
    guarded = {"course_settings.html", "preferences.html"}
    for name in guarded:
        src = (TEMPLATES / name).read_text(encoding="utf-8")
        assert f'class="{BAR}"' in src, f"{name} no longer uses the shared save bar"


def test_no_page_reinvents_a_save_row() -> None:
    """The names the two hand-written bars used, so neither comes back."""
    retired = ("save-button-container", "gl-preferences-actions")
    offenders = {}
    for root, suffix in ((CSS, ".css"), (TEMPLATES, ".html")):
        for p in _sources(root, suffix):
            hits = [n for n in retired if n in p.read_text(encoding="utf-8")]
            if hits:
                offenders[p.relative_to(REPO).as_posix()] = hits
    assert not offenders, f"retired save-bar names are back: {offenders}"


def test_disabled_buttons_keep_their_pointer_events() -> None:
    src = (CSS / "buttons.css").read_text(encoding="utf-8")
    m = re.search(r"^\.btn:disabled,.*?^\}", src, re.S | re.M)
    assert m, "the shared disabled-button rule is gone"
    assert "cursor: not-allowed" in m.group(0)
    assert "pointer-events" not in m.group(0), (
        "GitLab's disabled button stays a hit target so the not-allowed cursor "
        "shows; only a disabled <a> needs pointer-events: none"
    )
    anchor = re.search(r"^a\.btn\.is-disabled,\s*\na\.btn\.disabled \{(.*?)\}", src, re.S | re.M)
    assert anchor, "the disabled-anchor rule is gone"
    assert "pointer-events: none" in anchor.group(1), (
        "a disabled <a> has no native disabled attribute - without "
        "pointer-events: none nothing stops the navigation"
    )
