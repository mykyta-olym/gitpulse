"""Unit tests for course lifecycle and multi-tenant features.

Tests the compliance engine's enabled_checks filter,
course schemas, and feature flag configuration.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest

from app.compliance.engine import run_all_checks
from app.compliance.types import StudentContext

# ===============================================================
#  Stub objects
# ===============================================================


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


NOW = datetime(2025, 5, 15, 12, 0, 0, tzinfo=UTC)


@dataclass
class StubIssue:
    id: uuid.UUID = field(default_factory=_uuid)
    gitlab_iid: int = 1
    assignee_id: uuid.UUID | None = None
    state: str = "opened"


@dataclass
class StubMR:
    id: uuid.UUID = field(default_factory=_uuid)
    gitlab_iid: int = 1
    author_id: uuid.UUID | None = None
    merged_by_id: uuid.UUID | None = None
    state: str = "opened"
    source_branch: str = "issue-1-add-feature"
    target_branch: str = "main"
    branch_naming_ok: bool = True
    template_compliant: bool = True
    has_test_changes: bool = True
    has_issue_link: bool = True
    created_at: datetime = NOW
    merged_at: datetime | None = None


@dataclass
class StubCourseSettings:
    branch_pattern: str = r"^(issue|feat|fix|feature|bugfix|chore|hotfix|refactor)[/-]\d+(-.+)?$"
    mr_template_required_sections: list[str] = field(default_factory=list)
    min_reviews_per_mr: int = 2
    min_review_word_count: int = 30
    min_distinct_mrs_reviewed: int = 2
    mr_creation_deadline: datetime | None = None
    merge_deadline: datetime | None = None
    weight_issue_ownership: float = 0.08
    weight_branch_naming: float = 0.06
    weight_test_changes: float = 0.10
    weight_mr_issue_link: float = 0.08
    weight_mr_template: float = 0.05
    weight_review_count: float = 0.12
    weight_review_duty: float = 0.12
    weight_response_complete: float = 0.10
    weight_approvals: float = 0.09
    weight_merge_by_author: float = 0.07
    weight_closure: float = 0.06
    weight_pipeline_health: float = 0.07
    weight_commit_quality: float = 0.0
    green_threshold: float = 0.80
    yellow_threshold: float = 0.50
    test_file_patterns: list[str] = field(default_factory=lambda: ["**/test_*.py"])
    enabled_checks: list[str] = field(
        default_factory=lambda: [
            "R01",
            "R02",
            "R03",
            "R04",
            "R05",
            "R06",
            "R07",
            "R08",
            "R09",
            "R10",
            "R11",
            "R12",
            "R13",
        ]
    )


def _make_ctx(student_id: uuid.UUID | None = None) -> StudentContext:
    sid = student_id or _uuid()
    return StudentContext(
        student_id=sid,
        gitlab_user_id=42,
        gitlab_username="testuser",
        issues_assigned=[StubIssue(assignee_id=sid)],
        mrs_authored=[StubMR(author_id=sid)],
    )


# ===============================================================
#  Tests: enabled_checks filter
# ===============================================================


class TestEnabledChecksFilter:
    def test_all_enabled_returns_12(self) -> None:
        cs = StubCourseSettings()
        ctx = _make_ctx()
        results = run_all_checks(ctx, cs)
        assert len(results) == 13

    def test_disable_r12_skips_pipeline_check(self) -> None:
        cs = StubCourseSettings()
        cs.enabled_checks = [
            "R01",
            "R02",
            "R03",
            "R04",
            "R05",
            "R06",
            "R07",
            "R08",
            "R09",
            "R10",
            "R11",
        ]  # R12 removed
        ctx = _make_ctx()
        results = run_all_checks(ctx, cs)
        r12 = next(r for r in results if r.check_id == "R12")
        assert r12.weight == 0.0
        assert r12.score == 0.0
        assert r12.detail == "Check disabled"

    def test_only_r01_enabled(self) -> None:
        cs = StubCourseSettings()
        cs.enabled_checks = ["R01"]
        ctx = _make_ctx()
        results = run_all_checks(ctx, cs)
        enabled = [r for r in results if r.detail != "Check disabled"]
        assert len(enabled) == 1
        assert enabled[0].check_id == "R01"

    def test_empty_enabled_checks_disables_all(self) -> None:
        """An explicit empty selection means the teacher disabled every built-in."""
        cs = StubCourseSettings()
        cs.enabled_checks = []
        ctx = _make_ctx()
        results = run_all_checks(ctx, cs)
        disabled = [r for r in results if r.detail == "Check disabled"]
        assert len(disabled) == 13
        assert all(result.weight == 0 for result in results)

    def test_disabled_check_weight_is_zero(self) -> None:
        cs = StubCourseSettings()
        cs.enabled_checks = ["R01"]
        ctx = _make_ctx()
        results = run_all_checks(ctx, cs)
        total_weight = sum(r.weight for r in results)
        # Only R01 weight should be non-zero
        assert total_weight == pytest.approx(0.08, abs=0.001)


# ===============================================================
#  Tests: Course schemas
# ===============================================================


class TestCourseSchemas:
    def test_course_create(self) -> None:
        from app.schemas.courses import CourseCreate

        c = CourseCreate(code="ZSI", name="Software Integration", academic_year="2025/2026")
        assert c.semester == "winter"

    def test_course_read_includes_lifecycle(self) -> None:
        from app.schemas.courses import CourseRead

        fields = CourseRead.model_fields
        assert "archived_at" in fields
        assert "cloned_from_id" in fields
        assert "description" in fields

    def test_transfer_request_defaults(self) -> None:
        from app.schemas.courses import CourseTransferRequest

        r = CourseTransferRequest(academic_year="2026/2027", semester="summer")
        assert r.carry_mode == "all"
        assert r.webhook_mode == "move"
        assert r.archive_source is True
        assert r.enqueue_sync is True

    def test_settings_read_includes_new_fields(self) -> None:
        from app.schemas.courses import CourseSettingsRead

        fields = CourseSettingsRead.model_fields
        assert "enabled_checks" in fields
        assert "weekly_deadlines" in fields
        assert "weight_issue_ownership" in fields

    def test_settings_update_includes_new_fields(self) -> None:
        from app.schemas.courses import CourseSettingsUpdate

        u = CourseSettingsUpdate(
            enabled_checks=["R01", "R02"],
            weekly_deadlines=[{"week": 1, "label": "Sprint 1"}],
        )
        dump = u.model_dump(exclude_unset=True)
        assert len(dump["enabled_checks"]) == 2


# ===============================================================
#  Tests: Student schema with external ID
# ===============================================================


class TestStudentSchema:
    def test_student_create_with_gitlab_user_id(self) -> None:
        from app.schemas.students import StudentCreate

        s = StudentCreate(
            gitlab_user_id=42,
            gitlab_username="alice",
        )
        assert s.gitlab_user_id == 42

    def test_student_read_includes_gitlab_fields(self) -> None:
        from app.schemas.students import StudentRead

        fields = StudentRead.model_fields
        assert "gitlab_user_id" in fields
        assert "gitlab_username" in fields
