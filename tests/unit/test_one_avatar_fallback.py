"""An avatar is never an empty disc.

`_gpAvatarShowFallback` (static/js/_parts/core/46-avatar-fallback.js) handles a
failed `img[data-avatar-fallback]`. The contract it relied on was once "reveal
the image's next sibling", honoured in two of the five hand-written avatars:
the ticket submitter, the current assignee and the assignee dropdown put the
image alone inside an `{% if %}` or an `x-if` template, so a 404 avatar, an
expired GitLab URL or a dropped connection left an empty disc on all three.

`components/avatar.html` is GitLab's GlAvatar now, for every avatar in the app:
one `.gl-avatar` box holding the initial, with the picture laid over it. The
initial is there from the first frame, so a failed picture only has to be
hidden - there is no sibling to lose and nothing to reveal.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "src/app/templates"
COMPONENT = TEMPLATES / "components/avatar.html"


def _templates() -> list[Path]:
    return sorted(TEMPLATES.rglob("*.html"))


def _rel(p: Path) -> str:
    return p.relative_to(TEMPLATES).as_posix()


def test_the_component_exists() -> None:
    src = COMPONENT.read_text(encoding="utf-8")
    assert "{% macro avatar(" in src
    assert "{% macro avatar_alpine(" in src


def test_no_template_hand_writes_an_avatar() -> None:
    offenders = {}
    for p in _templates():
        if p == COMPONENT:
            continue
        hits = [
            line.strip()[:90]
            for line in p.read_text(encoding="utf-8").splitlines()
            if "gl-avatar-img" in line
            or 'class="gl-avatar ' in line
            or "data-avatar-fallback" in line
        ]
        if hits:
            offenders[_rel(p)] = hits
    assert not offenders, f"use avatar() / avatar_alpine() from components/avatar.html: {offenders}"


def test_the_initial_is_always_under_the_picture() -> None:
    """Render every branch: the initial and the picture share one box."""
    import sys

    sys.path.insert(0, str(REPO / "src"))
    from app.main import templates as app_templates

    def render(body: str) -> str:
        return app_templates.env.from_string(
            '{% from "components/avatar.html" import avatar, avatar_alpine %}' + body
        ).render(t=lambda s, **k: s, request=None)

    with_url = " ".join(render("{{ avatar('https://example/a.png', 'nikita', size=32) }}").split())
    box = re.fullmatch(
        r'<span class="gl-avatar gl-avatar-s32 [^"]*" aria-hidden="true">N<img [^>]*></span>',
        with_url,
    )
    assert box, f"the picture is not laid over its initial in one box: {with_url}"
    assert "data-avatar-fallback" in with_url

    no_url = " ".join(render("{{ avatar('', 'nikita', size=24) }}").split())
    assert re.fullmatch(
        r'<span class="gl-avatar gl-avatar-s24 [^"]*" aria-hidden="true">N</span>', no_url
    ), no_url

    alpine = " ".join(
        render("{{ avatar_alpine('u.avatar_url', \"(u.name || u.username || '?')\") }}").split()
    )
    assert alpine.index('x-text="(u.name') < alpine.index("<img"), (
        "the initial comes first, the picture over it"
    )


def test_the_handler_only_hides_the_picture() -> None:
    """With the initial already under it, falling back is hiding the picture."""
    js = (TEMPLATES / "static/js/_parts/core/46-avatar-fallback.js").read_text(encoding="utf-8")
    block = js.split("function _gpAvatarShowFallback", 1)
    assert len(block) == 2, "_gpAvatarShowFallback is gone"
    body = block[1].split("\n}", 1)[0]
    assert "img.classList.add('gl-hidden')" in body
    assert "nextElementSibling" not in body
