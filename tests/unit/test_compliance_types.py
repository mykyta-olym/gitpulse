"""Tests for app.compliance.types module."""


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_creation(self) -> None:
        from app.compliance.types import CheckResult

        result = CheckResult(
            check_id="R01",
            name="Issue Ownership",
            passed=True,
            detail="Student owns 1 issue",
        )
        assert result.check_id == "R01"
        assert result.name == "Issue Ownership"
        assert result.passed is True
        assert result.detail == "Student owns 1 issue"

    def test_default_weight_and_score(self) -> None:
        from app.compliance.types import CheckResult

        result = CheckResult(
            check_id="R02",
            name="Branch Naming",
            passed=False,
            detail="Branch does not match pattern",
        )
        assert result.weight == 0.0
        assert result.score == 0.0

    def test_custom_weight_and_score(self) -> None:
        from app.compliance.types import CheckResult

        result = CheckResult(
            check_id="R03",
            name="Test Changes",
            passed=True,
            detail="Test files changed",
            weight=0.15,
            score=0.15,
        )
        assert result.weight == 0.15
        assert result.score == 0.15


class TestCommunicationIndicators:
    """Tests for CommunicationIndicators dataclass."""

    def test_all_none_by_default(self) -> None:
        from app.compliance.types import CommunicationIndicators

        indicators = CommunicationIndicators()
        assert indicators.median_first_response_hours is None
        assert indicators.median_review_rounds is None
        assert indicators.discussion_resolution_pct is None
        assert indicators.review_word_depth is None
        assert indicators.author_response_word_depth is None
        assert indicators.median_time_to_merge_hours is None

    def test_with_values(self) -> None:
        from app.compliance.types import CommunicationIndicators

        indicators = CommunicationIndicators(
            median_first_response_hours=2.5,
            median_review_rounds=3.0,
            discussion_resolution_pct=0.85,
            review_word_depth=42.5,
            author_response_word_depth=35.0,
            median_time_to_merge_hours=24.0,
        )
        assert indicators.median_first_response_hours == 2.5
        assert indicators.median_review_rounds == 3.0
        assert indicators.discussion_resolution_pct == 0.85
        assert indicators.review_word_depth == 42.5
        assert indicators.author_response_word_depth == 35.0
        assert indicators.median_time_to_merge_hours == 24.0


class TestComplianceModuleImports:
    """Tests that the compliance module is importable."""

    def test_import_types(self) -> None:
        from app.compliance import types

        assert types is not None

    def test_import_check_result(self) -> None:
        from app.compliance.types import CheckResult

        assert CheckResult is not None
