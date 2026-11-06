"""View-model helpers for the course settings page."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

from app.utils.semester import get_effective_semester_end


def _display_date(value: date | None) -> str:
    return value.strftime("%d %b %Y") if value else ""


def build_semester_status(
    course: Any,
    *,
    today: date | None = None,
    grace_days: int = 14,
    default_length_weeks: int = 14,
) -> dict[str, object] | None:
    """Build the compact semester status shown in Course Settings.

    The settings page should not keep showing a plain "Week N" badge once the
    teaching window has ended. This helper mirrors the same effective end date
    and grace-period rules used by the auto-archive sweep, then returns a small
    template-ready view model.
    """
    cs = getattr(course, "settings", None)
    start = getattr(cs, "semester_start_date", None)
    if start is None:
        return None

    ref = today or datetime.now(tz=UTC).date()
    week = ((ref - start).days // 7) + 1 if ref >= start else None
    end = get_effective_semester_end(cs, default_length_weeks)
    explicit_end = getattr(cs, "semester_end_date", None) is not None
    skip_auto_archive = bool(getattr(cs, "skip_auto_archive", False))
    active = bool(getattr(course, "is_active", True))

    status: dict[str, object] = {
        "state": "active",
        "badge_label": "Week",
        "badge_value": week,
        "badge_class": "badge-primary",
        "start_label": "Started" if ref >= start else "Starts",
        "start_display": _display_date(start),
        "end_label": "Ends" if explicit_end else "Estimated end",
        "end_display": _display_date(end),
        "archive_label": "",
        "archive_display": "",
    }

    if not active:
        status.update(
            state="archived",
            badge_label="Archived",
            badge_value=None,
            badge_class="badge-secondary",
        )
        return status

    if ref < start:
        status.update(
            state="upcoming",
            badge_label="Upcoming",
            badge_value=None,
            badge_class="badge-secondary",
        )
        return status

    if end is None:
        return status

    archive_date = end + timedelta(days=grace_days)
    if ref > archive_date:
        status.update(
            state="auto_archive_skipped" if skip_auto_archive else "auto_archive_due",
            badge_label="Auto-archive skipped" if skip_auto_archive else "Auto-archive due",
            badge_value=None,
            badge_class="badge-warning" if skip_auto_archive else "badge-danger",
            archive_label="Auto-archive skipped" if skip_auto_archive else "Auto-archives",
            archive_display=_display_date(archive_date),
        )
    elif ref > end:
        status.update(
            state="grace",
            badge_label="Grace period",
            badge_value=None,
            badge_class="badge-warning",
            archive_label="Auto-archive skipped" if skip_auto_archive else "Auto-archives",
            archive_display=_display_date(archive_date),
        )

    return status
