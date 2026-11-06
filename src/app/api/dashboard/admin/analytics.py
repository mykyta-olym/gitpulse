"""Admin: course analytics routes + SSE stream."""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, select
from sqlalchemy import func as sa_func
from sqlalchemy.orm import load_only

from app.api.dashboard._access import _can_manage_course, _membership_role
from app.api.dashboard._helpers import (
    _course_data_staleness,
    _csrf_token,
    _not_found_response,
    _role_context,
    _semester_weeks_from_settings,
    _templates,
    _threshold_pcts,
    logger,
)
from app.compliance.check_registry import CATEGORIES, CHECK_DEFS, CHECK_DEFS_MAP
from app.compliance.cohort import scored_student_ids
from app.config import get_settings
from app.dependencies import DbSession, TeacherAuth
from app.i18n import translate_text
from app.models.commit import Commit
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.custom_check import CustomCheck
from app.models.issue import Issue
from app.models.merge_request import MergeRequest
from app.models.metric_snapshot import MetricSnapshot
from app.models.mr_note import MRNote
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.team import Team
from app.services.page_cache import CSP_NONCE_PLACEHOLDER as _PAGE_CACHE_NONCE
from app.services.page_cache import CSRF_PLACEHOLDER as _PAGE_CACHE_CSRF
from app.services.page_cache import build_cache_render_ctx as _page_cache_build_ctx
from app.services.page_cache import cacheable_role_ctx as _page_cache_role_ctx
from app.services.page_cache import get_cached as _page_cache_get
from app.services.page_cache import make_role_variant as _page_cache_role_variant
from app.services.page_cache import render_inline as _render_inline
from app.services.page_cache import set_cached as _page_cache_set
from app.utils.semester import semester_floor_utc
from app.utils.time_utils import get_current_week

router = APIRouter()


# -- Compliance trend ---------------------------------------------------------


def _week_row(week: int, scores: dict[Any, float], prev: dict[Any, float]) -> dict[str, Any]:
    """One week of the trend from each student's score that week, compared
    with the week before that has data."""
    values = list(scores.values())
    mean = sum(values) / len(values)
    std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5 if len(values) > 1 else 0.0
    compared = [(score, prev[sid]) for sid, score in scores.items() if sid in prev]
    return {
        "week_number": week,
        "avg_score": round(mean * 100, 1),
        "std_dev": round(std * 100, 1),
        "min_score": round(min(values) * 100, 1),
        "max_score": round(max(values) * 100, 1),
        "students_count": len(values),
        "improved_count": sum(1 for now, before in compared if now > before),
        "declined_count": sum(1 for now, before in compared if now < before),
    }


async def _trends_from_snapshots(
    db: DbSession, course_id: uuid.UUID, ref: date, ceiling: date
) -> list[dict[str, Any]]:
    """The trend from metric_snapshots, when the compliance history has none:
    each student's latest score of each week."""
    rows = await db.execute(
        select(
            MetricSnapshot.student_id,
            MetricSnapshot.weighted_score,
            MetricSnapshot.computed_at,
        )
        .where(
            MetricSnapshot.course_id == course_id,
            MetricSnapshot.computed_at <= ceiling,
            MetricSnapshot.student_id.in_(scored_student_ids(course_id)),
        )
        .order_by(MetricSnapshot.computed_at.desc(), MetricSnapshot.id.desc())
    )
    by_week: dict[int, dict[Any, float]] = {}
    for row in rows.all():
        week = get_current_week(ref, row.computed_at.date())
        if week >= 1:
            by_week.setdefault(week, {}).setdefault(row.student_id, float(row.weighted_score or 0))
    trends = []
    prev: dict[Any, float] = {}
    for week in sorted(by_week):
        trends.append(_week_row(week, by_week[week], prev))
        prev = by_week[week]
    return trends


async def _compliance_trends(
    db: DbSession, course: Course, ref: date | None, ceiling: date
) -> list[dict[str, Any]]:
    from app.services.compliance_history import ComplianceHistoryService

    try:
        # Full history window (API max): teaching weeks + exam period
        # (skuskove obdobie). Passing the teaching-week count (13) clipped
        # exam-period weeks off the trend. The service caps internally to the
        # current academic week, so this never over-extends.
        raw = await ComplianceHistoryService(db).get_weekly_compliance_trends(course.id, 52)
        trends = [
            {
                "week_number": t.week_number,
                "avg_score": t.avg_score,
                "std_dev": t.std_dev,
                "min_score": t.min_score,
                "max_score": t.max_score,
                "students_count": t.students_count,
                "improved_count": t.improved_count,
                "declined_count": t.declined_count,
            }
            for t in raw
        ]
    except Exception:
        logger.debug("analytics_trends_failed", course_id=str(course.id), exc_info=True)
        trends = []
    if trends or ref is None:
        return trends
    try:
        return await _trends_from_snapshots(db, course.id, ref, ceiling)
    except Exception as exc:
        logger.debug("analytics_trends_fallback_failed: %s", str(exc), exc_info=True)
        return []


# -- Activity per week --------------------------------------------------------


async def _per_week(
    db: DbSession,
    ref: date,
    project_ids: list[Any],
    ceiling: date,
    floor: datetime | None,
    created: Any,
    counted: Any,
    project: Any,
    join: tuple[Any, Any] | None = None,
) -> dict[int, int]:
    """How many rows per academic week, counted by the database per day (one
    row per day, not per commit), clamped to the semester when one is set:
    pre-semester template commits and archived MRs otherwise read as
    progress."""
    day = sa_func.date(created)
    where = [project.in_(project_ids), created.isnot(None), created <= ceiling]
    if floor is not None:
        where.append(created >= floor)
    stmt = select(day.label("d"), sa_func.count(counted).label("cnt"))
    if join is not None:
        stmt = stmt.join(*join)
    by_week: dict[int, int] = {}
    for row in (await db.execute(stmt.where(*where).group_by(day))).all():
        week = get_current_week(ref, row.d)
        if week >= 1:
            by_week[week] = by_week.get(week, 0) + row.cnt
    return by_week


async def _activity(
    db: DbSession,
    course_id: uuid.UUID,
    ref: date,
    project_ids: list[Any],
    ceiling: date,
    floor: datetime | None,
) -> list[dict[str, Any]]:
    """Commits, MRs, pipelines, issues and reviews per week."""
    args = (db, ref, project_ids, ceiling, floor)
    rows: list[dict[str, Any]] = []
    try:
        commits = await _per_week(*args, Commit.committed_at, Commit.id, Commit.project_id)
        mrs = await _per_week(
            *args, MergeRequest.created_at, MergeRequest.id, MergeRequest.project_id
        )
        pipes = await _per_week(*args, Pipeline.created_at, Pipeline.id, Pipeline.project_id)
        rows = [
            {
                "week": w,
                "commits": commits.get(w, 0),
                "merge_requests": mrs.get(w, 0),
                "pipelines": pipes.get(w, 0),
            }
            for w in sorted(set(commits) | set(mrs) | set(pipes))
        ]
    except Exception:
        logger.debug("analytics_activity_failed", course_id=str(course_id), exc_info=True)

    try:
        issues = await _per_week(*args, Issue.created_at, Issue.id, Issue.project_id)
        reviews = await _per_week(
            *args,
            MRNote.created_at,
            MRNote.id,
            MergeRequest.project_id,
            join=(MergeRequest, MRNote.merge_request_id == MergeRequest.id),
        )
    except Exception:
        logger.debug("analytics_issues_reviews_failed", course_id=str(course_id), exc_info=True)
        issues = reviews = {}
    have = {r["week"] for r in rows}
    for r in rows:
        r["issues"] = issues.get(r["week"], 0)
        r["reviews"] = reviews.get(r["week"], 0)
    rows += [
        {
            "week": w,
            "commits": 0,
            "merge_requests": 0,
            "pipelines": 0,
            "issues": issues.get(w, 0),
            "reviews": reviews.get(w, 0),
        }
        for w in sorted((set(issues) | set(reviews)) - have)
    ]
    return sorted(rows, key=lambda r: r["week"])


# -- Checklist breakdown ------------------------------------------------------


def _check_detail(snap: MetricSnapshot, code: str) -> Any:
    return (getattr(snap, "checks_detail", None) or {}).get(code, {})


async def _checklist(
    db: DbSession,
    course_id: uuid.UUID,
    cs: CourseSettings | None,
    ceiling: date,
    locale: str,
    yellow_pct: float,
) -> tuple[list[dict[str, Any]], int, int, bool]:
    """% of students passing each check (built-in + custom), from each
    student's latest snapshot; the students below yellow on average; the
    number of scored students; and whether there is anything to measure."""
    cohort = scored_student_ids(course_id)
    latest = (
        select(
            MetricSnapshot.student_id,
            sa_func.max(MetricSnapshot.computed_at).label("latest"),
        )
        .where(
            MetricSnapshot.course_id == course_id,
            MetricSnapshot.computed_at <= ceiling,
            MetricSnapshot.student_id.in_(cohort),
        )
        .group_by(MetricSnapshot.student_id)
        .subquery()
    )
    snaps = list(
        (
            await db.execute(
                select(MetricSnapshot)
                # Charts need check outcomes, not the snapshot's diagnostic
                # counters and arrays. Avoid fetching and decoding those here.
                .options(
                    load_only(
                        MetricSnapshot.student_id,
                        MetricSnapshot.checks_detail,
                        *(getattr(MetricSnapshot, attr) for attr, _, _ in CHECK_DEFS),
                    )
                )
                .join(
                    latest,
                    and_(
                        MetricSnapshot.student_id == latest.c.student_id,
                        MetricSnapshot.computed_at == latest.c.latest,
                    ),
                )
                .where(MetricSnapshot.course_id == course_id)
                .order_by(MetricSnapshot.id.desc())
            )
        )
        .scalars()
        # Simultaneous snapshots in two teams still describe one student.
        .unique(lambda snap: snap.student_id)
        .all()
    )
    students = (
        await db.execute(select(sa_func.count()).select_from(cohort.subquery()))
    ).scalar() or 0

    def row(code: str, label: str, category: str, passed: int) -> dict[str, Any]:
        expected = sum(1 for s in snaps if _check_detail(s, code).get("expected", True))
        return {
            "code": code,
            "label": label,
            "category": category,
            "passed": passed,
            "total": students,
            "pct": round(passed / students * 100, 1) if students else 0,
            "expected": expected > 0 or not snaps,
        }

    # Built-in checks from the registry - a new check in builtin_checks.json
    # lights up here - minus those the course disabled. The names are English
    # data with Slovak in the catalogue; a teacher's own override is their
    # words and is left as-is.
    builtin = [(code, attr) for attr, code, _ in CHECK_DEFS]
    enabled = set((cs.enabled_checks or []) if cs else [])
    overrides = (cs.check_configs or {}) if cs else {}
    data = []
    for code, attr in builtin:
        if enabled and code not in enabled:
            continue
        override = overrides.get(code, {}) or {}
        data.append(
            row(
                code,
                override.get("_name") or translate_text(locale, CHECK_DEFS_MAP.get(code, code)),
                override.get("_category") or CATEGORIES.get(code, "custom"),
                sum(1 for s in snaps if getattr(s, attr, False)),
            )
        )

    try:
        custom = (
            await db.execute(
                select(CustomCheck)
                .where(CustomCheck.course_id == course_id, CustomCheck.is_active.is_(True))
                .order_by(CustomCheck.sort_order)
            )
        ).scalars()
        for cc in custom:
            data.append(
                row(
                    cc.check_code,
                    cc.name,
                    cc.category or "custom",
                    sum(1 for s in snaps if (_check_detail(s, cc.check_code) or {}).get("pass")),
                )
            )
    except Exception:
        logger.debug("analytics_custom_checks_failed", exc_info=True)

    # At risk: a student whose pass rate over the expected checks is below
    # yellow. Built-ins read the boolean columns, custom checks checks_detail.
    at_risk = 0
    for s in snaps:
        expected_codes = {
            c["code"] for c in data if _check_detail(s, c["code"]).get("expected", True)
        }
        detail = getattr(s, "checks_detail", None) or {}
        results = [
            bool(getattr(s, attr, False)) for code, attr in builtin if code in expected_codes
        ]
        for code in expected_codes:
            if not code.startswith("R"):
                entry = detail.get(code, {}) if isinstance(detail, dict) else {}
                results.append(isinstance(entry, dict) and bool(entry.get("pass")))
        if results and sum(results) / len(results) * 100 < yellow_pct:
            at_risk += 1

    return data, at_risk, students, bool(students and snaps)


# -- Academic week ------------------------------------------------------------


def _week_context(cs: CourseSettings | None, semester_weeks: int) -> tuple[int, int, bool, int]:
    """(current teaching week, raw week, in the exam period, exam week)."""
    if not (cs and cs.semester_start_date):
        return 0, 0, False, 0
    raw = get_current_week(cs.semester_start_date)
    current = min(raw, semester_weeks)
    if raw <= semester_weeks:
        return current, raw, False, 0
    # Past the teaching weeks: the exam period, until the semester ends. An
    # explicit end date covers teaching AND exams (see the field's help text);
    # without one the end is the teaching weeks plus the default exam period -
    # ending at the last teaching week meant a course with no end date never
    # entered an exam period, and never closing it had the Week Analytics
    # picker stretch to the raw week (a course that ended in May showed a
    # "Week 21" pill in July).
    end = cs.semester_end_date or (
        cs.semester_start_date
        + timedelta(weeks=semester_weeks + get_settings().exam_period_default_weeks)
    )
    if datetime.now(UTC).date() > end:
        return current, raw, False, 0
    return current, raw, True, raw - semester_weeks


# -- Course Analytics --


@router.get("/courses/{course_id}/analytics", response_class=HTMLResponse)
async def course_analytics(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    auth: TeacherAuth,
) -> Response:
    """Analytics page: compliance trends and course activity summary."""
    course = await db.get(Course, course_id)
    if not course or not await _can_manage_course(course, auth, db):
        return _not_found_response(request, "Course", "Course not found")

    role_ctx = _role_context(auth)
    course_role = await _membership_role(db, course_id, auth)

    def respond(fragment: str) -> Response:
        # GitLab-style single-response delivery: the content inlined into the
        # full page.
        return _render_inline(
            request=request,
            fragment=fragment,
            csrf_token=_csrf_token(auth),
            role_ctx=role_ctx,
            templates=_templates(request),
            page_template="course_analytics.html",
            page_ctx={"course": course, "course_role": course_role},
        )

    # The computation is heavy (aggregates across snapshots, commits, MRs and
    # pipelines), and course-wide rather than personal, so the rendered body is
    # cached and served to any teacher/admin who can view the course. CSRF,
    # CSP nonce and personal fields are placeholders, substituted on serve.
    variant = _page_cache_role_variant(request, role_ctx)
    if "_gp_refresh" not in request.query_params:
        cached = _page_cache_get("course-analytics", course_id, variant)
        if cached is not None:
            return respond(cached)

    cs = course.settings
    green_pct, yellow_pct = _threshold_pcts(cs)
    semester_weeks = _semester_weeks_from_settings(cs)
    # Events dated past next week are data corruption (a week of grace for
    # timezone skew).
    ceiling = datetime.now(UTC).date() + timedelta(days=7)
    # Week 1 starts at the semester, or at the course's creation without one.
    ref: date | None = None
    if cs and cs.semester_start_date:
        ref = cs.semester_start_date
    elif course.created_at:
        ref = course.created_at.date()

    trends = await _compliance_trends(db, course, ref, ceiling)

    activity: list[dict[str, Any]] = []
    if ref:
        project_ids = list(
            (
                await db.execute(
                    select(GitLabProject.id)
                    .join(Team, GitLabProject.team_id == Team.id)
                    .where(Team.course_id == course_id, GitLabProject.is_active.is_(True))
                )
            ).scalars()
        )
        if project_ids:
            activity = await _activity(
                db, course_id, ref, project_ids, ceiling, semester_floor_utc(cs)
            )

    try:
        checklist, at_risk, checklist_students, has_data = await _checklist(
            db, course_id, cs, ceiling, getattr(request.state, "locale", "sk"), yellow_pct
        )
    except Exception:
        logger.debug("analytics_checklist_failed", course_id=str(course_id), exc_info=True)
        checklist, at_risk, checklist_students, has_data = [], 0, 0, False
    # No scored students, or no computed snapshot yet: nothing to measure, and
    # thirteen 0% bars read as "everyone fails" where the honest answer is "no
    # data" - the card shows its empty state instead.
    if not has_data:
        checklist, at_risk = [], 0

    current_week, raw_week, is_exam_period, exam_week = _week_context(cs, semester_weeks)
    # Weekly snapshots are immutable, so a course that accumulated stale
    # W14..W21 rows (before the W>N write cap) kept plotting phantom points and
    # stretching the picker after the semester ended. Every week-keyed series
    # is clipped to the teaching weeks, extended to the raw week only while
    # the exam period is open - and only with a semester configured: without
    # one the weeks count from the course's creation, and clipping to 13 would
    # hide a long-running, undated course's data.
    if cs and cs.semester_start_date:
        cap = raw_week if (is_exam_period and raw_week) else semester_weeks
        trends = [t for t in trends if t["week_number"] <= cap]
        activity = [a for a in activity if a.get("week", 0) <= cap]

    # The weekly-summary selector: weeks with data, and always 1..N.
    max_weeks = max(
        {a["week"] for a in activity}
        | {t["week_number"] for t in trends}
        | set(range(1, semester_weeks + 1)),
        default=semester_weeks,
    )

    (
        data_is_stale,
        latest_snapshot_at,
        data_days_old,
        current_week_groups,
        total_active_groups,
    ) = await _course_data_staleness(db, course_id)

    expected = [c for c in checklist if c.get("expected", True)]
    ctx = {
        "request": request,
        "course": course,
        "checklist_data": checklist,
        "checklist_students": checklist_students,
        "at_risk_count": at_risk,
        "green_pct": green_pct,
        "yellow_pct": yellow_pct,
        "max_weeks": max_weeks,
        "semester_weeks": semester_weeks,
        "current_week": current_week,
        # Teaching weeks are 1..N; in the exam period the raw week exceeds N.
        "display_weeks": (
            max(semester_weeks, max_weeks, raw_week) if is_exam_period else semester_weeks
        ),
        "now_week": raw_week if is_exam_period and raw_week else current_week,
        "is_exam_period": is_exam_period,
        "exam_week": exam_week,
        "latest_snapshot_at": latest_snapshot_at,
        "data_is_stale": data_is_stale,
        "data_days_old": data_days_old,
        "current_week_groups": current_week_groups,
        "total_active_groups": total_active_groups,
        "avg_compliance": (
            round(max(trends, key=lambda t: t["week_number"]).get("avg_score", 0), 1)
            if trends
            else None
        ),
        "checklist_avg": (
            round(sum(c["pct"] for c in expected) / len(expected), 1) if expected else None
        ),
        "total_activity": sum(a.get("commits", 0) + a.get("merge_requests", 0) for a in activity),
        "activity_data": activity,
        "trends": trends,
        "csrf_token": _PAGE_CACHE_CSRF,
        "csp_nonce": _PAGE_CACHE_NONCE,
        **_page_cache_role_ctx(role_ctx),
    }
    html = (
        _templates(request)
        .get_template("partials/course/_analytics_content.html")
        .render({**_page_cache_build_ctx(request), "request": request, **ctx})
    )
    # Long TTL (10 min): cold aggregation can be expensive on large courses.
    # Sync, metrics jobs and webhooks invalidate the cache and publish SSE
    # updates, so visible pages reload the fragment with fresh data.
    _page_cache_set("course-analytics", course_id, variant, html, ttl=600)
    return respond(html)
