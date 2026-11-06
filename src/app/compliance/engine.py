"""Compliance engine - orchestrates all checks and computes metrics.

Formulas
--------
Each check maps to a course team assignment requirement:

  R01  Issue Assigned     passed <=> |assigned_issues| >= min_issues (default 1)
  R02  Branch + MR        passed <=> |mrs_authored| >= 1 and
                                     (convention off or exists MR: branch_naming_ok)
  R03  Tests Written      passed <=> exists MR in authored: has_test_changes
  R04  MR Linked to Issue passed <=> exists MR in authored: has_issue_link
  R05  MR Description     passed <=> exists MR in authored: template_compliant
  R06  Review Received    passed <=> |{n.author_id : n in notes_on_own_mr}|
                                     >= min_reviews_per_mr
  R07  Code Review Given  passed <=> |{r.merge_request_id : r in reviews_given,
                                     r.is_meaningful}| >= min_distinct_mrs_reviewed
  R08  Review Response    passed <=> response_rate == 1.0 and
                                     exists response: contains_commit_ref
  R09  MR Approved        passed <=> |distinct approvers on own MR| >= min_reviews_per_mr
  R10  Merged by Author   passed <=> exists MR in authored: state=="merged" and
                                     merged_by_id == student_id
  R11  MR + Issue Closed  passed <=> (exists MR: state in {merged,closed}) and
                                     (exists issue: state=="closed")
  R12  Pipeline Green     passed <=> exists pipeline: status=="success" and has_test_job
  R13  Commit Quality     passed <=> web_editor_ratio <= max_web_editor_ratio (default 0.3)

Scoring
-------
  score(Rk) = weight_k if passed
             = weight_k x (partial_numerator / partial_denominator) for R06,R07,R08,R09
             = 0 otherwise
  weighted_score = sum(score(Rk)) / sum(weight_k) over the scored checks
                   (enabled, and expected this week when the course has a
                   weekly plan), so switching a check off cannot cap the score

Traffic Light
-------------
  GREEN  if weighted_score >= green_threshold (default 0.80)
  YELLOW if weighted_score >= yellow_threshold (default 0.50)
  RED    otherwise

Communication Indicators (non-scoring)
--------------------------------------
  median_first_response_hours  - median(first_reviewer_note.created_at - MR.created_at)
  median_review_rounds         - median(|{discussion_id} per MR|)
  discussion_resolution_pct    - |resolved resolvable notes| / |resolvable notes|
  review_word_depth            - avg(word_count) across reviewer notes on own MRs
  author_response_word_depth   - avg(word_count) across author responses
  median_time_to_merge_hours   - median(MR.merged_at - MR.created_at)
"""

import logging
import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar, cast
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from app.compliance.dynamic_checks import evaluate_custom_check
from app.compliance.engine_checks import run_all_checks
from app.compliance.roles import is_contributing_role
from app.compliance.types import CheckResult, CommunicationIndicators, StudentContext
from app.models.commit import Commit
from app.models.course_settings import CourseSettings
from app.models.custom_check import CustomCheck
from app.models.issue import Issue
from app.models.merge_request import MergeRequest
from app.models.metric_snapshot import MetricSnapshot
from app.models.mr_approval import MRApproval
from app.models.mr_note import MRNote
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.review_activity import ReviewActivity
from app.models.student import Student
from app.models.student_compliance_snapshot import StudentComplianceSnapshot
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_metric_snapshot import TeamMetricSnapshot
from app.utils.gitlab_patterns import is_web_editor_commit

logger = logging.getLogger(__name__)
ModelT = TypeVar("ModelT")


def _compute_response_rate(ctx: StudentContext) -> float:
    """Compute the review response rate for a student.

    Shared between the R08 check and the metric snapshot builder
    to guarantee identical values.
    """
    reviewer_discussions = {n.discussion_id for n in ctx.notes_on_own_mr if n.discussion_id}
    author_discussions = {n.discussion_id for n in ctx.own_responses if n.discussion_id}
    total_threads = len(reviewer_discussions)
    answered = len(reviewer_discussions & author_discussions)
    if total_threads > 0:
        return answered / total_threads
    # No reviewer threads yet - return 0 to avoid misleading "100%" in snapshots
    return 0.0


# -- Category score mapping --

_CHECK_CATEGORIES: dict[str, str] = {
    "R01": "issue",
    "R02": "mr",
    "R03": "mr",
    "R04": "mr",
    "R05": "mr",
    "R06": "review",
    "R07": "review",
    "R08": "review",
    "R09": "review",
    "R10": "mr",
    "R11": "mr",
    "R12": "ci",
    "R13": "commit",
}


def _compute_category_scores(
    checks: list[CheckResult],
    extra_categories: dict[str, str] | None = None,
) -> dict[str, float | None]:
    """Compute normalised category scores (0-1) from individual check results.

    Categories: issue, mr, review, ci, commit, custom (and any teacher-defined).
    Each category score = sum(check.score) / sum(check.weight) for checks in that
    category, or 0 if total weight is 0.

    The optional *extra_categories* dict maps custom check_id -> category
    (e.g. ``{"C01": "ci", "C02": "custom"}``).
    """
    merged = dict(_CHECK_CATEGORIES)
    if extra_categories:
        merged.update(extra_categories)

    cat_score: dict[str, float] = {}
    cat_weight: dict[str, float] = {}
    for c in checks:
        cat = merged.get(c.check_id, "custom")
        cat_score[cat] = cat_score.get(cat, 0.0) + c.score
        cat_weight[cat] = cat_weight.get(cat, 0.0) + c.weight
    result: dict[str, float | None] = {}
    all_cats = {"issue", "mr", "review", "ci", "commit"} | set(cat_score)
    for cat in sorted(all_cats):
        w = cat_weight.get(cat, 0.0)
        result[cat] = round(cat_score.get(cat, 0.0) / w, 4) if w > 0 else None
    return result


def _get_week_number(cs: CourseSettings, now: datetime) -> int:
    """Compute the current academic week from course settings.

    Uses ``semester_start_date`` from CourseSettings.  If not configured,
    falls back to the course ``created_at`` timestamp as the start of
    week 1 so we never return a meaningless ISO calendar week.
    """
    from app.utils.time_utils import get_current_week

    start = cs.semester_start_date
    if not start:
        # Derive from course created_at (the course row is accessible via
        # cs.course relationship, but to avoid extra DB hit, try the
        # settings own row creation timestamp or default to week 1).
        try:
            if cs.course and cs.course.created_at:
                start = cs.course.created_at.date()
        except Exception:
            logger.debug("failed to determine academic week from course.created_at")
    if start:
        return max(1, get_current_week(start, now.date()))
    # Absolute last resort - no semester_start and no course.created_at
    return 1


def _resolve_traffic_light(weighted_score: float, checks_total: int, cs: CourseSettings) -> str:
    """Map a weighted score to a traffic light.

    ``checks_total == 0`` means nothing was expected this week (e.g. week 1,
    before any check is introduced), so nothing was actually measured. The score
    itself stays at 1.0 so the student is NOT penalised - that part is
    intentional - but reporting GREEN claimed every student was fully compliant
    for a week in which zero checks ran, while the compliance history already
    treats ``checks_total == 0`` as N/A. GRAY is the neutral state the snapshot
    columns already default to, and the ``traffic_light`` badge macro renders it
    as "No compliance data available".
    """
    if checks_total == 0:
        return "GRAY"
    if weighted_score >= cs.green_threshold:
        return "GREEN"
    if weighted_score >= cs.yellow_threshold:
        return "YELLOW"
    return "RED"


def _get_expected_checks_for_week(cs: CourseSettings, week: int) -> set[str] | None:
    """Return the set of expected check codes for a given academic week.

    Uses the ``weekly_deadlines`` JSONB on CourseSettings.  The most recent
    week entry whose ``week`` value is ≤ *week* determines which checks are
    expected.

    Returns ``None`` when no ``weekly_deadlines`` are configured - the caller
    should then fall back to scoring ALL enabled checks (legacy behaviour).

    Returns an *empty* ``set()`` when deadlines are configured but the
    matching entry has an empty ``expected_checks`` list (e.g. week 1 -
    "no checks expected yet").  The caller treats an empty set as
    "nothing expected -> 100 % score".
    """
    deadlines: list[dict[str, Any]] = getattr(cs, "weekly_deadlines", None) or []
    if not deadlines:
        return None

    # Find the latest week config that is <= current week
    applicable = [d for d in deadlines if d.get("week", 0) <= week]
    if not applicable:
        # Before any defined week - use the first defined week's checks
        first = min(deadlines, key=lambda d: d.get("week", 999), default=None)
        if first:
            return set(first.get("expected_checks", []))
        return None

    latest = max(applicable, key=lambda d: d.get("week", 0))
    return set(latest.get("expected_checks", []))


@dataclass
class _TeamData:
    """A team's activity on its active projects, loaded once and narrowed to
    what counts."""

    issues: list[Issue]
    mrs: list[MergeRequest]
    notes: list[MRNote]
    approvals: list[MRApproval]
    reviews: list[ReviewActivity]
    pipelines: list[Pipeline]
    commits: list[Commit]

    @classmethod
    async def load(cls, session: AsyncSession, project_ids: list[UUID]) -> "_TeamData":
        issues = await _load_all(session, Issue, project_ids)
        mrs = await _load_all(session, MergeRequest, project_ids)
        commits = await _load_all(session, Commit, project_ids)
        mr_ids = [m.id for m in mrs]
        notes: list[MRNote] = []
        approvals: list[MRApproval] = []
        reviews: list[ReviewActivity] = []
        if mr_ids:
            notes = await _load_by_mr(session, MRNote, mr_ids)
            approvals = await _load_by_mr(session, MRApproval, mr_ids)
            reviews = await _load_by_mr(session, ReviewActivity, mr_ids)
        pipelines = await _load_all(session, Pipeline, project_ids)
        return cls(issues, mrs, notes, approvals, reviews, pipelines, commits)

    def counts(self) -> tuple[int, ...]:
        return tuple(
            len(x)
            for x in (
                self.issues,
                self.mrs,
                self.notes,
                self.approvals,
                self.reviews,
                self.pipelines,
                self.commits,
            )
        )

    def since(self, floor: datetime) -> "_TeamData":
        """Only the semester's: history imported from a template repository
        must not satisfy checks for a later course run. Notes, approvals and
        reviews also only on the semester's MRs."""
        mrs = _filter_entities_since(self.mrs, "created_at", floor)
        mr_ids = {m.id for m in mrs}
        return _TeamData(
            issues=_filter_entities_since(self.issues, "created_at", floor),
            mrs=mrs,
            notes=[
                n
                for n in _filter_entities_since(self.notes, "created_at", floor)
                if n.merge_request_id in mr_ids
            ],
            approvals=[
                a
                for a in _filter_entities_since(self.approvals, "approved_at", floor)
                if a.merge_request_id in mr_ids
            ],
            reviews=[
                r
                for r in _filter_entities_since(self.reviews, "first_note_at", floor)
                if r.merge_request_id in mr_ids
            ],
            pipelines=_filter_entities_since(self.pipelines, "created_at", floor),
            commits=_filter_entities_since(self.commits, "committed_at", floor),
        )

    def as_of(self, cutoff: datetime) -> "_TeamData":
        """What EXISTS by the cutoff (cumulative, not a one-week window): an
        issue assigned in W10 must not "un-pass" R01 in W11, and an MR merged
        in W12 counts toward W12 though it was created in W11. Each weekly
        snapshot answers "what does compliance look like by end of week N?"."""

        def upto(items: list[ModelT], attr: str) -> list[ModelT]:
            return [x for x in items if (ts := getattr(x, attr)) is not None and ts <= cutoff]

        return _TeamData(
            issues=upto(self.issues, "created_at"),
            mrs=upto(self.mrs, "created_at"),
            notes=upto(self.notes, "created_at"),
            approvals=upto(self.approvals, "approved_at"),
            reviews=upto(self.reviews, "first_note_at"),
            pipelines=upto(self.pipelines, "created_at"),
            commits=upto(self.commits, "committed_at"),
        )


@dataclass(frozen=True)
class _Roster:
    """Who in the team is scored, and who is kept out of the team aggregate:
    teachers, members a teacher/admin excluded from scoring, and peer mentors
    (they assist the team but are not scored)."""

    teachers: set[UUID]
    excluded: set[UUID]
    mentors: set[UUID]
    members: dict[UUID, TeamMember]
    active_count: int  # active scored members, for solo-team detection

    @classmethod
    def of(cls, team: Team) -> "_Roster":
        with_student = [m for m in team.members if m.student]
        teachers = {m.student.id for m in with_student if m.is_teacher}
        excluded = {
            m.student.id for m in with_student if getattr(m, "excluded_from_scoring", False)
        }
        mentors = {m.student.id for m in with_student if getattr(m, "is_mentor", False)}
        out = teachers | excluded | mentors
        return cls(
            teachers=teachers,
            excluded=excluded,
            mentors=mentors,
            members={m.student.id: m for m in with_student},
            active_count=sum(1 for m in with_student if m.is_active and m.student.id not in out),
        )

    def role_label(self, student_id: UUID) -> str:
        if student_id in self.teachers:
            return "Teacher"
        if student_id in self.excluded:
            return "Excluded"
        if student_id in self.mentors:
            return "Mentor"
        return "Student"


def _expected_checks(
    cs: CourseSettings,
    team_name: str,
    week: int,
    check_codes: set[str] | None,
    force_all_checks: bool,
) -> set[str] | None:
    """The checks scored this run; ``None`` scores every enabled check."""
    if check_codes:
        # A teacher selected specific checks.
        logger.info(
            "Selective checks: team=%s week=%d check_codes=%s",
            team_name,
            week,
            sorted(check_codes),
        )
        return check_codes
    if force_all_checks:
        logger.info(
            "Weekly scoring OVERRIDE: team=%s week=%d force_all_checks=True -> scoring ALL checks",
            team_name,
            week,
        )
        return None
    expected = _get_expected_checks_for_week(cs, week)
    logger.info(
        "Weekly scoring: team=%s week=%d expected_checks=%s",
        team_name,
        week,
        sorted(expected) if expected else "ALL",
    )
    return expected


def _score(
    checks: list[CheckResult], expected_ids: set[str] | None
) -> tuple[float, int, int, list[str]]:
    """(weighted score, checks passed, checks counted, bottlenecks).

    Only enabled checks are scored, and with weekly deadlines only those
    expected this week - a student is not penalised for a check the course
    switched off or has not introduced yet. The score divides by the weight of
    the scored checks, so the defaults (R09, R11 and R13 off) can still reach
    100 %; nothing to score scores 1.0.
    """
    scored = [
        c for c in checks if c.enabled and (expected_ids is None or c.check_id in expected_ids)
    ]
    weight = sum(c.weight for c in scored)
    return (
        min(sum(c.score for c in scored) / weight, 1.0) if weight > 0 else 1.0,
        sum(1 for c in scored if c.passed),
        len(scored),
        [c.detail for c in scored if not c.passed],
    )


def _is_non_contributing(member: TeamMember | None, ctx: StudentContext) -> bool:
    """A member with no activity who is either on a low role (guest /
    reporter) or only inherits the membership from the group - they may not
    even know they have access. They get a snapshot of their own but stay out
    of the team aggregate, so they do not drag the team's score down."""
    if member is None:
        return False
    if ctx.mrs_authored or ctx.issues_assigned or ctx.reviews_given or ctx.pipelines:
        return False
    return (
        not is_contributing_role(member.gitlab_access_level)
        or getattr(member, "membership_source", None) == "inherited"
    )


def _student_snapshot(
    team: Team,
    student: Student,
    cs: CourseSettings,
    now: datetime,
    data: _TeamData,
    all_mrs: list[MergeRequest],
    roster: _Roster,
    custom_checks: list[CustomCheck],
    expected_ids: set[str] | None,
) -> tuple[MetricSnapshot, StudentContext]:
    ctx = _build_student_context(
        student,
        data.issues,
        data.mrs,
        data.notes,
        data.approvals,
        data.reviews,
        data.pipelines,
        data.commits,
        all_mrs=all_mrs,
        team_member_count=roster.active_count,
    )
    logger.info(
        "%s %s (id=%s, gitlab_uid=%s): "
        "issues_assigned=%d mrs_authored=%d reviews_given=%d pipelines=%d "
        "(total_issues=%d total_mrs=%d)",
        roster.role_label(student.id),
        student.gitlab_username,
        student.id,
        student.gitlab_user_id,
        len(ctx.issues_assigned),
        len(ctx.mrs_authored),
        len(ctx.reviews_given),
        len(ctx.pipelines),
        len(data.issues),
        len(data.mrs),
    )
    checks = run_all_checks(ctx, cs)
    checks += [
        evaluate_custom_check(
            ctx,
            check_code=cc.check_code,
            name=cc.name,
            rule=cc.evaluation_rule,
            weight=cc.weight,
        )
        for cc in custom_checks
    ]
    weighted_score, passed, total, bottlenecks = _score(checks, expected_ids)
    logger.info(
        "Score for %s: weighted_score=%.4f checks_passed=%d/%d checks_detail=%s",
        student.gitlab_username,
        weighted_score,
        passed,
        total,
        {c.check_id: {"passed": c.passed, "score": round(c.score, 4)} for c in checks},
    )
    snapshot = _build_snapshot(
        team,
        student,
        cs,
        now,
        ctx,
        checks,
        compute_communication_indicators(ctx),
        weighted_score,
        passed,
        _resolve_traffic_light(weighted_score, total, cs),
        bottlenecks,
        data.reviews,
        checks_total_override=total,
        expected_check_ids=expected_ids,
    )
    return snapshot, ctx


async def _delete_superseded(
    session: AsyncSession, team: Team, now: datetime, student_ids: set[UUID] | None
) -> None:
    """Exactly ONE snapshot per (team, student, week).

    Every recompute used to INSERT a fresh row (the unique key carries
    ``computed_at``), so metric_snapshots grew by one row per student per run -
    ~882 rows per student and 506k rows in production, which pushed the
    per-group "latest snapshot per student" aggregate past 1.2 s. Only the rows
    this run supersedes go: same team, same ISO week, and ONLY the students
    being recomputed, so a partial recompute never drops anyone else's
    snapshot. The delete and the inserts share the transaction, so a failure
    rolls both back.
    """
    targets = {
        m.student.id
        for m in team.members
        if m.student and m.is_active and (student_ids is None or m.student.id in student_ids)
    }
    if not targets:
        return
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    await session.execute(
        delete(MetricSnapshot).where(
            MetricSnapshot.team_id == team.id,
            MetricSnapshot.student_id.in_(targets),
            MetricSnapshot.computed_at >= week_start,
            MetricSnapshot.computed_at < week_start + timedelta(days=7),
        )
    )


async def _flush_replacing(
    session: AsyncSession,
    team: Team,
    now: datetime,
    snapshots: list[MetricSnapshot],
    team_snap: TeamMetricSnapshot | None,
) -> None:
    """Flush inside a SAVEPOINT, so a duplicate key (the team recomputed within
    the same microsecond) does not poison the outer session: on conflict the
    rows at this timestamp are replaced, once."""
    try:
        async with session.begin_nested():
            await session.flush()
    except Exception:
        logger.warning(
            "Duplicate snapshot detected for team=%s at %s - replacing",
            team.id,
            now,
        )
        await session.rollback()
        await session.execute(
            delete(MetricSnapshot).where(
                MetricSnapshot.team_id == team.id,
                MetricSnapshot.computed_at == now,
            )
        )
        await session.execute(
            delete(TeamMetricSnapshot).where(
                TeamMetricSnapshot.team_id == team.id,
                TeamMetricSnapshot.computed_at == now,
            )
        )
        session.add_all(snapshots)
        if team_snap is not None:
            session.add(team_snap)
        await session.flush()


def _history_upsert(
    team: Team,
    student_id: UUID,
    week_number: int,
    now: datetime,
    snap: MetricSnapshot,
    prev_score: float | None,
    custom_categories: dict[str, str],
) -> Any:
    """The student's row of weekly compliance history, as INSERT ... ON
    CONFLICT DO UPDATE: the SELECT-then-INSERT it replaced raced (duplicate
    keys in production when two jobs processed the same student, or a student
    was in two teams of one course)."""
    detail: dict[str, Any] = snap.checks_detail or {}
    # Category scores from the expected checks only, so they agree with the
    # overall score (which counts only those under weekly deadlines).
    categories = _compute_category_scores(
        [
            CheckResult(
                check_id=cid,
                name=info.get("name", cid),
                passed=info.get("pass", False),
                detail=info.get("detail", ""),
                weight=info.get("weight", 0.0),
                score=info.get("score", 0.0),
            )
            for cid, info in detail.items()
            if info.get("expected", True)
        ],
        extra_categories=custom_categories,
    )
    delta = pct = None
    if prev_score is not None:
        delta = round(snap.weighted_score - prev_score, 4)
        if prev_score > 0:
            pct = round(((snap.weighted_score - prev_score) / prev_score) * 100, 2)
    stmt = pg_insert(StudentComplianceSnapshot).values(
        course_id=team.course_id,
        team_id=team.id,
        student_id=student_id,
        week_number=week_number,
        snapshot_date=now.date(),
        overall_score=round(snap.weighted_score, 4),
        commit_score=categories.get("commit"),
        mr_score=categories.get("mr"),
        review_score=categories.get("review"),
        ci_score=categories.get("ci"),
        issue_score=categories.get("issue"),
        prev_week_score=prev_score,
        improvement_delta=delta,
        improvement_pct=pct,
        raw_metrics={
            "checks_passed": snap.checks_passed,
            "checks_total": snap.checks_total,
            "traffic_light": snap.traffic_light,
            "checks_detail": detail,
        },
    )
    return stmt.on_conflict_do_update(
        constraint="uq_scs_student_course_week",
        set_={
            col: getattr(stmt.excluded, col)
            for col in (
                "team_id",
                "snapshot_date",
                "overall_score",
                "commit_score",
                "mr_score",
                "review_score",
                "ci_score",
                "issue_score",
                "prev_week_score",
                "improvement_delta",
                "improvement_pct",
                "raw_metrics",
            )
        },
    )


async def _write_compliance_history(
    session: AsyncSession,
    team: Team,
    week_number: int,
    now: datetime,
    snapshots: list[MetricSnapshot],
    custom_checks: list[CustomCheck],
) -> None:
    """Best-effort, inside a SAVEPOINT: an FK / integrity error here must not
    roll back the metric snapshots already flushed."""
    try:
        async with session.begin_nested():
            # Every member's previous-week score in ONE query, not one per
            # student (~50 round-trips per recompute for a large team).
            member_ids = [m.student.id for m in team.members if m.student and m.is_active]
            prev_scores: dict[UUID, float] = {}
            if member_ids:
                rows = await session.execute(
                    select(
                        StudentComplianceSnapshot.student_id,
                        StudentComplianceSnapshot.overall_score,
                    ).where(
                        StudentComplianceSnapshot.student_id.in_(member_ids),
                        StudentComplianceSnapshot.course_id == team.course_id,
                        StudentComplianceSnapshot.week_number == week_number - 1,
                    )
                )
                prev_scores = dict(rows.tuples().all())
            by_student: dict[UUID, MetricSnapshot] = {}
            for snap in snapshots:
                by_student.setdefault(snap.student_id, snap)
            custom_categories = {cc.check_code: cc.category for cc in custom_checks}
            for member in team.members:
                student = member.student
                if not student or not member.is_active or student.id not in by_student:
                    continue
                await session.execute(
                    _history_upsert(
                        team,
                        student.id,
                        week_number,
                        now,
                        by_student[student.id],
                        prev_scores.get(student.id),
                        custom_categories,
                    )
                )
            await session.flush()
    except Exception:
        logger.warning(
            "Failed to create compliance history snapshots for team %s (metrics still saved)",
            team.id,
            exc_info=True,
        )


# ===============================================================
#  Public API
# ===============================================================


async def _load_inputs(
    session: AsyncSession, team_id: str
) -> tuple[Team, CourseSettings, _TeamData, list[CustomCheck]] | None:
    """The team with its members, its course settings, the data of its active
    projects and the course's active custom checks - or None, logged, when
    there is nothing to compute."""
    # Members and their students loaded explicitly (no lazy loads), and
    # populate_existing so a Team already in the session is re-read.
    team = (
        await session.execute(
            select(Team)
            .where(Team.id == UUID(team_id))
            .options(selectinload(Team.members).selectinload(TeamMember.student))
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if not team:
        logger.error("Team %s not found", team_id)
        return None
    logger.info(
        "compute_team_metrics: team=%s members=%d",
        team.name,
        len(team.members) if team.members else 0,
    )

    cs = (
        await session.execute(
            select(CourseSettings).where(CourseSettings.course_id == team.course_id)
        )
    ).scalar_one_or_none()
    if not cs:
        logger.warning("No course settings for team %s", team_id)
        return None

    # Unlinked (is_active=False) projects are left out: their commits, MRs and
    # issues do not count until the project is restored.
    projects = list(
        (
            await session.execute(
                select(GitLabProject).where(
                    GitLabProject.team_id == team.id,
                    GitLabProject.is_active.is_(True),
                )
            )
        ).scalars()
    )
    if not projects:
        logger.warning("No projects found for team %s, skipping metric computation", team_id)
        return None

    data = await _TeamData.load(session, [p.id for p in projects])
    custom_checks = list(
        (
            await session.execute(
                select(CustomCheck)
                .where(CustomCheck.course_id == team.course_id, CustomCheck.is_active.is_(True))
                .order_by(CustomCheck.sort_order)
            )
        ).scalars()
    )
    logger.info(
        "Loaded data for team %s: %d projects, %d issues, %d MRs, "
        "%d notes, %d pipelines, %d commits, %d custom checks",
        team.name,
        len(projects),
        len(data.issues),
        len(data.mrs),
        len(data.notes),
        len(data.pipelines),
        len(data.commits),
        len(custom_checks),
    )
    return team, cs, data, custom_checks


def _scope(
    data: _TeamData, cs: CourseSettings, team: Team, as_of_week: int | None
) -> tuple[_TeamData, list[MergeRequest], datetime]:
    """The data the run scores, the semester's MRs and the run's clock.

    Only the current semester counts. A backfill (``as_of_week``) also sees
    the data only as it stood at that week's end, which is its clock."""
    now = datetime.now(UTC)
    floor = _semester_start_floor(cs)
    if floor is not None:
        before = data.counts()
        data = data.since(floor)
        if data.counts() != before:
            logger.info(
                "Semester-scoped metrics for team %s since %s: "
                "issues %d/%d, MRs %d/%d, notes %d/%d, approvals %d/%d, "
                "reviews %d/%d, pipelines %d/%d, commits %d/%d",
                team.name,
                floor.date(),
                *(n for pair in zip(data.counts(), before, strict=True) for n in pair),
            )
    # The semester's MRs, for pipeline branch attribution before the week cutoff.
    all_mrs = list(data.mrs)

    if as_of_week is not None:
        # Retroactive backfill: the week's end is the snapshot date and cutoff.
        # A live computation scores everything cumulatively instead - the
        # current score is the student's total progress, not this week's.
        sem_start = getattr(cs, "semester_start_date", None)
        if sem_start:
            now = datetime.combine(
                sem_start + timedelta(weeks=as_of_week - 1, days=6),
                now.time(),
                tzinfo=UTC,
            )
        data = data.as_of(now)
        logger.info(
            "Backfill cumulative as-of %s (week %d): "
            "%d issues, %d MRs, %d notes, %d pipelines, %d commits",
            now.date(),
            as_of_week,
            len(data.issues),
            len(data.mrs),
            len(data.notes),
            len(data.pipelines),
            len(data.commits),
        )
    return data, all_mrs, now


def _bucket(student: Student, roster: _Roster, ctx: StudentContext) -> str:
    """Where a member's snapshot goes: only "scored" members make the team
    aggregate - teachers, the admin-excluded, mentors and non-contributing
    members (by their GitLab role and what they did) stay out of it."""
    if student.id in roster.teachers:
        return "teacher"
    if student.id in roster.excluded:
        logger.info(
            "Excluding admin-excluded member from team aggregate: %s",
            student.gitlab_username,
        )
        return "excluded"
    if student.id in roster.mentors:
        logger.info("Excluding mentor from team aggregate: %s", student.gitlab_username)
        return "excluded"
    tm = roster.members.get(student.id)
    if tm is not None and _is_non_contributing(tm, ctx):
        logger.info(
            "Excluding non-contributing member from team aggregate: "
            "%s (role=%s, access_level=%s, source=%s)",
            student.gitlab_username,
            tm.gitlab_access_role,
            tm.gitlab_access_level,
            tm.membership_source,
        )
        return "non_contributing"
    return "scored"


async def compute_team_metrics(
    session: AsyncSession,
    team_id: str,
    *,
    force_all_checks: bool = False,
    student_ids: set[UUID] | None = None,
    check_codes: set[str] | None = None,
    as_of_week: int | None = None,
) -> None:
    """Recompute all metrics for every student in a team.

    Idempotent: produces a new snapshot row.  If a snapshot for the same
    (team, student, minute) already exists the DB UNIQUE constraint is the
    final safeguard.

    Parameters
    ----------
    force_all_checks:
        When ``True`` the weekly-deadline filter is bypassed and *all*
        enabled checks are scored, regardless of the current academic week.
        Useful for manual re-checks triggered by an admin / teacher.
    student_ids:
        When provided, only recompute metrics for these specific students.
        The team aggregate is still updated (using the new snapshot for the
        target students and the *most-recent* existing snapshots for the
        rest).  Passing this implies ``force_all_checks=True``.
    check_codes:
        When provided, only these specific check codes are evaluated
        (e.g. ``{"R01", "R03"}``).  Weekly-deadline filtering is
        bypassed (implies ``force_all_checks=True``).  ``None`` means
        evaluate according to the normal weekly-deadline / force rules.
    as_of_week:
        When provided, override the computed academic week number.  Used
        for retroactive backfill - the engine evaluates against the
        expected checks for *this* week and writes the snapshot with a
        date derived from the semester start.
    """
    if student_ids is not None or check_codes:
        force_all_checks = True

    inputs = await _load_inputs(session, team_id)
    if inputs is None:
        return
    team, cs, data, custom_checks = inputs

    data, all_mrs, now = _scope(data, cs, team, as_of_week)

    roster = _Roster.of(team)
    # An explicit `as_of_week` (backfill) is the week; deriving it from `now`
    # had backfill loops overwrite the current week's row instead of filling
    # weeks 1..8 (see `backfill_compliance_history`).
    week_number = as_of_week if as_of_week is not None else _get_week_number(cs, now)
    expected_ids = _expected_checks(cs, team.name, week_number, check_codes, force_all_checks)

    await _delete_superseded(session, team, now, student_ids)

    scored: list[MetricSnapshot] = []
    teachers: list[MetricSnapshot] = []
    excluded: list[MetricSnapshot] = []
    non_contributing: list[MetricSnapshot] = []
    for member in team.members:
        student = member.student
        if not student or not member.is_active:
            continue
        if student_ids is not None and student.id not in student_ids:
            continue
        snapshot, ctx = _student_snapshot(
            team, student, cs, now, data, all_mrs, roster, custom_checks, expected_ids
        )
        session.add(snapshot)
        {
            "teacher": teachers,
            "excluded": excluded,
            "non_contributing": non_contributing,
            "scored": scored,
        }[_bucket(student, roster, ctx)].append(snapshot)

    # The team aggregate: scored students only.
    team_snap: TeamMetricSnapshot | None = None
    if scored:
        team_snap = _build_team_snapshot(team, cs, now, scored, data.reviews, data.pipelines)
        session.add(team_snap)
    await _flush_replacing(
        session, team, now, [*scored, *teachers, *excluded, *non_contributing], team_snap
    )
    logger.info(
        "Metrics computed: team=%s students=%d teachers=%d excluded=%d "
        "non_contributing=%d (teachers + excluded + non-contributing excluded from aggregate)",
        team_id,
        len(scored),
        len(teachers),
        len(excluded),
        len(non_contributing),
    )

    # The weekly history freezes at the end of the teaching window. A LIVE
    # compute past the semester length stamped a W14..W21 row every sync - the
    # phantom "Week 21" in Week Analytics. The latest-score snapshot is already
    # flushed, so Run Checks and the score chip still refresh. Explicit
    # backfill is capped to the teaching window by its caller.
    if as_of_week is None:
        from app.api.dashboard._helpers import _semester_weeks_from_settings

        if week_number > _semester_weeks_from_settings(cs):
            return
    await _write_compliance_history(
        session, team, week_number, now, [*scored, *teachers, *excluded], custom_checks
    )


# ===============================================================
#  Compliance Checks (13 total)
# ===============================================================


# ===============================================================
#  Communication Indicators
# ===============================================================


def compute_communication_indicators(ctx: StudentContext) -> CommunicationIndicators:
    """Compute non-scoring diagnostic metrics about review communication.

    These help the teacher understand communication patterns:
    - How fast do reviewers respond?
    - How many rounds of discussion happen?
    - Are discussions resolved?
    - How substantive are the reviews?
    """
    comms = CommunicationIndicators()

    # -- Median first response time --
    # For each authored MR, find the earliest reviewer note
    first_response_hours: list[float] = []
    for mr in ctx.mrs_authored:
        mr_created = mr.created_at
        if not mr_created:
            continue
        reviewer_notes = [
            n for n in ctx.notes_on_own_mr if n.merge_request_id == mr.id and n.created_at
        ]
        if not reviewer_notes:
            continue
        note_times = [n.created_at for n in reviewer_notes if n.created_at is not None]
        if not note_times:
            continue
        earliest = min(note_times)
        delta_h = (earliest - mr_created).total_seconds() / 3600.0
        if delta_h >= 0:
            first_response_hours.append(delta_h)

    if first_response_hours:
        comms.median_first_response_hours = round(statistics.median(first_response_hours), 2)

    # -- Median review rounds (distinct discussions per MR) --
    rounds_per_mr: list[int] = []
    for mr in ctx.mrs_authored:
        discussions = {
            n.discussion_id
            for n in ctx.notes_on_own_mr
            if n.merge_request_id == mr.id and n.discussion_id
        }
        if discussions:
            rounds_per_mr.append(len(discussions))

    if rounds_per_mr:
        comms.median_review_rounds = round(statistics.median(rounds_per_mr), 1)

    # -- Discussion resolution percentage --
    resolvable = [n for n in ctx.notes_on_own_mr if n.is_resolvable]
    if resolvable:
        resolved = sum(1 for n in resolvable if n.is_resolved)
        comms.discussion_resolution_pct = round(resolved / len(resolvable) * 100.0, 1)

    # -- Review word depth (avg word count of reviewer notes) --
    reviewer_words = [n.word_count for n in ctx.notes_on_own_mr if n.word_count > 0]
    if reviewer_words:
        comms.review_word_depth = round(sum(reviewer_words) / len(reviewer_words), 1)

    # -- Author response word depth --
    response_words = [n.word_count for n in ctx.own_responses if n.word_count > 0]
    if response_words:
        comms.author_response_word_depth = round(sum(response_words) / len(response_words), 1)

    # -- Median time to merge --
    merge_hours: list[float] = []
    for mr in ctx.mrs_authored:
        if mr.state == "merged" and mr.merged_at and mr.created_at:
            delta_h = (mr.merged_at - mr.created_at).total_seconds() / 3600.0
            if delta_h >= 0:
                merge_hours.append(delta_h)

    if merge_hours:
        comms.median_time_to_merge_hours = round(statistics.median(merge_hours), 2)

    return comms


# ===============================================================
#  Internal helpers
# ===============================================================


def _build_student_context(
    student: Student,
    issues: list[Issue],
    mrs: list[MergeRequest],
    notes: list[MRNote],
    approvals: list[MRApproval],
    reviews: list[ReviewActivity],
    pipelines: list[Pipeline],
    commits: list[Commit] | None = None,
    *,
    all_mrs: list[MergeRequest] | None = None,
    team_member_count: int = 0,
) -> StudentContext:
    """Filter team-wide entities down to one student's perspective."""
    ctx = StudentContext(
        student_id=student.id,
        gitlab_user_id=student.gitlab_user_id or 0,
        gitlab_username=student.gitlab_username,
    )

    sid = student.id
    gid = student.gitlab_user_id

    # Match by internal student ID first, fallback to gitlab_user_id for unresolved entries
    ctx.issues_assigned = [
        i
        for i in issues
        if i.assignee_id == sid
        or (i.assignee_id is None and gid is not None and i.assignee_gitlab_id == gid)
    ]
    ctx.mrs_authored = [
        m
        for m in mrs
        if m.author_id == sid
        or (m.author_id is None and gid is not None and m.author_gitlab_id == gid)
    ]
    ctx.reviews_given = [r for r in reviews if r.reviewer_id == sid]

    own_mr_ids = {m.id for m in ctx.mrs_authored}

    def _is_student_note(n: MRNote) -> bool:
        """Check if note was authored by this student (by ID or gitlab_id fallback)."""
        if n.author_id == sid:
            return True
        return n.author_id is None and gid is not None and n.author_gitlab_id == gid

    # A bot account's note - the classroom assistant's review, a CI bot's
    # report - is no review thread the author owes an answer (R08): the
    # assistant writes "approved - merge it" after every review, which would
    # leave each exercise MR with threads nobody is meant to answer.
    from app.services.gitlab_import.helpers import is_bot_user

    others_notes = [
        n
        for n in notes
        if n.merge_request_id in own_mr_ids and not _is_student_note(n) and not n.is_system
    ]
    ctx.notes_on_own_mr = [
        n for n in others_notes if not (n.author_username and is_bot_user(n.author_username))
    ]
    ctx.bot_notes_on_own_mr = len(others_notes) - len(ctx.notes_on_own_mr)
    ctx.own_responses = [
        n
        for n in notes
        if n.merge_request_id in own_mr_ids and _is_student_note(n) and not n.is_system
    ]
    ctx.approvals_on_own_mr = [a for a in approvals if a.merge_request_id in own_mr_ids]

    # Approvals also surface as permanent GitLab system notes ("approved this
    # merge request"). GitLab clears the /approvals list once an MR merges and
    # its branch is deleted, so a re-sync wipes approvals_on_own_mr - but these
    # system notes survive. Derive distinct approvers from them (netting any
    # later "unapproved" note per author) so R09 stays correct for merged MRs.
    _appr_delta: dict[int, int] = {}
    for _n in notes:
        if (
            _n.merge_request_id in own_mr_ids
            and getattr(_n, "is_system", False)
            and _n.author_gitlab_id is not None
        ):
            _b = (_n.body or "").strip().lower()
            if _b.startswith("approved this merge request"):
                _appr_delta[_n.author_gitlab_id] = _appr_delta.get(_n.author_gitlab_id, 0) + 1
            elif _b.startswith("unapproved this merge request"):
                _appr_delta[_n.author_gitlab_id] = _appr_delta.get(_n.author_gitlab_id, 0) - 1
    ctx.approval_note_approver_ids = {aid for aid, _d in _appr_delta.items() if _d > 0}

    # Use all-time MR branches for pipeline attribution so that pipelines
    # running on a branch from a prior-week MR are still counted.
    all_authored = (
        [
            m
            for m in all_mrs
            if m.author_id == sid
            or (m.author_id is None and gid is not None and m.author_gitlab_id == gid)
        ]
        if all_mrs is not None
        else ctx.mrs_authored
    )
    own_branches = {m.source_branch for m in all_authored if m.source_branch}
    all_mr_ids = {m.id for m in all_authored}
    if team_member_count <= 1:
        # Solo team: all project pipelines belong to the only student.
        ctx.pipelines = list(pipelines)
    else:
        ctx.pipelines = [
            p for p in pipelines if p.ref in own_branches or p.merge_request_id in all_mr_ids
        ]
    ctx.all_team_notes = notes
    ctx.team_member_count = team_member_count

    # Commits authored by this student
    if commits is not None:
        ctx.commits = [
            c
            for c in commits
            if c.author_id == sid
            or (c.author_id is None and gid is not None and c.author_gitlab_id == gid)
        ]

    return ctx


def _find_check(checks: list[CheckResult], check_id: str) -> CheckResult:
    for c in checks:
        if c.check_id == check_id:
            return c
    return CheckResult(check_id=check_id, name="", passed=False, detail="Not evaluated")


def _build_snapshot(
    team: Team,
    student: Student,
    cs: CourseSettings,
    now: datetime,
    ctx: StudentContext,
    checks: list[CheckResult],
    comms: CommunicationIndicators,
    weighted_score: float,
    checks_passed: int,
    traffic: str,
    bottlenecks: list[str],
    all_reviews: list[ReviewActivity],
    *,
    checks_total_override: int | None = None,
    expected_check_ids: set[str] | None = None,
) -> MetricSnapshot:
    """Construct a MetricSnapshot from check results + communication indicators."""
    # R08 sub-values - use shared helper for consistency with the R08 check
    reviewer_discussions = {n.discussion_id for n in ctx.notes_on_own_mr if n.discussion_id}
    author_discussions = {n.discussion_id for n in ctx.own_responses if n.discussion_id}
    total_threads = len(reviewer_discussions)
    answered = len(reviewer_discussions & author_discussions)
    response_rate = _compute_response_rate(ctx)

    return MetricSnapshot(
        team_id=team.id,
        student_id=student.id,
        course_id=team.course_id,
        computed_at=now,
        # R01
        issues_assigned=len(ctx.issues_assigned),
        r01_issue_assigned=_find_check(checks, "R01").passed,
        # R02
        branches_total=len(ctx.mrs_authored),
        branches_correctly_named=sum(1 for m in ctx.mrs_authored if m.branch_naming_ok),
        r02_branch_naming=_find_check(checks, "R02").passed,
        # R03
        mrs_with_test_changes=sum(1 for m in ctx.mrs_authored if m.has_test_changes),
        r03_test_changes=_find_check(checks, "R03").passed,
        # R04
        mrs_created=len(ctx.mrs_authored),
        mrs_with_issue_link=sum(1 for m in ctx.mrs_authored if m.has_issue_link),
        r04_mr_issue_link=_find_check(checks, "R04").passed,
        # R05
        mrs_template_compliant=sum(1 for m in ctx.mrs_authored if m.template_compliant),
        r05_mr_template=_find_check(checks, "R05").passed,
        # R06
        own_mr_review_count=len({n.author_id for n in ctx.notes_on_own_mr if n.author_id}),
        r06_reviews_received=_find_check(checks, "R06").passed,
        # R07
        distinct_mrs_reviewed=len({r.merge_request_id for r in ctx.reviews_given}),
        meaningful_reviews_given=len(
            {r.merge_request_id for r in ctx.reviews_given if r.is_meaningful}
        ),
        r07_review_duty=_find_check(checks, "R07").passed,
        # R08
        total_review_threads=total_threads,
        answered_threads=answered,
        response_rate=round(response_rate, 4),
        responses_with_commit_ref=sum(1 for n in ctx.own_responses if n.contains_commit_ref),
        r08_response_quality=_find_check(checks, "R08").passed,
        # R09 - count distinct approvers from the live list UNION the permanent
        # approval system notes (the live list is cleared once an MR merges).
        own_mr_approvals=len(
            {a.approver_gitlab_id for a in ctx.approvals_on_own_mr} | ctx.approval_note_approver_ids
        ),
        r09_approvals=_find_check(checks, "R09").passed,
        # R10
        own_mr_merged=any(m.state == "merged" for m in ctx.mrs_authored),
        own_mr_merged_by_self=any(
            m.state == "merged"
            and (
                m.merged_by_id == student.id
                or (m.merged_by_id is None and m.merged_by_gitlab_id == ctx.gitlab_user_id)
            )
            for m in ctx.mrs_authored
        ),
        r10_merged_by_author=_find_check(checks, "R10").passed,
        # R11
        own_mr_closed=any(m.state in ("merged", "closed") for m in ctx.mrs_authored),
        linked_issue_closed=any(i.state == "closed" for i in ctx.issues_assigned),
        r11_closure_state=_find_check(checks, "R11").passed,
        # R12
        pipeline_total_count=len(ctx.pipelines),
        pipeline_success_count=sum(1 for p in ctx.pipelines if p.status == "success"),
        pipeline_has_test_job=any(p.has_test_job for p in ctx.pipelines),
        r12_pipeline_health=_find_check(checks, "R12").passed,
        # R13
        commits_total=len([c for c in ctx.commits if not getattr(c, "is_merge_commit", False)]),
        commits_web_editor=sum(
            1
            for c in ctx.commits
            if not getattr(c, "is_merge_commit", False) and is_web_editor_commit(c.title)
        ),
        r13_commit_quality=_find_check(checks, "R13").passed,
        # Communication indicators
        median_first_response_hours=comms.median_first_response_hours,
        median_review_rounds=comms.median_review_rounds,
        discussion_resolution_pct=comms.discussion_resolution_pct,
        review_word_depth=comms.review_word_depth,
        author_response_word_depth=comms.author_response_word_depth,
        median_time_to_merge_hours=comms.median_time_to_merge_hours,
        # Aggregates
        checks_passed=checks_passed,
        checks_total=checks_total_override if checks_total_override is not None else len(checks),
        weighted_score=round(weighted_score, 4),
        traffic_light=traffic,
        checks_detail={
            c.check_id: {
                "name": c.name,
                "pass": c.passed,
                "detail": c.detail,
                "weight": c.weight,
                "score": round(c.score, 4),
                "expected": c.enabled
                and (c.check_id in expected_check_ids if expected_check_ids is not None else True),
            }
            for c in checks
        },
        bottlenecks=bottlenecks[:10],
    )


def _build_team_snapshot(
    team: Team,
    cs: CourseSettings,
    now: datetime,
    student_snapshots: list[MetricSnapshot],
    all_reviews: list[ReviewActivity],
    all_pipelines: list[Pipeline],
) -> TeamMetricSnapshot:
    """Aggregate individual snapshots into a team-level summary."""
    scores = [s.weighted_score for s in student_snapshots]
    avg_score = sum(scores) / len(scores)

    # Same rule as the per-student light: when nothing was expected this week
    # every member snapshot carries checks_total == 0 (and a non-penalising 1.0
    # score), so averaging them would report a GREEN team for a week in which no
    # check ran. Summing checks_total makes that case collapse to GRAY while any
    # real evaluation keeps the normal thresholds.
    team_checks_total = sum(s.checks_total for s in student_snapshots)
    team_tl = _resolve_traffic_light(avg_score, team_checks_total, cs)

    # Review coverage: fraction of team MRs that have ≥1 review activity
    member_ids = {s.student_id for s in student_snapshots}
    mr_count = sum(s.mrs_created for s in student_snapshots)
    # Only count reviews on MRs authored by team members
    team_reviewed_mrs = len(
        {r.merge_request_id for r in all_reviews if r.reviewer_id in member_ids}
    )
    review_coverage = min((team_reviewed_mrs / mr_count * 100.0) if mr_count > 0 else 0.0, 100.0)

    # Review reciprocity: every member both authored AND reviewed
    authors = {s.student_id for s in student_snapshots if s.mrs_created > 0}
    reviewers = {r.reviewer_id for r in all_reviews if r.reviewer_id in member_ids}
    reciprocity = authors == reviewers == member_ids if member_ids else False

    # Pipeline pass rate
    if all_pipelines:
        pass_rate = (
            sum(1 for p in all_pipelines if p.status == "success") / len(all_pipelines) * 100.0
        )
    else:
        pass_rate = None

    return TeamMetricSnapshot(
        team_id=team.id,
        course_id=team.course_id,
        computed_at=now,
        member_count=len(student_snapshots),
        members_green=sum(1 for s in student_snapshots if s.traffic_light == "GREEN"),
        members_yellow=sum(1 for s in student_snapshots if s.traffic_light == "YELLOW"),
        members_red=sum(1 for s in student_snapshots if s.traffic_light == "RED"),
        members_gray=sum(1 for s in student_snapshots if s.traffic_light == "GRAY"),
        avg_weighted_score=round(avg_score, 4),
        min_weighted_score=round(min(scores), 4) if scores else None,
        max_weighted_score=round(max(scores), 4) if scores else None,
        overall_traffic_light=team_tl,
        review_coverage_pct=round(review_coverage, 1),
        review_reciprocity_flag=reciprocity,
        team_pipeline_pass_rate=round(pass_rate, 1) if pass_rate is not None else None,
        bottlenecks=list(dict.fromkeys(b for s in student_snapshots for b in s.bottlenecks))[:5],
        detail_json={
            "per_student": {
                str(s.student_id): {
                    "score": s.weighted_score,
                    "traffic": s.traffic_light,
                    "checks_passed": s.checks_passed,
                }
                for s in student_snapshots
            },
        },
    )


async def _load_all(
    session: AsyncSession,
    model: type[ModelT],
    project_ids: list[UUID],
) -> list[ModelT]:
    project_id_col = cast(Any, model).project_id
    stmt: Select[Any] = select(model).where(project_id_col.in_(project_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())


# One bind parameter is sent per id in an IN clause, and the PostgreSQL wire
# protocol caps a statement at 32767 of them. A team whose projects hold more
# merge requests than that made the whole recompute fail with asyncpg's
# "the number of query arguments cannot exceed 32767" rather than degrade, so
# ids are queried in batches comfortably under the limit.
_MAX_QUERY_IDS = 10_000


async def _load_by_mr(
    session: AsyncSession,
    model: type[ModelT],
    mr_ids: list[UUID],
) -> list[ModelT]:
    mr_id_col = cast(Any, model).merge_request_id
    rows: list[ModelT] = []
    for start in range(0, len(mr_ids), _MAX_QUERY_IDS):
        batch = mr_ids[start : start + _MAX_QUERY_IDS]
        stmt: Select[Any] = select(model).where(mr_id_col.in_(batch))
        result = await session.execute(stmt)
        rows.extend(result.scalars().all())
    return rows


def _semester_start_floor(cs: CourseSettings) -> datetime | None:
    """Return the UTC lower boundary for course-scoped activity."""
    sem_start = getattr(cs, "semester_start_date", None)
    if sem_start is None:
        return None
    return datetime.combine(sem_start, datetime.min.time(), tzinfo=UTC)


def _filter_entities_since(
    items: Iterable[ModelT],
    attr: str,
    lower_bound: datetime | None,
) -> list[ModelT]:
    """Keep entities whose timestamp belongs to the active course semester."""
    if lower_bound is None:
        return list(items)
    kept: list[ModelT] = []
    for item in items:
        ts = getattr(item, attr, None)
        if ts is not None and ts >= lower_bound:
            kept.append(item)
    return kept


# ===============================================================
#  Retroactive backfill
# ===============================================================


async def backfill_compliance_history(
    session: AsyncSession,
    team_id: str,
) -> int:
    """Recompute compliance snapshots for past weeks where the team had activity.

    After a project is synced late (e.g. added at week 8 but active since
    week 1), this function fills in ComplianceSnapshots for past weeks.
    Existing snapshots are updated via upsert so that weekly-deadline
    changes, bug-fixes, or late-added entities are reflected correctly.

    Skips weeks BEFORE the team had any GitLab activity (no commits, MRs,
    or issues yet) so the UI does not show fabricated 0 % / 100 % rows for
    weeks where the project literally did not exist. Any pre-existing
    snapshots in those pre-activity weeks are deleted so stale fake rows
    from earlier buggy backfills get cleaned up.

    Returns the number of weeks processed.
    """

    from app.utils.time_utils import get_current_week

    team_stmt = select(Team).where(Team.id == UUID(team_id))
    team_result = await session.execute(team_stmt)
    team = team_result.scalar_one_or_none()
    if not team:
        return 0

    cs_stmt = select(CourseSettings).where(CourseSettings.course_id == team.course_id)
    cs_result = await session.execute(cs_stmt)
    cs = cs_result.scalar_one_or_none()
    if not cs:
        return 0

    semester_start = getattr(cs, "semester_start_date", None)
    if not semester_start:
        return 0

    current_week = get_current_week(semester_start, datetime.now(UTC).date())
    if current_week <= 1:
        return 0
    # Never backfill past the teaching window. Once the raw week exceeds the
    # semester length (exam period / abandoned course) the weekly history is
    # complete - manufacturing W14..W21 rows produced the phantom "Week 21"
    # pill in Week Analytics long after the semester ended.
    from app.api.dashboard._helpers import _semester_weeks_from_settings

    semester_weeks = _semester_weeks_from_settings(cs)
    current_week = min(current_week, semester_weeks + 1)
    semester_floor = datetime.combine(semester_start, datetime.min.time(), tzinfo=UTC)

    # -- Determine the team's first activity week ------------------------
    # Prefer MR / Issue timestamps as the "first real activity" signal -
    # GitLab auto-creates an initial README commit at project creation
    # time which would otherwise anchor first_activity to W1 and cause
    # the backfill to fabricate 0 % rows for every week before real work
    # began. Fall back to commits only when no MRs/issues exist yet (and
    # then only count commits authored by team members, not system/bot
    # users on the initial bootstrap commit).
    project_ids_subq = select(GitLabProject.id).where(
        GitLabProject.team_id == UUID(team_id),
        GitLabProject.is_active.is_(True),
    )

    intentional_signals: list[datetime] = []

    mr_ts = (
        await session.execute(
            select(func.min(MergeRequest.created_at)).where(
                MergeRequest.project_id.in_(project_ids_subq),
                MergeRequest.created_at >= semester_floor,
            )
        )
    ).scalar_one_or_none()
    if mr_ts is not None:
        intentional_signals.append(mr_ts)

    issue_ts = (
        await session.execute(
            select(func.min(Issue.created_at)).where(
                Issue.project_id.in_(project_ids_subq),
                Issue.created_at >= semester_floor,
            )
        )
    ).scalar_one_or_none()
    if issue_ts is not None:
        intentional_signals.append(issue_ts)

    earliest_signals: list[datetime] = list(intentional_signals)

    # Fallback: no MRs and no issues -> use commits, but only those authored
    # by a known team member. Ignore unattributed / bootstrap commits.
    if not earliest_signals:
        from app.models.team_member import TeamMember

        member_student_ids_subq = select(TeamMember.student_id).where(
            TeamMember.team_id == UUID(team_id)
        )
        commit_ts = (
            await session.execute(
                select(func.min(Commit.committed_at)).where(
                    Commit.project_id.in_(project_ids_subq),
                    Commit.author_id.in_(member_student_ids_subq),
                    Commit.committed_at >= semester_floor,
                )
            )
        ).scalar_one_or_none()
        if commit_ts is not None:
            earliest_signals.append(commit_ts)

    if not earliest_signals:
        deleted = await session.execute(
            delete(StudentComplianceSnapshot).where(
                StudentComplianceSnapshot.team_id == UUID(team_id),
                StudentComplianceSnapshot.week_number < current_week,
            )
        )
        deleted_count = getattr(deleted, "rowcount", 0) or 0
        logger.info(
            "Backfill skipped for team %s: no current-semester commits/MRs/issues found"
            " (removed %d stale weekly snapshot(s))",
            team_id,
            deleted_count,
        )
        return 0

    first_activity = min(earliest_signals).date()
    first_week = max(1, get_current_week(semester_start, first_activity))

    # Drop any stale snapshots for weeks BEFORE the team had activity -
    # earlier buggy backfills may have written fake 0 % / 100 % rows there.
    if first_week > 1:
        deleted = await session.execute(
            delete(StudentComplianceSnapshot).where(
                StudentComplianceSnapshot.team_id == UUID(team_id),
                StudentComplianceSnapshot.week_number < first_week,
            )
        )
        deleted_count = getattr(deleted, "rowcount", 0) or 0
        if deleted_count:
            logger.info(
                "Backfill cleaned %d stale pre-activity snapshot(s) for team %s (weeks < %d)",
                deleted_count,
                team_id,
                first_week,
            )

    if first_week >= current_week:
        # Team became active this week - nothing to backfill, current-week
        # snapshot is already written by the inline compute_team_metrics call.
        return 0

    # Recorded weekly history is IMMUTABLE: only fill weeks that have no
    # snapshot yet. Backfill used to recompute every past week from the
    # current DB state and upsert over it, so when GitLab data was later
    # deleted (branch/MR removed) a re-sync silently rewrote a student's
    # historical score downward - the "my score was 1.5x higher a few weeks
    # ago and now it's gone" report. A week that was already scored stays as
    # it was recorded; we only ever fill genuine gaps.
    existing_weeks_res = await session.execute(
        select(StudentComplianceSnapshot.week_number)
        .where(StudentComplianceSnapshot.team_id == UUID(team_id))
        .distinct()
    )
    existing_weeks = {w for (w,) in existing_weeks_res.all()}

    weeks_to_process = [w for w in range(first_week, current_week) if w not in existing_weeks]
    if not weeks_to_process:
        return 0

    logger.info(
        "Backfilling compliance history for team %s: missing weeks %s "
        "(first activity %s -> W%d; %d week(s) already recorded, left intact)",
        team_id,
        weeks_to_process,
        first_activity.isoformat(),
        first_week,
        len(existing_weeks),
    )

    filled = 0
    for week in weeks_to_process:
        try:
            await compute_team_metrics(session, team_id, as_of_week=week)
            filled += 1
        except Exception:
            logger.warning("Failed to backfill week %d for team %s", week, team_id, exc_info=True)
    return filled
