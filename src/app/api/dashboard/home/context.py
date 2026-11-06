"""Role-specific context helpers for the dashboard home page."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_ as sa_and
from sqlalchemy import func, select
from sqlalchemy import or_ as sa_or

from app.api.dashboard._helpers import (
    _DEFAULT_GREEN_THRESHOLD,
    _DEFAULT_YELLOW_THRESHOLD,
    _student_match_condition,
    course_settings_for,
    logger,
)
from app.dependencies import DbSession
from app.i18n import translate_text
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.merge_request import MergeRequest
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.support_ticket import SupportTicket
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.webhook_event import WebhookEvent


async def _build_sidebar_badges(
    role: str,
    active_ids: list[uuid.UUID],
    db: DbSession,
) -> dict[str, int]:
    """Compute sidebar badge counts based on role.

    Only returns actionable notification counts (e.g. failed events).
    Badges with count 0 are omitted so the sidebar stays clean.
    """

    badges: dict[str, int] = {}
    try:
        if role in ("admin", "teacher"):
            # DLQ events - dead-lettered webhook events needing attention
            dlq_count_result = await db.execute(
                select(func.count(WebhookEvent.id)).where(
                    WebhookEvent.dead_letter_at.isnot(None),
                ),
            )
            dlq = dlq_count_result.scalar() or 0
            if dlq:
                badges["events"] = dlq

            # Open support tickets in visible courses.
            try:
                _badge_where = [SupportTicket.status.in_(["open", "in_progress"])]
                if active_ids:
                    _badge_where.append(SupportTicket.course_id.in_(active_ids))
                open_tickets_r = await db.execute(
                    select(func.count(SupportTicket.id)).where(*_badge_where),
                )
                open_tickets = open_tickets_r.scalar() or 0
                if open_tickets:
                    badges["support_tickets"] = open_tickets
            except Exception:  # noqa: S110 - best-effort badge enrichment
                pass
        # student - no actionable badges for now
    except Exception:
        logger.debug("sidebar badges query failed")
    return badges


def _greeting_word(locale: str = "sk") -> str:
    """Return a time-of-day greeting word for the dashboard title.

    Server-side fallback so the swapped-in content already shows a real
    greeting (not a generic "Hi") and never visibly flickers.  The client
    re-evaluates against the *viewer's* local clock in an inline pre-paint
    script, correcting the rare boundary-hour mismatch without a flash.
    Server time is UTC; the inline script is authoritative for display.
    """
    hour = datetime.now(UTC).hour
    if 5 <= hour < 12:
        key = "Good morning"
    elif 12 <= hour < 18:
        key = "Good afternoon"
    else:
        key = "Good evening"
    return translate_text(locale, key)


async def _build_student_context(
    active_ids: list[uuid.UUID],
    db: DbSession,
    _auth: dict[str, str],
) -> dict[str, Any]:
    """Build student-specific dashboard context: teams, compliance, deadlines."""

    ctx: dict[str, Any] = {
        "team_names": {},
        "team_ids": [],
        "compliance_pct": 0,
        "traffic_light": "green",
        "next_deadline": None,
        "open_mrs": 0,
        "failed_pipelines": 0,
    }

    gitlab_username = _auth.get("gitlab_username", "") or _auth.get("user", "")
    if not gitlab_username or not active_ids:
        return ctx

    try:
        # Resolve student record
        _stu_stmt = select(Student).where(
            _student_match_condition(_auth),
        )
        _stu_result = await db.execute(_stu_stmt)
        _student = _stu_result.scalar_one_or_none()
        if not _student:
            return ctx

        # Find student's teams across active courses (noload members/projects - not needed)
        from sqlalchemy.orm import noload

        team_stmt = (
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .options(noload(Team.members), noload(Team.projects))
            .where(
                TeamMember.student_id == _student.id,
                Team.course_id.in_(active_ids),
            )
        )
        team_result = await db.execute(team_stmt)
        student_teams = list(team_result.scalars().all())

        for t in student_teams:
            ctx["team_names"][str(t.course_id)] = t.name

        if not student_teams:
            return ctx

        team_ids = [t.id for t in student_teams]
        ctx["team_ids"] = [str(tid) for tid in team_ids]

        compliance_scores, courses_by_id = await _compliance_scores(db, _student, student_teams)
        if compliance_scores:
            avg = sum(compliance_scores) / len(compliance_scores)
            ctx["compliance_pct"] = round(avg)
            ctx["traffic_light"] = _traffic_light(avg, student_teams, courses_by_id)

        # "Your progress" counts the student's own work, as the Open MRs card
        # does: their open merge requests, and the failed pipelines of their
        # merge requests or branches (the engine's rule for a student's pipelines).
        own_mr = _own_mr_condition(_student)
        ctx["open_mrs"] = await _count_in_teams(
            db, team_ids, MergeRequest, sa_and(MergeRequest.state == "opened", own_mr), "open MRs"
        )
        own_branch = (
            select(MergeRequest.id)
            .where(
                own_mr,
                MergeRequest.project_id == Pipeline.project_id,
                MergeRequest.source_branch == Pipeline.ref,
            )
            .exists()
        )
        own_mr_pipeline = Pipeline.merge_request_id.in_(select(MergeRequest.id).where(own_mr))
        ctx["failed_pipelines"] = await _count_in_teams(
            db,
            team_ids,
            Pipeline,
            sa_and(Pipeline.status == "failed", sa_or(own_mr_pipeline, own_branch)),
            "failed pipelines",
        )
        ctx["next_deadline"] = await _next_deadline(db, active_ids)

    except Exception:
        logger.debug("student context build failed")
    return ctx


async def _compliance_scores(
    db: DbSession,
    student: Student,
    student_teams: list[Team],
) -> tuple[list[float], dict[uuid.UUID, Course]]:
    """The student's score in each group from its latest snapshot, and the
    groups' courses (for their thresholds)."""
    team_ids = [t.id for t in student_teams]
    compliance_scores: list[float] = []
    courses_by_id: dict[uuid.UUID, Course] = {}
    try:
        from app.models.metric_snapshot import MetricSnapshot

        # Batch-fetch latest snapshot per team for this student
        latest_sub = (
            select(
                MetricSnapshot.team_id,
                func.max(MetricSnapshot.computed_at).label("max_at"),
            )
            .where(
                MetricSnapshot.team_id.in_(team_ids),
                MetricSnapshot.student_id == student.id,
            )
            .group_by(MetricSnapshot.team_id)
            .subquery()
        )
        snap_stmt = select(MetricSnapshot).join(
            latest_sub,
            sa_and(
                MetricSnapshot.team_id == latest_sub.c.team_id,
                MetricSnapshot.computed_at == latest_sub.c.max_at,
                MetricSnapshot.student_id == student.id,
            ),
        )
        snap_result = await db.execute(snap_stmt)
        snaps_by_team = {s.team_id: s for s in snap_result.scalars().all()}

        # Batch-fetch courses for threshold lookup
        course_ids = list({t.course_id for t in student_teams})
        course_result = await db.execute(select(Course).where(Course.id.in_(course_ids)))
        courses_by_id = {c.id: c for c in course_result.scalars().all()}

        for t in student_teams:
            snap = snaps_by_team.get(t.id)
            if not snap or not snap.traffic_light:
                continue
            # Skip "no data" weeks (no expected checks this week): their
            # weighted_score is a deliberate non-penalising 1.0, so counting
            # it as 100% would inflate the student's headline compliance_pct
            # while the badge (correctly) shows GRAY. Consistent with GRAY =
            # "No compliance data available".
            if snap.checks_total == 0:
                continue
            if snap.weighted_score is not None:
                compliance_scores.append(snap.weighted_score * 100)
            else:
                tl = snap.traffic_light
                _c_fb = courses_by_id.get(t.course_id)
                _cs_fb = _c_fb.settings if _c_fb else None
                _gt = _cs_fb.green_threshold if _cs_fb else _DEFAULT_GREEN_THRESHOLD
                _yt = _cs_fb.yellow_threshold if _cs_fb else _DEFAULT_YELLOW_THRESHOLD
                _g = _gt * 100
                _y = _yt * 100
                _tl_fallback = {
                    "GREEN": (_g + 100) / 2,
                    "YELLOW": (_y + _g) / 2,
                    "RED": _y / 2,
                    "GRAY": _y,
                }
                compliance_scores.append(_tl_fallback.get(tl, _y))
    except Exception:
        logger.debug("Failed to load compliance scores", exc_info=True)
    return compliance_scores, courses_by_id


def _traffic_light(
    avg: float,
    student_teams: list[Team],
    courses_by_id: dict[uuid.UUID, Course],
) -> str:
    """The light for an average score, on the thresholds of the first of the
    student's courses that has settings (the defaults otherwise)."""
    from app.models.course_settings import CourseSettings as _Cs

    _green_cut = _Cs.green_threshold.default.arg * 100
    _yellow_cut = _Cs.yellow_threshold.default.arg * 100
    for t in student_teams:
        _course = courses_by_id.get(t.course_id)
        _cs = getattr(_course, "settings", None) if _course else None
        if _cs:
            _green_cut = _cs.green_threshold * 100
            _yellow_cut = _cs.yellow_threshold * 100
            break
    if avg >= _green_cut:
        return "green"
    if avg >= _yellow_cut:
        return "yellow"
    return "red"


def _own_mr_condition(student: Student) -> Any:
    """Merge requests the student authored, by row link or by GitLab user id."""
    if student.gitlab_user_id is None:
        return MergeRequest.author_id == student.id
    return sa_or(
        MergeRequest.author_id == student.id,
        MergeRequest.author_gitlab_id == student.gitlab_user_id,
    )


async def _count_in_teams(
    db: DbSession,
    team_ids: list[uuid.UUID],
    model: Any,
    condition: Any,
    what: str,
) -> int:
    """How many rows of ``model`` in the groups' projects meet ``condition``
    (0 when the count fails - the dashboard still renders)."""
    try:
        stmt = (
            select(func.count(model.id))
            .select_from(model)
            .join(GitLabProject, GitLabProject.id == model.project_id)
            .where(GitLabProject.team_id.in_(team_ids), condition)
        )
        return (await db.execute(stmt)).scalar() or 0
    except Exception:
        logger.debug(f"Failed to count {what}", exc_info=True)
        return 0


async def _next_deadline(db: DbSession, active_ids: list[uuid.UUID]) -> dict[str, Any] | None:
    """The nearest upcoming MR-creation or merge deadline of the courses."""
    try:
        dl_rows = await course_settings_for(db, active_ids)
        now_utc = datetime.now(UTC)
        nearest_deadline: dict[str, Any] | None = None
        for cs_row in dl_rows.values():
            for label, dt_val in [
                ("MR Creation Deadline", cs_row.mr_creation_deadline),
                ("Merge Deadline", cs_row.merge_deadline),
            ]:
                if dt_val and dt_val >= now_utc:
                    days_left = (dt_val - now_utc).days
                    if nearest_deadline is None or days_left < nearest_deadline["days_left"]:
                        nearest_deadline = {
                            "title": label,
                            "due": dt_val.isoformat(),
                            "days_left": days_left,
                        }
        return nearest_deadline
    except Exception:
        logger.debug("Failed to compute next deadline", exc_info=True)
        return None


async def _build_admin_context(db: DbSession) -> dict[str, Any]:
    """Build admin dashboard context: system health snapshot."""

    ctx: dict[str, Any] = {
        "jobs_queued": 0,
        "jobs_running": 0,
        "jobs_failed_24h": 0,
        "jobs_completed_24h": 0,
        "jobs_total": 0,
        "webhooks_pending": 0,
        "db_ok": True,
    }
    try:
        # One round-trip, not five. These were five separate SELECT count(*)
        # statements against the same table, differing only in their WHERE
        # clause, and the dashboard issued every one of them on every render -
        # five of the fifty queries that page used to make. Conditional
        # aggregation asks all five questions in a single pass.
        #
        # The cutoff is computed once here too; it used to be evaluated
        # separately for the failed and completed counts, so the two windows
        # could differ by the time between the queries.
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        counts = (
            await db.execute(
                select(
                    func.count(BackgroundJob.id).filter(BackgroundJob.status == "enqueued"),
                    func.count(BackgroundJob.id).filter(BackgroundJob.status == "running"),
                    func.count(BackgroundJob.id).filter(
                        BackgroundJob.status == "failed",
                        BackgroundJob.completed_at >= cutoff,
                    ),
                    func.count(BackgroundJob.id).filter(
                        BackgroundJob.status == "completed",
                        BackgroundJob.completed_at >= cutoff,
                    ),
                    func.count(BackgroundJob.id),
                )
            )
        ).one()
        (
            ctx["jobs_queued"],
            ctx["jobs_running"],
            ctx["jobs_failed_24h"],
            ctx["jobs_completed_24h"],
            ctx["jobs_total"],
        ) = (c or 0 for c in counts)

        try:
            pending = await db.execute(
                select(func.count(WebhookEvent.id)).where(
                    WebhookEvent.processed.is_(False),
                ),
            )
            ctx["webhooks_pending"] = pending.scalar() or 0
        except Exception:
            logger.debug("Failed to count pending webhooks", exc_info=True)
    except Exception:
        logger.debug("admin context build failed")
    return ctx
