"""Dashboard home page, stats, sidebar badges, and global search."""

import contextlib
import json as _json
import uuid
from typing import Any

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy import func as _fn
from sqlalchemy import func as sa_fn
from sqlalchemy.orm import load_only, selectinload

from app.api.dashboard._access import (
    _ensure_session_user_in_db,
    _filter_courses_for_user,
)
from app.api.dashboard._helpers import (
    _csrf_token,
    _pop_notifications,
    _role_context,
    _templates,
    logger,
)
from app.api.dashboard.home.activity import _build_activity_feed
from app.api.dashboard.home.attention import _build_attention_items
from app.api.dashboard.home.changelog import _get_changelog_entries
from app.api.dashboard.home.context import (
    _build_admin_context,
    _build_sidebar_badges,
    _build_student_context,
    _greeting_word,
)
from app.api.dashboard.home.course_health import _build_course_health
from app.api.dashboard.home.quick_access import _build_quick_access
from app.api.dashboard.home.stats import (
    _build_stat_cards,
    _count_red_teams,
)
from app.api.dashboard.home.sync_info import _load_course_sync_info
from app.config import get_settings
from app.dependencies import DashboardAuth, DbSession
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.academic_periods import (
    ALL_PERIODS,
    count_students,
    courses_in_scope,
    period_scope_context,
    requested_period,
)
from app.services.greeting_phrase import get_phrase as get_greeting_phrase
from app.utils.constants import PAGE_SIZE_SEARCH

router = APIRouter()


@router.get("/status", response_class=RedirectResponse)
async def status_redirect(auth: DashboardAuth) -> Response:
    """Keep old bookmarks useful without exposing admin diagnostics to other roles."""
    target = "/dashboard/admin/system" if auth.get("role") == "admin" else "/dashboard/"
    return RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store"})


async def _scoped_courses(
    request: Request, db: DbSession, reader_courses: list[Course]
) -> tuple[list[Course], dict[str, object]]:
    """The reader's courses in the academic period on screen, and that scope.

    ONE call for the page and for all three of its live refreshers - stats,
    attention items and the activity feed. Each used to be free to scope, or
    not, on its own, and the stats and the feed did not: on the first SSE push
    or tab return the KPI cards and the feed switched from the term on screen
    to every term at once, beside a course grid that still showed one. The
    refreshers read the period from the same query parameter the page does, and
    the page's JavaScript passes it on.

    The default is computed from the courses THIS reader can see, not the whole
    database: a student whose only course is last summer's must open on last
    summer, not on whatever newer term somebody else's course is in.
    """
    scope = await period_scope_context(
        db,
        requested_period(request),
        include_none=False,
        visible_courses=reader_courses,
    )
    return courses_in_scope(reader_courses, scope), scope


async def _students_in_view(
    db: DbSession, role: str, scope: dict[str, object], scoped: list[Course]
) -> int:
    """The "Students" card: the students of the courses on screen.

    An administrator looking at every period sees every registered student -
    the figure User Management shows for the same view; everyone else sees the
    students of the courses in front of them.
    """
    if role == "admin" and scope.get("selected_key") == ALL_PERIODS:
        return await count_students(db, None)
    return await count_students(db, [c.id for c in scoped])


def _other_period(
    reader_courses: list[Course], period_scope: dict[str, Any]
) -> dict[str, Any] | None:
    """The newest OTHER term holding the reader's courses: where an empty term
    points them ("Show 2025/2026 - Summer")."""
    from app.services.academic_periods import periods_of

    others = [p for p in periods_of(reader_courses) if p.key != period_scope.get("selected_key")]
    if not others or period_scope.get("selected_key") == ALL_PERIODS:
        return None
    return {
        "key": others[0].key,
        "academic_year": others[0].academic_year,
        "semester": others[0].semester,
    }


async def _auto_archive_sweep(settings: Any) -> None:
    """Archive the courses whose semester has ended - from the staff dashboard."""
    # Opportunistic semester-end auto-archive. No cron/scheduler daemon runs
    # (workers start with_scheduler=False), so the staff dashboard is what makes
    # the "Auto-archives <date>" promise actually happen. We run the sweep INLINE
    # here (own throwaway session, not the request's db, and not a worker job -
    # the worker fork + asyncio.run path was an extra failure surface that left
    # nothing archived). A Redis SET NX EX lock throttles it to at most once per
    # ~15 min across all staff; on any error the lock is dropped so the next load
    # retries. Idempotent + wrapped so it never blocks or fails the dashboard.
    _lock_key = "gp:auto_archive_sweep_v2"
    try:
        from app.redis_pool import get_redis

        _redis = get_redis()
        if _redis.set(_lock_key, "1", nx=True, ex=900):
            try:
                from app.db.session import async_session_ctx
                from app.workers.sweep_auto_archive import archive_due_courses

                async with async_session_ctx() as _sweep_session:
                    _n = await archive_due_courses(_sweep_session, settings)
                if _n:
                    logger.info("auto_archive_sweep_inline archived=%d", _n)
            except Exception:
                # Release the lock so the next dashboard load retries instead
                # of waiting out the full throttle window after a failure.
                with contextlib.suppress(Exception):
                    _redis.delete(_lock_key)
                logger.warning("auto_archive_sweep_inline_failed", exc_info=True)
    except Exception:
        logger.debug("auto_archive_sweep_trigger_skipped", exc_info=True)


async def _live_group_count(db: Any, course_ids: list[uuid.UUID]) -> int:
    """The headline "Groups" counter. Soft-deleted (unlinked/archived) groups
    must NOT inflate it - it describes live groups only, so a deleted group
    drops out immediately instead of lingering."""
    result = await db.execute(
        select(func.count(Team.id)).where(
            Team.course_id.in_(course_ids),
            Team.is_active.is_(True),
        )
    )
    return result.scalar() or 0


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: DbSession, _auth: DashboardAuth) -> Response:

    role_ctx = _role_context(_auth)
    role = role_ctx["user_role"]
    _settings = get_settings()

    # Preferences > Behavior > "Homepage". Only on a real navigation: an HTMX
    # request is the app swapping the dashboard in, and redirecting that would
    # take the reader somewhere they did not click.
    # homepage_redirect_for() re-checks the role, so a demoted teacher whose
    # pinned page is now closed to them falls back here instead of bouncing off
    # the role gate on every sign-in.
    if not request.headers.get("HX-Request"):
        from app.api.dashboard.preferences import homepage_redirect_for

        target = homepage_redirect_for(role, _auth.get("default_homepage"))
        if target:
            return RedirectResponse(url=target, status_code=303)

    # Ensure session user exists in DB (self-healing after DB restart/wipe)
    try:
        await _ensure_session_user_in_db(db, _auth)
    except Exception:
        logger.debug("ensure_session_user_skipped", exc_info=True)

    # -- Content: heavy queries --

    # All courses
    stmt = select(Course).order_by(Course.academic_year.desc(), Course.semester, Course.code)
    result = await db.execute(stmt)
    all_courses = list(result.scalars().all())

    # Filter courses based on user's access
    all_courses = await _filter_courses_for_user(all_courses, _auth, db)

    # -- Academic period scope --
    # Everything below - the cards, the KPIs, the at-risk counts - is derived
    # from `active_ids`, so scoping the list here scopes the whole page and the
    # numbers can never describe a different term than the cards beside them.
    reader_courses = all_courses
    all_courses, period_scope = await _scoped_courses(request, db, reader_courses)
    # Whether the reader has ANY course, in any term - archived ones count.
    # When the chosen term is empty but this is true, the page must still draw
    # the section header - the selector lives in it - instead of the "create
    # your first course" onboarding, which would both mislead and strand the
    # reader on an empty term with no control left to leave it by. It counted
    # ACTIVE courses only, so once every course was archived (a finished term)
    # the selector vanished and the archived courses could not be reached.
    has_courses_elsewhere = bool(reader_courses)
    other_period = _other_period(reader_courses, period_scope)

    active_courses = [c for c in all_courses if c.is_active]
    archived_courses = [c for c in all_courses if not c.is_active]

    # Group active by year/semester
    grouped: dict[str, list[Course]] = {}
    for c in active_courses:
        key = f"{c.academic_year} - {c.semester}"
        grouped.setdefault(key, []).append(c)

    active_ids = [c.id for c in active_courses]

    # total_teams / total_students populate the admin & teacher "Groups" and
    # "Students" stat cards only. The student dashboard uses neither (student
    # cards come from _build_student_stat_cards, and no template reads the raw
    # context vars), so both counts are skipped entirely for students - two fewer
    # queries on every student dashboard load, the majority case.
    is_staff = role in ("admin", "teacher")

    if is_staff:
        await _auto_archive_sweep(_settings)

    total_teams = await _live_group_count(db, active_ids) if is_staff and active_ids else 0

    # Load actual teams for Quick Access sidebar (teacher/admin)

    qa_teams: list[Team] = []
    qa_projects: list[GitLabProject] = []
    qa_team_meta: dict[uuid.UUID, dict[str, Any]] = {}
    if role in ("admin", "teacher") and active_ids:
        qa_teams, qa_projects, qa_team_meta = await _build_quick_access(db, active_ids)

    total_students = 0
    if is_staff:
        total_students = await _students_in_view(db, role, period_scope, all_courses)

    # Per-course sync status for dashboard badges (running/queued/total/
    # synced) - see _load_course_sync_info docstring for semantics.
    course_sync_info = await _load_course_sync_info(active_ids, db)

    # -- Role-based stat cards --
    # Pre-compute expensive queries shared across helpers
    red_teams_count: int | None = None
    if role in ("admin", "teacher") and active_ids:
        red_teams_count = await _count_red_teams(active_ids, db)

    stat_cards = await _build_stat_cards(
        role,
        active_courses,
        active_ids,
        db,
        _auth,
        total_teams=total_teams,
        total_students=total_students,
        period_key=str(period_scope["selected_key"]),
    )

    # -- Items that need your attention --
    locale = getattr(request.state, "locale", "sk")
    attention_items = await _build_attention_items(
        role,
        active_ids,
        course_sync_info,
        db,
        _auth,
        locale=locale,
        red_teams_count=red_teams_count,
        active_courses=active_courses,
        archived_courses=archived_courses,
        lifecycle_courses=reader_courses,
    )

    # -- Recent activity (role-filtered) --
    recent_activity = await _build_activity_feed(
        role,
        active_ids,
        db,
        _auth,
        archived_ids=[c.id for c in archived_courses],
        locale=locale,
        courses=all_courses,
    )

    # -- Student-specific context (compliance, team info, deadlines) --
    student_ctx: dict[str, Any] = {}
    if role == "student":
        student_ctx = await _build_student_context(active_ids, db, _auth)

    # -- Admin system snapshot --
    admin_ctx: dict[str, Any] = {}
    if role in ("admin", "teacher"):
        admin_ctx = await _build_admin_context(db)

    # -- Course-level traffic lights for teacher/admin cards --
    course_health: dict[str, Any] = {}
    if role in ("admin", "teacher") and active_ids:
        course_health = await _build_course_health(active_ids, db)

    # -- Changelog entries for sidebar widget --
    changelog_entries = _get_changelog_entries(locale=locale)

    _dash_ctx = {
        "request": request,
        "active_courses": active_courses,
        "archived_courses": archived_courses,
        "grouped_courses": grouped,
        "period_scope": period_scope,
        "has_courses_elsewhere": has_courses_elsewhere,
        "other_period": other_period,
        # Import INTO an existing course is not about the term on screen: the
        # target list offers every active course the reader has, in any term.
        "import_target_courses": [c for c in reader_courses if c.is_active],
        "total_teams": total_teams,
        "total_students": total_students,
        "qa_teams": qa_teams,
        "qa_projects": qa_projects,
        "qa_team_meta": qa_team_meta,
        "course_sync_info": course_sync_info,
        "recent_activity": recent_activity,
        "stat_cards": stat_cards,
        "attention_items": attention_items,
        "student_ctx": student_ctx,
        "admin_ctx": admin_ctx,
        "course_health": course_health,
        "changelog_entries": changelog_entries,
        "greeting_word": _greeting_word(locale=getattr(request.state, "locale", "sk")),
        # A cached read and nothing else - a miss returns None and the heading
        # falls back to the greeting word above. See services/greeting_phrase.py.
        "greeting_phrase": get_greeting_phrase(),
        "csrf_token": _csrf_token(_auth),
        "llm_enabled": _settings.llm_analysis_enabled,
        **role_ctx,
    }
    return _templates(request).TemplateResponse(request, "dashboard.html", _dash_ctx)


@router.get("/stats", response_class=JSONResponse)
async def dashboard_stats(request: Request, db: DbSession, _auth: DashboardAuth) -> Response:
    """Lightweight JSON stats for live-updating the dashboard counters.

    Returns role-specific stat card values so the JS refreshDashboardStats()
    can update whichever cards are visible for the current user.

    Short-TTL Redis cache (5 s) collapses burst calls - SSE update + job-complete
    fallback + visibilitychange can all arrive within a 3 s window.  5 s staleness
    is imperceptible and the next SSE push will trigger a fresh cache-miss anyway.
    """

    from app.redis_pool import get_redis as _get_redis

    role = _auth.get("role", "student")
    # The period is part of the key: two tabs on two terms must not answer
    # each other's polls.
    _period_param = (requested_period(request) or "").strip()[:32]
    _cache_key = f"dashboard:stats:{_auth.get('user', '')}:{role}:{_period_param}"
    with contextlib.suppress(Exception):
        _cached = _get_redis().get(_cache_key)
        if _cached:
            return JSONResponse(_json.loads(_cached))

    stmt = select(Course).order_by(Course.code)
    result = await db.execute(stmt)
    reader_courses = list(result.scalars().all())
    reader_courses = await _filter_courses_for_user(reader_courses, _auth, db)
    all_courses, _scope = await _scoped_courses(request, db, reader_courses)
    active_courses = [c for c in all_courses if c.is_active]
    active_ids = [c.id for c in active_courses]

    # Counts feed the admin/teacher stat cards only; students never use them,
    # so skip both queries for students (this endpoint is polled on SSE / tab
    # return, so the saving recurs).

    _total_teams = 0
    _total_students = 0
    if role in ("admin", "teacher"):
        _teams_r = await db.execute(
            select(_fn.count(Team.id)).where(
                Team.course_id.in_(active_ids),
                Team.is_active.is_(True),
            )
        )
        _total_teams = _teams_r.scalar() or 0
        _total_students = await _students_in_view(db, role, _scope, all_courses)

    stat_cards = await _build_stat_cards(
        role,
        active_courses,
        active_ids,
        db,
        _auth,
        total_teams=_total_teams,
        total_students=_total_students,
        period_key=str(_scope["selected_key"]),
    )

    payload: dict[str, Any] = {card["id"]: card["value"] for card in stat_cards}
    # Ship the tone alongside the number. A poll that refreshed a compliance
    # score without its state would leave a card coloured for the OLD value -
    # green over a number that just fell into the red band.
    payload["_states"] = {c["id"]: c.get("state", "") for c in stat_cards}

    # Include per-course health for live course-card badge updates
    if role in ("teacher", "admin") and active_ids:
        payload["_course_health"] = await _build_course_health(active_ids, db)

    with contextlib.suppress(Exception):
        _get_redis().setex(_cache_key, 5, _json.dumps(payload, default=str))

    return JSONResponse(payload)


@router.get("/attention-items", response_class=HTMLResponse)
async def dashboard_attention_items(
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """Return rendered attention-items HTML fragment for live refresh."""

    role = _auth.get("role", "student")

    stmt = (
        select(Course)
        .options(
            load_only(
                Course.id,
                Course.code,
                Course.name,
                Course.is_active,
                # `archived_at` is what the lifecycle suggestions are built
                # from ("archived over 2 years ago", "reactivate?"). Leaving
                # it out meant this fragment quietly produced a SHORTER list
                # than the page it refreshes, so the card lost an item - and
                # 91px of height - the moment the tab regained focus.
                Course.archived_at,
                # And `academic_year` is what the "new academic year started -
                # reactivate?" suggestion compares against, so it has to come
                # along too. The load list has to carry every column the
                # attention builder reads, not just the ones the card shows.
                Course.academic_year,
                Course.semester,
            ),
        )
        .order_by(Course.code)
    )
    result = await db.execute(stmt)
    reader_courses = list(result.scalars().all())
    reader_courses = await _filter_courses_for_user(reader_courses, _auth, db)
    # The same period scope the page load applied, by the same function.
    all_courses, _scope = await _scoped_courses(request, db, reader_courses)
    active_courses = [c for c in all_courses if c.is_active]
    archived_courses = [c for c in all_courses if not c.is_active]
    active_ids = [c.id for c in active_courses]

    # Lightweight sync info (same as dashboard page load).
    course_sync_info = await _load_course_sync_info(active_ids, db)

    # The page load passes this too. Leaving it out here meant the live
    # refresh built a SHORTER list than the one the reader was looking at: the
    # "groups in the red" item is only produced when the count is supplied, so
    # it vanished on the first refresh - measured as the card losing a child
    # and 91px of height the moment the tab regained focus.
    red_teams_count: int | None = None
    if role in ("admin", "teacher") and active_ids:
        red_teams_count = await _count_red_teams(active_ids, db)

    locale = getattr(request.state, "locale", "sk")
    attention_items = await _build_attention_items(
        role,
        active_ids,
        course_sync_info,
        db,
        _auth,
        locale=locale,
        red_teams_count=red_teams_count,
        active_courses=active_courses,
        archived_courses=archived_courses,
        lifecycle_courses=reader_courses,
    )

    tpl = _templates(request).get_template("partials/dashboard/_attention_items.html")
    html = tpl.render({"request": request, "attention_items": attention_items})
    return HTMLResponse(html)


@router.get("/activity", response_class=HTMLResponse)
async def dashboard_activity(
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    """Return the rendered "Follow the latest updates" feed fragment.

    Lets the dashboard refresh the activity feed live (on SSE push / poll /
    tab-return) without a full page reload, so lifecycle events - group or
    project deletion and restoration, syncs, pipeline runs - appear as they
    happen.
    """

    role_ctx = _role_context(_auth)
    role = role_ctx["user_role"]

    stmt = (
        select(Course)
        .options(
            load_only(
                Course.id,
                Course.code,
                Course.name,
                Course.is_active,
                # The period columns, so the feed can be scoped like the page.
                Course.academic_year,
                Course.semester,
                # What the "Course created" / "Course archived" rows are
                # derived from. Without them each refresh raised on the lazy
                # load, and a swallowing try hid it: the rows the page showed
                # vanished on the first refresh.
                Course.created_at,
                Course.archived_at,
            ),
        )
        .order_by(Course.code)
    )
    result = await db.execute(stmt)
    reader_courses = list(result.scalars().all())
    reader_courses = await _filter_courses_for_user(reader_courses, _auth, db)
    # The same period the page shows - a feed that refreshed across every term
    # replaced the term's events with the whole installation's on tab return.
    all_courses, _scope = await _scoped_courses(request, db, reader_courses)
    active_courses = [c for c in all_courses if c.is_active]
    active_ids = [c.id for c in active_courses]
    _archived_ids = [c.id for c in all_courses if not c.is_active]

    locale = getattr(request.state, "locale", "sk")
    recent_activity = await _build_activity_feed(
        role, active_ids, db, _auth, archived_ids=_archived_ids, locale=locale, courses=all_courses
    )

    tpl = _templates(request).get_template("partials/dashboard/_activity_feed.html")
    html = tpl.render(
        {
            "request": request,
            "recent_activity": recent_activity,
            "active_courses": active_courses,
            "has_courses_elsewhere": bool(reader_courses),
            **role_ctx,
        },
    )
    return HTMLResponse(html)


@router.get("/sidebar-badges", response_class=JSONResponse)
async def sidebar_badges_api(db: DbSession, _auth: DashboardAuth) -> Response:
    """Lightweight JSON endpoint for live-updating sidebar badge counts.

    Returns role-specific badge counts so the JS SidebarBadgeController
    can update counters dynamically without full page reload.

    Short-TTL Redis cache (5 s) collapses burst calls from simultaneous
    SSE updates, job completions, and tab-return events.
    """

    from app.redis_pool import get_redis as _get_redis

    role = _auth.get("role", "student")
    _cache_key = f"dashboard:badges:{_auth.get('user', '')}:{role}"
    with contextlib.suppress(Exception):
        _cached = _get_redis().get(_cache_key)
        if _cached:
            return JSONResponse(_json.loads(_cached))

    stmt = (
        select(Course)
        .options(
            load_only(Course.id, Course.code, Course.is_active),
        )
        .order_by(Course.code)
    )
    result = await db.execute(stmt)
    all_courses = list(result.scalars().all())
    all_courses = await _filter_courses_for_user(all_courses, _auth, db)
    active_courses = [c for c in all_courses if c.is_active]
    active_ids = [c.id for c in active_courses]

    badges = await _build_sidebar_badges(role, active_ids, db)
    with contextlib.suppress(Exception):
        _get_redis().setex(_cache_key, 5, _json.dumps(badges, default=str))
    return JSONResponse(badges)


@router.get("/search", response_class=JSONResponse)
async def global_search(
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
    q: str = Query("", max_length=200),
    scope: str = Query("all", pattern="^(all|pages|users|courses|students)$"),
) -> Response:
    """Global search endpoint - returns users, courses, teams, students matching *q*.

    Scopes
    ------
    * ``all``      - hybrid search across all entity types
    * ``pages``    - client-side only (no backend work)
    * ``users``    - system users (admin/teacher only)
    * ``courses``  - courses + teams the caller can access
    * ``students`` - students within accessible courses (all roles)
    """

    query = q.strip().lower()
    results: dict[str, list[dict[str, Any]]] = {
        "users": [],
        "courses": [],
        "teams": [],
        "students": [],
    }
    role = _auth.get("role", "student")
    is_admin = role == "admin"
    is_teacher = role in ("admin", "teacher")

    if not query:
        return JSONResponse(results)

    escaped_q = query.replace("%", "\\%").replace("_", "\\_")
    like_q = f"%{escaped_q}%"

    # -- Search users (admin/teacher only) --
    if scope in ("all", "users") and is_teacher:
        stmt = (
            select(User)
            .where(
                User.is_active.is_(True),
                sa_fn.lower(sa_fn.coalesce(User.full_name, User.username)).like(like_q)
                | sa_fn.lower(User.username).like(like_q)
                | sa_fn.lower(sa_fn.coalesce(User.email, "")).like(like_q),
            )
            .order_by(User.username)
            .limit(PAGE_SIZE_SEARCH)
        )
        user_rows = await db.execute(stmt)
        for u in user_rows.scalars().all():
            # Admin links to user admin page; teacher to dashboard
            href = "/dashboard/admin/users" if is_admin else "/dashboard"
            results["users"].append(
                {
                    "id": str(u.id),
                    "username": u.username,
                    "name": u.full_name or u.username,
                    "email": u.email or "",
                    "role": u.role,
                    "avatar_url": u.avatar_url or "",
                    "href": href,
                }
            )

    # -- Search courses --
    if scope in ("all", "courses"):
        stmt_c = (
            select(Course)
            .where(
                sa_fn.lower(Course.name).like(like_q) | sa_fn.lower(Course.code).like(like_q),
            )
            .order_by(Course.code)
            .limit(PAGE_SIZE_SEARCH)
        )
        course_rows = await db.execute(stmt_c)
        all_matched = list(course_rows.scalars().all())
        all_matched = await _filter_courses_for_user(all_matched, _auth, db)
        for c in all_matched[:8]:
            results["courses"].append(
                {
                    "id": str(c.id),
                    "code": c.code,
                    "name": c.name,
                    "year": c.academic_year or "",
                    "semester": c.semester or "",
                    "active": c.is_active,
                    "href": f"/dashboard/courses/{c.id}",
                }
            )

    # -- Search teams (within accessible courses) --
    if scope in ("all", "courses"):
        _accessible_ids: list[Any] | None = None

        if is_admin:
            stmt_t = (
                select(Team)
                .options(selectinload(Team.course))
                .where(Team.is_active.is_(True), sa_fn.lower(Team.name).like(like_q))
                .order_by(Team.name)
                .limit(PAGE_SIZE_SEARCH)
            )
        else:
            # Build accessible course list for non-admin roles
            all_courses_list = list((await db.execute(select(Course).limit(500))).scalars().all())
            accessible = await _filter_courses_for_user(all_courses_list, _auth, db)
            _accessible_ids = [c.id for c in accessible]
            if not _accessible_ids:
                stmt_t = None
            else:
                stmt_t = (
                    select(Team)
                    .options(selectinload(Team.course))
                    .where(
                        Team.is_active.is_(True),
                        sa_fn.lower(Team.name).like(like_q),
                        Team.course_id.in_(_accessible_ids),
                    )
                    .order_by(Team.name)
                    .limit(PAGE_SIZE_SEARCH)
                )

        if stmt_t is not None:
            team_rows_list = list((await db.execute(stmt_t)).scalars().all())
        else:
            team_rows_list = []

        for t in team_rows_list:
            course_name = t.course.code if t.course else ""
            results["teams"].append(
                {
                    "id": str(t.id),
                    "name": t.name,
                    "course_id": str(t.course_id),
                    "course_name": course_name,
                    # The group's term: tim-03 exists in every year's course.
                    "course_year": t.course.academic_year if t.course else "",
                    "course_semester": t.course.semester if t.course else "",
                    "href": f"/dashboard/teams/{t.id}",
                }
            )

    # -- Search students (all roles - filtered by accessible courses) --
    if scope in ("all", "students"):
        from app.models.student import Student

        # Resolve accessible course IDs (reuse if already computed)
        if is_admin:
            stu_stmt = (
                select(Student, Team.id, Team.name, Team.course_id)
                .join(TeamMember, TeamMember.student_id == Student.id)
                .join(Team, Team.id == TeamMember.team_id)
                .where(
                    sa_fn.lower(sa_fn.coalesce(Student.full_name, Student.gitlab_username)).like(
                        like_q
                    )
                    | sa_fn.lower(Student.gitlab_username).like(like_q),
                )
                .order_by(Student.gitlab_username)
                .limit(PAGE_SIZE_SEARCH)
            )
        else:
            all_courses_list_s = list((await db.execute(select(Course).limit(500))).scalars().all())
            accessible_s = await _filter_courses_for_user(all_courses_list_s, _auth, db)
            accessible_ids_s = [c.id for c in accessible_s]
            if not accessible_ids_s:
                stu_stmt = None
            else:
                stu_stmt = (
                    select(Student, Team.id, Team.name, Team.course_id)
                    .join(TeamMember, TeamMember.student_id == Student.id)
                    .join(Team, Team.id == TeamMember.team_id)
                    .where(
                        Team.course_id.in_(accessible_ids_s),
                        sa_fn.lower(
                            sa_fn.coalesce(Student.full_name, Student.gitlab_username)
                        ).like(like_q)
                        | sa_fn.lower(Student.gitlab_username).like(like_q),
                    )
                    .order_by(Student.gitlab_username)
                    .limit(PAGE_SIZE_SEARCH)
                )

        stu_rows = (await db.execute(stu_stmt)).all() if stu_stmt is not None else []

        for row in stu_rows:
            stu, team_id, team_name, _cid = row
            results["students"].append(
                {
                    "id": str(stu.id),
                    "username": stu.gitlab_username,
                    "name": stu.full_name or stu.gitlab_username,
                    "team": team_name or "",
                    "team_id": str(team_id),
                    "href": f"/dashboard/students/{stu.id}/team/{team_id}",
                }
            )

    return JSONResponse(results)


@router.get("/notifications", response_class=JSONResponse)
async def get_notifications(auth: DashboardAuth) -> JSONResponse:
    """Return and consume pending one-time notifications for the current user."""
    username = auth.get("user", "") or auth.get("gitlab_username", "")
    items = _pop_notifications(username)
    # Also check by gitlab_username if different
    gl_user = auth.get("gitlab_username", "")
    if gl_user and gl_user != username:
        items.extend(_pop_notifications(gl_user))
    return JSONResponse({"notifications": items})
