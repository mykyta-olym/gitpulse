"""Every icon the activity feed names must exist in the icon set.

A name with no macro branch silently renders the question-mark fallback, which
is how `user-x` shipped: the feed asked for an icon the set never had, and the
row showed "?" instead of a glyph. Nothing else would have caught it.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _available_icon_names() -> set[str]:
    macro = (_REPO / "src/app/templates/components/icons.html").read_text(encoding="utf-8")
    return set(re.findall(r"name == '([^']+)'", macro))


def _feed_icon_names() -> set[str]:
    from app.api.dashboard.home.activity import _AUDIT_ICONS, _JOB_TYPES

    return {icon for icon, _ in _AUDIT_ICONS.values()} | {
        icon for icon, _, _ in _JOB_TYPES.values()
    }


def test_every_activity_feed_icon_exists() -> None:
    available = _available_icon_names()
    used = _feed_icon_names()
    assert used, "the icon maps are empty"
    missing = sorted(name for name in used if name not in available)
    assert not missing, (
        f"activity feed references icons that components/icons.html does not define: {missing}. "
        "They render as the question-mark fallback."
    )
