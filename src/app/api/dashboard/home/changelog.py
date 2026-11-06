"""Dashboard "Latest changes" entries and localisation helpers.

The changelog *data* lives in :data:`changelog_entries.json` (sibling
file) so this module stays focused on a single responsibility: loading and
localising those entries for the dashboard widget. Keeping the ~1.5k lines of
hand-maintained release notes out of the Python source keeps the module
reviewable and lets the entries be validated as plain data.
"""

from __future__ import annotations

import json
from pathlib import Path

_ENTRIES_PATH = Path(__file__).with_name("changelog_entries.json")

_CHANGELOG_ENTRIES: list[dict[str, str]] = json.loads(_ENTRIES_PATH.read_text(encoding="utf-8"))
"""Newest-first dashboard changelog entries loaded from the JSON data file.

Each entry has ``date``, ``title`` (Slovak), ``title_en`` (English) and
``tag`` keys. Validated by ``tests/unit/test_changelog_entries.py``.
"""


def _normalise_limit(limit: int | None, default: int = 5) -> int:
    """Return a non-negative entry limit for list slicing."""
    if limit is None:
        return default
    return max(0, limit)


def _get_changelog_entries(locale: str = "sk", limit: int = 5) -> list[dict[str, str]]:
    """Return recent changelog entries localised for the dashboard."""
    key = "title" if locale == "sk" else "title_en"
    max_items = _normalise_limit(limit)
    if max_items == 0:
        return []

    return [
        {
            "date": entry["date"],
            "title": entry.get(key, entry["title"]),
            "tag": entry.get("tag", "feat"),
        }
        for entry in _CHANGELOG_ENTRIES[:max_items]
    ]
