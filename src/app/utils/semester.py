"""Semester lifecycle helpers.

Exposes two small pure functions used by:

* the dashboard attention items - surface a "semester ended, archive
  recommended" hint once a course's semester is over (archiving is a manual
  action; there is no recurring auto-archive job).
* `app.api.dashboard.admin.events` - surfaces the effective semester-end date
  next to each course so operators can see when a course is over.

Design notes
------------
A course is considered *over* when::

    effective_end + grace_days < today

`effective_end` is the first non-null of:

    1. `CourseSettings.semester_end_date` (explicit, teacher-controlled).
    2. `CourseSettings.semester_start_date + semester_default_length_weeks`
       - used when the teacher has not set an end date but did configure
       the start; avoids leaving automation running forever on a course
       that was imported once and abandoned.

If neither is set, the course is considered *open-ended* and is never
auto-archived by this helper (falls back to manual archival via the
admin UI).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from app.models.course_settings import CourseSettings

# Acceptable bounds for `semester_start_date` / `semester_end_date`.
# A teacher entering a date far outside this window is almost certainly a typo
# (e.g. `0204-09-22` instead of `2024-09-22`). Catching it at the form layer
# prevents corrupt scoping that would either (a) include literally all
# historical GitLab data in compliance scoring, or (b) exclude every commit
# and silently break dashboards.
#
# The lower bound auto-rolls forward each calendar year (today.year - 2)
# so the form never accepts dates that are >2 years stale - a course whose
# semester started that long ago is almost certainly an archival typo.
# A wider fallback (`SEMESTER_DATE_MIN_FALLBACK`) is kept for tests and
# back-compat call sites that import the symbol directly.
SEMESTER_DATE_MIN_FALLBACK = date(2020, 1, 1)
SEMESTER_DATE_MAX_OFFSET_DAYS = 365 * 2  # at most ~2 years in the future
SEMESTER_DATE_MIN_OFFSET_YEARS = 2  # accept dates up to N years before today


def semester_date_min(today: date | None = None) -> date:
    """Return the lower bound for a valid semester date (inclusive).

    Computed as January 1st of `(today.year - SEMESTER_DATE_MIN_OFFSET_YEARS)`
    so the form auto-tightens every year instead of accepting decade-old
    dates that would silently break commit scoping.
    """
    ref = today or date.today()  # noqa: DTZ011 - calendar-day check
    return date(ref.year - SEMESTER_DATE_MIN_OFFSET_YEARS, 1, 1)


class SemesterDateError(ValueError):
    """Raised when a semester start/end date is outside the allowed window."""


def get_effective_semester_end(
    cs: CourseSettings | None,
    default_length_weeks: int,
) -> date | None:
    """Return the effective last-day-of-semester date or None if unknown.

    Prefers explicit `semester_end_date`; falls back to
    `semester_start_date + default_length_weeks` to avoid leaving the
    automation running forever on forgotten courses.
    """
    if cs is None:
        return None
    if cs.semester_end_date is not None:
        return cs.semester_end_date
    if cs.semester_start_date is not None:
        return cs.semester_start_date + timedelta(weeks=default_length_weeks)
    return None


def is_semester_over(
    cs: CourseSettings | None,
    grace_days: int,
    default_length_weeks: int,
    today: date | None = None,
) -> bool:
    """True if the semester ended more than `grace_days` days ago.

    Open-ended courses (neither end nor start configured) are never
    reported as over - they are governed by manual archival only.
    """
    end = get_effective_semester_end(cs, default_length_weeks)
    if end is None:
        return False
    cutoff = end + timedelta(days=grace_days)
    ref = today or date.today()  # noqa: DTZ011 - date-only comparison
    return ref > cutoff


__all__ = [
    "SEMESTER_DATE_MAX_OFFSET_DAYS",
    "SEMESTER_DATE_MIN_FALLBACK",
    "SEMESTER_DATE_MIN_OFFSET_YEARS",
    "SemesterDateError",
    "get_effective_semester_end",
    "is_semester_over",
    "semester_date_min",
    "semester_floor_utc",
    "validate_semester_date",
    "validate_semester_window",
]


def semester_floor_utc(cs: CourseSettings | None) -> datetime | None:
    """Return the UTC midnight of `semester_start_date` or None if unset.

    Centralised so every dashboard, worker, and report uses the *exact*
    same lower bound for "current semester" filtering. Any divergence
    here would split the meaning of "current semester" between sync,
    scoring, and view layers.
    """
    if cs is None or cs.semester_start_date is None:
        return None
    return datetime.combine(cs.semester_start_date, time.min, tzinfo=UTC)


def validate_semester_date(
    value: date,
    *,
    field_name: str = "semester_start_date",
    today: date | None = None,
) -> date:
    """Validate a single semester date.

    Rejects values that fall outside `[semester_date_min(), today + 2y]`.
    A bad date here silently breaks commit fetching (no commits qualify
    as "current semester") so we fail loud at form submission instead.
    """
    ref = today or date.today()  # noqa: DTZ011 - calendar-day check
    upper = ref + timedelta(days=SEMESTER_DATE_MAX_OFFSET_DAYS)
    lower = semester_date_min(ref)
    if value < lower:
        raise SemesterDateError(
            f"{field_name}: {value.isoformat()} is before "
            f"{lower.isoformat()} - did you mean a more recent year?",
        )
    if value > upper:
        raise SemesterDateError(
            f"{field_name}: {value.isoformat()} is more than 2 years in the "
            f"future ({upper.isoformat()}) - sync would return no data.",
        )
    return value


def validate_semester_window(
    start: date | None,
    end: date | None,
    *,
    today: date | None = None,
    stored_start: date | None = None,
    stored_end: date | None = None,
) -> None:
    """Validate both bounds and their relative ordering.

    `end` must not precede `start`, and an empty window
    (`start == end`) is rejected because it produces a zero-length
    semester where every entity is out of scope.

    The range bounds apply only to a date that CHANGED from ``stored_start`` /
    ``stored_end``. They are there to catch a typo as it is typed
    (``0204-09-22``), and they move: the floor is 1 January two years back, so
    a course's own, correct start date sinks below it two years later.
    Re-checking the stored value made every later save of that course - of
    any setting at all - fail with "is before ...". The ordering is always
    checked.
    """
    if start is not None and start != stored_start:
        validate_semester_date(start, field_name="semester_start_date", today=today)
    if end is not None and end != stored_end:
        validate_semester_date(end, field_name="semester_end_date", today=today)
    if start is not None and end is not None and end <= start:
        raise SemesterDateError(
            f"semester_end_date ({end.isoformat()}) must be strictly after "
            f"semester_start_date ({start.isoformat()}).",
        )
