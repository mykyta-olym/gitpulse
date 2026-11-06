"""Native links, Back and search share the application's navigation policy."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JS = REPO / "src/app/templates/static/js"
UI_HELPERS = JS / "_parts/core/30-data-actions.js"
NAV = JS / "_parts/core/42-spa-navigation.js"
PALETTE = JS / "search-palette.js"

# `location.href = ...` is correct in these: following a server-side redirect
# after a form post (it may rewrite the session, and only a real navigation
# carries that), a hard reload after a change to the shell itself, and the
# fallbacks Back and the search palette keep for URLs that are not ours.
_ALLOWED_HARD_NAV = re.compile(
    r"(redirect|logout|login|language|oauth|reload|fallback"
    r"|backHref|window\.location\.href = href)",
    re.IGNORECASE,
)


def _assignments(path: Path) -> list[str]:
    """Every line that assigns `window.location.href`, with its neighbours, so a
    line reads in the context that says whether it is a fallback."""
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for i, line in enumerate(lines):
        if re.search(r"window\.location\.href\s*=", line):
            out.append("\n".join(lines[max(0, i - 3) : i + 1]))
    return out


def test_the_app_offers_a_navigation_to_go_through() -> None:
    src = NAV.read_text(encoding="utf-8")
    assert "GP.navigateTo = function" in src, "there is nothing for the handlers to call"
    assert "function _spaUrl" in src, (
        "the URL policy must be shared with Back and the search palette"
    )
    body = src.split("GP.navigateTo = function", 1)[1].split("\n  };", 1)[0]
    assert "_spaUrl(href)" in body, "it does not check whether the URL is ours to swap"
    assert "return false" in body, "it cannot tell the caller to fall back"


def test_back_links_ask_first() -> None:
    src = UI_HELPERS.read_text(encoding="utf-8")
    block = src.split("data-nav-back", 1)[1][:900]
    assert "GP.navigateTo?.(" in block, "Back must ask the app before a full navigation"


def test_the_search_palette_asks_first() -> None:
    body = PALETTE.read_text(encoding="utf-8").split("function navigateTo(", 1)[1][:600]
    assert "GP.navigateTo(" in body, "a jump from the palette is still a full page load"


def test_every_remaining_hard_navigation_is_a_deliberate_one() -> None:
    """Not a ban - a hard load is right for the endpoints that rewrite the
    session or the shell. Each one just has to say which it is."""
    stray = []
    for path in (UI_HELPERS, NAV, PALETTE):
        for chunk in _assignments(path):
            if not _ALLOWED_HARD_NAV.search(chunk):
                stray.append(f"{path.name}:\n{chunk}")
    assert not stray, "a navigation the app cannot see:\n\n" + "\n\n".join(stray)
