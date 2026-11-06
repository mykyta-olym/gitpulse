"""Unit tests for the semester-scoped sync window helper.

The sync job scopes every GitLab fetch (issues, MRs, pipelines, commits)
to the active course semester when one is configured, so historical
template/fork history is never imported into a fresh course run.
"""

from datetime import date
from types import SimpleNamespace

from app.workers.sync_common import _semester_sync_since_iso


def test_returns_none_when_course_missing() -> None:
    assert _semester_sync_since_iso(None) is None


def test_returns_none_when_settings_missing() -> None:
    course = SimpleNamespace(settings=None)
    assert _semester_sync_since_iso(course) is None


def test_returns_none_when_semester_start_missing() -> None:
    course = SimpleNamespace(settings=SimpleNamespace(semester_start_date=None))
    assert _semester_sync_since_iso(course) is None


def test_returns_iso_with_utc_midnight_when_semester_start_set() -> None:
    course = SimpleNamespace(settings=SimpleNamespace(semester_start_date=date(2026, 2, 17)))
    assert _semester_sync_since_iso(course) == "2026-02-17T00:00:00+00:00"
