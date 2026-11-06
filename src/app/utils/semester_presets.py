"""Semester calendar presets.

Provides a small list of preconfigured semester date ranges so teachers
can one-click populate ``semester_start_date`` / ``semester_end_date``
without copy-pasting dates from the TUKE FEI academic calendar.

Dates follow the official TUKE FEI KPI academic calendar - used for all
Informatika study programs (1st, 2nd, 3rd year, etc., the calendar is
identical for every year of study at TUKE FEI).

Structure
---------
Each preset exposes:

* ``id`` - stable slug used by the UI / API.
* ``label_en`` / ``label_sk`` - localized display names.
* ``start_date`` - Monday of week 1 (first teaching day).
* ``end_date`` - last day of the exam period (the final date after
  which the course should stop generating automation load).

The UI does not list them as presets of their own: a preset IS a term with
its official dates, so every dialog that picks a course's term fills the
dates from here (see ``app.utils.academic_period`` and the period fields in
``components/academic_period.html``). Teachers can still change the dates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime


@dataclass(frozen=True)
class SemesterPreset:
    """A single named semester calendar entry."""

    id: str
    label_en: str
    label_sk: str
    start_date: date
    end_date: date
    academic_year: str
    semester: str  # "winter" or "summer" - matches Course.semester

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label_en": self.label_en,
            "label_sk": self.label_sk,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "academic_year": self.academic_year,
            "semester": self.semester,
        }


# -------------------------------------------------------------
# TUKE FEI KPI academic calendars.
#
# Sources: https://www.fei.tuke.sk/ (Akademický kalendár).
# Verified against the official PDFs for each year.
#
# Semester = 13 teaching weeks + ~6 weeks exam period.
# end_date is set to the LAST DAY of the exam period - this is the
# moment after which automation for that semester should wind down.
# -------------------------------------------------------------
PRESETS: tuple[SemesterPreset, ...] = (
    SemesterPreset(
        id="tuke-fei-ws-2025-2026",
        label_en="TUKE FEI - Winter 2025/2026 (Informatika, all years)",
        label_sk="TUKE FEI - Zimný semester 2025/2026 (Informatika, všetky ročníky)",
        start_date=date(2025, 9, 22),
        end_date=date(2026, 2, 13),
        academic_year="2025/2026",
        semester="winter",
    ),
    SemesterPreset(
        id="tuke-fei-ss-2025-2026",
        label_en="TUKE FEI - Summer 2025/2026 (Informatika, all years)",
        label_sk="TUKE FEI - Letný semester 2025/2026 (Informatika, všetky ročníky)",
        start_date=date(2026, 2, 16),
        end_date=date(2026, 6, 26),
        academic_year="2025/2026",
        semester="summer",
    ),
    SemesterPreset(
        id="tuke-fei-ws-2026-2027",
        label_en="TUKE FEI - Winter 2026/2027 (Informatika, all years)",
        label_sk="TUKE FEI - Zimný semester 2026/2027 (Informatika, všetky ročníky)",
        start_date=date(2026, 9, 21),
        end_date=date(2027, 2, 12),
        academic_year="2026/2027",
        semester="winter",
    ),
    SemesterPreset(
        id="tuke-fei-ss-2026-2027",
        label_en="TUKE FEI - Summer 2026/2027 (Informatika, all years)",
        label_sk="TUKE FEI - Letný semester 2026/2027 (Informatika, všetky ročníky)",
        start_date=date(2027, 2, 8),
        end_date=date(2027, 6, 25),
        academic_year="2026/2027",
        semester="summer",
    ),
)


def get_presets(today: date | None = None) -> list[dict[str, str]]:
    """Return the RELEVANT presets as JSON-serializable dicts.

    Presets whose semester has fully ended (``end_date`` before ``today``) are
    dropped so a list of them never offers a past semester - the reported
    "stale presets". Only the current + upcoming semesters remain. Served by
    ``GET /dashboard/semester-presets``.
    """
    ref = today or datetime.now(UTC).date()
    return [p.to_dict() for p in PRESETS if p.end_date >= ref]


def find_preset(preset_id: str) -> SemesterPreset | None:
    """Look up a preset by its stable ID."""
    return next((p for p in PRESETS if p.id == preset_id), None)


def preset_for(academic_year: str, semester: str) -> SemesterPreset | None:
    """The official calendar of one academic period, or ``None`` if the table
    does not reach it.

    What a course's dates default to: a course created, imported or transferred
    into 2026/2027 summer runs on the TUKE dates of 2026/2027 summer, so every
    dialog that picks a period fills its dates from here rather than from
    whichever preset the reader last clicked.
    """
    return next(
        (p for p in PRESETS if p.academic_year == academic_year and p.semester == semester),
        None,
    )


def running_preset(today: date | None = None) -> SemesterPreset | None:
    """The term whose dates contain ``today``, or ``None`` between two terms.

    Two terms can contain the same day: the winter exam period runs into the
    first week of summer teaching (2027-02-08 .. 2027-02-12). The later-starting
    one wins - by then summer has begun, a new course belongs to it, and the
    week column should count its weeks - and it wins in every caller, because
    every caller asks here.
    """
    ref = today or datetime.now(UTC).date()
    containing = [p for p in PRESETS if p.start_date <= ref <= p.end_date]
    return max(containing, key=lambda p: p.start_date) if containing else None


def current_semester(today: date | None = None) -> SemesterPreset | None:
    """The semester we are in, or the next one about to start.

    Gives pages with NO course in context - the admin events replay range, the
    create-course dialog, any future date field - the same semester anchor the
    course pages get, so every calendar in the app numbers its weeks the same
    way instead of some showing a week column and others none.
    """
    ref = today or datetime.now(UTC).date()
    running = running_preset(ref)
    if running is not None:
        return running
    ordered = sorted(PRESETS, key=lambda p: p.start_date)
    return next((p for p in ordered if p.start_date > ref), None)


def current_semester_start(today: date | None = None) -> str:
    """ISO start date of :func:`current_semester`, or '' when out of calendar."""
    p = current_semester(today)
    return p.start_date.isoformat() if p else ""


__all__ = [
    "PRESETS",
    "SemesterPreset",
    "current_semester",
    "current_semester_start",
    "find_preset",
    "get_presets",
    "preset_for",
    "running_preset",
]
