"""The academic period a page is scoped to.

A course carries ``academic_year`` + ``semester``; a person does not. Every
question about "the students of 2026/2027 summer" therefore goes through the
courses they are in, and this module is the part that names and orders that
period. The edge cases below are the ones that decide whether a filter built on
it is usable, and each was measured against the real TUKE preset table before
being written down.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.utils.academic_period import (
    SEMESTERS,
    AcademicPeriod,
    academic_year_for,
    calendar_period,
    calendar_periods,
    in_session,
    merge_periods,
    parse_key,
)
from app.utils.semester_presets import PRESETS

# The day after the last preset ends - the cliff every "current period" helper
# in the app falls off unless it is handled on purpose.
LAST_PRESET_END = max(p.end_date for p in PRESETS)


def test_a_period_rejects_a_semester_that_is_not_one() -> None:
    with pytest.raises(ValueError, match="unknown semester"):
        AcademicPeriod("2026/2027", "autumn")


def test_a_key_survives_a_url_and_comes_back_the_same() -> None:
    """The key cannot carry the '/' of "2026/2027", so it is rewritten."""
    period = AcademicPeriod("2026/2027", "summer")
    assert period.key == "2026-2027-summer"
    assert parse_key(period.key) == period


@pytest.mark.parametrize(
    "junk",
    ["", None, "junk", "../../etc/passwd", "2026-2027-autumn", "2026-2027", "a-b-winter"],
)
def test_junk_in_the_url_is_refused_rather_than_raising(junk: str | None) -> None:
    """The value arrives from a query string, so anyone can put anything in it."""
    assert parse_key(junk) is None


def test_periods_sort_newest_first_with_winter_before_summer() -> None:
    periods = [
        AcademicPeriod("2025/2026", "summer"),
        AcademicPeriod("2026/2027", "winter"),
        AcademicPeriod("2025/2026", "winter"),
    ]
    newest_first = sorted(periods, key=lambda p: p.sort_key, reverse=True)
    assert [p.key for p in newest_first] == [
        "2026-2027-winter",
        "2025-2026-summer",
        "2025-2026-winter",
    ]


def test_in_session_is_none_between_two_semesters() -> None:
    """A real state, and the reason it is kept separate from calendar_period.

    Mid-July is inside no term at all; a page that wants an answer for every
    date wants calendar_period, and one that wants to say "Current" honestly
    wants this.
    """
    assert in_session(date(2026, 7, 15)) is None
    assert in_session(date(2026, 9, 23)) == AcademicPeriod("2026/2027", "winter")


def test_calendar_period_answers_on_every_date_including_the_holidays() -> None:
    """In the gap it names the term about to start, not the one that ended."""
    assert calendar_period(date(2026, 9, 23)) == AcademicPeriod("2026/2027", "winter")
    assert calendar_period(date(2026, 7, 15)) == AcademicPeriod("2026/2027", "winter")
    assert calendar_period(date(2026, 2, 14)) == AcademicPeriod("2025/2026", "summer")


def test_calendar_period_keeps_working_past_the_end_of_the_preset_table() -> None:
    """The presets stop; the app does not.

    ``current_semester()`` returns ``None`` from here on, so anything built
    directly on it would lose its period entirely on that date. The fallback
    derives one from the shape of the TUKE year instead.
    """
    day_after = date(LAST_PRESET_END.year, LAST_PRESET_END.month, LAST_PRESET_END.day)
    for probe in (day_after, date(2028, 1, 1), date(2030, 3, 5), date(2031, 11, 2)):
        period = calendar_period(probe)
        assert period.semester in SEMESTERS
        assert period.start_year > 2000, probe


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2028, 10, 1), ("2028/2029", "winter")),
        (date(2029, 1, 20), ("2028/2029", "winter")),
        (date(2029, 3, 5), ("2028/2029", "summer")),
        # July and August belong to no term - the reader means the one starting.
        (date(2029, 7, 20), ("2029/2030", "winter")),
        (date(2029, 8, 20), ("2029/2030", "winter")),
    ],
)
def test_the_derived_fallback_follows_the_shape_of_the_tuke_year(
    day: date, expected: tuple[str, str]
) -> None:
    assert calendar_period(day) == AcademicPeriod(*expected)


def test_the_year_rolls_over_in_august() -> None:
    """The same rule ``_suggest_academic_year`` uses, written once."""
    assert academic_year_for(date(2026, 7, 31)) == "2025/2026"
    assert academic_year_for(date(2026, 8, 1)) == "2026/2027"


def test_both_semesters_of_every_year_are_offered() -> None:
    """A period that holds nothing is selectable and visibly empty.

    Listing only the periods that have courses would make an empty winter
    *missing*, which reads as "that year never happened" rather than "nothing
    was taught then".
    """
    options = calendar_periods(date(2026, 9, 23))
    years = {p.academic_year for p in options}
    for year in years:
        for semester in SEMESTERS:
            assert AcademicPeriod(year, semester) in options, (year, semester)


def test_the_options_are_newest_first() -> None:
    options = calendar_periods(date(2026, 9, 23))
    assert options == sorted(options, key=lambda p: p.sort_key, reverse=True)


def test_a_period_older_than_the_calendar_is_merged_in_not_filtered_out() -> None:
    """An import can create a course in a year the preset table never had.

    Dropping it would make its students unreachable on every page that scopes
    by period - the one place they would still need to be found.
    """
    ancient = AcademicPeriod("2019/2020", "summer")
    merged = merge_periods(calendar_periods(date(2026, 9, 23)), [ancient])
    assert ancient in merged
    assert merged == sorted(merged, key=lambda p: p.sort_key, reverse=True)
