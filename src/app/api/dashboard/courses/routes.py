"""Course detail, roster, and lifecycle routes."""

import uuid

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import noload

from app.api.dashboard._access import (
    _can_manage_course,
    _can_view_course,
    _filter_teams_for_user,
    _membership_role,
    _runs_course,
)
from app.api.dashboard._helpers import (
    _course_data_staleness,
    _csrf_token,
    _extended_checks,
    _feature_disabled_response,
    _not_found_response,
    _role_context,
    _templates,
    logger,
)
from app.api.dashboard._stats import latest_team_metric_map
from app.api.dashboard.courses.activity import course_activity, recent_mrs
from app.api.dashboard.courses.overview import (
    by_light,
    group_contributors,
    light_counts,
    never_synced_count,
    stale_metrics_days,
    team_projects,
    team_sync_states,
)
from app.api.helpers.course_sync_state import last_updated
from app.config import get_settings
from app.dependencies import (
    CSRFCheck,
    DashboardAuth,
    DbSession,
    RateLimitDep,
    TeacherAuth,
)
from app.models.course import Course
from app.models.team import Team
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
from app.services.webhook_activity import compute_webhook_activity

router = APIRouter()


@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_detail(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    settings = get_settings()
    course = await db.get(Course, course_id)
    if not course:
        return _not_found_response(request, "Course")

    # Check access permission
    if not await _can_view_course(course, _auth, db):
        role = _auth.get("role", "student")
        if role == "admin":
            hint = "Check course membership settings."
        elif role == "teacher":
            hint = "Contact the system administrator if you believe you should have access."
        else:
            hint = "Contact your instructor if you believe you should have access."
        return _not_found_response(
            request,
            "Course",
            message="You don't have access to this course.",
            suggestion=hint,
        )

    # Teachers and admins keep soft-deleted groups in the listing (dimmed,
    # restorable). Students keep their OWN archived group visible too, so they
    # can still open it and read their score - ``_filter_teams_for_user``
    # restricts a student to the team(s) they belong to, so they never see
    # other courses' deleted groups.
    course_role = await _membership_role(db, course_id, _auth)
    _can_edit = _runs_course(_auth, course_role)
    stmt = (
        select(Team).where(Team.course_id == course_id).order_by(Team.is_active.desc(), Team.name)
    )
    result = await db.execute(stmt)
    teams = list(result.scalars().all())

    # Filter teams for students (they only see their own team)
    teams = await _filter_teams_for_user(teams, _auth, db)

    # Soft-deleted (archived) groups stay in ``teams`` for display (dimmed,
    # restorable for staff; read-only for the owning student) but they must
    # NOT pollute course-level aggregates: contributor totals, green/red
    # health counts, sync counters and "never synced" warnings all describe
    # the LIVE course. An archived group counting toward them would make the
    # course look unhealthier (or busier) than it is and never clear until a
    # hard delete. Compute every headline metric over active teams only.
    active_teams = [t for t in teams if t.is_active]
    active_team_ids = [t.id for t in active_teams]

    role_ctx = {**_role_context(_auth), "can_edit": _can_edit}

    # -- GitLab-style single-response delivery --
    # The heavy content body is rendered (or cache-hit) and inlined into the
    # full page in ONE response - no deferred HTMX fetch, no full-body placeholder
    # swap. See ``render_inline``.
    #
    # Measured before deciding to keep it that way. Every query below, timed in
    # the production container against the largest course (9 groups):
    #   latest_team_metric_map 3.8ms  team_contributor_counts 11.5ms
    #   total_distinct_contributors 11.0ms  staleness 5.8ms  projects 3.6ms
    #   webhooks 1.8ms  jobs 1.3ms  checks 1.2ms  course+teams 3.9ms
    #   -> 44ms of database work for the whole page, which renders warm in 13ms.
    # Deferring any of that to a second request would cost more than it saves:
    # the round-trip alone is longer than the work. Lazy loading belongs where
    # the wait is real - it is on the images (see components/avatar.html) and on
    # the per-page JS bundles - not here.

    # -- Short-lived Redis cache (60s) for the heavy content body --
    # Course detail aggregates per-team metrics, contributor counts,
    # sync job statuses, webhook activity and project trees - easily
    # 0.5-2s on populous courses. The output varies by locale,
    # viewer role flags, the ``?sort=status`` query param, and the
    # course-membership role. Per-user CSRF / username / nonce are
    # placeholdered and substituted per response.
    _c_sort = request.query_params.get("sort", "")
    # Readers see their own groups; course staff share the full course view.
    _c_variant = _page_cache_role_variant(
        request,
        role_ctx,
        course_role or "",
        _c_sort,
        _auth.get("user", "") if not _can_edit else "",
    )
    _c_cached = _page_cache_get("course", course_id, _c_variant)
    if _c_cached is not None:
        return _render_inline(
            request=request,
            fragment=_c_cached,
            csrf_token=_csrf_token(_auth),
            role_ctx=role_ctx,
            templates=_templates(request),
            page_template="course_detail.html",
            # The page's own actions are rendered by the SHELL now, next to the
            # title, so the shell needs to know who is looking. They used to be
            # a loose button row inside the cached fragment.
            page_ctx={"course": course, "can_edit": _can_edit, "course_role": course_role},
        )

    # Batch-fetch each team's latest metrics snapshot in one query.
    team_metrics = await latest_team_metric_map(db, [t.id for t in teams])
    # Every displayed group, archived ones included, so a dimmed row still
    # shows the count it last had.
    team_contributors = await group_contributors(db, course, [t.id for t in teams])
    sync_status_by_team, sync_counts = await team_sync_states(db, active_team_ids)

    # Archived groups are excluded - they no longer represent live course health.
    green_teams_count, red_teams_count = light_counts(active_teams, team_metrics)
    logger.info(
        "course_detail green=%d red=%d metrics=%d",
        green_teams_count,
        red_teams_count,
        len(team_metrics),
    )

    sort_by_status = request.query_params.get("sort") == "status"
    if sort_by_status:
        teams = by_light(teams, team_metrics)

    projects_by_team = await team_projects(db, teams, _can_edit)
    # Warn teachers when metrics are outdated.
    data_stale_days = stale_metrics_days(team_metrics, active_teams)

    _wh_report = await compute_webhook_activity(db, [course.id] if course else [])
    has_webhook = course is not None and _wh_report.has_webhook(course.id)

    # Check for recent webhook activity (last 48h) to detect broken webhooks
    has_recent_webhook_activity = course is not None and course.id in _wh_report.active

    # Snapshot freshness for the "Showing data from last sync" banner - same helper
    # the Activity/Analytics tabs use, so the main course tab shows the same
    # freshness note (to everyone, not just editors). The template renders it only
    # when the editor-only "Data may be outdated" banner is not already shown.
    (
        _c_is_stale,
        _c_latest_at,
        _c_days_old,
        _c_current_week_groups,
        _c_total_active_groups,
    ) = await _course_data_staleness(db, course_id)

    _c_ctx = {
        **_page_cache_build_ctx(request),
        "request": request,
        "course": course,
        "teams": teams,
        "team_metrics": team_metrics,
        "team_contributors": team_contributors,
        "team_projects": projects_by_team,
        # green/red are counted for the log line above and handed on with it;
        # no template renders them either, but they cost nothing to pass since
        # they are already in hand.
        "green_teams_count": green_teams_count,
        "red_teams_count": red_teams_count,
        "sync_status_by_team": sync_status_by_team,
        **sync_counts,
        "data_stale_days": data_stale_days,
        "never_synced_count": never_synced_count(active_teams, projects_by_team),
        "has_webhook": has_webhook,
        "has_recent_webhook_activity": has_recent_webhook_activity,
        "data_is_stale": _c_is_stale,
        "latest_snapshot_at": _c_latest_at,
        "data_days_old": _c_days_old,
        "current_week_groups": _c_current_week_groups,
        "total_active_groups": _c_total_active_groups,
        "course_role": course_role,
        "feature_multi_tenant": settings.feature_multi_tenant,
        "gitlab_url": settings.gitlab_url,
        "sort_by_status": sort_by_status,
        "csrf_token": _PAGE_CACHE_CSRF,
        "csp_nonce": _PAGE_CACHE_NONCE,
        "checks": await _extended_checks(db, course.id),
        **_page_cache_role_ctx(role_ctx),
    }
    _c_rendered = (
        _templates(request).get_template("partials/course/_detail_content.html").render(_c_ctx)
    )
    _page_cache_set("course", course_id, _c_variant, _c_rendered)
    return _render_inline(
        request=request,
        fragment=_c_rendered,
        csrf_token=_csrf_token(_auth),
        role_ctx=role_ctx,
        templates=_templates(request),
        page_template="course_detail.html",
        page_ctx={"course": course, "can_edit": _can_edit, "course_role": course_role},
    )


@router.get("/courses/{course_id}/live-data")
async def course_live_data(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """The Groups table's rows as JSON, for live DOM updates."""

    course = await db.get(Course, course_id)
    if not course:
        return JSONResponse({"error": "not_found"}, status_code=404)
    if not await _can_view_course(course, _auth, db):
        return JSONResponse({"error": "forbidden"}, status_code=403)

    stmt = select(Team).where(Team.course_id == course_id, Team.is_active.is_(True))
    result = await db.execute(stmt)
    teams = list(result.scalars().all())
    teams = await _filter_teams_for_user(teams, _auth, db)

    team_data = []
    if teams:
        metrics_map = await latest_team_metric_map(db, [t.id for t in teams])
        member_counts = await group_contributors(db, course, [t.id for t in teams])
        sync_states, _counts = await team_sync_states(db, [t.id for t in teams])
        for t in teams:
            snap = metrics_map.get(t.id)
            sync_state = sync_states.get(t.id)
            updated, updated_iso = last_updated(snap, sync_state)
            team_data.append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "members": member_counts.get(t.id, 0),
                    "avg_score": (
                        round(snap.avg_weighted_score * 100)
                        if snap and snap.avg_weighted_score is not None
                        else None
                    ),
                    "traffic_light": snap.overall_traffic_light if snap else None,
                    "sync_status": sync_state,
                    "last_updated": updated,
                    "last_updated_iso": updated_iso,
                }
            )
    # The groups' rows are all the page refreshes: the KPI strip the course
    # totals fed (groups, contributors, green, red) was removed in June, and
    # its counters were being written into elements that no longer exist.
    return JSONResponse({"teams": team_data})


# -- Course Activity Monitor --


@router.get("/courses/{course_id}/projects", include_in_schema=False)
async def course_activity_page_legacy_url(course_id: uuid.UUID) -> RedirectResponse:
    """Permanent redirect from the old path.

    The page is the Activity tab and has always been labelled that way in the
    navigation, but its URL said /projects - so the address bar contradicted the
    page. Existing links and bookmarks keep working through this redirect.
    """
    return RedirectResponse(f"/dashboard/courses/{course_id}/activity", status_code=301)


@router.get("/courses/{course_id}/activity", response_class=HTMLResponse)
async def course_activity_page(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """Activity Monitor - pipeline health and activity across all teams."""

    course = await db.get(Course, course_id)
    if not course:
        return _not_found_response(request, "Course")

    # Check access permission
    if not await _can_view_course(course, _auth, db):
        role = _auth.get("role", "student")
        if role == "admin":
            hint = "Check course membership settings."
        elif role == "teacher":
            hint = "Contact the system administrator if you believe you should have access."
        else:
            hint = "Contact your instructor if you believe you should have access."
        return _not_found_response(
            request,
            "Course",
            message="You don't have access to this course.",
            suggestion=hint,
        )

    course_role = await _membership_role(db, course_id, _auth)
    role_ctx = {**_role_context(_auth), "can_edit": _runs_course(_auth, course_role)}

    # -- GitLab-style single-response delivery -- content inlined into the full
    # page.
    # Only course staff share the full projection; readers cache their own groups.
    _ca_variant = _page_cache_role_variant(
        request, role_ctx, _auth.get("user", "") if not role_ctx["can_edit"] else ""
    )
    _ca_cached = (
        None
        if request.headers.get("cache-control") == "no-cache"
        else _page_cache_get("course-activity", course_id, _ca_variant)
    )
    if _ca_cached is not None:
        return _render_inline(
            request=request,
            fragment=_ca_cached,
            csrf_token=_csrf_token(_auth),
            role_ctx=role_ctx,
            templates=_templates(request),
            page_template="course_activity.html",
            page_ctx={"course": course, "course_role": course_role},
        )

    # Fetch all teams for this course (noload members/projects - not needed here)

    stmt = (
        select(Team)
        .where(Team.course_id == course_id)
        .options(noload(Team.members), noload(Team.projects))
        .order_by(Team.name)
    )
    result = await db.execute(stmt)
    teams = list(result.scalars().all())

    # Filter teams for students (they only see their own team)
    teams = await _filter_teams_for_user(teams, _auth, db)

    activity = await course_activity(db, course, teams)
    # Most active groups first
    team_activity = sorted(activity.rows, key=lambda x: x["mr_count"], reverse=True)

    # Stale-data banner inputs
    (
        _ca_is_stale,
        _ca_latest_at,
        _ca_days_old,
        _ca_current_week_groups,
        _ca_total_active_groups,
    ) = await _course_data_staleness(db, course_id)

    _ca_ctx = {
        **_page_cache_build_ctx(request),
        "request": request,
        "course": course,
        "teams": teams,
        "projects": activity.projects,
        "pipeline_stats": activity.pipeline_stats,
        "team_activity": team_activity,
        "recent_mrs": await recent_mrs(db, activity.projects, activity.mr_cutoff),
        "gitlab_url": get_settings().gitlab_url,
        "data_is_stale": _ca_is_stale,
        "latest_snapshot_at": _ca_latest_at,
        "data_days_old": _ca_days_old,
        "current_week_groups": _ca_current_week_groups,
        "total_active_groups": _ca_total_active_groups,
        "csrf_token": _PAGE_CACHE_CSRF,
        "csp_nonce": _PAGE_CACHE_NONCE,
        **_page_cache_role_ctx(role_ctx),
    }
    _ca_rendered = (
        _templates(request).get_template("partials/course/_activity_content.html").render(_ca_ctx)
    )
    _page_cache_set("course-activity", course_id, _ca_variant, _ca_rendered)
    return _render_inline(
        request=request,
        fragment=_ca_rendered,
        csrf_token=_csrf_token(_auth),
        role_ctx=role_ctx,
        templates=_templates(request),
        page_template="course_activity.html",
        page_ctx={"course": course, "course_role": course_role},
    )


# -- Course Lifecycle (multi-tenant dashboard actions) --


@router.get("/courses/{course_id}/status")
async def course_status(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> JSONResponse:
    """Lightweight course liveness for the read-only banner poll.

    Course pages poll this so a course archived in another tab or by another
    user flips to read-only without a manual refresh. One indexed ``db.get``,
    no heavy work, never cached.
    """
    course = await db.get(Course, course_id)
    if not course or not await _can_view_course(course, _auth, db):
        return JSONResponse({"error": "not_found"}, status_code=404)
    return JSONResponse(
        {
            "is_active": bool(course.is_active),
            "archived_at": course.archived_at.isoformat() if course.archived_at else None,
        },
        headers={"Cache-Control": "no-store"},
    )


@router.post("/courses/{course_id}/archive")
async def course_archive_ui(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    # Access control
    course = await db.get(Course, course_id)
    if not course or not await _can_manage_course(course, _auth, db):
        return _not_found_response(request, "Course", message="Access denied.")

    settings = get_settings()
    if not settings.feature_multi_tenant:
        return _feature_disabled_response(
            request,
            "Course Archiving (Multi-tenant)",
            "Course archiving requires multi-tenant mode to be enabled.",
            "FEATURE_MULTI_TENANT=true",
        )

    from app.services.courses import archive_course

    await archive_course(db, course_id, actor=_auth.get("user", "system"))
    return Response(status_code=303, headers={"Location": "/dashboard/"})


@router.post("/courses/{course_id}/activate")
async def course_activate_ui(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    # Access control
    course = await db.get(Course, course_id)
    if not course or not await _can_manage_course(course, _auth, db):
        return _not_found_response(request, "Course", message="Access denied.")

    settings = get_settings()
    if not settings.feature_multi_tenant:
        return _feature_disabled_response(
            request,
            "Course Activation (Multi-tenant)",
            "Course activation requires multi-tenant mode to be enabled.",
            "FEATURE_MULTI_TENANT=true",
        )

    from app.services.courses import activate_course

    await activate_course(db, course_id)
    return Response(status_code=303, headers={"Location": "/dashboard/"})
