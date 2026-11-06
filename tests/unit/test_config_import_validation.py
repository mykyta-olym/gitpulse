"""Validation applied when a course configuration is imported from JSON.

This is the path a teacher hits by dropping a file into "Import Full Course
Configuration", and it is the only thing standing between an arbitrary JSON
document and the settings row. It clamps, truncates and rejects rather than
trusting the file, and every one of those guards was previously unverified.

The functions under test are pure - they take the settings object, the parsed
dict and an error list - so no database is involved.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from app.api.dashboard.courses.settings_config import (
    _apply_builtin_checks_from_config,
    _apply_settings_from_config,
    _check_json_depth,
)


class _Settings:
    """Stand-in for the CourseSettings row, with the defaults it ships with."""

    def __init__(self, **overrides: Any) -> None:
        self.branch_pattern = ""
        self.gitlab_group_path = None
        self.mr_template_required_sections: list[str] = []
        self.test_file_patterns: list[str] = []
        self.enabled_checks: list[str] = []
        self.check_configs: dict[str, Any] = {}
        self.min_reviews_per_mr = 1
        self.min_review_word_count = 10
        self.min_distinct_mrs_reviewed = 1
        self.green_threshold = 0.8
        self.yellow_threshold = 0.5
        self.semester_start_date: date | None = None
        self.semester_end_date: date | None = None
        for key, value in overrides.items():
            setattr(self, key, value)


def _apply(data: dict[str, Any], **overrides: Any) -> tuple[_Settings, list[str]]:
    cs = _Settings(**overrides)
    errors: list[str] = []
    _apply_settings_from_config(cs, data, errors)
    return cs, errors


class TestStringAndPatternFields:
    def test_branch_pattern_is_applied(self) -> None:
        cs, errors = _apply({"branch_pattern": r"^issue-\d+"})

        assert cs.branch_pattern == r"^issue-\d+"
        assert errors == []

    def test_invalid_regex_is_reported_not_swallowed(self) -> None:
        """An unbalanced group would otherwise blow up at scoring time."""
        _, errors = _apply({"branch_pattern": "^(unclosed"})

        assert any("branch_pattern" in e for e in errors)

    def test_overlong_string_is_truncated_to_the_column_width(self) -> None:
        cs, _ = _apply({"branch_pattern": "a" * 500})

        assert len(cs.branch_pattern) == 200


class TestArrayFields:
    def test_entries_are_stripped_and_empties_dropped(self) -> None:
        cs, _ = _apply({"test_file_patterns": ["  *_test.py  ", "", "tests/*"]})

        assert cs.test_file_patterns == ["*_test.py", "tests/*"]

    def test_a_non_list_is_ignored_rather_than_coerced(self) -> None:
        cs, _ = _apply({"test_file_patterns": "*_test.py"})

        assert cs.test_file_patterns == []


class TestNumericClamping:
    @pytest.mark.parametrize(
        ("given", "expected"),
        [(0, 1), (5, 5), (500, 100)],
    )
    def test_integers_are_clamped_into_range(self, given: int, expected: int) -> None:
        cs, _ = _apply({"min_reviews_per_mr": given})

        assert cs.min_reviews_per_mr == expected

    def test_clamping_is_reported_so_the_teacher_sees_it(self) -> None:
        _, errors = _apply({"min_reviews_per_mr": 500})

        assert any("clamped" in e for e in errors)

    def test_a_non_numeric_integer_is_reported(self) -> None:
        _, errors = _apply({"min_reviews_per_mr": "many"})

        assert any("min_reviews_per_mr" in e for e in errors)

    def test_thresholds_are_clamped_to_the_unit_interval(self) -> None:
        cs, _ = _apply({"green_threshold": 5.0, "yellow_threshold": -2.0})

        assert cs.green_threshold == 1.0
        assert cs.yellow_threshold == 0.0


class TestThresholdOrdering:
    def test_green_below_yellow_is_rejected(self) -> None:
        """Inverted thresholds would colour every student backwards."""
        _, errors = _apply({"green_threshold": 0.3, "yellow_threshold": 0.9})

        assert any("green_threshold" in e and "yellow_threshold" in e for e in errors)

    def test_correct_ordering_passes(self) -> None:
        _, errors = _apply({"green_threshold": 0.8, "yellow_threshold": 0.5})

        assert errors == []


class TestSemesterDates:
    def test_valid_dates_are_parsed(self) -> None:
        cs, errors = _apply(
            {"semester_start_date": "2026-02-10", "semester_end_date": "2026-05-20"}
        )

        assert cs.semester_start_date == date(2026, 2, 10)
        assert cs.semester_end_date == date(2026, 5, 20)
        assert errors == []

    def test_a_malformed_date_is_reported_and_the_old_value_kept(self) -> None:
        cs, errors = _apply(
            {"semester_start_date": "10/02/2026"},
            semester_start_date=date(2026, 1, 1),
        )

        assert any("semester_start_date" in e for e in errors)
        assert cs.semester_start_date == date(2026, 1, 1)


class TestBuiltinChecks:
    def test_unknown_check_code_is_reported(self) -> None:
        cs = _Settings()
        errors: list[str] = []

        _apply_builtin_checks_from_config(cs, [{"check_code": "R99"}], errors)

        assert any("R99" in e for e in errors)

    def test_active_flag_drives_enabled_checks_both_ways(self) -> None:
        cs = _Settings(enabled_checks=["R02"])
        errors: list[str] = []

        _apply_builtin_checks_from_config(
            cs,
            [
                {"check_code": "R01", "is_active": True},
                {"check_code": "R02", "is_active": False},
            ],
            errors,
        )

        assert "R01" in cs.enabled_checks
        assert "R02" not in cs.enabled_checks

    def test_weight_is_clamped_to_the_unit_interval(self) -> None:
        cs = _Settings()
        errors: list[str] = []

        _apply_builtin_checks_from_config(cs, [{"check_code": "R01", "weight": 42}], errors)

        weights = [v for k, v in vars(cs).items() if k.startswith("weight_")]
        assert weights
        assert all(0.0 <= w <= 1.0 for w in weights)

    def test_a_non_numeric_weight_is_reported(self) -> None:
        cs = _Settings()
        errors: list[str] = []

        _apply_builtin_checks_from_config(cs, [{"check_code": "R01", "weight": "heavy"}], errors)

        assert any("weight" in e for e in errors)


class TestJsonDepthGuard:
    def test_a_shallow_document_is_accepted(self) -> None:
        assert _check_json_depth({"a": {"b": [1, 2, 3]}}) is True

    def test_a_deeply_nested_document_is_rejected(self) -> None:
        """Guards the parser against a hand-crafted nesting bomb."""
        payload: Any = "leaf"
        for _ in range(60):
            payload = {"nested": payload}

        assert _check_json_depth(payload) is False


class TestWeeklyDeadlines:
    """The weekly schedule drives progressive evaluation, so a malformed
    import must be rejected entry-by-entry rather than accepted wholesale."""

    @staticmethod
    def _apply(weekly: list[Any]) -> tuple[_Settings, list[str]]:
        from app.api.dashboard.courses.settings_config import _apply_weekly_deadlines

        cs = _Settings()
        cs.weekly_deadlines = []
        errors: list[str] = []
        _apply_weekly_deadlines(cs, weekly, errors)
        return cs, errors

    def test_a_valid_schedule_is_applied(self) -> None:
        cs, errors = self._apply(
            [{"week": 3, "label": "Git basics", "expected_checks": ["R01", "R02"]}]
        )

        assert errors == []
        assert cs.weekly_deadlines[0]["week"] == 3
        assert cs.weekly_deadlines[0]["expected_checks"] == ["R01", "R02"]

    def test_a_non_object_entry_is_reported(self) -> None:
        _, errors = self._apply(["week 3"])

        assert any("not an object" in e for e in errors)

    def test_a_missing_week_is_reported(self) -> None:
        _, errors = self._apply([{"label": "no week"}])

        assert any("week" in e for e in errors)

    @pytest.mark.parametrize("week", [0, 53, -1])
    def test_out_of_range_weeks_are_rejected(self, week: int) -> None:
        cs, errors = self._apply([{"week": week}])

        assert any("out of range" in e for e in errors)
        assert cs.weekly_deadlines == []

    def test_duplicate_weeks_are_rejected_keeping_the_first(self) -> None:
        cs, errors = self._apply([{"week": 3, "label": "first"}, {"week": 3, "label": "second"}])

        assert any("duplicate" in e for e in errors)
        assert len(cs.weekly_deadlines) == 1
        assert cs.weekly_deadlines[0]["label"] == "first"

    def test_expected_checks_must_be_an_array(self) -> None:
        cs, errors = self._apply([{"week": 3, "expected_checks": "R01"}])

        assert any("expected_checks" in e for e in errors)
        assert cs.weekly_deadlines[0]["expected_checks"] == []

    def test_a_malformed_deadline_is_reported(self) -> None:
        _, errors = self._apply([{"week": 3, "mr_deadline": "20th of May"}])

        assert any("mr_deadline" in e for e in errors)

    def test_a_missing_label_defaults_to_the_week_number(self) -> None:
        cs, _ = self._apply([{"week": 7}])

        assert cs.weekly_deadlines[0]["label"] == "Week 7"
