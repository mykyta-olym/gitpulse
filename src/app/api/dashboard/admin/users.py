"""Admin: user listing, info, enrichment routes."""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import suppress
from typing import Any
from urllib.parse import quote_plus

from fastapi import APIRouter, BackgroundTasks, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.orm import load_only

from app.api.dashboard._helpers import (
    _clear_enrichment_status,
    _csrf_token,
    _feature_disabled_response,
    _get_enrichment_status,
    _role_context,
    _set_enrichment_status,
    _templates,
    _try_start_enrichment,
    logger,
)
from app.api.dashboard.admin.enrichment import (
    _run_gitlab_enrichment,
    _sync_roles_from_config,
)
from app.config import get_settings
from app.dependencies import AdminAuth, CSRFCheck, DbSession, RateLimitDep, TeacherAuth
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.course_membership import CourseMembership
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.academic_periods import (
    current_marker,
    period_scope_context,
    periods_for_users,
    requested_period,
    scope_students_to_period,
)
from app.services.job_control import ACTIVE_JOB_STATUSES, cancel_background_jobs
from app.utils.academic_period import AcademicPeriod

router = APIRouter()


# -- Admin: User List (JSON) --


@router.get("/admin/users/list")
async def admin_users_list(db: DbSession, auth: AdminAuth) -> Response:
    """Return user list as JSON for live table updates during enrichment."""

    try:
        result = await db.execute(
            select(User)
            .where(User.is_bot.is_(False))
            .order_by(User.username)
            .limit(5000)
            .options(
                load_only(
                    User.id,
                    User.username,
                    User.gitlab_user_id,
                    User.full_name,
                    User.email,
                    User.role,
                    User.is_active,
                )
            )
        )
        users = list(result.scalars().all())
    except Exception:
        logger.exception("admin_users_list_db_error")
        return JSONResponse({"error": "Database query failed"}, status_code=500)

    return JSONResponse(
        {
            "users": [
                {
                    "id": str(u.id),
                    "username": u.username,
                    "gitlab_user_id": u.gitlab_user_id,
                    "full_name": u.full_name,
                    "email": u.email or None,
                    "role": u.role,
                    "is_active": u.is_active,
                }
                for u in users
            ],
        },
    )


def _as_student(user: User) -> list[Any]:
    """Conditions matching the Student rows that are this user: a User and a
    Student are the same person by GitLab username (or login)."""
    conds: list[Any] = []
    if user.gitlab_username:
        conds.append(Student.gitlab_username == user.gitlab_username)
    if user.username and user.username != user.gitlab_username:
        conds.append(Student.gitlab_username == user.username)
    return conds


async def _shares_a_course(db: DbSession, auth: dict[str, Any], user: User) -> bool:
    """Whether a non-admin caller may look at this user: they share a course,
    as course members or through the user's group membership."""
    if auth.get("role", "student") == "admin":
        return True
    caller_user_id = auth.get("user_id")
    if not caller_user_id:
        return True
    from sqlalchemy import or_

    caller_courses = select(CourseMembership.course_id).where(
        CourseMembership.user_id == uuid.UUID(caller_user_id)
    )
    target_in_course = await db.execute(
        select(CourseMembership.id)
        .where(
            CourseMembership.user_id == user.id,
            CourseMembership.course_id.in_(caller_courses),
        )
        .limit(1)
    )
    if target_in_course.first():
        return True
    # Also check via team membership (student -> team -> course)
    match_conds = _as_student(user)
    if not match_conds:
        return False
    target_team_stmt = (
        select(Team.course_id)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .join(Student, TeamMember.student_id == Student.id)
        .where(TeamMember.is_active.is_(True), or_(*match_conds))
    )
    target_in_shared = await db.execute(
        select(CourseMembership.id)
        .where(
            CourseMembership.user_id == uuid.UUID(caller_user_id),
            CourseMembership.course_id.in_(target_team_stmt),
        )
        .limit(1)
    )
    return target_in_shared.first() is not None


async def _user_course_roles(db: DbSession, user: User) -> list[dict[str, Any]]:
    """The user's course memberships - and, for an admin, every other course
    too, implicitly."""
    course_roles: list[dict[str, Any]] = []
    try:
        cm_rows = (
            await db.execute(
                select(
                    CourseMembership.role,
                    Course.id.label("course_id"),
                    Course.code.label("course_code"),
                    Course.name.label("course_name"),
                    Course.academic_year,
                    Course.semester,
                    Course.is_active.label("course_active"),
                )
                .join(Course, CourseMembership.course_id == Course.id)
                .where(CourseMembership.user_id == user.id)
                .order_by(Course.name)
            )
        ).all()
        course_roles.extend(
            {
                "course_id": str(cr.course_id),
                "course_code": cr.course_code,
                "course_name": cr.course_name,
                "course_url": f"/dashboard/courses/{cr.course_id}",
                "role": cr.role,
                "academic_year": cr.academic_year,
                "semester": cr.semester,
                "is_active": bool(cr.course_active),
            }
            for cr in cm_rows
        )
    except Exception:
        logger.exception("user_info_course_membership_failed", extra={"user_id": str(user.id)})

    if user.role != "admin":
        return course_roles
    # Admin implicit access: admins can access ALL courses
    owned_course_ids = {cr["course_id"] for cr in course_roles}
    try:
        all_courses = (
            await db.execute(
                select(
                    Course.id,
                    Course.code,
                    Course.name,
                    Course.academic_year,
                    Course.semester,
                    Course.is_active,
                ).order_by(Course.name)
            )
        ).all()
        for ac in all_courses:
            cid = str(ac.id)
            if cid not in owned_course_ids:
                course_roles.append(
                    {
                        "course_id": cid,
                        "course_code": ac.code,
                        "course_name": ac.name,
                        "course_url": f"/dashboard/courses/{ac.id}",
                        "role": "admin",
                        "academic_year": ac.academic_year,
                        "semester": ac.semester,
                        "is_active": bool(ac.is_active),
                        "implicit": True,
                    }
                )
                owned_course_ids.add(cid)
    except Exception:
        logger.exception("user_info_admin_courses_failed", extra={"user_id": str(user.id)})
    return course_roles


async def _user_group_memberships(db: DbSession, user: User) -> list[dict[str, Any]]:
    """The groups the user is on as a student, each with its projects.

    Raises when the query fails - the caller answers 500.
    """
    match_conds = _as_student(user)
    if not match_conds:
        return []
    from sqlalchemy import or_

    rows = (
        await db.execute(
            select(
                Team.name.label("team_name"),
                Team.id.label("team_id"),
                Team.is_active.label("team_active"),
                Course.name.label("course_name"),
                Course.code.label("course_code"),
                Course.id.label("course_id"),
                Course.academic_year,
                Course.semester,
                Course.is_active.label("course_active"),
                TeamMember.is_teacher,
                TeamMember.is_mentor,
                TeamMember.gitlab_access_role,
                GitLabProject.gitlab_project_name,
                GitLabProject.gitlab_project_path,
                GitLabProject.id.label("project_id"),
            )
            .join(TeamMember, TeamMember.team_id == Team.id)
            .join(Student, TeamMember.student_id == Student.id)
            .join(Course, Team.course_id == Course.id)
            .outerjoin(GitLabProject, GitLabProject.team_id == Team.id)
            .where(TeamMember.is_active.is_(True), or_(*match_conds))
            .order_by(Course.name, Team.name)
        )
    ).all()

    # One row per group-and-project: fold the projects into their group.
    by_group: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        key = (str(r.course_id), str(r.team_id))
        group = by_group.get(key)
        if group is None:
            group = by_group[key] = {
                "course_name": r.course_name,
                "course_code": r.course_code,
                "course_id": str(r.course_id),
                "course_url": f"/dashboard/courses/{r.course_id}",
                "course_active": bool(r.course_active),
                "academic_year": r.academic_year,
                "semester": r.semester,
                "team_name": r.team_name,
                "team_id": str(r.team_id),
                "team_url": f"/dashboard/teams/{r.team_id}",
                "team_active": bool(r.team_active),
                "is_teacher": r.is_teacher,
                "is_mentor": r.is_mentor,
                "access_role": r.gitlab_access_role,
                "projects": [],
            }
        if r.project_id and r.gitlab_project_name:
            group["projects"].append(
                {
                    "name": r.gitlab_project_name,
                    "path": r.gitlab_project_path,
                    "url": f"/dashboard/teams/{r.team_id}",
                }
            )
    return list(by_group.values())


@router.get("/admin/users/{user_id}/info")
async def admin_user_info(user_id: uuid.UUID, db: DbSession, auth: TeacherAuth) -> Response:
    """Return user info: profile, course memberships, group memberships, projects."""

    try:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    except Exception:
        logger.exception("user_info_user_lookup_failed", extra={"user_id": str(user_id)})
        return JSONResponse(
            {"detail": "Failed to look up user record", "memberships": []}, status_code=500
        )
    if not user:
        return JSONResponse({"user": None, "memberships": [], "detail": "User not found"})

    # A teacher sees only the users of their own courses.
    if not await _shares_a_course(db, auth, user):
        return JSONResponse({"detail": "Access denied", "memberships": []}, status_code=403)

    avatar_url = user.avatar_url
    profile: dict[str, Any] = {
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_bot": bool(user.is_bot),
        "gitlab_username": user.gitlab_username,
        "gitlab_user_id": user.gitlab_user_id,
        "avatar_url": avatar_url,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

    course_roles = await _user_course_roles(db, user)
    try:
        memberships = await _user_group_memberships(db, user)
    except Exception:
        logger.exception(
            "user_info_membership_query_failed",
            extra={"user_id": str(user_id), "username": user.username},
        )
        return JSONResponse(
            {"detail": "Failed to load membership data", "memberships": []}, status_code=500
        )

    return JSONResponse(
        {
            "profile": profile,
            "user": user.username,
            "full_name": user.full_name,
            "course_roles": course_roles,
            "memberships": memberships,
        }
    )


@router.get("/admin/users/by-username/{username}/info")
async def admin_user_info_by_username(username: str, db: DbSession, auth: TeacherAuth) -> Response:
    """Look up User by gitlab_username and redirect to the UUID-based info endpoint.

    Falls back to Student data when no User record exists (e.g. inherited
    GitLab members who never logged in).
    """

    # Basic input validation
    username = username.strip()
    if not username or len(username) > 255:
        return JSONResponse({"user": None, "memberships": [], "detail": "Invalid username"})

    try:
        user = (
            await db.execute(
                select(User.id).where(
                    (User.gitlab_username == username) | (User.username == username)
                )
            )
        ).scalar_one_or_none()
    except Exception:
        logger.exception("admin_user_info_by_username_db_error")
        return JSONResponse(
            {"user": None, "memberships": [], "detail": "Database error"},
            status_code=500,
        )
    if user:
        return await admin_user_info(user, db, auth)

    # -- Fallback: build a profile from Student data (no User record) --
    try:
        student = (
            await db.execute(select(Student).where(Student.gitlab_username == username))
        ).scalar_one_or_none()
    except Exception:
        logger.exception("admin_user_info_student_fallback_error")
        return JSONResponse(
            {"user": None, "memberships": [], "detail": "Database error"},
            status_code=500,
        )
    if not student:
        return JSONResponse({"user": None, "memberships": [], "detail": "User not found"})

    # -- Access check: a non-admin teacher may only view a student who shares
    # at least one of their courses. The User-based path above is already
    # scoped; without the same guard here the Student-fallback (members who
    # never logged in, so have no User row) would let any teacher enumerate
    # students in courses they don't teach, exposing the student's full
    # cross-course membership map. Deny by default. --
    caller_role = auth.get("role", "student")
    if caller_role != "admin":
        caller_user_id = auth.get("user_id")
        shared = False
        if caller_user_id:
            student_courses = (
                select(Team.course_id)
                .join(TeamMember, TeamMember.team_id == Team.id)
                .where(
                    TeamMember.student_id == student.id,
                    TeamMember.is_active.is_(True),
                )
            )
            shared_row = await db.execute(
                select(CourseMembership.id)
                .where(
                    CourseMembership.user_id == uuid.UUID(caller_user_id),
                    CourseMembership.course_id.in_(student_courses),
                )
                .limit(1)
            )
            shared = shared_row.first() is not None
        if not shared:
            return JSONResponse({"detail": "Access denied", "memberships": []}, status_code=403)

    # Build profile from Student record
    avatar_url = None  # No stored photograph: the avatar component shows initials.

    profile: dict[str, Any] = {
        "username": student.gitlab_username,
        "full_name": student.full_name,
        "email": student.email if student.email and student.email != "PRIVATE" else None,
        "role": "student",
        "is_active": True,
        "gitlab_username": student.gitlab_username,
        "gitlab_user_id": student.gitlab_user_id,
        "avatar_url": avatar_url,
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "no_user_account": True,
    }

    # -- Group memberships from TeamMember -> Student --
    memberships: list[dict[str, Any]] = []
    try:
        rows = (
            await db.execute(
                select(
                    Team.name.label("team_name"),
                    Team.id.label("team_id"),
                    Team.is_active.label("team_active"),
                    Course.name.label("course_name"),
                    Course.code.label("course_code"),
                    Course.id.label("course_id"),
                    Course.academic_year,
                    Course.semester,
                    Course.is_active.label("course_active"),
                    TeamMember.is_teacher,
                    TeamMember.is_mentor,
                    TeamMember.gitlab_access_role,
                    GitLabProject.gitlab_project_name,
                    GitLabProject.gitlab_project_path,
                    GitLabProject.id.label("project_id"),
                )
                .join(TeamMember, TeamMember.team_id == Team.id)
                .join(Student, TeamMember.student_id == Student.id)
                .join(Course, Team.course_id == Course.id)
                .outerjoin(GitLabProject, GitLabProject.team_id == Team.id)
                .where(TeamMember.is_active.is_(True), Student.id == student.id)
                .order_by(Course.name, Team.name)
            )
        ).all()
        seen: set[tuple[str, str]] = set()
        for r in rows:
            key = (str(r.course_id), str(r.team_id))
            if key in seen:
                for m in memberships:
                    if m["course_id"] == str(r.course_id) and m["team_id"] == str(r.team_id):
                        if r.project_id and r.gitlab_project_name:
                            m["projects"].append(
                                {
                                    "name": r.gitlab_project_name,
                                    "path": r.gitlab_project_path,
                                    "url": f"/dashboard/teams/{r.team_id}",
                                }
                            )
                        break
                continue
            seen.add(key)
            projects = []
            if r.project_id and r.gitlab_project_name:
                projects.append(
                    {
                        "name": r.gitlab_project_name,
                        "path": r.gitlab_project_path,
                        "url": f"/dashboard/teams/{r.team_id}",
                    }
                )
            memberships.append(
                {
                    "course_name": r.course_name,
                    "course_code": r.course_code,
                    "course_id": str(r.course_id),
                    "course_url": f"/dashboard/courses/{r.course_id}",
                    "course_active": bool(r.course_active),
                    "academic_year": r.academic_year,
                    "semester": r.semester,
                    "team_name": r.team_name,
                    "team_id": str(r.team_id),
                    "team_url": f"/dashboard/teams/{r.team_id}",
                    "team_active": bool(r.team_active),
                    "is_teacher": r.is_teacher,
                    "is_mentor": r.is_mentor,
                    "access_role": r.gitlab_access_role,
                    "projects": projects,
                }
            )
    except Exception:
        logger.exception("admin_user_info_student_memberships_error")

    return JSONResponse(
        {
            "profile": profile,
            "user": student.gitlab_username,
            "full_name": student.full_name,
            "course_roles": [],
            "memberships": memberships,
        }
    )


# -- Admin: Users Page --


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, db: DbSession, auth: AdminAuth) -> Response:
    """Admin page for managing users."""
    settings = get_settings()
    if not settings.feature_rbac:
        return _feature_disabled_response(
            request,
            "Role-Based Access Control (RBAC)",
            "User management requires RBAC to be enabled.",
            "FEATURE_RBAC=true",
        )

    from app.utils.constants import NO_LOGIN_HASH

    # In dev/debug mode, auto-create session user if not in DB (e.g. after DB wipe)
    if settings.debug:
        _existing = await db.execute(select(User).where(User.username == auth.get("user")))
        if not _existing.scalar_one_or_none():
            _new = User(
                username=auth["user"],
                full_name=auth.get("user", "Dev User"),
                email=auth.get("email", f"{auth['user']}@dev.local"),
                password_hash=NO_LOGIN_HASH,
                role=auth.get("role", "admin"),
                is_active=True,
                gitlab_username=auth.get("gitlab_username", auth.get("user")),
            )
            db.add(_new)
            await db.flush()

    # Split humans vs bots: the table shows humans by default and a
    # separate collapsible "Service accounts" panel below shows the bots.
    # Two separate queries keep the partial index ix_users_is_bot_false hot.
    # -- Academic period scope --
    # A person carries no period; the courses they are in do. So the page is
    # scoped by narrowing STUDENTS to the ones who reach a course in the chosen
    # period, and leaving admins, teachers and service accounts alone - they
    # are not cohort-bound, and a User Management that loses its own admins
    # when the term turns over is worse than no scope at all.
    period_scope = await period_scope_context(db, requested_period(request))
    scope_key = str(period_scope["selected_key"])
    selected = period_scope["selected"]
    period = (
        AcademicPeriod(
            academic_year=str(selected["academic_year"]),
            semester=str(selected["semester"]),
        )
        if isinstance(selected, dict)
        else None
    )

    humans_stmt = scope_students_to_period(
        select(User).where(User.is_bot.is_(False)), period, scope=scope_key
    )
    humans_result = await db.execute(humans_stmt.order_by(User.username).limit(5000))
    users = list(humans_result.scalars().all())
    # Service accounts are never cohort-bound: a bot belongs to the installation,
    # not to a year. Scoping them would empty the Service Accounts view for
    # every period but one, for no reason a reader could name.
    bots_result = await db.execute(
        select(User).where(User.is_bot.is_(True)).order_by(User.username).limit(5000)
    )
    bot_users = list(bots_result.scalars().all())

    # One query for every badge on the page rather than one per row.
    user_periods = await periods_for_users(db, [u.id for u in users])
    current_period, _current_running = current_marker()

    _users_ctx = {
        "request": request,
        "users": users,
        "bot_users": bot_users,
        "period_scope": period_scope,
        "user_periods": {
            str(uid): [{"academic_year": p.academic_year, "semester": p.semester} for p in periods]
            for uid, periods in user_periods.items()
        },
        "current_period_key": current_period.key,
        "csrf_token": _csrf_token(auth),
        "current_user": auth,
        **_role_context(auth),
    }
    return _templates(request).TemplateResponse(request, "admin_users.html", _users_ctx)


@router.get("/admin/users/enrich-gitlab/status")
async def get_enrichment_status(auth: AdminAuth) -> Response:
    """Get current GitLab enrichment status (for polling fallback)."""
    status = _get_enrichment_status()
    if not status:
        return JSONResponse({"status": "idle"})
    return JSONResponse(status)


@router.post("/admin/users/enrich-gitlab/cancel")
async def cancel_enrichment(
    db: DbSession,
    _auth: AdminAuth,
    _csrf: CSRFCheck,
) -> Response:
    """Cancel the active GitLab enrichment task."""
    jobs = list(
        (
            await db.execute(
                select(BackgroundJob)
                .where(
                    BackgroundJob.job_type == "enrichment",
                    BackgroundJob.status.in_(ACTIVE_JOB_STATUSES),
                )
                .order_by(BackgroundJob.enqueued_at.desc())
                .limit(5)
            )
        )
        .scalars()
        .all()
    )
    cancelled = await cancel_background_jobs(
        db,
        jobs,
        reason="Cancelled by admin",
    )
    await db.commit()
    message = "Enrichment cancelled." if cancelled else "No active enrichment to cancel."
    _set_enrichment_status(
        status="cancelled" if cancelled else "idle",
        message=message,
    )
    return JSONResponse(
        {
            "status": "cancelled" if cancelled else "idle",
            "cancelled": cancelled,
            "message": message,
        }
    )


@router.get("/admin/users/enrich-gitlab/stream", name="enrichment_stream")
async def enrichment_stream(
    request: Request,
    auth: AdminAuth,
) -> Response:
    """Stream GitLab enrichment status via Server-Sent Events.

    Subscribes to Redis ``enrichment_progress`` channel for real-time
    progress updates.  Falls back to in-memory status polling every 2s.

    Events:
      - ``data`` with JSON enrichment status payload
      - Named ``complete`` event when enrichment finishes
      - Heartbeat comments every 15s
    """

    async def _redis_enrichment_listener(
        queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        """Listen to Redis ``enrichment_progress`` channel."""
        from app.api.dashboard._helpers import _redis_channel_listener

        await _redis_channel_listener("enrichment_progress", queue)

    async def _event_generator() -> AsyncGenerator[str, None]:
        redis_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=200)
        redis_task: asyncio.Task[None] | None = None

        try:
            redis_task = asyncio.create_task(_redis_enrichment_listener(redis_queue))
        except Exception:
            logger.warning("enrichment_redis_listener_start_failed", exc_info=True)

        poll_interval = 0.5
        heartbeat_counter = 0.0
        prev_hash = ""

        try:
            while True:
                if await request.is_disconnected():
                    break

                # Drain Redis pub/sub messages (real-time from background task)
                while not redis_queue.empty():
                    try:
                        data = redis_queue.get_nowait()
                        yield f"data: {json.dumps(data, default=str)}\n\n"
                        status_val = str(data.get("status", "")).lower()
                        if status_val in ("completed", "failed", "cancelled"):
                            yield f"event: complete\ndata: {json.dumps(data, default=str)}\n\n"
                            return
                    except asyncio.QueueEmpty:
                        break

                # Fallback: poll in-memory status dict
                status = _get_enrichment_status()
                snapshot = status or {"status": "idle"}
                snap_hash = json.dumps(snapshot, sort_keys=True, default=str)

                if snap_hash != prev_hash:
                    prev_hash = snap_hash
                    yield f"data: {json.dumps(snapshot, default=str)}\n\n"
                    status_val = str(snapshot.get("status", "")).lower()
                    if status_val in ("completed", "failed", "cancelled"):
                        yield f"event: complete\ndata: {json.dumps(snapshot, default=str)}\n\n"
                        return
                    if status_val == "idle":
                        # No enrichment running; close stream
                        return

                heartbeat_counter += poll_interval
                if heartbeat_counter >= 15:
                    heartbeat_counter = 0
                    yield ": heartbeat\n\n"

                await asyncio.sleep(poll_interval)
        finally:
            if redis_task and not redis_task.done():
                redis_task.cancel()
                with suppress(asyncio.CancelledError, Exception):
                    await redis_task

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


@router.post("/admin/users/{user_id}/enrich")
async def enrich_single_user(
    user_id: uuid.UUID,
    db: DbSession,
    auth: AdminAuth,
    _csrf: CSRFCheck,
) -> Response:
    """Enrich a single user from GitLab (fetch email, full_name, avatar)."""
    from app.services.gitlab.client import GitLabClient

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return JSONResponse({"ok": False, "detail": "User not found"}, status_code=404)

    search_name = user.gitlab_username or user.username
    if not search_name:
        return JSONResponse({"ok": False, "detail": "No GitLab username"})

    settings = get_settings()
    if not settings.gitlab_url or not settings.gitlab_api_token:
        return JSONResponse({"ok": False, "detail": "GitLab not configured"})

    updated_fields: list[str] = []
    try:
        async with GitLabClient(
            base_url=settings.gitlab_url,
            private_token=settings.gitlab_api_token,
            timeout=10,
            max_retries=1,
        ) as gl:
            gl_users = await gl.search_users(search_name)
            if not gl_users:
                return JSONResponse({"ok": False, "detail": "User not found on GitLab"})
            gl_user = gl_users[0]

            if not user.gitlab_username:
                user.gitlab_username = search_name
                updated_fields.append("gitlab_username")
            if not user.gitlab_user_id and gl_user.get("id"):
                user.gitlab_user_id = gl_user["id"]
                updated_fields.append("gitlab_user_id")
            if not user.email or user.email == "PRIVATE":
                email = (
                    gl_user.get("email")
                    or gl_user.get("public_email")
                    or gl_user.get("commit_email")
                )
                if not email:
                    from app.services.arena_email import lookup_email

                    email = await lookup_email(search_name, get_settings())
                if email:
                    user.email = email
                    updated_fields.append("email")
            if not user.full_name:
                name = gl_user.get("name")
                if name and name != search_name:
                    user.full_name = name
                    updated_fields.append("full_name")
            avatar = gl_user.get("avatar_url")
            if avatar and not user.avatar_url:
                user.avatar_url = avatar
                updated_fields.append("avatar_url")

            await db.commit()
    except Exception:
        logger.exception("single_user_enrich_failed", extra={"user_id": str(user_id)})
        return JSONResponse({"ok": False, "detail": "GitLab API error"}, status_code=502)

    msg = f"Updated: {', '.join(updated_fields)}" if updated_fields else "Already up to date"

    return JSONResponse(
        {
            "ok": True,
            "message": msg,
            "updated_fields": updated_fields,
            "profile": {
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "gitlab_username": user.gitlab_username,
                "gitlab_user_id": user.gitlab_user_id,
                "avatar_url": user.avatar_url,
            },
        }
    )


@router.post("/admin/users/enrich-gitlab")
async def enrich_users_from_gitlab(
    request: Request,
    db: DbSession,
    auth: AdminAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
    background_tasks: BackgroundTasks,
) -> Response:
    """Fetch missing user details (full_name, email) from GitLab API.

    Supports both AJAX (Accept: application/json) and form POST.
    AJAX callers get a JSON response so they can decide whether to
    show the global job bar without a page reload flash.
    """
    want_json = "application/json" in request.headers.get("accept", "")

    # Atomic check-and-set: prevents TOCTOU race if two admins click simultaneously
    if not _try_start_enrichment():
        if want_json:
            return JSONResponse(
                {
                    "started": False,
                    "reason": "already_running",
                    "message": "Enrichment already in progress",
                },
            )
        return RedirectResponse(
            url="/dashboard/admin/users?error=Enrichment+already+in+progress",
            status_code=303,
        )

    try:
        from sqlalchemy import or_

        settings = get_settings()
        if not settings.gitlab_api_token:
            _clear_enrichment_status()  # Release lock since we won't proceed
            if want_json:
                return JSONResponse(
                    {
                        "started": False,
                        "reason": "no_token",
                        "message": "GitLab API token not configured",
                    },
                    status_code=400,
                )
            return RedirectResponse(
                url="/dashboard/admin/users?error=GitLab+API+token+not+configured",
                status_code=303,
            )

        # Count total users to enrich for progress tracking
        # Include PRIVATE emails for re-check too, and users missing gitlab_user_id
        # Also include users where gitlab_username is NULL (fallback to username)
        user_stmt = select(User).where(
            or_(
                User.email.is_(None),
                User.email == "PRIVATE",
                User.full_name.is_(None),
                User.gitlab_user_id.is_(None),
            ),
        )
        user_result = await db.execute(user_stmt)
        users_to_enrich = list(user_result.scalars().all())

        # Only count users for progress total - students are enriched via
        # cross-linking and a small second pass; counting them separately
        # inflates the total (same person appears as User + Student).
        total = len(users_to_enrich)

        if total == 0:
            # Check if there are students that still need enrichment - the user
            # phase found nothing, but students may have missing emails/names
            # that the arena API can fill.
            from app.models.student import Student as StudentModel

            student_need_stmt = (
                select(sa_func.count())
                .select_from(StudentModel)
                .where(
                    or_(
                        StudentModel.email.is_(None),
                        StudentModel.email == "PRIVATE",
                        StudentModel.full_name.is_(None),
                    ),
                )
            )
            students_needing = (await db.execute(student_need_stmt)).scalar() or 0

            if students_needing == 0:
                # Truly nothing to do
                roles_updated = await _sync_roles_from_config(db)
                _clear_enrichment_status()  # Release lock since nothing else to do
                if roles_updated:
                    msg = f"{roles_updated} role(s) updated from config"
                else:
                    msg = "No users need enrichment"
                if want_json:
                    return JSONResponse(
                        {"started": False, "reason": "not_needed", "message": msg},
                    )
                return RedirectResponse(
                    url=f"/dashboard/admin/users?success={msg.replace(' ', '+')}",
                    status_code=303,
                )

            # Students need enrichment - proceed with background task
            # (the user phase will be empty, but student phase will run)
            total = students_needing

        # Update status with actual total count
        _set_enrichment_status(
            status="running",
            message="Starting GitLab enrichment...",
            total=total,
            processed=0,
        )

        # Create a BackgroundJob record so enrichment appears in Job History
        from datetime import UTC, datetime

        bg_job = BackgroundJob(
            job_type="enrichment",
            status="running",
            started_at=datetime.now(UTC),
        )
        db.add(bg_job)
        await db.flush()
        job_id = str(bg_job.id)
        await db.commit()

        # Schedule the background task
        background_tasks.add_task(
            _run_gitlab_enrichment,
            settings.gitlab_url,
            settings.gitlab_api_token,
            settings.gitlab_api_timeout_seconds,
            job_id,
        )

        # Return immediately - page will poll for status
        if want_json:
            return JSONResponse(
                {
                    "started": True,
                    "total": total,
                    "message": f"Enriching {total} profiles...",
                    "job_id": job_id,
                    "cancel_url": "/dashboard/admin/users/enrich-gitlab/cancel",
                },
            )
        return RedirectResponse(url="/dashboard/admin/users", status_code=303)
    except Exception as exc:
        logger.error("gitlab_enrichment_start_failed", exc_info=True)
        _clear_enrichment_status()
        if want_json:
            return JSONResponse(
                {
                    "started": False,
                    "reason": "error",
                    "message": f"Failed to start enrichment: {exc}",
                },
                status_code=500,
            )
        return RedirectResponse(
            url=f"/dashboard/admin/users?error={quote_plus(str(exc))}",
            status_code=303,
        )
