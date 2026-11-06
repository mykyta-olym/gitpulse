"""Weekly compliance history of a course's students.

The course's record of its students' work over the semester: one compliance
snapshot per student per week, captured after each team sync
(workers/sweep_compliance.py); the per-student history the student page draws;
and the weekly course trend the Analytics page plots.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import datetime as _dt
from typing import Any

import sqlalchemy as sa
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.compliance.cohort import scored_student_ids
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.metric_snapshot import MetricSnapshot
from app.models.student_compliance_snapshot import StudentComplianceSnapshot
from app.utils.time_utils import get_current_week

logger = logging.getLogger(__name__)

# Category mapping for deriving scores from MetricSnapshot.checks_detail
_FALLBACK_CHECK_CATEGORIES: dict[str, str] = {
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


def _derive_category_scores(checks_detail: dict[str, Any] | None) -> dict[str, float | None]:
    """Compute category scores from MetricSnapshot.checks_detail JSONB.

    Returns a dict with keys 'issue', 'mr', 'review', 'ci', 'commit'. Values are
    normalised 0-1 floats or None if no checks contributed to a category.
    """
    if not checks_detail:
        return {}
    cat_score: dict[str, float] = {}
    cat_weight: dict[str, float] = {}
    for cid, info in checks_detail.items():
        if not isinstance(info, dict):
            continue
        cat = _FALLBACK_CHECK_CATEGORIES.get(cid, "custom")
        score = info.get("score", 0.0)
        weight = info.get("weight", 0.0)
        if not weight:
            continue
        cat_score[cat] = cat_score.get(cat, 0.0) + score
        cat_weight[cat] = cat_weight.get(cat, 0.0) + weight
    result: dict[str, float | None] = {}
    for cat in ("issue", "mr", "review", "ci", "commit"):
        w = cat_weight.get(cat, 0.0)
        result[cat] = round(cat_score.get(cat, 0.0) / w, 4) if w > 0 else None
    return result


def _snapshots_by_week(
    snapshots: list[StudentComplianceSnapshot],
    semester_start: date | None,
    current_week: int | None,
) -> dict[int, StudentComplianceSnapshot]:
    """Compliance snapshots keyed by the teaching week of their date.

    The stored week_number is not trusted when a semester start is known: the
    teacher may have moved the start since, or an earlier buggy backfill
    stored a future week (a row with week_number=11 dated 2026-04-23 while the
    current week is 10). The snapshot date is a real calendar date, so the
    week is derived from it, rows outside the teaching window are dropped, and
    newest-first a correctly-keyed later row wins over an older one.

    The derived week is kept HERE, never written to the ORM row: that would
    mark it dirty, and autoflush would UPDATE week_number into the
    (student_id, course_id, week_number) unique constraint - a 409.
    """
    if not semester_start:
        return {int(s.week_number): s for s in snapshots}
    by_week: dict[int, StudentComplianceSnapshot] = {}
    for s in snapshots:  # newest first
        week = get_current_week(semester_start, s.snapshot_date)
        if week < 1 or (current_week is not None and week > current_week) or week in by_week:
            continue
        by_week[week] = s
    return by_week


def _empty_row(week: int, snapshot_date: str | None) -> dict[str, Any]:
    return {
        "week_number": week,
        "snapshot_date": snapshot_date,
        "overall_score": None,
        "commit_score": None,
        "mr_score": None,
        "review_score": None,
        "ci_score": None,
        "issue_score": None,
        "improvement_delta": None,
        "improvement_pct": None,
        "checks_detail": None,
    }


def _row_from_compliance(week: int, s: StudentComplianceSnapshot) -> dict[str, Any]:
    raw: dict[str, object] = s.raw_metrics if isinstance(s.raw_metrics, dict) else {}
    # A week with zero expected checks (e.g. before the curriculum introduces
    # any check) is N/A, not 100%. The engine stores a vacuous overall_score=1.0
    # for it; the whole row is null so the Weekly Breakdown shows "-" (overall
    # AND every category) and the trend skips the point, consistent with the
    # heatmap rendering that week as all-N/A.
    na = raw.get("checks_total") == 0
    return {
        "week_number": week,
        "snapshot_date": s.snapshot_date.isoformat(),
        "overall_score": None if na else s.overall_score,
        "commit_score": None if na else s.commit_score,
        "mr_score": None if na else s.mr_score,
        "review_score": None if na else s.review_score,
        "ci_score": None if na else s.ci_score,
        "issue_score": None if na else s.issue_score,
        "improvement_delta": None if na else s.improvement_delta,
        "improvement_pct": None if na else s.improvement_pct,
        "checks_detail": raw.get("checks_detail"),
    }


def _row_from_metric(week: int, ms: MetricSnapshot) -> dict[str, Any]:
    cat_scores = _derive_category_scores(ms.checks_detail)
    na = (ms.checks_total or 0) == 0  # the same N/A rule as above
    return {
        "week_number": week,
        "snapshot_date": ms.computed_at.date().isoformat(),
        "overall_score": None if na else ms.weighted_score,
        "commit_score": None if na else cat_scores.get("commit"),
        "mr_score": None if na else cat_scores.get("mr"),
        "review_score": None if na else cat_scores.get("review"),
        "ci_score": None if na else cat_scores.get("ci"),
        "issue_score": None if na else cat_scores.get("issue"),
        "improvement_delta": None,
        "improvement_pct": None,
        "checks_detail": ms.checks_detail,
    }


def _history_from_metrics(
    metric_snaps: list[MetricSnapshot],
    semester_start: date | None,
    weeks: int,
) -> list[dict[str, Any]]:
    """History from MetricSnapshot alone, before any compliance snapshot
    exists: the latest per teaching week, weeks 1..max."""
    if not metric_snaps:
        return []
    week_best: dict[int, MetricSnapshot] = {}
    for ms in metric_snaps:  # newest first
        wk = get_current_week(semester_start, ms.computed_at.date()) if semester_start else 1
        if wk >= 1 and wk not in week_best:
            week_best[wk] = ms
    # Cap to avoid chart blow-up from corrupt/future dates
    max_week = min(max(week_best) if week_best else 1, weeks)
    history: list[dict[str, Any]] = []
    prev_score: float | None = None
    for wk in range(1, max_week + 1):
        snap = week_best.get(wk)
        if snap is None:
            history.append(_empty_row(wk, None))
            continue
        improvement_delta = None
        improvement_pct = None
        if prev_score is not None:
            improvement_delta = round(snap.weighted_score - prev_score, 4)
            if prev_score > 0:
                improvement_pct = round(((snap.weighted_score - prev_score) / prev_score) * 100, 2)
        cat_scores = _derive_category_scores(snap.checks_detail)
        history.append(
            {
                "week_number": wk,
                "snapshot_date": snap.computed_at.date().isoformat(),
                "overall_score": snap.weighted_score,
                "commit_score": cat_scores.get("commit"),
                "mr_score": cat_scores.get("mr"),
                "review_score": cat_scores.get("review"),
                "ci_score": cat_scores.get("ci"),
                "issue_score": cat_scores.get("issue"),
                "improvement_delta": improvement_delta,
                "improvement_pct": improvement_pct,
                "checks_detail": snap.checks_detail,
            }
        )
        prev_score = snap.weighted_score
    return history


@dataclass
class ComplianceSnapshot:
    """Weekly compliance snapshot for a student."""

    course_id: uuid.UUID
    team_id: uuid.UUID
    student_id: uuid.UUID
    week_number: int
    snapshot_date: date
    overall_score: float
    commit_score: float | None = None
    mr_score: float | None = None
    review_score: float | None = None
    ci_score: float | None = None
    issue_score: float | None = None
    prev_week_score: float | None = None
    raw_metrics: dict[str, Any] | None = None

    @property
    def improvement_delta(self) -> float | None:
        """Calculate absolute improvement."""
        if self.prev_week_score is not None:
            return self.overall_score - self.prev_week_score
        return None

    @property
    def improvement_pct(self) -> float | None:
        """Calculate percentage improvement."""
        if self.prev_week_score is not None and self.prev_week_score > 0:
            return ((self.overall_score - self.prev_week_score) / self.prev_week_score) * 100
        return None


@dataclass
class WeeklyComplianceTrend:
    """Weekly compliance trend data."""

    week_number: int
    week_start: date | None
    avg_score: float
    median_score: float
    min_score: float
    max_score: float
    std_dev: float
    students_count: int
    improved_count: int
    declined_count: int
    unchanged_count: int


class ComplianceHistoryService:
    """The weekly compliance snapshots of a course's students."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session
        self._week_cache: dict[int | str | uuid.UUID, int] = {}  # course_id -> current week

    async def record_compliance_snapshot(
        self,
        snapshot: ComplianceSnapshot,
    ) -> int | None:
        """Record a weekly compliance snapshot for a student.

        Uses PostgreSQL upsert (ON CONFLICT DO UPDATE) so that re-running
        the post-sync capture within the same week updates existing rows
        instead of raising a UniqueViolationError.
        """
        try:
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            values = {
                "course_id": snapshot.course_id,
                "team_id": snapshot.team_id,
                "student_id": snapshot.student_id,
                "week_number": snapshot.week_number,
                "snapshot_date": snapshot.snapshot_date,
                "overall_score": snapshot.overall_score,
                "commit_score": snapshot.commit_score,
                "mr_score": snapshot.mr_score,
                "review_score": snapshot.review_score,
                "ci_score": snapshot.ci_score,
                "issue_score": snapshot.issue_score,
                "prev_week_score": snapshot.prev_week_score,
                "improvement_delta": snapshot.improvement_delta,
                "improvement_pct": snapshot.improvement_pct,
                "raw_metrics": snapshot.raw_metrics,
            }

            stmt = pg_insert(StudentComplianceSnapshot).values(**values)
            upsert = stmt.on_conflict_do_update(
                constraint="uq_scs_student_course_week",
                set_={
                    "overall_score": stmt.excluded.overall_score,
                    "commit_score": stmt.excluded.commit_score,
                    "mr_score": stmt.excluded.mr_score,
                    "review_score": stmt.excluded.review_score,
                    "ci_score": stmt.excluded.ci_score,
                    "issue_score": stmt.excluded.issue_score,
                    "prev_week_score": stmt.excluded.prev_week_score,
                    "improvement_delta": stmt.excluded.improvement_delta,
                    "improvement_pct": stmt.excluded.improvement_pct,
                    "raw_metrics": stmt.excluded.raw_metrics,
                    "snapshot_date": stmt.excluded.snapshot_date,
                },
            ).returning(StudentComplianceSnapshot.id)

            result = await self.db.execute(upsert)
            row = result.scalar_one_or_none()
            return int(row) if row is not None else None

        except Exception as exc:
            logger.warning("Failed to record compliance snapshot: %s", exc)
            return None

    async def capture_team_snapshots(
        self,
        team_id: uuid.UUID,
        course_id: uuid.UUID,
        week: int,
    ) -> int:
        """Capture compliance snapshots for all students in a team.

        Queries the latest ``MetricSnapshot`` per student and records a
        ``ComplianceSnapshot`` for each.  Returns the number of snapshots
        recorded.

        NOTE: This is the fallback path. The authoritative writer is
        ``app.compliance.engine.compute_team_metrics`` which populates full
        per-check data (``raw_metrics.checks_detail``) and category scores.
        This method also populates those fields so the heatmap / breakdown
        still render when only the post-sync capture ran (e.g. initial
        deployment before any full metric compute).

        Performance: early-exits without doing any work when no
        ``MetricSnapshot`` has been written for this team since the last
        ``StudentComplianceSnapshot`` for the same week.  This makes the
        post-sync trigger and the periodic fallback effectively free
        when nothing changed (no new commits/MRs/etc.).
        ``StudentComplianceSnapshot.created_at`` has ``server_default=now()``
        and is intentionally *not* in the upsert ``set_={...}`` clause, so
        it preserves the original insertion time and works as a reliable
        "last computed" marker.
        """

        # -- Early no-op guard: skip when source metrics haven't moved --
        metric_max = (
            await self.db.execute(
                select(func.max(MetricSnapshot.computed_at)).where(
                    MetricSnapshot.team_id == team_id,
                    MetricSnapshot.course_id == course_id,
                )
            )
        ).scalar_one_or_none()
        if metric_max is None:
            # No source data yet -> nothing to snapshot.
            return 0
        compliance_max = (
            await self.db.execute(
                select(func.max(StudentComplianceSnapshot.created_at)).where(
                    StudentComplianceSnapshot.team_id == team_id,
                    StudentComplianceSnapshot.course_id == course_id,
                    StudentComplianceSnapshot.week_number == week,
                )
            )
        ).scalar_one_or_none()
        if compliance_max is not None and compliance_max >= metric_max:
            logger.debug(
                "Skipping compliance snapshot for team %s week %d: no new metrics "
                "(metric_max=%s <= compliance_max=%s)",
                team_id,
                week,
                metric_max,
                compliance_max,
            )
            return 0

        result = await self.db.execute(
            select(MetricSnapshot)
            .where(
                MetricSnapshot.team_id == team_id,
                MetricSnapshot.course_id == course_id,
            )
            .distinct(MetricSnapshot.student_id)
            .order_by(MetricSnapshot.student_id, MetricSnapshot.computed_at.desc())
        )
        latest_snaps = list(result.scalars().all())
        recorded = 0
        for ms in latest_snaps:
            checks_detail = ms.checks_detail or {}
            cat_scores = _derive_category_scores(checks_detail) if checks_detail else {}
            snapshot = ComplianceSnapshot(
                course_id=course_id,
                team_id=team_id,
                student_id=ms.student_id,
                week_number=week,
                snapshot_date=datetime.now(UTC).date(),
                overall_score=float(ms.weighted_score or 0),
                commit_score=cat_scores.get("commit"),
                mr_score=cat_scores.get("mr"),
                review_score=cat_scores.get("review"),
                ci_score=cat_scores.get("ci"),
                issue_score=cat_scores.get("issue"),
                raw_metrics={
                    "checks_passed": ms.checks_passed,
                    "checks_total": ms.checks_total,
                    "traffic_light": ms.traffic_light,
                    "checks_detail": checks_detail,
                },
            )
            sid = await self.record_compliance_snapshot(snapshot)
            if sid is not None:
                recorded += 1
        return recorded

    async def get_student_compliance_history(
        self,
        student_id: int | uuid.UUID,
        course_id: int | uuid.UUID,
        weeks: int = 52,
    ) -> list[dict[str, Any]]:
        """Get compliance history for a student.

        Prefers ``StudentComplianceSnapshot`` rows (populated automatically by
        the compliance engine).  If none exist yet, falls back to the most
        recent ``MetricSnapshot`` rows so the UI is never empty.

        When ComplianceSnapshots have gaps, MetricSnapshot data is merged in
        for those missing weeks (using real ``computed_at`` dates from sync).
        """
        semester_start, current_week = await self._teaching_window(course_id)

        result = await self.db.execute(
            select(StudentComplianceSnapshot)
            .where(
                and_(
                    StudentComplianceSnapshot.student_id == student_id,
                    StudentComplianceSnapshot.course_id == course_id,
                )
            )
            .order_by(StudentComplianceSnapshot.week_number.desc())
            .limit(weeks)
        )
        snap_by_week = _snapshots_by_week(
            list(result.scalars().all()), semester_start, current_week
        )
        metric_snaps = await self._latest_metric_snapshots(student_id, course_id, weeks)
        if not snap_by_week:
            return _history_from_metrics(metric_snaps, semester_start, weeks)

        # MetricSnapshot data fills the weeks the compliance snapshots miss.
        ms_by_week: dict[int, MetricSnapshot] = {}
        for ms in metric_snaps:
            wk = get_current_week(semester_start, ms.computed_at.date()) if semester_start else 1
            if wk < 1:
                continue
            if current_week is not None and wk > current_week:
                continue
            if wk not in ms_by_week and wk not in snap_by_week:
                ms_by_week[wk] = ms
        max_week = max(snap_by_week)
        if ms_by_week:
            max_week = max(max_week, max(ms_by_week))
        # Cap to avoid chart blow-up from corrupt/future dates
        max_week = min(max_week, weeks)
        if current_week is not None:
            max_week = min(max_week, current_week)

        # Start from the first week with ACTUAL data - never fabricate null
        # rows for pre-activity weeks. If a team joined at W8, the chart /
        # table / heatmap show W8..current only, not W1..W7 as empty stubs
        # (which misleads teachers into thinking data was lost, and clutters
        # the Weekly Breakdown with em-dash rows).
        min_week = min(set(snap_by_week) | set(ms_by_week))
        filled: list[dict[str, Any]] = []
        for wk in range(min_week, max_week + 1):
            if wk in snap_by_week:
                filled.append(_row_from_compliance(wk, snap_by_week[wk]))
            elif wk in ms_by_week:
                filled.append(_row_from_metric(wk, ms_by_week[wk]))
            else:
                date_str = (
                    (semester_start + timedelta(weeks=wk - 1)).isoformat()
                    if semester_start
                    else None
                )
                filled.append(_empty_row(wk, date_str))
        return filled

    async def _teaching_window(self, course_id: int | uuid.UUID) -> tuple[date | None, int | None]:
        """The course's semester start and the teaching week it is in today.

        The week is capped at the semester's length: a snapshot stamped after
        the semester ended (raw week 14..21) would otherwise still plot on the
        student trend / heatmap and drive the "W21" radar header - the
        compliance card is explicitly "across the semester". Capped only when
        a REAL semester is configured: if the start fell back to the course's
        creation date, the teaching-week count is meaningless and a cap at 13
        would hide a long-running course's history.
        """
        course_obj = (
            await self.db.execute(select(Course).where(Course.id == course_id))
        ).scalar_one_or_none()
        cs_obj = (
            await self.db.execute(
                select(CourseSettings).where(CourseSettings.course_id == course_id)
            )
        ).scalar_one_or_none()
        semester_start = (cs_obj.semester_start_date if cs_obj else None) or (
            course_obj.created_at.date() if course_obj and course_obj.created_at else None
        )
        today = _dt.now(UTC).date()
        current_week = get_current_week(semester_start, today) if semester_start else None
        if current_week is not None and cs_obj and cs_obj.semester_start_date:
            from app.api.dashboard._helpers import _semester_weeks_from_settings

            current_week = min(current_week, _semester_weeks_from_settings(cs_obj))
        return semester_start, current_week

    async def _latest_metric_snapshots(
        self,
        student_id: int | uuid.UUID,
        course_id: int | uuid.UUID,
        weeks: int,
    ) -> list[MetricSnapshot]:
        result = await self.db.execute(
            select(MetricSnapshot)
            .where(
                and_(
                    MetricSnapshot.student_id == student_id,
                    MetricSnapshot.course_id == course_id,
                )
            )
            .order_by(MetricSnapshot.computed_at.desc())
            .limit(weeks)
        )
        return list(result.scalars().all())

    async def get_weekly_compliance_trends(
        self,
        course_id: int | uuid.UUID,
        weeks: int = 52,
    ) -> list[WeeklyComplianceTrend]:
        """Get weekly compliance trends for a course.

        Uses the same active, included student cohort as the course checklist
        and fallback trend, including when old snapshots are still present.
        """

        # Get aggregated data per week (students only)
        result = await self.db.execute(
            select(
                StudentComplianceSnapshot.week_number,
                func.min(StudentComplianceSnapshot.snapshot_date).label("week_start"),
                func.avg(StudentComplianceSnapshot.overall_score).label("avg_score"),
                sa.func.percentile_cont(0.5)
                .within_group(StudentComplianceSnapshot.overall_score)
                .label("median_score"),
                func.min(StudentComplianceSnapshot.overall_score).label("min_score"),
                func.max(StudentComplianceSnapshot.overall_score).label("max_score"),
                func.stddev(StudentComplianceSnapshot.overall_score).label("std_dev"),
                func.count().label("students_count"),
                func.sum(
                    func.cast(StudentComplianceSnapshot.improvement_delta > 0, sa.Integer)
                ).label("improved_count"),
                func.sum(
                    func.cast(StudentComplianceSnapshot.improvement_delta < 0, sa.Integer)
                ).label("declined_count"),
            )
            .where(
                StudentComplianceSnapshot.course_id == course_id,
                StudentComplianceSnapshot.student_id.in_(scored_student_ids(course_id)),
            )
            .group_by(StudentComplianceSnapshot.week_number)
            .order_by(StudentComplianceSnapshot.week_number.desc())
            .limit(weeks)
        )

        rows = result.all()
        trends = []

        # Build week->row lookup for gap-filling
        week_map: dict[int, Any] = {}
        for row in rows:
            week_map[row.week_number] = row

        if week_map:
            min_week = min(week_map)
            max_week = max(week_map)

            # Also consider current academic week so chart extends to "now"
            try:
                from app.utils.time_utils import get_current_week

                cs_result = await self.db.execute(
                    select(CourseSettings).where(CourseSettings.course_id == course_id)
                )
                cs_row = cs_result.scalar_one_or_none()
                if cs_row and cs_row.semester_start_date:
                    from datetime import UTC, datetime

                    cur_week = get_current_week(
                        cs_row.semester_start_date,
                        datetime.now(UTC).date(),
                    )
                    if cur_week > max_week:
                        max_week = cur_week
            except Exception:
                logger.debug("Failed to read max week from course settings", exc_info=True)

            for wn in range(min_week, max_week + 1):
                wk_row = week_map.get(wn)
                if wk_row is not None:
                    improved = wk_row.improved_count or 0
                    declined = wk_row.declined_count or 0
                    unchanged = wk_row.students_count - improved - declined
                    trends.append(
                        WeeklyComplianceTrend(
                            week_number=wk_row.week_number,
                            week_start=wk_row.week_start,
                            avg_score=round(float(wk_row.avg_score or 0) * 100, 1),
                            median_score=round(
                                float(wk_row.median_score or wk_row.avg_score or 0) * 100,
                                1,
                            ),
                            min_score=round(float(wk_row.min_score or 0) * 100, 1),
                            max_score=round(float(wk_row.max_score or 0) * 100, 1),
                            std_dev=round(float(wk_row.std_dev or 0) * 100, 1),
                            students_count=wk_row.students_count,
                            improved_count=wk_row.improved_count or 0,
                            declined_count=wk_row.declined_count or 0,
                            unchanged_count=unchanged,
                        )
                    )
                else:
                    # Skip weeks with no data - showing 0.0 is misleading
                    # (implies students scored 0 when actually no evaluation ran)
                    pass

        return trends

    async def current_week(self, course_id: int | str | uuid.UUID) -> int:
        """Get the current academic week for a course.

        Uses ``CourseSettings.semester_start_date`` when available so the
        calculation is not tied to hardcoded calendar dates.  Falls back
        to ``_get_week_number`` from the compliance engine (which also
        reads the same column) and finally to the ISO week number.
        """
        if course_id in self._week_cache:
            return self._week_cache[course_id]

        from app.utils.time_utils import get_current_week

        today = datetime.now(UTC).date()
        semester_start: date | None = None

        # Try to read semester_start_date from course settings
        try:
            cid = course_id if isinstance(course_id, uuid.UUID) else uuid.UUID(str(course_id))
            course = await self.db.get(Course, cid)
            if course and course.settings and course.settings.semester_start_date:
                semester_start = course.settings.semester_start_date
        except Exception:
            logger.debug("semester_start_date lookup failed", exc_info=True)

        if semester_start:
            week_number = max(1, get_current_week(semester_start, today))
        else:
            # Fallback: derive from course.created_at if available
            try:
                if course and course.created_at:
                    week_number = max(1, get_current_week(course.created_at.date(), today))
                else:
                    week_number = 1
            except Exception:
                week_number = 1

        self._week_cache[course_id] = week_number
        return week_number
