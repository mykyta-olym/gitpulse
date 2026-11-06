"""Tests for dynamic custom check evaluation and Pydantic schemas.

Covers all rule types (count, field_check, ratio, word_count),
partial scoring, edge cases, and the CustomCheck CRUD schemas.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest
from pydantic import ValidationError

from app.compliance.dynamic_checks import (
    _compare,
    _eval_count,
    _eval_field_check,
    _eval_ratio,
    _eval_word_count,
    _get_entities,
    _matches_filter,
    evaluate_custom_check,
)
from app.compliance.types import StudentContext
from app.schemas.custom_check import CustomCheckCreate, CustomCheckUpdate

# -- Helpers --


@dataclass
class FakeIssue:
    title: str = "Issue"
    state: str = "opened"
    label_names: list[str] = field(default_factory=list)


@dataclass
class FakeMR:
    title: str = "MR"
    has_test_changes: bool = False
    has_issue_link: bool = False
    state: str = "merged"
    branch_name: str = "feature/x"


@dataclass
class FakeNote:
    word_count: int = 10
    discussion_id: str = "d1"
    body: str = "test"


@dataclass
class FakePipeline:
    status: str = "success"


def _ctx(
    issues: list[Any] | None = None,
    mrs: list[Any] | None = None,
    notes: list[Any] | None = None,
    pipelines: list[Any] | None = None,
    reviews: list[Any] | None = None,
    responses: list[Any] | None = None,
) -> StudentContext:
    from uuid import uuid4

    return StudentContext(
        student_id=uuid4(),
        gitlab_user_id=1,
        gitlab_username="test-user",
        issues_assigned=issues or [],
        mrs_authored=mrs or [],
        notes_on_own_mr=notes or [],
        pipelines=pipelines or [],
        reviews_given=reviews or [],
        own_responses=responses or [],
    )


# -- _compare --


class TestCompare:
    def test_gte(self) -> None:
        assert _compare(3, ">=", 2) is True
        assert _compare(2, ">=", 2) is True
        assert _compare(1, ">=", 2) is False

    def test_lte(self) -> None:
        assert _compare(1, "<=", 2) is True
        assert _compare(3, "<=", 2) is False

    def test_gt(self) -> None:
        assert _compare(3, ">", 2) is True
        assert _compare(2, ">", 2) is False

    def test_lt(self) -> None:
        assert _compare(1, "<", 2) is True
        assert _compare(2, "<", 2) is False

    def test_eq(self) -> None:
        assert _compare(2, "==", 2) is True
        assert _compare(3, "==", 2) is False

    def test_neq(self) -> None:
        assert _compare(3, "!=", 2) is True
        assert _compare(2, "!=", 2) is False

    def test_unknown_operator_defaults_to_gte(self) -> None:
        assert _compare(2, "~", 2) is True


# -- _matches_filter --


class TestMatchesFilter:
    def test_empty_filter_matches_all(self) -> None:
        assert _matches_filter(FakeIssue(), {}) is True

    def test_single_field_match(self) -> None:
        assert _matches_filter(FakeIssue(state="opened"), {"state": "opened"}) is True

    def test_single_field_mismatch(self) -> None:
        assert _matches_filter(FakeIssue(state="closed"), {"state": "opened"}) is False

    def test_list_value_in(self) -> None:
        assert _matches_filter(FakeIssue(state="opened"), {"state": ["opened", "closed"]}) is True

    def test_list_value_not_in(self) -> None:
        assert _matches_filter(FakeIssue(state="merged"), {"state": ["opened", "closed"]}) is False

    def test_missing_field(self) -> None:
        assert _matches_filter(FakeIssue(), {"nonexistent": True}) is False


# -- _get_entities --


class TestGetEntities:
    def test_known_types(self) -> None:
        ctx = _ctx(
            issues=[FakeIssue()],
            mrs=[FakeMR()],
            pipelines=[FakePipeline()],
        )
        assert len(_get_entities(ctx, "issue")) == 1
        assert len(_get_entities(ctx, "merge_request")) == 1
        assert len(_get_entities(ctx, "pipeline")) == 1

    def test_unknown_type_returns_empty(self) -> None:
        assert _get_entities(_ctx(), "unknown") == []


# -- _eval_count --


class TestEvalCount:
    def test_pass(self) -> None:
        ctx = _ctx(mrs=[FakeMR(), FakeMR()])
        r = _eval_count(ctx, "C01", "Count", {"entity": "merge_request", "threshold": 2}, 0.1)
        assert r.passed is True
        assert r.score == 0.1

    def test_fail(self) -> None:
        ctx = _ctx(mrs=[FakeMR()])
        r = _eval_count(ctx, "C01", "Count", {"entity": "merge_request", "threshold": 3}, 0.1)
        assert r.passed is False
        assert r.score == 0.0

    def test_partial_scoring(self) -> None:
        ctx = _ctx(mrs=[FakeMR()])
        r = _eval_count(
            ctx,
            "C01",
            "Count",
            {"entity": "merge_request", "threshold": 4, "partial_scoring": True},
            0.1,
        )
        assert r.passed is False
        assert r.score == pytest.approx(0.025)  # 0.1 * (1/4)

    def test_with_filter(self) -> None:
        ctx = _ctx(mrs=[FakeMR(state="merged"), FakeMR(state="opened")])
        r = _eval_count(
            ctx,
            "C01",
            "Count",
            {"entity": "merge_request", "filter": {"state": "merged"}, "threshold": 1},
            0.1,
        )
        assert r.passed is True
        assert "1/1" in r.detail

    def test_empty_entities(self) -> None:
        r = _eval_count(_ctx(), "C01", "Count", {"entity": "merge_request", "threshold": 1}, 0.1)
        assert r.passed is False


# -- _eval_field_check --


class TestEvalFieldCheck:
    def test_any_mode_pass(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_test_changes=True), FakeMR(has_test_changes=False)])
        r = _eval_field_check(
            ctx,
            "C02",
            "Field",
            {
                "entity": "merge_request",
                "field": "has_test_changes",
                "expected": True,
                "match_mode": "any",
            },
            0.1,
        )
        assert r.passed is True

    def test_any_mode_fail(self) -> None:
        ctx = _ctx(mrs=[FakeMR(), FakeMR()])
        r = _eval_field_check(
            ctx,
            "C02",
            "Field",
            {
                "entity": "merge_request",
                "field": "has_test_changes",
                "expected": True,
                "match_mode": "any",
            },
            0.1,
        )
        assert r.passed is False

    def test_all_mode_pass(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_test_changes=True), FakeMR(has_test_changes=True)])
        r = _eval_field_check(
            ctx,
            "C02",
            "Field",
            {
                "entity": "merge_request",
                "field": "has_test_changes",
                "expected": True,
                "match_mode": "all",
            },
            0.1,
        )
        assert r.passed is True

    def test_all_mode_fail(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_test_changes=True), FakeMR(has_test_changes=False)])
        r = _eval_field_check(
            ctx,
            "C02",
            "Field",
            {
                "entity": "merge_request",
                "field": "has_test_changes",
                "expected": True,
                "match_mode": "all",
            },
            0.1,
        )
        assert r.passed is False

    def test_partial_scoring(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_test_changes=True), FakeMR(), FakeMR(), FakeMR()])
        r = _eval_field_check(
            ctx,
            "C02",
            "Field",
            {
                "entity": "merge_request",
                "field": "has_test_changes",
                "expected": True,
                "match_mode": "all",
                "partial_scoring": True,
            },
            0.2,
        )
        assert r.passed is False
        assert r.score == pytest.approx(0.05)  # 0.2 * (1/4)

    def test_missing_field_name(self) -> None:
        ctx = _ctx(mrs=[FakeMR()])
        r = _eval_field_check(ctx, "C02", "Field", {"entity": "merge_request", "field": ""}, 0.1)
        assert r.passed is False
        assert "required" in r.detail.lower()

    def test_no_entities(self) -> None:
        r = _eval_field_check(
            _ctx(),
            "C02",
            "Field",
            {"entity": "merge_request", "field": "has_test_changes", "expected": True},
            0.1,
        )
        assert r.passed is False


# -- _eval_ratio --


class TestEvalRatio:
    def test_pass(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_issue_link=True), FakeMR(has_issue_link=True)])
        r = _eval_ratio(
            ctx,
            "C03",
            "Ratio",
            {
                "entity": "merge_request",
                "numerator_filter": {"has_issue_link": True},
                "denominator_filter": {},
                "threshold": 0.5,
            },
            0.1,
        )
        assert r.passed is True
        assert r.score == 0.1

    def test_fail(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_issue_link=True), FakeMR(), FakeMR(), FakeMR()])
        r = _eval_ratio(
            ctx,
            "C03",
            "Ratio",
            {
                "entity": "merge_request",
                "numerator_filter": {"has_issue_link": True},
                "threshold": 0.8,
            },
            0.1,
        )
        assert r.passed is False

    def test_partial_scoring(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_issue_link=True), FakeMR()])
        r = _eval_ratio(
            ctx,
            "C03",
            "Ratio",
            {
                "entity": "merge_request",
                "numerator_filter": {"has_issue_link": True},
                "threshold": 1.0,
                "partial_scoring": True,
            },
            0.1,
        )
        assert r.passed is False
        assert 0 < r.score < 0.1

    def test_no_denominator(self) -> None:
        r = _eval_ratio(_ctx(), "C03", "Ratio", {"entity": "merge_request"}, 0.1)
        assert r.passed is False


# -- _eval_word_count --


class TestEvalWordCount:
    def test_pass(self) -> None:
        ctx = _ctx(notes=[FakeNote(word_count=50), FakeNote(word_count=40)])
        r = _eval_word_count(ctx, "C04", "Words", {"entity": "note", "min_avg_words": 30}, 0.1)
        assert r.passed is True
        assert r.score == 0.1

    def test_fail_low_count(self) -> None:
        ctx = _ctx(notes=[FakeNote(word_count=5), FakeNote(word_count=10)])
        r = _eval_word_count(ctx, "C04", "Words", {"entity": "note", "min_avg_words": 30}, 0.1)
        assert r.passed is False

    def test_no_notes(self) -> None:
        r = _eval_word_count(_ctx(), "C04", "Words", {"entity": "note", "min_avg_words": 10}, 0.1)
        assert r.passed is False

    def test_threshold_fallback(self) -> None:
        """avg_word_count-style rule: 'threshold' used when 'min_avg_words' absent."""
        ctx = _ctx(notes=[FakeNote(word_count=50), FakeNote(word_count=40)])
        r = _eval_word_count(
            ctx,
            "C04",
            "Words",
            {"entity": "note", "operator": ">=", "threshold": 30},
            0.1,
        )
        assert r.passed is True
        assert r.score == 0.1

    def test_threshold_fallback_fail(self) -> None:
        ctx = _ctx(notes=[FakeNote(word_count=5), FakeNote(word_count=3)])
        r = _eval_word_count(
            ctx,
            "C04",
            "Words",
            {"entity": "note", "operator": ">=", "threshold": 30},
            0.1,
        )
        assert r.passed is False

    def test_avg_word_count_via_dispatcher(self) -> None:
        """'avg_word_count' alias routes to _eval_word_count."""
        ctx = _ctx(notes=[FakeNote(word_count=50)])
        r = evaluate_custom_check(
            ctx,
            "C01",
            "Commit quality",
            {"type": "avg_word_count", "entity": "note", "threshold": 8},
            0.05,
        )
        assert r.passed is True
        assert r.score == 0.05


# -- evaluate_custom_check (dispatcher) --


class TestEvaluateCustomCheck:
    def test_unknown_rule_type(self) -> None:
        r = evaluate_custom_check(_ctx(), "C99", "Unk", {"type": "unicorn"}, 0.1)
        assert r.passed is False
        assert "Unknown" in r.detail

    def test_exception_is_caught(self) -> None:
        """A rule with an invalid filter shouldn't crash."""
        r = evaluate_custom_check(
            _ctx(),
            "C99",
            "Bad",
            {"type": "count", "threshold": "INVALID_NOT_A_NUMBER"},
            0.1,
        )
        # Either a graceful result or an error detail
        assert r.check_id == "C99"

    def test_dispatches_count(self) -> None:
        ctx = _ctx(issues=[FakeIssue()])
        r = evaluate_custom_check(
            ctx, "C01", "Count", {"type": "count", "entity": "issue", "threshold": 1}, 0.1
        )
        assert r.passed is True

    def test_dispatches_field_check(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_test_changes=True)])
        r = evaluate_custom_check(
            ctx,
            "C02",
            "Field",
            {
                "type": "field_check",
                "entity": "merge_request",
                "field": "has_test_changes",
                "expected": True,
            },
            0.1,
        )
        assert r.passed is True

    def test_dispatches_ratio(self) -> None:
        ctx = _ctx(mrs=[FakeMR(has_issue_link=True)])
        r = evaluate_custom_check(
            ctx,
            "C03",
            "Ratio",
            {
                "type": "ratio",
                "entity": "merge_request",
                "numerator_filter": {"has_issue_link": True},
                "threshold": 1.0,
            },
            0.1,
        )
        assert r.passed is True

    def test_dispatches_word_count(self) -> None:
        ctx = _ctx(notes=[FakeNote(word_count=50)])
        r = evaluate_custom_check(
            ctx, "C04", "Words", {"type": "word_count", "entity": "note", "min_avg_words": 10}, 0.1
        )
        assert r.passed is True


# -- Pydantic Schemas --


class TestCustomCheckCreate:
    def test_defaults(self) -> None:
        cc = CustomCheckCreate()
        assert cc.check_code == ""
        assert cc.name == "Custom Check"
        assert cc.category == "custom"
        assert cc.weight == 0.05
        assert cc.is_active is True
        assert cc.evaluation_rule == {}

    def test_valid_categories(self) -> None:
        for cat in ("issue", "mr", "review", "ci", "custom"):
            cc = CustomCheckCreate(category=cat)
            assert cc.category == cat

    def test_invalid_category_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CustomCheckCreate(category="process")  # type: ignore[arg-type]

    def test_weight_range(self) -> None:
        cc = CustomCheckCreate(weight=0.0)
        assert cc.weight == 0.0
        cc = CustomCheckCreate(weight=1.0)
        assert cc.weight == 1.0
        with pytest.raises(ValidationError):
            CustomCheckCreate(weight=1.5)
        with pytest.raises(ValidationError):
            CustomCheckCreate(weight=-0.1)

    def test_invalid_rule_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CustomCheckCreate(evaluation_rule={"type": "magic"})

    def test_valid_rule_types(self) -> None:
        for rt in ("count", "field_check", "ratio", "word_count", "avg_word_count"):
            cc = CustomCheckCreate(evaluation_rule={"type": rt})
            assert cc.evaluation_rule["type"] == rt

    def test_empty_rule_accepted(self) -> None:
        cc = CustomCheckCreate(evaluation_rule={})
        assert cc.evaluation_rule == {}

    def test_name_max_length(self) -> None:
        cc = CustomCheckCreate(name="A" * 200)
        assert len(cc.name) == 200
        with pytest.raises(ValidationError):
            CustomCheckCreate(name="A" * 201)


class TestCustomCheckUpdate:
    def test_all_none_ok(self) -> None:
        u = CustomCheckUpdate()
        data = u.model_dump(exclude_unset=True)
        assert data == {}

    def test_partial_update(self) -> None:
        u = CustomCheckUpdate(name="Renamed", weight=0.3)
        data = u.model_dump(exclude_unset=True)
        assert data == {"name": "Renamed", "weight": 0.3}

    def test_invalid_category(self) -> None:
        with pytest.raises(ValidationError):
            CustomCheckUpdate(category="ci_cd")  # type: ignore[arg-type]

    def test_invalid_rule_type(self) -> None:
        with pytest.raises(ValidationError):
            CustomCheckUpdate(evaluation_rule={"type": "unknown"})

    def test_weight_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            CustomCheckUpdate(weight=2.0)
