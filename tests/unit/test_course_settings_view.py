"""Unit tests for build_semester_status helper."""

from datetime import date
from types import SimpleNamespace

from app.api.dashboard.courses.settings_view import build_semester_status


def test_build_semester_status_none_start_date() -> None:
    # If settings or semester_start_date is missing, it should return None
    course = SimpleNamespace(settings=SimpleNamespace(semester_start_date=None))
    assert build_semester_status(course) is None

    course_no_settings = SimpleNamespace(settings=None)
    assert build_semester_status(course_no_settings) is None


def test_build_semester_status_upcoming() -> None:
    # Today is before start date
    cs = SimpleNamespace(
        semester_start_date=date(2026, 9, 21),
        semester_end_date=date(2026, 12, 25),
        skip_auto_archive=False,
    )
    course = SimpleNamespace(settings=cs, is_active=True)
    status = build_semester_status(course, today=date(2026, 9, 1))
    assert status is not None
    assert status["state"] == "upcoming"
    assert status["badge_label"] == "Upcoming"
    assert status["badge_value"] is None
    assert status["badge_class"] == "badge-secondary"
    assert status["start_label"] == "Starts"
    assert status["start_display"] == "21 Sep 2026"


def test_build_semester_status_active() -> None:
    # Today is during semester (Week 3)
    cs = SimpleNamespace(
        semester_start_date=date(2026, 2, 16),
        semester_end_date=date(2026, 6, 26),
        skip_auto_archive=False,
    )
    course = SimpleNamespace(settings=cs, is_active=True)
    status = build_semester_status(course, today=date(2026, 3, 4))
    assert status is not None
    assert status["state"] == "active"
    # (date(2026, 3, 4) - date(2026, 2, 16)).days = 16. 16 // 7 = 2. 2 + 1 = Week 3
    assert status["badge_value"] == 3
    assert status["badge_label"] == "Week"
    assert status["badge_class"] == "badge-primary"
    assert status["start_label"] == "Started"
    assert status["end_label"] == "Ends"
    assert status["end_display"] == "26 Jun 2026"


def test_build_semester_status_grace_period() -> None:
    # Today is after end but within grace period (14 days)
    cs = SimpleNamespace(
        semester_start_date=date(2026, 2, 16),
        semester_end_date=date(2026, 6, 26),
        skip_auto_archive=False,
    )
    course = SimpleNamespace(settings=cs, is_active=True)
    status = build_semester_status(course, today=date(2026, 7, 3), grace_days=14)
    assert status is not None
    assert status["state"] == "grace"
    assert status["badge_label"] == "Grace period"
    assert status["badge_value"] is None
    assert status["badge_class"] == "badge-warning"
    assert status["archive_label"] == "Auto-archives"
    assert status["archive_display"] == "10 Jul 2026"  # June 26 + 14 days


def test_build_semester_status_auto_archive_due() -> None:
    # Today is past grace period, skip_auto_archive is False
    cs = SimpleNamespace(
        semester_start_date=date(2026, 2, 16),
        semester_end_date=date(2026, 6, 26),
        skip_auto_archive=False,
    )
    course = SimpleNamespace(settings=cs, is_active=True)
    status = build_semester_status(course, today=date(2026, 7, 15), grace_days=14)
    assert status is not None
    assert status["state"] == "auto_archive_due"
    assert status["badge_label"] == "Auto-archive due"
    assert status["badge_class"] == "badge-danger"
    assert status["archive_label"] == "Auto-archives"
    assert status["archive_display"] == "10 Jul 2026"


def test_build_semester_status_auto_archive_skipped() -> None:
    # Today is past grace period, but skip_auto_archive is True
    cs = SimpleNamespace(
        semester_start_date=date(2026, 2, 16),
        semester_end_date=date(2026, 6, 26),
        skip_auto_archive=True,
    )
    course = SimpleNamespace(settings=cs, is_active=True)
    status = build_semester_status(course, today=date(2026, 7, 15), grace_days=14)
    assert status is not None
    assert status["state"] == "auto_archive_skipped"
    assert status["badge_label"] == "Auto-archive skipped"
    assert status["badge_class"] == "badge-warning"
    assert status["archive_label"] == "Auto-archive skipped"
    assert status["archive_display"] == "10 Jul 2026"


def test_build_semester_status_archived() -> None:
    # Course is archived (is_active=False)
    cs = SimpleNamespace(
        semester_start_date=date(2026, 2, 16),
        semester_end_date=date(2026, 6, 26),
        skip_auto_archive=False,
    )
    course = SimpleNamespace(settings=cs, is_active=False)
    status = build_semester_status(course, today=date(2026, 3, 4))
    assert status is not None
    assert status["state"] == "archived"
    assert status["badge_label"] == "Archived"
    assert status["badge_value"] is None
    assert status["badge_class"] == "badge-secondary"
