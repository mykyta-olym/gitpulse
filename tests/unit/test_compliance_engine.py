"""Unit tests for the compliance engine.

Tests each of the 12 compliance checks (R01-R12), communication indicators,
traffic-light thresholds, partial scoring, and per-student constraints
(1 issue, 1 MR, 2 reviews) as specified by the ZSI course requirements.

All tests use plain dataclass stubs - no database or async needed.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from app.compliance.engine import (
    _build_student_context,
    _filter_entities_since,
    _get_expected_checks_for_week,
    _semester_start_floor,
    compute_communication_indicators,
    run_all_checks,
)
from app.compliance.types import CheckResult, StudentContext

# ===============================================================
#  Stub objects that mimic SQLAlchemy model attributes
# ===============================================================


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


NOW = datetime(2025, 5, 15, 12, 0, 0, tzinfo=UTC)


@dataclass
class StubIssue:
    id: uuid.UUID = field(default_factory=_uuid)
    project_id: uuid.UUID = field(default_factory=_uuid)
    gitlab_iid: int = 1
    assignee_id: uuid.UUID | None = None
    author_id: uuid.UUID | None = None
    state: str = "opened"


@dataclass
class StubMR:
    id: uuid.UUID = field(default_factory=_uuid)
    project_id: uuid.UUID = field(default_factory=_uuid)
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
    description: str = (
        "Implement feature X with proper error handling and test coverage for all edge cases"
    )
    created_at: datetime = NOW
    merged_at: datetime | None = None


@dataclass
class StubNote:
    id: uuid.UUID = field(default_factory=_uuid)
    merge_request_id: uuid.UUID = field(default_factory=_uuid)
    author_id: uuid.UUID | None = None
    author_gitlab_id: int | None = None
    author_username: str | None = None
    is_system: bool = False
    discussion_id: str | None = None
    contains_commit_ref: bool = False
    word_count: int = 50
    char_count: int = 300
    is_resolvable: bool = False
    is_resolved: bool | None = None
    created_at: datetime = NOW


@dataclass
class StubApproval:
    id: uuid.UUID = field(default_factory=_uuid)
    merge_request_id: uuid.UUID = field(default_factory=_uuid)
    approver_gitlab_id: int = 100
    approver_student_id: uuid.UUID | None = None


@dataclass
class StubReviewActivity:
    id: uuid.UUID = field(default_factory=_uuid)
    merge_request_id: uuid.UUID = field(default_factory=_uuid)
    reviewer_id: uuid.UUID | None = None
    is_meaningful: bool = True
    note_count: int = 3
    total_words: int = 150


@dataclass
class StubPipeline:
    id: uuid.UUID = field(default_factory=_uuid)
    project_id: uuid.UUID = field(default_factory=_uuid)
    ref: str = "issue-1-add-feature"
    status: str = "success"
    has_test_job: bool = True


@dataclass
class StubCommit:
    id: uuid.UUID = field(default_factory=_uuid)
    project_id: uuid.UUID = field(default_factory=_uuid)
    sha: str = "abc1234567890"
    title: str | None = "Fix user authentication flow"
    message: str | None = None
    author_id: uuid.UUID | None = None
    author_gitlab_id: int | None = None
    parent_shas: list[str] = field(default_factory=list)
    committed_at: datetime = NOW

    @property
    def is_merge_commit(self) -> bool:
        return len(self.parent_shas) > 1


@dataclass
class StubCourseSettings:
    """Mimics CourseSettings with default weights summing to 1.0."""

    branch_pattern: str = r"^(issue|feat|fix|feature|bugfix|chore|hotfix|refactor)[/-]\d+(-.+)?$"
    mr_template_required_sections: list[str] = field(default_factory=list)
    min_reviews_per_mr: int = 2
    min_review_word_count: int = 30
    min_distinct_mrs_reviewed: int = 2
    mr_creation_deadline: datetime | None = None
    merge_deadline: datetime | None = None

    # Weights sum to 1.0 across the 12 checks the engine evaluates.
    # R08 (Response Quality) absorbs what was originally split as
    # "response completeness" + "commit references", so its weight is 0.10.
    weight_issue_ownership: float = 0.08  # R01
    weight_branch_naming: float = 0.06  # R02
    weight_test_changes: float = 0.10  # R03
    weight_mr_issue_link: float = 0.08  # R04
    weight_mr_template: float = 0.05  # R05
    weight_review_count: float = 0.12  # R06
    weight_review_duty: float = 0.12  # R07
    weight_response_complete: float = 0.10  # R08
    weight_approvals: float = 0.09  # R09
    weight_merge_by_author: float = 0.07  # R10
    weight_closure: float = 0.06  # R11
    weight_pipeline_health: float = 0.07  # R12
    weight_commit_quality: float = 0.0  # R13 - opt-in, default 0

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
    check_configs: dict[str, Any] = field(default_factory=dict)
    weekly_deadlines: list[dict[str, Any]] = field(default_factory=list)
    semester_start_date: object = None


@dataclass
class StubTimestamped:
    created_at: datetime | None


# ===============================================================
#  Helpers
# ===============================================================


class TestSemesterActivityScoping:
    def test_semester_start_floor_uses_course_start_date(self) -> None:
        cs = StubCourseSettings(semester_start_date=date(2026, 4, 19))

        assert _semester_start_floor(cs) == datetime(2026, 4, 19, tzinfo=UTC)

    def test_filter_entities_since_removes_pre_semester_history(self) -> None:
        lower_bound = datetime(2026, 4, 19, tzinfo=UTC)
        before = StubTimestamped(created_at=datetime(2022, 5, 16, tzinfo=UTC))
        current = StubTimestamped(created_at=datetime(2026, 4, 20, tzinfo=UTC))
        missing_timestamp = StubTimestamped(created_at=None)

        assert _filter_entities_since(
            [before, current, missing_timestamp], "created_at", lower_bound
        ) == [current]


def _make_student_id() -> uuid.UUID:
    return _uuid()


def _make_perfect_context(student_id: uuid.UUID | None = None) -> StudentContext:
    """Build a StudentContext where ALL 12 checks pass.

    Models the ideal ZSI workflow:
    - 1 issue self-assigned
    - 1 MR with correct branch, template, tests, issue link
    - 2 peer reviewers left notes (distinct author_ids)
    - Student responded to all threads with commit refs
    - 2 approvals
    - MR merged by author
    - Issue closed
    - Pipeline green with test job
    """
    sid = student_id or _make_student_id()
    mr_id = _uuid()
    reviewer_a = _make_student_id()
    reviewer_b = _make_student_id()

    issue = StubIssue(assignee_id=sid, state="closed")

    mr = StubMR(
        id=mr_id,
        author_id=sid,
        merged_by_id=sid,
        state="merged",
        merged_at=NOW + timedelta(hours=24),
        created_at=NOW,
    )

    # 2 reviewer notes on own MR (distinct discussions)
    note_a = StubNote(
        merge_request_id=mr_id,
        author_id=reviewer_a,
        discussion_id="disc-1",
        word_count=60,
        created_at=NOW + timedelta(hours=2),
    )
    note_b = StubNote(
        merge_request_id=mr_id,
        author_id=reviewer_b,
        discussion_id="disc-2",
        word_count=45,
        created_at=NOW + timedelta(hours=3),
    )

    # Author responses in same discussions with commit refs
    resp_a = StubNote(
        merge_request_id=mr_id,
        author_id=sid,
        discussion_id="disc-1",
        contains_commit_ref=True,
        word_count=40,
        created_at=NOW + timedelta(hours=4),
    )
    resp_b = StubNote(
        merge_request_id=mr_id,
        author_id=sid,
        discussion_id="disc-2",
        contains_commit_ref=True,
        word_count=35,
        created_at=NOW + timedelta(hours=5),
    )

    # 2 approvals from distinct people
    appr_a = StubApproval(merge_request_id=mr_id, approver_gitlab_id=1001)
    appr_b = StubApproval(merge_request_id=mr_id, approver_gitlab_id=1002)

    # Review duty: reviewed 2 distinct peer MRs
    peer_mr1 = _uuid()
    peer_mr2 = _uuid()
    review_1 = StubReviewActivity(merge_request_id=peer_mr1, reviewer_id=sid)
    review_2 = StubReviewActivity(merge_request_id=peer_mr2, reviewer_id=sid)

    pipeline = StubPipeline(ref="issue-1-add-feature")

    commit1 = StubCommit(
        author_id=sid,
        title="Add user authentication module",
    )
    commit2 = StubCommit(
        author_id=sid,
        title="Fix login edge case for expired tokens",
    )

    ctx = StudentContext(
        student_id=sid,
        gitlab_user_id=42,
        gitlab_username="student42",
    )
    ctx.team_member_count = 3
    ctx.issues_assigned = [issue]
    ctx.mrs_authored = [mr]
    ctx.notes_on_own_mr = [note_a, note_b]
    ctx.own_responses = [resp_a, resp_b]
    ctx.approvals_on_own_mr = [appr_a, appr_b]
    ctx.reviews_given = [review_1, review_2]
    ctx.pipelines = [pipeline]
    ctx.commits = [commit1, commit2]
    ctx.all_team_notes = [note_a, note_b, resp_a, resp_b]

    return ctx


def _find(checks: list[CheckResult], check_id: str) -> CheckResult:
    for c in checks:
        if c.check_id == check_id:
            return c
    raise ValueError(f"{check_id} not found in checks")


# ===============================================================
#  Test: Perfect Student (all checks pass)
# ===============================================================


class TestPerfectStudent:
    """A student who follows the ZSI workflow perfectly should pass all 12 checks."""

    def setup_method(self) -> None:
        self.ctx = _make_perfect_context()
        self.cs = StubCourseSettings()
        self.checks = run_all_checks(self.ctx, self.cs)

    def test_all_12_checks_present(self) -> None:
        assert len(self.checks) == 13

    def test_all_checks_pass(self) -> None:
        for c in self.checks:
            assert c.passed, f"{c.check_id} ({c.name}) failed: {c.detail}"

    def test_weighted_score_equals_1(self) -> None:
        total = sum(c.score for c in self.checks)
        assert abs(total - 1.0) < 0.01

    def test_traffic_light_green(self) -> None:
        total = sum(c.score for c in self.checks)
        assert total >= self.cs.green_threshold


# ===============================================================
#  Test: R01 - Issue Ownership (exactly 1 issue)
# ===============================================================


class TestR01IssueOwnership:
    def test_pass_exactly_one_issue(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        checks = run_all_checks(ctx, cs)
        r01 = _find(checks, "R01")
        assert r01.passed
        assert r01.score == cs.weight_issue_ownership

    def test_fail_zero_issues(self) -> None:
        ctx = _make_perfect_context()
        ctx.issues_assigned = []
        r01 = _find(run_all_checks(ctx, StubCourseSettings()), "R01")
        assert not r01.passed
        assert r01.score == 0.0
        assert "No issue" in r01.detail

    def test_pass_two_issues(self) -> None:
        """Having multiple issues is fine - R01 requires >= 1 by default."""
        ctx = _make_perfect_context()
        sid = ctx.student_id
        ctx.issues_assigned = [
            StubIssue(assignee_id=sid, state="closed"),
            StubIssue(assignee_id=sid, gitlab_iid=2, state="opened"),
        ]
        r01 = _find(run_all_checks(ctx, StubCourseSettings()), "R01")
        assert r01.passed
        assert "2 issue(s) assigned" in r01.detail

    def test_configurable_min_issues(self) -> None:
        """R01 respects check_configs min_issues override."""
        ctx = _make_perfect_context()
        sid = ctx.student_id
        ctx.issues_assigned = [
            StubIssue(assignee_id=sid, state="closed"),
        ]
        cs = StubCourseSettings()
        cs.check_configs = {"R01": {"min_issues": 2}}
        r01 = _find(run_all_checks(ctx, cs), "R01")
        assert not r01.passed
        assert "1/2 issue(s)" in r01.detail


# ===============================================================
#  Test: R02 - Branch Naming
# ===============================================================


class TestR02BranchNaming:
    def test_pass_correct_pattern(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        cs.check_configs = {"R02": {"require_branch_convention": True}}
        r02 = _find(run_all_checks(ctx, cs), "R02")
        assert r02.passed

    def test_fail_bad_branch(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].branch_naming_ok = False
        cs = StubCourseSettings()
        cs.check_configs = {"R02": {"require_branch_convention": True}}
        r02 = _find(run_all_checks(ctx, cs), "R02")
        assert not r02.passed
        assert "does not match" in r02.detail

    def test_fail_no_mr(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored = []
        r02 = _find(run_all_checks(ctx, StubCourseSettings()), "R02")
        assert not r02.passed
        assert "No MR" in r02.detail

    def test_pass_convention_disabled(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].branch_naming_ok = False
        cs = StubCourseSettings()
        cs.check_configs = {"R02": {"require_branch_convention": False}}
        r02 = _find(run_all_checks(ctx, cs), "R02")
        assert r02.passed
        assert "not required" in r02.detail

    def test_pass_convention_default_permissive(self) -> None:
        """Default (no cfg) is permissive: passes with any MR present."""
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].branch_naming_ok = False
        r02 = _find(run_all_checks(ctx, StubCourseSettings()), "R02")
        assert r02.passed
        assert "not required" in r02.detail


# ===============================================================
#  Test: R03 - Test Changes
# ===============================================================


class TestR03TestChanges:
    def test_pass_has_tests(self) -> None:
        ctx = _make_perfect_context()
        r03 = _find(run_all_checks(ctx, StubCourseSettings()), "R03")
        assert r03.passed

    def test_fail_no_tests(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].has_test_changes = False
        r03 = _find(run_all_checks(ctx, StubCourseSettings()), "R03")
        assert not r03.passed
        assert r03.score == 0.0

    def test_fail_min_test_files_threshold(self) -> None:
        ctx = _make_perfect_context()
        # Only 1 MR with tests, but require 2
        cs = StubCourseSettings()
        cs.check_configs = {"R03": {"min_test_files": 2}}
        r03 = _find(run_all_checks(ctx, cs), "R03")
        assert not r03.passed
        assert "1/2" in r03.detail


# ===============================================================
#  Test: R04 - MR-Issue Link
# ===============================================================


class TestR04MRIssueLink:
    def test_pass_has_link(self) -> None:
        ctx = _make_perfect_context()
        r04 = _find(run_all_checks(ctx, StubCourseSettings()), "R04")
        assert r04.passed

    def test_fail_no_link(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].has_issue_link = False
        r04 = _find(run_all_checks(ctx, StubCourseSettings()), "R04")
        assert not r04.passed

    def test_pass_issue_ref_not_required(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].has_issue_link = False
        cs = StubCourseSettings()
        cs.check_configs = {"R04": {"require_issue_ref": False}}
        r04 = _find(run_all_checks(ctx, cs), "R04")
        assert r04.passed
        assert "not required" in r04.detail


# ===============================================================
#  Test: R05 - MR Template
# ===============================================================


class TestR05MRTemplate:
    def test_pass_compliant(self) -> None:
        ctx = _make_perfect_context()
        r05 = _find(run_all_checks(ctx, StubCourseSettings()), "R05")
        assert r05.passed

    def test_fail_short_description(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].description = "short"
        r05 = _find(run_all_checks(ctx, StubCourseSettings()), "R05")
        assert not r05.passed
        assert "too short" in r05.detail

    def test_fail_template_required_but_not_compliant(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].template_compliant = False
        cs = StubCourseSettings()
        cs.check_configs = {"R05": {"require_template": True}}
        r05 = _find(run_all_checks(ctx, cs), "R05")
        assert not r05.passed
        assert "missing" in r05.detail

    def test_pass_template_not_required_ignores_compliance(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].template_compliant = False
        r05 = _find(run_all_checks(ctx, StubCourseSettings()), "R05")
        # Default require_template=False, so template_compliant is irrelevant
        assert r05.passed


# ===============================================================
#  Test: R06 - Review Received (≥2 distinct reviewers on own MR)
# ===============================================================


class TestR06ReviewReceived:
    def test_pass_two_reviewers(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        r06 = _find(run_all_checks(ctx, cs), "R06")
        assert r06.passed
        assert r06.score == cs.weight_review_count

    def test_partial_one_reviewer(self) -> None:
        ctx = _make_perfect_context()
        # Remove one reviewer note -> only 1 distinct reviewer
        ctx.notes_on_own_mr = [ctx.notes_on_own_mr[0]]
        cs = StubCourseSettings()
        r06 = _find(run_all_checks(ctx, cs), "R06")
        assert not r06.passed
        # Partial: 1/2 x weight
        expected = cs.weight_review_count * 0.5
        assert abs(r06.score - expected) < 0.001
        assert "1/2" in r06.detail

    def test_zero_reviewers(self) -> None:
        ctx = _make_perfect_context()
        ctx.notes_on_own_mr = []
        r06 = _find(run_all_checks(ctx, StubCourseSettings()), "R06")
        assert not r06.passed
        assert r06.score == 0.0


# ===============================================================
#  Test: R07 - Review Duty (≥2 distinct MRs meaningfully reviewed)
# ===============================================================


class TestR07ReviewDuty:
    def test_pass_two_meaningful(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        r07 = _find(run_all_checks(ctx, cs), "R07")
        assert r07.passed
        assert r07.score == cs.weight_review_duty

    def test_partial_one_reviewed(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        ctx.reviews_given = [ctx.reviews_given[0]]
        r07 = _find(run_all_checks(ctx, cs), "R07")
        assert not r07.passed
        assert abs(r07.score - cs.weight_review_duty * 0.5) < 0.001

    def test_fail_reviewed_but_not_meaningful(self) -> None:
        ctx = _make_perfect_context()
        for r in ctx.reviews_given:
            r.is_meaningful = False
        r07 = _find(run_all_checks(ctx, StubCourseSettings()), "R07")
        assert not r07.passed
        assert r07.score == 0.0

    def test_honours_custom_word_threshold(self) -> None:
        """F3: reviews below the course's min_review_word_count don't count,
        even if flagged is_meaningful (which uses the default 15-word floor)."""
        ctx = _make_perfect_context()
        for r in ctx.reviews_given:
            r.is_meaningful = True
            r.total_words = 20  # meaningful by default, but below a 50-word bar
        cs = StubCourseSettings()
        cs.min_review_word_count = 50
        r07 = _find(run_all_checks(ctx, cs), "R07")
        assert not r07.passed
        assert r07.score == 0.0


# ===============================================================
#  Test: R08 - Response Quality (all threads + commit ref)
# ===============================================================


class TestR08ResponseQuality:
    def test_pass_all_answered_with_commit(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        r08 = _find(run_all_checks(ctx, cs), "R08")
        assert r08.passed
        assert abs(r08.score - cs.weight_response_complete) < 0.001

    def test_fail_unanswered_thread(self) -> None:
        ctx = _make_perfect_context()
        # Add a 3rd discussion that author didn't respond to
        extra_note = StubNote(
            merge_request_id=ctx.mrs_authored[0].id,
            author_id=_make_student_id(),
            discussion_id="disc-3",
        )
        ctx.notes_on_own_mr.append(extra_note)
        cs = StubCourseSettings()
        cs.check_configs = {"R08": {"require_commit_ref": True}}
        r08 = _find(run_all_checks(ctx, cs), "R08")
        assert not r08.passed
        # 2/3 threads answered + has commit ref -> 0.5x(2/3) + 0.5x1 = 0.833
        expected = cs.weight_response_complete * (0.5 * (2 / 3) + 0.5 * 1.0)
        assert abs(r08.score - expected) < 0.001

    def test_fail_no_commit_ref(self) -> None:
        ctx = _make_perfect_context()
        for r in ctx.own_responses:
            r.contains_commit_ref = False
        cs = StubCourseSettings()
        cs.check_configs = {"R08": {"require_commit_ref": True}}
        r08 = _find(run_all_checks(ctx, cs), "R08")
        assert not r08.passed
        # All answered (rate=1.0) but no commit ref -> 0.5x1 + 0.5x0 = 0.5
        expected = cs.weight_response_complete * 0.5
        assert abs(r08.score - expected) < 0.001

    def test_pass_no_threads_but_has_commit_ref(self) -> None:
        """If no review threads exist, response_rate defaults to 1.0."""
        ctx = _make_perfect_context()
        ctx.notes_on_own_mr = []
        # But author still has a response with commit ref (edge case)
        ctx.own_responses = [
            StubNote(
                merge_request_id=ctx.mrs_authored[0].id,
                author_id=ctx.student_id,
                contains_commit_ref=True,
            )
        ]
        r08 = _find(run_all_checks(ctx, StubCourseSettings()), "R08")
        # 0 threads -> rate=1.0, has commit ref -> passed
        assert r08.passed

    def test_a_bot_accounts_notes_are_no_threads_to_answer(self) -> None:
        """The classroom assistant (a group access token's bot user) writes
        "approved - merge it" on the student's MR: no thread the author owes
        an answer. A teacher's comment still is one; R06's hint still counts
        the bot's note among the comments that are no team member's."""
        sid = _make_student_id()
        student = SimpleNamespace(id=sid, gitlab_user_id=7, gitlab_username="jana")
        mr = StubMR(author_id=sid)
        notes = [
            StubNote(
                merge_request_id=mr.id,
                author_gitlab_id=99,
                author_username="group_3_bot_596ca9c752b0b40b0190223f3496802d",
                discussion_id="bot",
            ),
            StubNote(
                merge_request_id=mr.id,
                author_gitlab_id=5,
                author_username="teacher",
                discussion_id="teacher",
            ),
            StubNote(
                merge_request_id=mr.id,
                author_id=sid,
                author_gitlab_id=7,
                author_username="jana",
                discussion_id="teacher",
            ),
        ]
        ctx = _build_student_context(
            student,  # type: ignore[arg-type]
            [],
            [mr],  # type: ignore[list-item]
            notes,  # type: ignore[arg-type]
            [],
            [],
            [],
            team_member_count=3,
        )
        assert [n.discussion_id for n in ctx.notes_on_own_mr] == ["teacher"]
        checks = run_all_checks(ctx, StubCourseSettings())
        r08 = _find(checks, "R08")
        assert r08.passed
        assert r08.detail == "1/1 threads answered"
        assert "bot comments: 2" in _find(checks, "R06").detail


# ===============================================================
#  Test: R09 - Approval Received (≥2 distinct approvers)
# ===============================================================


class TestR09ApprovalReceived:
    def test_pass_two_approvals(self) -> None:
        ctx = _make_perfect_context()
        r09 = _find(run_all_checks(ctx, StubCourseSettings()), "R09")
        assert r09.passed

    def test_partial_one_approval(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        cs.check_configs = {"R09": {"min_approvals": 2}}
        ctx.approvals_on_own_mr = [ctx.approvals_on_own_mr[0]]
        r09 = _find(run_all_checks(ctx, cs), "R09")
        assert not r09.passed
        expected = cs.weight_approvals * 0.5
        assert abs(r09.score - expected) < 0.001

    def test_same_approver_twice_counts_once(self) -> None:
        ctx = _make_perfect_context()
        # Both approvals from same gitlab_id
        ctx.approvals_on_own_mr[1].approver_gitlab_id = ctx.approvals_on_own_mr[
            0
        ].approver_gitlab_id
        cs = StubCourseSettings()
        cs.check_configs = {"R09": {"min_approvals": 2}}
        r09 = _find(run_all_checks(ctx, cs), "R09")
        assert not r09.passed
        assert "1/2" in r09.detail

    def test_note_derived_approvers_survive_cleared_approval_list(self) -> None:
        # Regression: GitLab clears the /approvals list once an MR merges and its
        # branch is deleted, so a re-sync wipes approvals_on_own_mr. The permanent
        # "approved this merge request" system notes must keep R09 passing.
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        cs.check_configs = {"R09": {"min_approvals": 2}}
        ctx.approvals_on_own_mr = []  # cleared by post-merge re-sync
        ctx.approval_note_approver_ids = {9001, 9002}  # two distinct note approvers
        r09 = _find(run_all_checks(ctx, cs), "R09")
        assert r09.passed

    def test_note_and_live_approvers_union_deduped(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        cs.check_configs = {"R09": {"min_approvals": 2}}
        live_id = ctx.approvals_on_own_mr[0].approver_gitlab_id
        ctx.approvals_on_own_mr = [ctx.approvals_on_own_mr[0]]  # 1 live approver
        ctx.approval_note_approver_ids = {live_id, 9002}  # same live id + one new
        r09 = _find(run_all_checks(ctx, cs), "R09")
        assert r09.passed  # 2 distinct: live_id and 9002


# ===============================================================
#  Test: R10 - Merged by Author
# ===============================================================


class TestR10MergedByAuthor:
    def test_pass_merged_by_self(self) -> None:
        ctx = _make_perfect_context()
        r10 = _find(run_all_checks(ctx, StubCourseSettings()), "R10")
        assert r10.passed

    def test_fail_merged_by_other(self) -> None:
        ctx = _make_perfect_context()
        # Unknown / non-team merger - not a resolved student
        ctx.mrs_authored[0].merged_by_id = None
        ctx.mrs_authored[0].merged_by_gitlab_id = 999999
        r10 = _find(run_all_checks(ctx, StubCourseSettings()), "R10")
        assert not r10.passed
        assert "unknown" in r10.detail.lower()

    def test_fail_not_merged(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].state = "opened"
        ctx.mrs_authored[0].merged_at = None
        r10 = _find(run_all_checks(ctx, StubCourseSettings()), "R10")
        assert not r10.passed
        assert "not yet merged" in r10.detail

    def test_reviewer_gates_merge(self) -> None:
        ctx = _make_perfect_context()
        # Author merged, but config requires reviewer to merge
        cs = StubCourseSettings()
        cs.check_configs = {"R10": {"forbid_self_merge": True}}
        r10 = _find(run_all_checks(ctx, cs), "R10")
        assert not r10.passed
        assert "reviewer should" in r10.detail


# ===============================================================
#  Test: R11 - Closure State (MR + issue closed)
# ===============================================================


class TestR11ClosureState:
    def test_pass_both_closed(self) -> None:
        ctx = _make_perfect_context()
        r11 = _find(run_all_checks(ctx, StubCourseSettings()), "R11")
        assert r11.passed

    def test_fail_mr_still_open(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].state = "opened"
        r11 = _find(run_all_checks(ctx, StubCourseSettings()), "R11")
        assert not r11.passed
        assert "No merged" in r11.detail

    def test_fail_issue_still_open(self) -> None:
        ctx = _make_perfect_context()
        ctx.issues_assigned[0].state = "opened"
        r11 = _find(run_all_checks(ctx, StubCourseSettings()), "R11")
        assert not r11.passed
        assert "no assigned issue is closed" in r11.detail or "still open" in r11.detail

    def test_pass_partial_closure_allowed(self) -> None:
        ctx = _make_perfect_context()
        ctx.issues_assigned[0].state = "opened"
        cs = StubCourseSettings()
        cs.check_configs = {"R11": {"require_both_closed": False}}
        r11 = _find(run_all_checks(ctx, cs), "R11")
        assert r11.passed  # MR closed is enough


# ===============================================================
#  Test: R12 - Pipeline Health (success + test job)
# ===============================================================


class TestR12PipelineHealth:
    def test_pass_green_with_test(self) -> None:
        ctx = _make_perfect_context()
        r12 = _find(run_all_checks(ctx, StubCourseSettings()), "R12")
        assert r12.passed

    def test_fail_no_pipeline(self) -> None:
        ctx = _make_perfect_context()
        ctx.pipelines = []
        r12 = _find(run_all_checks(ctx, StubCourseSettings()), "R12")
        assert not r12.passed
        assert "No pipelines" in r12.detail

    def test_fail_pipeline_failed(self) -> None:
        ctx = _make_perfect_context()
        ctx.pipelines[0].status = "failed"
        r12 = _find(run_all_checks(ctx, StubCourseSettings()), "R12")
        assert not r12.passed
        assert "failing" in r12.detail.lower() or "No successful" in r12.detail

    def test_fail_no_test_job(self) -> None:
        ctx = _make_perfect_context()
        ctx.pipelines[0].has_test_job = False
        r12 = _find(run_all_checks(ctx, StubCourseSettings()), "R12")
        assert not r12.passed
        assert "no test job" in r12.detail.lower()


# ===============================================================
#  Test: R13 - Commit Quality (web editor detection)
# ===============================================================


class TestR13CommitQuality:
    def test_pass_all_meaningful_commits(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings(weight_commit_quality=0.07)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert r13.passed
        assert "meaningful" in r13.detail.lower() or "commit(s)" in r13.detail

    def test_fail_no_commits(self) -> None:
        """No commits -> fail (no activity should not give free credit)."""
        ctx = _make_perfect_context()
        ctx.commits = []
        cs = StubCourseSettings(weight_commit_quality=0.07)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert not r13.passed
        assert r13.score == 0.0

    def test_fail_all_web_editor(self) -> None:
        sid = _make_student_id()
        ctx = _make_perfect_context(sid)
        ctx.commits = [
            StubCommit(author_id=sid, title="Update README.md"),
            StubCommit(author_id=sid, title="Create .gitlab-ci.yml"),
            StubCommit(author_id=sid, title="Delete old-file.txt"),
        ]
        cs = StubCourseSettings(weight_commit_quality=0.07)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert not r13.passed
        assert "web-editor" in r13.detail.lower() or "git CLI" in r13.detail

    def test_pass_below_threshold(self) -> None:
        """1 web-editor out of 5 -> 20% ≤ 30% default threshold."""
        sid = _make_student_id()
        ctx = _make_perfect_context(sid)
        ctx.commits = [
            StubCommit(author_id=sid, title="Update README.md"),
            StubCommit(author_id=sid, title="Implement auth module"),
            StubCommit(author_id=sid, title="Add unit tests for login"),
            StubCommit(author_id=sid, title="Fix edge case in parser"),
            StubCommit(author_id=sid, title="Refactor database layer"),
        ]
        cs = StubCourseSettings(weight_commit_quality=0.07)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert r13.passed

    def test_fail_above_threshold(self) -> None:
        """3 web-editor out of 5 -> 60% > 30% threshold."""
        sid = _make_student_id()
        ctx = _make_perfect_context(sid)
        ctx.commits = [
            StubCommit(author_id=sid, title="Update README.md"),
            StubCommit(author_id=sid, title="Create config.yml"),
            StubCommit(author_id=sid, title="Delete temp.txt"),
            StubCommit(author_id=sid, title="Implement auth module"),
            StubCommit(author_id=sid, title="Add unit tests for login"),
        ]
        cs = StubCourseSettings(weight_commit_quality=0.07)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert not r13.passed

    def test_merge_commits_excluded(self) -> None:
        """Merge commits should not count toward the ratio."""
        sid = _make_student_id()
        ctx = _make_perfect_context(sid)
        ctx.commits = [
            StubCommit(author_id=sid, title="Good commit message"),
            StubCommit(
                author_id=sid,
                title="Merge branch 'main' into feature",
                parent_shas=["aaa", "bbb"],
            ),
        ]
        cs = StubCourseSettings(weight_commit_quality=0.07)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert r13.passed

    def test_configurable_ratio(self) -> None:
        """Custom max_web_editor_ratio is respected."""
        sid = _make_student_id()
        ctx = _make_perfect_context(sid)
        ctx.commits = [
            StubCommit(author_id=sid, title="Update README.md"),
            StubCommit(author_id=sid, title="Good commit"),
        ]
        cs = StubCourseSettings(weight_commit_quality=0.07)
        # 50% web editor, threshold at 60% -> should pass
        cs.check_configs = {"R13": {"max_web_editor_ratio": 0.6}}
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert r13.passed

        # 50% web editor, threshold at 40% -> should fail
        cs.check_configs = {"R13": {"max_web_editor_ratio": 0.4}}
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert not r13.passed

    def test_apply_suggestion_pattern(self) -> None:
        """'Apply N suggestion(s)' also counts as web-editor commit."""
        sid = _make_student_id()
        ctx = _make_perfect_context(sid)
        ctx.commits = [
            StubCommit(author_id=sid, title="Apply 1 suggestion(s) to 1 file(s)"),
        ]
        cs = StubCourseSettings(weight_commit_quality=0.07)
        cs.check_configs = {"R13": {"max_web_editor_ratio": 0.0}}
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert not r13.passed

    def test_zero_weight_disabled(self) -> None:
        """When weight is 0, R13 still runs but contributes no score."""
        ctx = _make_perfect_context()
        cs = StubCourseSettings(weight_commit_quality=0.0)
        r13 = _find(run_all_checks(ctx, cs), "R13")
        assert r13.passed
        assert r13.score == 0.0
        assert r13.weight == 0.0


# ===============================================================
#  Test: Traffic Light Thresholds
# ===============================================================


class TestTrafficLightThresholds:
    """weighted_score determines traffic light color."""

    def _score(self, ctx: StudentContext, cs: StubCourseSettings) -> float:
        scores = [float(c.score) for c in run_all_checks(ctx, cs)]
        return float(sum(scores))

    def test_green_at_080(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings(green_threshold=0.80)
        score = self._score(ctx, cs)
        assert score >= 0.80
        # Verify classification
        assert score >= cs.green_threshold

    def test_yellow_range(self) -> None:
        """Remove enough checks to land in YELLOW (0.50-0.79)."""
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        # Break R03 (0.10), R06 (0.12), R07 (0.12) -> lose 0.34 -> ~0.66
        ctx.mrs_authored[0].has_test_changes = False
        ctx.notes_on_own_mr = []
        ctx.reviews_given = []
        score = self._score(ctx, cs)
        assert cs.yellow_threshold <= score < cs.green_threshold

    def test_red_below_050(self) -> None:
        """Break enough checks to land in RED."""
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        # Break R01, R02, R03, R04, R05, R06, R07 -> lose >0.60
        ctx.issues_assigned = []
        ctx.mrs_authored = []
        ctx.notes_on_own_mr = []
        ctx.own_responses = []
        ctx.reviews_given = []
        ctx.pipelines = []
        score = self._score(ctx, cs)
        assert score < cs.yellow_threshold


# ===============================================================
#  Test: Partial Scoring for R06, R07, R08, R09
# ===============================================================


class TestPartialScoring:
    """Checks R06, R07, R08, R09 give partial credit proportional to progress."""

    def test_r06_half_credit(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        ctx.notes_on_own_mr = [ctx.notes_on_own_mr[0]]  # 1 of 2 reviewers
        r06 = _find(run_all_checks(ctx, cs), "R06")
        assert not r06.passed
        assert abs(r06.score - cs.weight_review_count * 0.5) < 0.001

    def test_r07_half_credit(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        ctx.reviews_given = [ctx.reviews_given[0]]  # 1 of 2 MRs
        r07 = _find(run_all_checks(ctx, cs), "R07")
        assert not r07.passed
        assert abs(r07.score - cs.weight_review_duty * 0.5) < 0.001

    def test_r09_half_credit(self) -> None:
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        cs.check_configs = {"R09": {"min_approvals": 2}}
        ctx.approvals_on_own_mr = [ctx.approvals_on_own_mr[0]]  # 1 of 2
        r09 = _find(run_all_checks(ctx, cs), "R09")
        assert not r09.passed
        assert abs(r09.score - cs.weight_approvals * 0.5) < 0.001


# ===============================================================
#  Test: Per-Student Constraints (1 issue, 1 MR, 2 reviews)
# ===============================================================


class TestPerStudentConstraints:
    """ZSI requirement: each student works on exactly 1 issue -> 1 MR, reviews 2 peers."""

    def test_ideal_workflow_all_pass(self) -> None:
        ctx = _make_perfect_context()
        checks = run_all_checks(ctx, StubCourseSettings())
        assert all(c.passed for c in checks)
        assert len(ctx.issues_assigned) == 1
        assert len(ctx.mrs_authored) == 1
        assert len({r.merge_request_id for r in ctx.reviews_given}) == 2

    def test_extra_issue_passes_r01(self) -> None:
        """Having multiple issues is fine - R01 requires >= 1 by default."""
        ctx = _make_perfect_context()
        ctx.issues_assigned.append(StubIssue(assignee_id=ctx.student_id))
        r01 = _find(run_all_checks(ctx, StubCourseSettings()), "R01")
        assert r01.passed

    def test_zero_reviews_given_fails_r07(self) -> None:
        ctx = _make_perfect_context()
        ctx.reviews_given = []
        r07 = _find(run_all_checks(ctx, StubCourseSettings()), "R07")
        assert not r07.passed
        assert r07.score == 0.0

    def test_only_one_review_given_partial(self) -> None:
        ctx = _make_perfect_context()
        ctx.reviews_given = [ctx.reviews_given[0]]
        r07 = _find(run_all_checks(ctx, StubCourseSettings()), "R07")
        assert not r07.passed
        assert r07.score > 0  # partial credit


# ===============================================================
#  Test: Communication Indicators
# ===============================================================


class TestCommunicationIndicators:
    def test_perfect_context_indicators(self) -> None:
        ctx = _make_perfect_context()
        comms = compute_communication_indicators(ctx)

        # MR created at NOW, first reviewer note at NOW+2h -> 2.0h
        assert comms.median_first_response_hours == 2.0

        # 2 distinct discussions on the MR
        assert comms.median_review_rounds == 2.0

        # Review word depth: avg(60, 45) = 52.5
        assert comms.review_word_depth == 52.5

        # Author response word depth: avg(40, 35) = 37.5
        assert comms.author_response_word_depth == 37.5

        # MR merged at NOW+24h -> 24.0h
        assert comms.median_time_to_merge_hours == 24.0

    def test_no_notes_gives_none(self) -> None:
        ctx = _make_perfect_context()
        ctx.notes_on_own_mr = []
        ctx.own_responses = []
        comms = compute_communication_indicators(ctx)
        assert comms.median_first_response_hours is None
        assert comms.median_review_rounds is None
        assert comms.review_word_depth is None
        assert comms.author_response_word_depth is None

    def test_discussion_resolution(self) -> None:
        ctx = _make_perfect_context()
        # Make both notes resolvable, one resolved
        ctx.notes_on_own_mr[0].is_resolvable = True
        ctx.notes_on_own_mr[0].is_resolved = True
        ctx.notes_on_own_mr[1].is_resolvable = True
        ctx.notes_on_own_mr[1].is_resolved = False
        comms = compute_communication_indicators(ctx)
        assert comms.discussion_resolution_pct == 50.0

    def test_no_resolvable_gives_none(self) -> None:
        ctx = _make_perfect_context()
        comms = compute_communication_indicators(ctx)
        # Default notes are not resolvable
        assert comms.discussion_resolution_pct is None

    def test_not_merged_gives_none(self) -> None:
        ctx = _make_perfect_context()
        ctx.mrs_authored[0].state = "opened"
        ctx.mrs_authored[0].merged_at = None
        comms = compute_communication_indicators(ctx)
        assert comms.median_time_to_merge_hours is None

    def test_median_with_multiple_mrs(self) -> None:
        """Test median computation with 2 authored MRs."""
        ctx = _make_perfect_context()
        mr2_id = _uuid()
        mr2 = StubMR(
            id=mr2_id,
            author_id=ctx.student_id,
            merged_by_id=ctx.student_id,
            state="merged",
            created_at=NOW,
            merged_at=NOW + timedelta(hours=48),
        )
        ctx.mrs_authored.append(mr2)
        # Add a reviewer note on mr2 at NOW+6h
        note_c = StubNote(
            merge_request_id=mr2_id,
            author_id=_make_student_id(),
            discussion_id="disc-3",
            word_count=80,
            created_at=NOW + timedelta(hours=6),
        )
        ctx.notes_on_own_mr.append(note_c)

        comms = compute_communication_indicators(ctx)
        # First response: MR1 -> 2h, MR2 -> 6h -> median = 4.0
        assert comms.median_first_response_hours == 4.0
        # Merge times: MR1 -> 24h, MR2 -> 48h -> median = 36.0
        assert comms.median_time_to_merge_hours == 36.0


# ===============================================================
#  Test: Weight Sum
# ===============================================================


class TestWeightSum:
    """Default weights should sum to 1.0 across all 12 checks."""

    def test_weights_sum_to_one(self) -> None:
        """The 12 check weights used by the engine must sum to 1.0."""
        cs = StubCourseSettings()
        total = (
            cs.weight_issue_ownership  # R01
            + cs.weight_branch_naming  # R02
            + cs.weight_test_changes  # R03
            + cs.weight_mr_issue_link  # R04
            + cs.weight_mr_template  # R05
            + cs.weight_review_count  # R06
            + cs.weight_review_duty  # R07
            + cs.weight_response_complete  # R08
            + cs.weight_approvals  # R09
            + cs.weight_merge_by_author  # R10
            + cs.weight_closure  # R11
            + cs.weight_pipeline_health  # R12
            + cs.weight_commit_quality  # R13
        )
        assert abs(total - 1.0) < 0.01

    def test_check_count(self) -> None:
        ctx = _make_perfect_context()
        checks = run_all_checks(ctx, StubCourseSettings())
        assert len(checks) == 13

    def test_each_check_has_unique_id(self) -> None:
        ctx = _make_perfect_context()
        checks = run_all_checks(ctx, StubCourseSettings())
        ids = [c.check_id for c in checks]
        assert len(ids) == len(set(ids))


# ===============================================================
#  Weekly check filtering
# ===============================================================


class TestWeeklyCheckFiltering:
    """Verify _get_expected_checks_for_week against weekly_deadlines."""

    @staticmethod
    def _make_cs(**overrides: Any) -> StubCourseSettings:
        return StubCourseSettings(**overrides)

    def test_no_deadlines_returns_none(self) -> None:
        cs = self._make_cs(weekly_deadlines=[])
        assert _get_expected_checks_for_week(cs, 5) is None

    def test_no_deadlines_attr_returns_none(self) -> None:
        cs = self._make_cs()
        # StubCourseSettings has no weekly_deadlines attr -> should return None
        assert _get_expected_checks_for_week(cs, 5) is None

    def test_week_matches_exact(self) -> None:
        cs = self._make_cs(
            weekly_deadlines=[
                {"week": 2, "expected_checks": ["R01"]},
                {"week": 4, "expected_checks": ["R01", "R02", "R04"]},
            ]
        )
        result = _get_expected_checks_for_week(cs, 2)
        assert result == {"R01"}

    def test_week_between_deadlines_uses_latest_applicable(self) -> None:
        cs = self._make_cs(
            weekly_deadlines=[
                {"week": 2, "expected_checks": ["R01"]},
                {"week": 4, "expected_checks": ["R01", "R02", "R04"]},
                {"week": 8, "expected_checks": ["R01", "R02", "R03", "R04"]},
            ]
        )
        # Week 6 is between 4 and 8 -> uses week 4 config
        result = _get_expected_checks_for_week(cs, 6)
        assert result == {"R01", "R02", "R04"}

    def test_week_after_last_deadline(self) -> None:
        cs = self._make_cs(
            weekly_deadlines=[
                {"week": 2, "expected_checks": ["R01"]},
                {"week": 12, "expected_checks": ["R01", "R02", "R03"]},
            ]
        )
        # Week 15 is past the last config -> uses week 12
        result = _get_expected_checks_for_week(cs, 15)
        assert result == {"R01", "R02", "R03"}

    def test_week_before_first_deadline(self) -> None:
        cs = self._make_cs(
            weekly_deadlines=[
                {"week": 3, "expected_checks": ["R01"]},
                {"week": 6, "expected_checks": ["R01", "R02"]},
            ]
        )
        # Week 1 is before any deadline -> uses first defined week
        result = _get_expected_checks_for_week(cs, 1)
        assert result == {"R01"}

    def test_includes_custom_checks(self) -> None:
        cs = self._make_cs(
            weekly_deadlines=[
                {"week": 12, "expected_checks": ["R01", "R02", "C01", "C02"]},
            ]
        )
        result = _get_expected_checks_for_week(cs, 12)
        assert result == {"R01", "R02", "C01", "C02"}

    def test_empty_expected_checks_returns_empty_set(self) -> None:
        cs = self._make_cs(
            weekly_deadlines=[
                {"week": 1, "expected_checks": []},
            ]
        )
        # Empty expected_checks -> empty set (no checks expected = 100% score)
        result = _get_expected_checks_for_week(cs, 1)
        assert result == set()

    def test_weekly_scoring_normalises_weights(self) -> None:
        """When only R01 is expected, passing it should yield 100% score."""
        ctx = _make_perfect_context()
        cs = StubCourseSettings()
        checks = run_all_checks(ctx, cs)

        # Simulate weekly filtering: only R01
        expected_ids = {"R01"}
        expected_results = [c for c in checks if c.check_id in expected_ids]
        total_w = sum(c.weight for c in expected_results)
        score = sum(c.score for c in expected_results) / total_w if total_w > 0 else 0
        assert abs(score - 1.0) < 0.001, f"Expected 100% but got {score}"

    def test_weekly_scoring_partial_pass(self) -> None:
        """When 2 of 3 expected checks pass, score is partial."""
        ctx = _make_perfect_context()
        # Break R02 so it fails (bad branch name)
        for m in ctx.mrs_authored:
            m.source_branch = "bad-branch"
            m.branch_naming_ok = False
        cs = StubCourseSettings()
        # Opt into strict branch-name enforcement so the bad branch actually
        # fails (R02 is permissive-by-default since 2026-04-24).
        cs.check_configs = {"R02": {"require_branch_convention": True}}
        checks = run_all_checks(ctx, cs)

        expected_ids = {"R01", "R02", "R04"}
        expected_results = [c for c in checks if c.check_id in expected_ids]
        total_w = sum(c.weight for c in expected_results)
        raw_score = sum(c.score for c in expected_results) / total_w
        # R01 passes, R02 fails, R04 passes -> 2/3 checks pass, score < 1.0
        assert raw_score < 1.0
        assert raw_score > 0.5
