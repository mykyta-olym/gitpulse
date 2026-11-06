"""Regression tests for student dashboard activity scoping."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from app.api.dashboard.students.diffs import _build_diff_views, _diff_line_stats
from app.api.dashboard.students.profile import _course_activity_window


def test_course_activity_window_starts_at_semester_start_and_ends_near_now() -> None:
    course = SimpleNamespace(
        settings=SimpleNamespace(
            semester_start_date=date(2026, 4, 19),
            semester_end_date=date(2026, 6, 30),
        )
    )
    now = datetime(2026, 5, 16, 12, 0, tzinfo=UTC)

    start, end_exclusive, label = _course_activity_window(course, now=now)

    assert start == datetime(2026, 4, 19, tzinfo=UTC)
    assert end_exclusive == now + timedelta(minutes=5)
    assert label == "2026-04-19 - 2026-05-16"


def test_course_activity_window_respects_past_semester_end() -> None:
    course = SimpleNamespace(
        settings=SimpleNamespace(
            semester_start_date=date(2026, 4, 19),
            semester_end_date=date(2026, 4, 30),
        )
    )
    now = datetime(2026, 5, 16, 12, 0, tzinfo=UTC)

    start, end_exclusive, label = _course_activity_window(course, now=now)

    assert start == datetime(2026, 4, 19, tzinfo=UTC)
    assert end_exclusive == datetime(2026, 5, 1, tzinfo=UTC)
    assert label == "2026-04-19 - 2026-04-30"


def test_course_activity_window_disabled_without_semester_start() -> None:
    course = SimpleNamespace(
        settings=SimpleNamespace(
            semester_start_date=None,
            semester_end_date=None,
        )
    )

    assert _course_activity_window(course) == (None, None, "")


def test_diff_line_stats_counts_changes_excluding_headers() -> None:
    text = "@@ -1,2 +1,3 @@\n ctx\n+added\n+also\n-removed\n+++ b/x\n--- a/x"
    assert _diff_line_stats(text) == (2, 1)
    assert _diff_line_stats(None) == (0, 0)
    assert _diff_line_stats("") == (0, 0)


def test_build_diff_views_classifies_and_orders() -> None:
    diffs = [
        SimpleNamespace(
            file_path="z.py",
            old_path=None,
            diff="@@\n+a",
            new_file=False,
            deleted_file=True,
            renamed_file=False,
        ),
        SimpleNamespace(
            file_path="a/new.py",
            old_path=None,
            diff="@@\n+x\n+y",
            new_file=True,
            deleted_file=False,
            renamed_file=False,
        ),
        SimpleNamespace(
            file_path="b/old.py",
            old_path="b/older.py",
            diff="@@\n-q\n+w",
            new_file=False,
            deleted_file=False,
            renamed_file=True,
        ),
    ]

    views = _build_diff_views(diffs)  # type: ignore[arg-type]

    # deleted files sort last; others by path
    assert [v["file_path"] for v in views] == ["a/new.py", "b/old.py", "z.py"]
    assert [v["change"] for v in views] == ["new", "renamed", "deleted"]
    new_view = views[0]
    assert new_view["additions"] == 2
    assert new_view["deletions"] == 0
