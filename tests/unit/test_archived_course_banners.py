"""An archived course is not nagged about stale data.

Archiving a course makes it read-only: Sync All is blocked, and its data going
out of date is the expected consequence rather than something to act on. The
freshness banners were rendered anyway, so an archived course stacked

    Data may be outdated - ... - Try running Sync All to refresh the data.

directly under the strip that had just said the course is read-only: advice the
reader cannot take, printed under the reason they cannot take it.

The archived strip (partials/course/_archived_banner.html) is the one that
belongs there, and it says everything these two would.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[2] / "src/app/templates/partials/course"

# tab template -> the banner call that must be gated on the course being active
_GATED = {
    "_detail_content.html": ("stale_data_banner(", "Data may be outdated"),
    "_activity_content.html": ("stale_data_banner(",),
    "_analytics_content.html": ("stale_data_banner(",),
}


_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)


def _src(name: str) -> str:
    """Template source with Jinja comments stripped - a comment that quotes the
    banner text is not a render of it."""
    return _COMMENT.sub("", (TEMPLATES / name).read_text(encoding="utf-8"))


def _raw(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def test_every_tab_defines_the_archived_flag() -> None:
    for name in _GATED:
        assert "_course_archived" in _raw(name), (
            f"{name} never works out whether the course is archived"
        )


def test_the_flag_is_derived_from_the_course_itself() -> None:
    """The same condition the archived strip uses, so the two cannot disagree."""
    for name in _GATED:
        assert re.search(r"_course_archived\s*=.*not course\.is_active", _raw(name)), (
            f"{name} derives the archived flag from something other than course.is_active"
        )


def _guard_for(src: str, marker: str) -> str:
    """The statement that decides whether `marker` renders.

    For a `{% call %}` block that is the `{% if %}` immediately above it; for a
    plain `{{ ... }}` call it is the call itself.
    """
    idx = src.index(marker)
    if marker.endswith("("):
        return src[idx : src.index("}}", idx)]
    head = src[:idx]
    # The enclosing conditional, not the {% call %} it wraps.
    return head[head.rindex("{% if") :]


def test_freshness_banners_are_suppressed_when_archived() -> None:
    for name, markers in _GATED.items():
        src = _src(name)
        for marker in markers:
            guard = _guard_for(src, marker)
            assert "not _course_archived" in guard, (
                f"{name}: {marker!r} is rendered without checking _course_archived, so an "
                f"archived course is still told to run a sync it cannot run. Guard was: {guard!r}"
            )
