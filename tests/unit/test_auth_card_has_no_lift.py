"""The auth card never moves - it only fades.

Clicking Logout lifted the card 4px (measured in Chromium: card top 137px ->
133px) and held the navigation for 140ms so the lift could play. The
accompanying `opacity: 0` in the same rule never applied at all: `.login-card`
carries `animation: fadeIn ... both` (loaders.css), and a filled animation
outranks a plain declaration, so the card stayed fully opaque and the 4px hop
was the whole of what the reader saw.

The entrance fade stays - loaders.css records it as a deliberate exception to
"no page-enter animation", and it carries no transform (fadeIn is opacity 0 to
1), so the card does not move on the way in either.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOGIN_CSS = REPO / "src/app/templates/static/css/login.css"
LOADERS_CSS = REPO / "src/app/templates/static/css/loaders.css"
ANIMATIONS_CSS = REPO / "src/app/templates/static/css/animations.css"
LOGOUT_JS = REPO / "src/app/templates/static/js/pages/logout.js"


def test_no_exit_state_moves_the_card() -> None:
    css = LOGIN_CSS.read_text(encoding="utf-8")
    assert "auth-is-leaving" not in css, "the exit lift is back in login.css"
    for m in re.finditer(r"^\.login-card[^{]*\{(.*?)\}", css, re.S | re.M):
        assert "transform:" not in m.group(1), (
            f"the auth card must not be transformed: {' '.join(m.group(1).split())[:80]}"
        )


def test_nothing_still_applies_the_leaving_class() -> None:
    js = LOGOUT_JS.read_text(encoding="utf-8")
    assert "auth-is-leaving" not in js


def test_logout_is_not_held_back_for_an_animation() -> None:
    js = LOGOUT_JS.read_text(encoding="utf-8")
    delays = [int(d) for d in re.findall(r"\},\s*(\d+)\s*\)", js)]
    assert delays, "the submit no longer yields at all before navigating"
    assert max(delays) == 0, f"logout still waits before submitting, with nothing to play: {delays}"


def test_the_entrance_fade_survives_and_carries_no_transform() -> None:
    """Removing the lift must not take the documented entrance with it."""
    loaders = LOADERS_CSS.read_text(encoding="utf-8")
    m = re.search(r"^\.login-card \{(.*?)\}", loaders, re.S | re.M)
    assert m, "the login card's deliberate entrance is gone"
    assert "fadeIn" in m.group(1)
    frames = re.search(
        r"@keyframes fadeIn \{(.*?)\n\}", ANIMATIONS_CSS.read_text(encoding="utf-8"), re.S
    )
    assert frames, "the fadeIn keyframes are gone"
    assert "transform" not in frames.group(1), (
        "fadeIn grew a transform - the card would move on entrance again"
    )
