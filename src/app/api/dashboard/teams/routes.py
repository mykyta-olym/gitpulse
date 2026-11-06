"""Team detail, live data, LLM analysis, and export routes."""

import uuid
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dashboard._access import _can_manage_team, _can_view_team
from app.api.dashboard._helpers import (
    _csrf_token,
    _extended_checks,
    _not_found_response,
    _role_context,
    _templates,
    _threshold_pcts,
    logger,
)
from app.api.dashboard._roster import member_roles
from app.api.dashboard._stats import latest_student_metric_map
from app.api.dashboard.teams.detail import (
    llm_analyses,
    student_primary_projects,
    template_only_projects,
)
from app.api.dashboard.teams.member_exclusion import (
    find_active_scoring_job,
    invalidate_member_scoring_views,
    lock_member_scoring_scope,
    member_base_category,
    member_can_toggle_scoring,
    member_visible_category,
    recompute_after_member_scoring_toggle,
)
from app.config import get_settings
from app.dependencies import CSRFCheck, DashboardAuth, DbSession, TeacherAuth
from app.models.course import Course
from app.models.metric_snapshot import MetricSnapshot
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_metric_snapshot import TeamMetricSnapshot
from app.services.page_cache import (
    CSP_NONCE_PLACEHOLDER as _PAGE_CACHE_NONCE,
)
from app.services.page_cache import (
    CSRF_PLACEHOLDER as _PAGE_CACHE_CSRF,
)
from app.services.page_cache import (
    build_cache_render_ctx as _page_cache_build_ctx,
)
from app.services.page_cache import (
    cacheable_role_ctx as _page_cache_role_ctx,
)
from app.services.page_cache import (
    get_cached as _page_cache_get,
)
from app.services.page_cache import (
    make_role_variant as _page_cache_role_variant,
)
from app.services.page_cache import (
    render_inline as _render_inline,
)
from app.services.page_cache import (
    set_cached as _page_cache_set,
)

router = APIRouter()

from app.api.dashboard.teams.llm import router as _llm_router  # noqa: E402

router.include_router(_llm_router)


# -- Load Team Data Helper --


async def _load_team_data(
    db: DbSession,
    team_id: uuid.UUID,
    include_inactive: bool = False,
) -> tuple[
    Team | None,
    Course | None,
    list[Student],
    dict[uuid.UUID, MetricSnapshot],
    TeamMetricSnapshot | None,
    list[GitLabProject],
]:
    """Load all team data needed for detail page and exports.

    Returns None as first element if team not found, allowing callers
    to show a friendly 'not found' page.
    """
    stmt = select(Team).where(Team.id == team_id).options(selectinload(Team.members))
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if not team:
        return None, None, [], {}, None, []

    course = await db.get(Course, team.course_id)

    # Include ALL active members - client-side filter bar handles visibility
    # (core / inherited / teacher / observer categories)
    all_member_ids = [m.student_id for m in team.active_members]
    students: list[Student] = []
    if all_member_ids:
        s_stmt = select(Student).where(Student.id.in_(all_member_ids))
        s_result = await db.execute(s_stmt)
        students = list(s_result.scalars().all())
        # GitLab project/group bots (project_<id>_bot_*, etc.) sometimes
        # leak into the team roster - they live under User Management,
        # not the member table.  Strip them up-front so the Members
        # table, scoring cohort and Issues to Address all agree.
        from app.services.gitlab_import.helpers import is_bot_user as _is_bot_user

        students = [
            s for s in students if not (s.gitlab_username and _is_bot_user(s.gitlab_username))
        ]
        # Group Members shows STUDENTS only - never teachers, mentors or a
        # Project Manager. Drop anyone flagged teacher/mentor on their team
        # membership so instructors do not appear in the roster.
        _member_by_student = {m.student_id: m for m in team.active_members}
        students = [
            s
            for s in students
            if not (
                getattr(_member_by_student.get(s.id), "is_teacher", False)
                or getattr(_member_by_student.get(s.id), "is_mentor", False)
            )
        ]
    snapshots = await latest_student_metric_map(db, [s.id for s in students], team_id)

    tm_stmt = (
        select(TeamMetricSnapshot)
        .where(TeamMetricSnapshot.team_id == team_id)
        .order_by(TeamMetricSnapshot.computed_at.desc())
        .limit(1)
    )
    tm_result = await db.execute(tm_stmt)
    team_metric = tm_result.scalar_one_or_none()

    # Admins (``include_inactive``) keep soft-deleted/unlinked projects in the
    # listing so they can review and restore them; everyone else only sees
    # active projects. Active rows sort first so deleted ones sink to the
    # bottom of the (dimmed) list.
    #
    # GitLab renames a project to ``<path>-<hash>-deletion_scheduled-<id>`` when
    # it is scheduled for deletion on GitLab's side. Those tombstones are not
    # teacher-managed "unlinked" projects and must never appear as restorable
    # ghost rows, so filter them out of every listing (active or not).
    p_stmt = select(GitLabProject).where(
        GitLabProject.team_id == team_id,
        ~GitLabProject.gitlab_project_path.contains("deletion_scheduled", autoescape=True),
    )
    if not include_inactive:
        p_stmt = p_stmt.where(GitLabProject.is_active.is_(True))
    p_stmt = p_stmt.order_by(
        GitLabProject.is_active.desc(),
        GitLabProject.gitlab_project_path,
    )
    p_result = await db.execute(p_stmt)
    projects = list(p_result.scalars().all())

    return team, course, students, snapshots, team_metric, projects


# -- Team Detail --


@router.get("/teams/{team_id}", response_class=HTMLResponse)
async def team_detail(
    team_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    team, course, students, snapshots, team_metric, projects = await _load_team_data(
        db, team_id, include_inactive=True
    )
    if not team:
        return _not_found_response(request, "Group")

    # Check access permission
    if not await _can_view_team(team, _auth, db):
        return _not_found_response(
            request,
            "Group",
            message="You don't have access to this group.",
            suggestion="You can only view groups you are a member of.",
        )

    role_ctx = {**_role_context(_auth), "can_edit": await _can_manage_team(team, _auth, db)}
    if not role_ctx["can_edit"]:
        projects = [project for project in projects if project.is_active]

    # -- GitLab-style single-response delivery -- content inlined into the full
    # page.
    # -- Content body: short Redis cache --
    # Team detail aggregates extended checks, LLM analyses, contributor
    # counts and webhook activity - easily 1-2s per request on a
    # populous team. The rendered HTML only varies by locale and the
    # viewer's role flags, so it is safe to cache and share across
    # users at the same permission level. Per-user fields are rendered
    # as placeholders and substituted by :func:`personalize`.
    _t_variant = _page_cache_role_variant(request, role_ctx)
    _t_cached = _page_cache_get("team", team_id, _t_variant)
    if _t_cached is not None:
        return _render_inline(
            request=request,
            fragment=_t_cached,
            csrf_token=_csrf_token(_auth),
            role_ctx=role_ctx,
            templates=_templates(request),
            page_template="team_detail.html",
            page_ctx={"team": team, "course": course},
        )

    # Build membership map and user roles for badge display
    memberships: dict[uuid.UUID, Any] = {m.student_id: m for m in team.active_members}

    user_roles, course_roles = await member_roles(db, students, course)
    llm_enabled = get_settings().llm_analysis_enabled
    team_llm_analyses = await llm_analyses(db, projects) if llm_enabled else []

    cs = course.settings if course else None
    green_pct, yellow_pct = _threshold_pcts(cs)

    _t_ctx = {
        **_page_cache_build_ctx(request),
        "request": request,
        "team": team,
        "course": course,
        "students": students,
        "snapshots": snapshots,
        "memberships": memberships,
        "user_roles": user_roles,
        "course_roles": course_roles,
        "team_metric": team_metric,
        "projects": projects,
        "checks": await _extended_checks(db, course.id if course else None),
        "feature_llm_suggestions": llm_enabled,
        "llm_analyses": team_llm_analyses,
        "template_project_ids": await template_only_projects(db, course, projects, students),
        "student_project_map": await student_primary_projects(db, course, projects, students),
        "gitlab_url": get_settings().gitlab_url,
        "csrf_token": _PAGE_CACHE_CSRF,
        "csp_nonce": _PAGE_CACHE_NONCE,
        "green_pct": green_pct,
        "yellow_pct": yellow_pct,
        **_page_cache_role_ctx(role_ctx),
    }
    _t_rendered = (
        _templates(request).get_template("partials/team/_detail_content.html").render(_t_ctx)
    )
    _page_cache_set("team", team_id, _t_variant, _t_rendered)
    return _render_inline(
        request=request,
        fragment=_t_rendered,
        csrf_token=_csrf_token(_auth),
        role_ctx=role_ctx,
        templates=_templates(request),
        page_template="team_detail.html",
        page_ctx={"team": team, "course": course},
    )


# -- Team Detail Live Data (JSON) --


@router.get("/teams/{team_id}/live-data")
async def team_live_data(
    team_id: uuid.UUID,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """Return metrics for the member rows visible to this viewer."""
    team, _course, students, snapshots, _team_metric, _projects = await _load_team_data(db, team_id)
    if not team:
        return JSONResponse({"error": "not_found"}, status_code=404)

    if not await _can_view_team(team, _auth, db):
        return JSONResponse({"error": "forbidden"}, status_code=403)

    if _auth.get("role") == "student" and not await _can_manage_team(team, _auth, db):
        return JSONResponse({"students": []})

    memberships_by_student = {m.student_id: m for m in team.active_members}

    # Student check data
    students_data = []
    for s in sorted(students, key=lambda x: x.full_name or x.gitlab_username or ""):
        snap = snapshots.get(s.id)
        membership = memberships_by_student.get(s.id)
        students_data.append(
            {
                "id": str(s.id),
                "excluded_from_scoring": (
                    bool(membership.excluded_from_scoring) if membership else False
                ),
                "member_category": (
                    member_visible_category(membership) if membership else "direct"
                ),
                "member_base_category": (
                    member_base_category(membership) if membership else "direct"
                ),
                "score": (
                    round(snap.weighted_score * 100)
                    if snap and snap.weighted_score is not None
                    else None
                ),
                "checks_passed": snap.checks_passed if snap else 0,
                "checks_total": snap.checks_total if snap else 0,
                "mrs_created": snap.mrs_created if snap else 0,
                "issues_assigned": snap.issues_assigned if snap else 0,
                "pipeline_success": snap.pipeline_success_count if snap else 0,
                "pipeline_total": snap.pipeline_total_count if snap else 0,
            },
        )

    return JSONResponse(
        {
            "students": students_data,
        },
    )


# -- Member Exclusion Toggle --


@router.post("/teams/{team_id}/members/{student_id}/toggle-exclusion")
async def toggle_member_exclusion(
    team_id: uuid.UUID,
    student_id: uuid.UUID,
    db: DbSession,
    _auth: TeacherAuth,
    _csrf: CSRFCheck,
) -> Response:
    """Toggle excluded_from_scoring for a team member.

    When excluded, the student's individual snapshot is still computed
    but is NOT counted in the team aggregate score - same as teachers.
    """
    team = await db.get(Team, team_id)
    if not team:
        return JSONResponse({"error": "not_found"}, status_code=404)
    if not await _can_manage_team(team, _auth, db):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    # An archived course is read-only: reject scoring-membership changes even if
    # a stale client still shows the control enabled.
    _course = await db.get(Course, team.course_id)
    if _course is not None and not _course.is_active:
        return JSONResponse(
            {
                "error": "course_archived",
                "message": (
                    "This course is archived and read-only. Reactivate it to make changes."
                ),
            },
            status_code=403,
        )

    await lock_member_scoring_scope(db, team_id)
    active_job = await find_active_scoring_job(db, team_id)
    if active_job is not None:
        return JSONResponse(
            {
                "error": "scoring_locked",
                "message": (
                    "Scoring membership is locked while sync or checks are running. "
                    "Wait for the active process to finish, then try again."
                ),
                "job_type": active_job.job_type,
                "job_status": active_job.status,
                "job_id": str(active_job.id),
            },
            status_code=409,
        )

    stmt = (
        select(TeamMember)
        .where(
            TeamMember.team_id == team_id,
            TeamMember.student_id == student_id,
            TeamMember.is_active.is_(True),
        )
        .with_for_update()
    )
    result = await db.execute(stmt)
    tm = result.scalar_one_or_none()
    if not tm:
        return JSONResponse({"error": "member_not_found"}, status_code=404)
    if not member_can_toggle_scoring(tm):
        return JSONResponse(
            {
                "error": "role_already_excluded",
                "message": (
                    "This member is already excluded from team scoring by role. "
                    "Teachers and mentors do not need the scoring toggle."
                ),
                "member_category": member_visible_category(tm),
                "member_base_category": member_base_category(tm),
            },
            status_code=409,
        )

    # Toggle
    _old_excluded = tm.excluded_from_scoring
    tm.excluded_from_scoring = not tm.excluded_from_scoring
    await db.flush()

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="member_exclusion_toggled",
        # The USERNAME, like every other audit write. `user_id` is the session's
        # id field, which on the OAuth path is GitLab's numeric user id - the
        # activity feed then showed rows as a bare number ("0001 - ...").
        actor=str(_auth.get("user") or _auth.get("gitlab_username") or "system"),
        entity_type="team_member",
        entity_id=team_id,
        detail={
            "student_id": str(student_id),
            "excluded_from_scoring": tm.excluded_from_scoring,
            "previous": _old_excluded,
        },
    )

    logger.info(
        "member_exclusion_toggled",
        team_id=str(team_id),
        student_id=str(student_id),
        excluded=tm.excluded_from_scoring,
    )
    await recompute_after_member_scoring_toggle(db, team_id=team_id)
    invalidated = await invalidate_member_scoring_views(
        db,
        team_id=team_id,
        course_id=team.course_id,
        student_ids=[student_id],
    )
    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update(
            "team",
            str(team_id),
            "member_exclusion_toggled",
            extra={"student_id": str(student_id), "excluded": tm.excluded_from_scoring},
        )
        publish_dashboard_update(
            "course",
            str(team.course_id),
            "member_exclusion_toggled",
            extra={"team_id": str(team_id), "student_id": str(student_id)},
        )
    return JSONResponse(
        {
            "excluded_from_scoring": tm.excluded_from_scoring,
            "student_id": str(student_id),
            "member_category": member_visible_category(tm),
            "member_base_category": member_base_category(tm),
            "metrics_recomputed": True,
            "cache_invalidated": invalidated,
        }
    )
