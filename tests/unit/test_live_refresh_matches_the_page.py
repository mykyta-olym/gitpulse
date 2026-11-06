"""The live refresh must build the SAME list the page built.

Alt-tabbing back to the dashboard made the "Items that need your attention"
card lose an item and 91px of height. It was not a rendering wobble: the
refresh endpoint really did produce a shorter list. It loads its courses with
`load_only(id, code, name, is_active)`, and the attention builder reads
`archived_at`, `academic_year` and `semester` to decide the lifecycle
suggestions - so the "ZARCH-TEST - new academic year started, reactivate?" item
existed on page load and vanished on the first refresh.

Two independent gaps, both of the same kind: the refresh endpoint has to hand
`_build_attention_items` everything the page hands it. It also omitted
`red_teams_count`, which gates the "groups at critical risk" item.

Measured after: 4 items from both paths, and the dashboard holds its height
across a hide/show cycle instead of shrinking 1307px -> 1216px.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOME = REPO / "src/app/api/dashboard/home/routes.py"
ATTENTION = REPO / "src/app/api/dashboard/home/attention.py"


def _fragment() -> str:
    src = HOME.read_text(encoding="utf-8")
    start = src.index("async def dashboard_attention_items(")
    return src[start : src.index("\n@router.", start)]


def test_the_fragment_loads_every_column_the_builder_reads() -> None:
    """`load_only` is a promise about which columns exist; anything the
    attention builder touches has to be on it."""
    loaded = set(re.findall(r"Course\.(\w+),", _fragment()))
    builder = ATTENTION.read_text(encoding="utf-8")
    needed = {
        name
        for name in ("archived_at", "academic_year", "semester", "code", "name", "is_active")
        if re.search(rf"\bc\.{name}\b", builder)
    }
    missing = sorted(needed - loaded)
    assert not missing, (
        f"the refresh loads fewer columns than the builder reads, so it will "
        f"silently produce a shorter list than the page: {missing}"
    )


def test_the_fragment_passes_the_same_gating_count() -> None:
    frag = _fragment()
    assert "red_teams_count" in frag, (
        "without it the 'groups at critical risk' item is dropped on refresh"
    )
    assert "_count_red_teams" in frag


def test_both_paths_call_the_same_builder() -> None:
    """If they ever diverge into two builders, none of the above helps."""
    src = HOME.read_text(encoding="utf-8")
    assert src.count("_build_attention_items(") == 2


ACTIVITY = REPO / "src/app/api/dashboard/home/activity.py"


def _activity_fragment() -> str:
    src = HOME.read_text(encoding="utf-8")
    start = src.index("async def dashboard_activity(")
    return src[start : src.index("\n@router.", start)]


def test_the_activity_refresh_loads_every_column_the_feed_reads() -> None:
    """The feed derives "Course created" and "Course archived" rows from the
    courses. The refresh loaded neither column, so each refresh raised on the
    lazy load - hidden by a swallowing try - and those rows vanished."""
    loaded = set(re.findall(r"Course\.(\w+),", _activity_fragment()))
    feed = ACTIVITY.read_text(encoding="utf-8")
    needed = {
        name
        for name in ("archived_at", "created_at", "code", "name", "is_active")
        if re.search(rf"\bc\.{name}\b", feed)
    }
    assert needed, "the feed no longer reads course columns - update this test"
    missing = sorted(needed - loaded)
    assert not missing, f"the activity refresh loads fewer columns than the feed reads: {missing}"
