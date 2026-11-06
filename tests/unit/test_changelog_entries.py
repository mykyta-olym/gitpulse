"""Dashboard changelog entries must have the fields and types required to render."""

import tomllib
from datetime import date
from pathlib import Path

from app.api.dashboard.home.changelog import _CHANGELOG_ENTRIES, _get_changelog_entries

REQUIRED_KEYS = {"date", "title", "title_en", "tag"}
# Changelog entries are a one-line widget on the dashboard, not release notes.
# Keep them short and scannable - one punchy sentence, not a paragraph.
MAX_TITLE_LEN = 160
_ROOT = Path(__file__).resolve().parent.parent.parent
_PYPROJECT = _ROOT / "pyproject.toml"


def test_changelog_entries_are_short() -> None:
    for idx, entry in enumerate(_CHANGELOG_ENTRIES):
        for key in ("title", "title_en"):
            length = len(entry.get(key, ""))
            assert length <= MAX_TITLE_LEN, (
                f"entry #{idx} ({entry.get('date')}) {key} is {length} chars "
                f"(max {MAX_TITLE_LEN}) - keep changelog entries short and scannable"
            )


def _current_release_date() -> date:
    version = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    calver = version.split(".post", 1)[0]
    year, month, day = (int(part) for part in calver.split("."))
    return date(year, month, day)


def test_every_changelog_entry_has_required_keys() -> None:
    for idx, entry in enumerate(_CHANGELOG_ENTRIES):
        missing = REQUIRED_KEYS - entry.keys()
        assert not missing, f"entry #{idx} ({entry.get('date')}) missing {missing}"


def test_changelog_entries_are_not_future_dated() -> None:
    current_release_date = _current_release_date()
    for idx, entry in enumerate(_CHANGELOG_ENTRIES):
        entry_date = date.fromisoformat(entry["date"])
        assert entry_date <= current_release_date, (
            f"entry #{idx} ({entry.get('title_en', entry.get('title'))}) is dated "
            f"{entry_date}, after release day {current_release_date}"
        )


def test_changelog_entries_are_newest_first() -> None:
    dates = [date.fromisoformat(entry["date"]) for entry in _CHANGELOG_ENTRIES]
    assert dates == sorted(dates, reverse=True)


def test_dashboard_changelog_keeps_widget_sized_entry_list() -> None:
    assert len(_CHANGELOG_ENTRIES) == 3


def test_get_changelog_entries_localised_sk() -> None:
    out = _get_changelog_entries(locale="sk", limit=3)
    assert len(out) == 3
    for row in out:
        assert set(row.keys()) == {"date", "title", "tag"}


def test_get_changelog_entries_localised_en() -> None:
    out = _get_changelog_entries(locale="en", limit=3)
    assert len(out) == 3
    for row in out:
        assert set(row.keys()) == {"date", "title", "tag"}


def test_get_changelog_entries_rejects_negative_limits() -> None:
    assert _get_changelog_entries(limit=0) == []
    assert _get_changelog_entries(limit=-1) == []
