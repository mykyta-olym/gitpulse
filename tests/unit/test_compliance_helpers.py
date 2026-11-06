"""Unit tests for compliance engine pure helpers."""

from dataclasses import dataclass
from uuid import uuid4

from app.compliance.engine import (
    _compute_category_scores,
    _compute_response_rate,
    _find_check,
)
from app.compliance.engine_checks import _cfg_bool, _cfg_int, _partial_ratio
from app.compliance.types import CheckResult, StudentContext


@dataclass
class _FakeNote:
    discussion_id: str | None = None


class TestCfgInt:
    """Validate safe integer config reader."""

    def test_reads_existing_key(self) -> None:
        assert _cfg_int({"min_count": 5}, "min_count", 0) == 5

    def test_uses_default_for_missing_key(self) -> None:
        assert _cfg_int({}, "min_count", 3) == 3

    def test_handles_none_value(self) -> None:
        assert _cfg_int({"min_count": None}, "min_count", 7) == 7

    def test_handles_empty_string(self) -> None:
        assert _cfg_int({"min_count": ""}, "min_count", 2) == 2

    def test_converts_string_number(self) -> None:
        assert _cfg_int({"min_count": "10"}, "min_count", 0) == 10


class TestCfgBool:
    """Validate safe bool config reader (JSON strings + native values)."""

    def test_uses_default_for_missing_key(self) -> None:
        assert _cfg_bool({}, "flag", True) is True
        assert _cfg_bool({}, "flag", False) is False

    def test_native_bool_passthrough(self) -> None:
        assert _cfg_bool({"flag": True}, "flag", False) is True
        assert _cfg_bool({"flag": False}, "flag", True) is False

    def test_falsey_strings_are_false(self) -> None:
        for s in ("false", "False", "0", "no", "NO"):
            assert _cfg_bool({"flag": s}, "flag", True) is False

    def test_other_strings_are_true(self) -> None:
        for s in ("true", "1", "yes", "on"):
            assert _cfg_bool({"flag": s}, "flag", False) is True

    def test_non_string_non_bool_normalises_via_bool(self) -> None:
        assert _cfg_bool({"flag": 1}, "flag", False) is True
        assert _cfg_bool({"flag": 0}, "flag", True) is False
        assert _cfg_bool({"flag": None}, "flag", True) is False


class TestPartialRatio:
    """Validate capped partial-credit ratio."""

    def test_below_threshold_is_fractional(self) -> None:
        assert _partial_ratio(1, 2) == 0.5

    def test_at_or_above_threshold_caps_at_one(self) -> None:
        assert _partial_ratio(2, 2) == 1.0
        assert _partial_ratio(5, 2) == 1.0

    def test_zero_threshold_does_not_divide_by_zero(self) -> None:
        assert _partial_ratio(0, 0) == 0.0
        assert _partial_ratio(3, 0) == 1.0

    def test_zero_numerator(self) -> None:
        assert _partial_ratio(0, 4) == 0.0


class TestComputeCategoryScores:
    """Validate category score aggregation."""

    def test_single_check_passed(self) -> None:
        checks = [
            CheckResult(
                check_id="R01", name="Issue", passed=True, detail="ok", weight=1.0, score=1.0
            )
        ]
        scores = _compute_category_scores(checks)
        assert scores["issue"] == 1.0

    def test_single_check_failed(self) -> None:
        checks = [
            CheckResult(
                check_id="R01", name="Issue", passed=False, detail="fail", weight=1.0, score=0.0
            )
        ]
        scores = _compute_category_scores(checks)
        assert scores["issue"] == 0.0

    def test_mixed_categories(self) -> None:
        checks = [
            CheckResult(
                check_id="R01", name="Issue", passed=True, detail="ok", weight=0.5, score=0.5
            ),
            CheckResult(check_id="R12", name="CI", passed=True, detail="ok", weight=0.5, score=0.5),
        ]
        scores = _compute_category_scores(checks)
        assert scores["issue"] == 1.0
        assert scores["ci"] == 1.0

    def test_empty_category_is_none(self) -> None:
        scores = _compute_category_scores([])
        assert scores["issue"] is None
        assert scores["mr"] is None
        assert scores["review"] is None
        assert scores["ci"] is None

    def test_extra_categories_mapping(self) -> None:
        checks = [
            CheckResult(
                check_id="C01", name="Custom", passed=True, detail="ok", weight=1.0, score=1.0
            ),
        ]
        scores = _compute_category_scores(checks, extra_categories={"C01": "ci"})
        assert scores["ci"] == 1.0


class TestFindCheck:
    """Validate check lookup by ID."""

    def test_finds_existing_check(self) -> None:
        checks = [
            CheckResult(check_id="R01", name="Issue", passed=True, detail="ok"),
            CheckResult(check_id="R02", name="MR", passed=False, detail="fail"),
        ]
        result = _find_check(checks, "R01")
        assert result.check_id == "R01"
        assert result.passed is True

    def test_returns_default_for_missing(self) -> None:
        result = _find_check([], "R99")
        assert result.check_id == "R99"
        assert result.passed is False
        assert result.detail == "Not evaluated"


class TestComputeResponseRate:
    """Validate review response rate computation."""

    def test_all_answered(self) -> None:
        ctx = StudentContext(
            student_id=uuid4(),
            gitlab_user_id=1,
            gitlab_username="test",
            notes_on_own_mr=[_FakeNote("d1"), _FakeNote("d2")],
            own_responses=[_FakeNote("d1"), _FakeNote("d2")],
        )
        assert _compute_response_rate(ctx) == 1.0

    def test_none_answered(self) -> None:
        ctx = StudentContext(
            student_id=uuid4(),
            gitlab_user_id=1,
            gitlab_username="test",
            notes_on_own_mr=[_FakeNote("d1"), _FakeNote("d2")],
            own_responses=[],
        )
        assert _compute_response_rate(ctx) == 0.0

    def test_no_discussions(self) -> None:
        ctx = StudentContext(
            student_id=uuid4(),
            gitlab_user_id=1,
            gitlab_username="test",
        )
        assert _compute_response_rate(ctx) == 0.0

    def test_partial_response(self) -> None:
        ctx = StudentContext(
            student_id=uuid4(),
            gitlab_user_id=1,
            gitlab_username="test",
            notes_on_own_mr=[_FakeNote("d1"), _FakeNote("d2"), _FakeNote("d3"), _FakeNote("d4")],
            own_responses=[_FakeNote("d1"), _FakeNote("d3")],
        )
        assert _compute_response_rate(ctx) == 0.5

    def test_ignores_null_discussion_ids(self) -> None:
        ctx = StudentContext(
            student_id=uuid4(),
            gitlab_user_id=1,
            gitlab_username="test",
            notes_on_own_mr=[_FakeNote(None), _FakeNote("d1")],
            own_responses=[_FakeNote("d1")],
        )
        assert _compute_response_rate(ctx) == 1.0
