"""The academic period a page is looking at: one academic year and one semester.

A course carries ``academic_year`` + ``semester``; a *person* does not. A
student belongs to a period only through the courses they are a member of, so
"the students of 2026/2027 summer" is a question about memberships, never about
a column on ``users``. Everything here is about naming, validating and ordering
that period so every page, dialog and API asks it the same way.

Why a module of its own
-----------------------
Three different "what period is it?" answers used to exist, and they disagreed:
an August-rollover year guess with no semester in it (the top bar and the
course dialogs), ``semester_presets.current_semester()`` (the date pickers),
and a hand-rolled month rule in the dashboard JavaScript. In July they named
three different terms.

There is one answer now, :func:`period_of_date`, defined at every date: inside
a term, that term; in the gap before one, the one about to start; past the end
of the preset table, derived from the shape of the TUKE year.
:func:`calendar_period` is that answer for today, and :func:`in_session` is
kept separate so a page can still tell "we are inside this one" from "this one
has not started yet".

``semester.py`` is about a single course's OWN start/end dates and whether it
is over. This is about which period a page is scoped to, and which dates a
period has by the official calendar - what a new course's dates default to.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Final

from app.utils.semester_presets import PRESETS, preset_for, running_preset

#: The two terms, in the order they run inside one academic year.
SEMESTERS: Final[tuple[str, str]] = ("winter", "summer")

#: A key is what travels in a URL, so it cannot carry the "/" of "2026/2027".
_KEY_SEPARATOR: Final[str] = "-"

#: How an academic year is written on a course, in the TUKE calendar and in
#: every dialog: two consecutive calendar years. "-" is accepted on the way in
#: (a hand-written JSON config) and stored as "/".
_ACADEMIC_YEAR_RE: Final[re.Pattern[str]] = re.compile(r"^(\d{4})[/-](\d{4})$")

#: TUKE rolls the academic year over in August: before it, we are still in the
#: year that started last calendar year.
_YEAR_ROLLOVER_MONTH: Final[int] = 8

#: How far ahead a term may start and still be the one a day belongs to. Long
#: enough for the summer holidays (late June to late September) and the
#: February gap; far too short to pull a day from a year before the preset
#: table into the table's first term.
_GAP_LOOKAHEAD_DAYS: Final[int] = 120

#: Month boundaries of the TUKE terms, used only as the fallback for dates the
#: preset table does not cover. Winter teaching starts late September and its
#: exam period runs into February; summer runs from mid-February to late June;
#: July and August belong to no term at all.
_WINTER_MONTHS: Final[frozenset[int]] = frozenset({9, 10, 11, 12, 1})
_SUMMER_MONTHS: Final[frozenset[int]] = frozenset({2, 3, 4, 5, 6})


@dataclass(frozen=True, slots=True)
class AcademicPeriod:
    """One academic year and one semester - e.g. 2026/2027 summer."""

    academic_year: str
    semester: str

    def __post_init__(self) -> None:
        if self.semester not in SEMESTERS:
            raise ValueError(f"unknown semester {self.semester!r}; expected one of {SEMESTERS}")

    @property
    def key(self) -> str:
        """URL-safe identity, e.g. ``2026-2027-summer``."""
        return f"{self.academic_year.replace('/', _KEY_SEPARATOR)}{_KEY_SEPARATOR}{self.semester}"

    @property
    def start_year(self) -> int:
        """The calendar year the academic year starts in, for ordering."""
        head = self.academic_year.split("/", 1)[0].strip()
        return int(head) if head.isdigit() else 0

    @property
    def sort_key(self) -> tuple[int, int]:
        """Chronological order: by year, then winter before summer."""
        return (self.start_year, SEMESTERS.index(self.semester))

    def next_year(self) -> AcademicPeriod:
        """The same term one academic year later - where a yearly course runs next.

        What "Transfer to New Semester" should offer by default. A course that
        runs every summer runs next summer; defaulting to the source course's own
        term instead proposes the one it is already in, which the create API
        refuses as a duplicate.
        """
        start = self.start_year
        if not start:
            return self
        return AcademicPeriod(f"{start + 1}/{start + 2}", self.semester)

    def next_term(self) -> AcademicPeriod:
        """The term that follows this one: winter -> summer of the same year,
        summer -> winter of the next."""
        if self.semester == "winter":
            return AcademicPeriod(self.academic_year, "summer")
        start = self.start_year
        return AcademicPeriod(f"{start + 1}/{start + 2}", "winter") if start else self

    def previous_term(self) -> AcademicPeriod:
        """The term before this one: summer -> winter of the same year,
        winter -> summer of the previous."""
        if self.semester == "summer":
            return AcademicPeriod(self.academic_year, "winter")
        start = self.start_year
        return AcademicPeriod(f"{start - 1}/{start}", "summer") if start else self

    def official_dates(self) -> tuple[date, date] | None:
        """First teaching day and last exam day by the TUKE calendar, if known.

        ``None`` for a period the preset table does not reach (a year before it,
        or after it ends). A caller then has no official dates to offer, which is
        a real answer - not a reason to guess.
        """
        preset = preset_for(self.academic_year, self.semester)
        return (preset.start_date, preset.end_date) if preset else None

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"{self.academic_year} {self.semester}"


def normalize_academic_year(value: str | None) -> str:
    """The one accepted spelling of an academic year, or ``ValueError``.

    A course whose year is not two consecutive years ("2026/2028", "26/27",
    "2026") cannot be ordered, cannot be put in a URL and never matches a
    period, so it would silently vanish from every period-scoped page. Every
    way in - the dialogs, the REST API, the JSON config import, the GitLab
    import - goes through here, so none of them can create one.
    """
    text = (value or "").strip().replace(" ", "")
    match = _ACADEMIC_YEAR_RE.match(text)
    if match is None or int(match.group(2)) != int(match.group(1)) + 1:
        raise ValueError(
            f"academic_year must be two consecutive years, e.g. 2026/2027 (got {value!r})"
        )
    return f"{match.group(1)}/{match.group(2)}"


def normalize_semester(value: str | None) -> str:
    """``winter`` or ``summer``, or ``ValueError``. Case and spaces forgiven."""
    text = (value or "").strip().lower()
    if text not in SEMESTERS:
        raise ValueError(f"semester must be 'winter' or 'summer' (got {value!r})")
    return text


def parse_key(value: str | None) -> AcademicPeriod | None:
    """Read a period back out of a URL, or ``None`` if it is not one.

    Never raises: the value comes from a query string, so a stranger can put
    anything in it and the caller falls back to its default.
    """
    if not value:
        return None
    parts = value.strip().split(_KEY_SEPARATOR)
    if len(parts) != 3:
        return None
    first, second, semester = parts
    if semester not in SEMESTERS:
        return None
    try:
        academic_year = normalize_academic_year(f"{first}/{second}")
    except ValueError:
        return None
    return AcademicPeriod(academic_year=academic_year, semester=semester)


def academic_year_for(today: date) -> str:
    """The academic year a date falls in, by the August rollover."""
    start = today.year if today.month >= _YEAR_ROLLOVER_MONTH else today.year - 1
    return f"{start}/{start + 1}"


def in_session(today: date | None = None) -> AcademicPeriod | None:
    """The period we are INSIDE right now, or ``None``.

    ``None`` on any day between two semesters and on any day past the end of
    the preset table - both are real states, and a caller that wants an answer
    for every date wants :func:`calendar_period` instead. Where two terms
    overlap (the winter exams run into the first week of summer teaching) the
    later-starting one is the one we are in; see ``running_preset``.
    """
    preset = running_preset(today or datetime.now(UTC).date())
    return AcademicPeriod(preset.academic_year, preset.semester) if preset else None


def period_of_date(day: date) -> AcademicPeriod:
    """The period a day belongs to. Defined at EVERY date.

    Inside a term, that term. In the gap before one, the one about to start -
    during the summer holidays a reader asking about "now" means the coming
    winter, not the summer that finished in June, and a semester start date
    picked in late August belongs to the winter it opens. Outside the preset
    table it is derived from the shape of the TUKE year instead of giving up,
    because a filter that returns nothing at all the day the table runs out is
    worse than one that is a fortnight out at the term boundary.
    """
    current = in_session(day)
    if current is not None:
        return current

    horizon = day + timedelta(days=_GAP_LOOKAHEAD_DAYS)
    upcoming = [p for p in PRESETS if day < p.start_date <= horizon]
    if upcoming:
        head = min(upcoming, key=lambda p: p.start_date)
        return AcademicPeriod(head.academic_year, head.semester)

    return _derived_period(day)


def calendar_period(today: date | None = None) -> AcademicPeriod:
    """The period a reader means today - :func:`period_of_date` for today.

    What a new course defaults to, what the top bar shows and what the period
    selector marks as Current (or Upcoming).
    """
    return period_of_date(today or datetime.now(UTC).date())


def _derived_period(today: date) -> AcademicPeriod:
    """Fallback for dates the TUKE preset table does not reach.

    The table currently ends on 2027-06-25. After that every page would have no
    period at all, so fall back to the shape of the TUKE year: September to
    January is winter, February to June is summer, and July / August belong to
    the winter that is about to start.
    """
    if today.month in _WINTER_MONTHS:
        return AcademicPeriod(academic_year_for(today), "winter")
    if today.month in _SUMMER_MONTHS:
        return AcademicPeriod(academic_year_for(today), "summer")
    # July / August: between years. The reader means the term about to start,
    # which belongs to the academic year that begins this August.
    start = today.year
    return AcademicPeriod(f"{start}/{start + 1}", "winter")


def calendar_periods(today: date | None = None) -> list[AcademicPeriod]:
    """The periods a scope selector offers even when no course is in them.

    Both terms of the academic year the calendar is in - an empty winter is
    selectable and visibly empty, rather than missing - and the term after
    today's, so the coming one can be looked at before it starts. NOT every
    term of the preset table: a finished term that holds nothing is only
    noise, and the list grew by two every year. Terms that hold courses are
    merged in by the caller (see ``merge_periods``) however old they are, so
    history stays reachable.
    """
    current = calendar_period(today)
    found = {AcademicPeriod(current.academic_year, semester) for semester in SEMESTERS}
    found.add(current.next_term())
    return sorted(found, key=lambda p: p.sort_key, reverse=True)


#: What a course dialog says about each term it offers.
TERM_CURRENT: Final[str] = "current"
TERM_UPCOMING: Final[str] = "upcoming"
TERM_ENDED: Final[str] = "ended"
TERM_LATER: Final[str] = "later"


def dialog_periods(
    today: date | None = None,
    *,
    past_terms: int = 0,
    ahead_terms: int = 3,
    include: AcademicPeriod | None = None,
) -> list[tuple[AcademicPeriod, str]]:
    """The terms a dialog that creates or moves a course offers, newest first.

    The calendar's term and the ``ahead_terms`` after it; ``past_terms``
    before it only where a finished term is a real answer (importing last
    summer's GitLab group for its history). The old dialogs offered a fixed
    span of six YEARS two back and three ahead plus a separate list of presets,
    so a new course could be put into 2024/2025 with one careless click.
    ``include`` adds the course's own term when it is outside that span - the
    Edit dialog must show where the course is.

    Each term comes with its state: ``current`` (running), ``upcoming`` (the
    calendar's term before it starts), ``ended`` or ``later``.
    """
    ref = today or datetime.now(UTC).date()
    anchor = calendar_period(ref)
    running = in_session(ref)
    terms = [anchor]
    nxt = anchor
    for _ in range(ahead_terms):
        nxt = nxt.next_term()
        terms.append(nxt)
    prev = anchor
    for _ in range(past_terms):
        prev = prev.previous_term()
        terms.append(prev)
    if include is not None and include not in terms:
        terms.append(include)

    def state(period: AcademicPeriod) -> str:
        if running is not None and period == running:
            return TERM_CURRENT
        if period == anchor:
            return TERM_UPCOMING
        return TERM_ENDED if period.sort_key < anchor.sort_key else TERM_LATER

    return [(p, state(p)) for p in sorted(terms, key=lambda p: p.sort_key, reverse=True)]


def merge_periods(
    known: list[AcademicPeriod], present: list[AcademicPeriod]
) -> list[AcademicPeriod]:
    """All periods worth offering, newest first.

    ``present`` are the periods that actually hold courses. They are merged in
    rather than filtered against, because a course can sit in a year older than
    the preset table reaches (an import of an old GitLab group) and its
    students have to remain reachable.
    """
    return sorted(set(known) | set(present), key=lambda p: p.sort_key, reverse=True)


def calendar_windows() -> list[dict[str, str]]:
    """Every term of the TUKE calendar with its dates, oldest first.

    What the period fields need to keep a term and its dates together in the
    browser: which official dates a term has, and which term a typed start
    date falls in. Past terms too, because a date typed into last summer still
    has to be recognised as last summer.
    """
    return [
        {
            "id": p.id,
            "academic_year": p.academic_year,
            "semester": p.semester,
            "start": p.start_date.isoformat(),
            "end": p.end_date.isoformat(),
        }
        for p in sorted(PRESETS, key=lambda p: p.start_date)
    ]


__all__ = [
    "SEMESTERS",
    "AcademicPeriod",
    "academic_year_for",
    "calendar_period",
    "calendar_periods",
    "calendar_windows",
    "dialog_periods",
    "in_session",
    "merge_periods",
    "normalize_academic_year",
    "normalize_semester",
    "parse_key",
    "period_of_date",
]
