"""Admin: course teacher management routes."""

import json
import re
import uuid

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select

from app.api.dashboard._access import _can_manage_course, _membership_role
from app.api.dashboard._helpers import (
    _conflict_redirect,
    _csrf_token,
    _not_found_response,
    _parse_form_timestamp,
    _push_notification,
    _role_context,
    _templates,
    logger,
)
from app.api.errors import check_optimistic_lock, raise_not_found
from app.dependencies import CSRFCheck, DbSession, RateLimitDep, TeacherAuth
from app.models.course import Course
from app.models.course_membership import CourseMembership
from app.models.user import User
from app.services.academic_periods import (
    courses_in_scope,
    period_scope_context,
    requested_period,
)

router = APIRouter()


# -- Admin: Course Teacher Management --


@router.get("/admin/courses", response_class=HTMLResponse)
async def admin_courses_page(request: Request, db: DbSession, auth: TeacherAuth) -> Response:
    """Page for managing course teacher assignments (admin sees all, teacher sees own)."""
    role_ctx = _role_context(auth)
    is_admin = role_ctx.get("is_admin", False)

    # Get courses - admin sees all, teacher sees only their own
    stmt = (
        select(Course)
        .order_by(Course.academic_year.desc(), Course.semester, Course.code)
        .limit(1000)
    )
    result = await db.execute(stmt)
    courses = list(result.scalars().all())

    if not is_admin:
        # Teachers see courses where they have a CourseMembership
        teacher_user = auth.get("user", "").lower()
        teacher_gl = auth.get("gitlab_username", "").lower()

        # Check CourseMembership for the current user

        membership_course_ids: set[object] = set()
        try:
            user_conditions = []
            if teacher_gl:
                user_conditions.append(User.gitlab_username == auth.get("gitlab_username", ""))
            if teacher_user and teacher_user != teacher_gl:
                user_conditions.append(User.username == auth.get("user", ""))
            if user_conditions:
                from sqlalchemy import or_ as sa_or

                user_row = (
                    await db.execute(
                        select(User.id).where(User.is_active.is_(True), sa_or(*user_conditions))
                    )
                ).first()
                if user_row:
                    mem_stmt = select(CourseMembership.course_id).where(
                        CourseMembership.user_id == user_row[0],
                    )
                    mem_result = await db.execute(mem_stmt)
                    membership_course_ids = {row[0] for row in mem_result.all()}
        except Exception:
            logger.exception("admin_courses_page_membership_lookup_failed")

        courses = [c for c in courses if c.id in membership_course_ids]

    # -- Academic period scope --
    # Resolved AFTER the teacher filter and from the courses that survived it:
    # a teacher who only teaches summer courses must open this page on their
    # summer, not on whichever newer term somebody else's course is in - that
    # would be an empty table with every course they own one click away. A
    # course carries its period directly, so there is no "no period" view.
    period_scope = await period_scope_context(
        db, requested_period(request), include_none=False, visible_courses=courses
    )
    courses = courses_in_scope(courses, period_scope)
    # Match the shared table's case-insensitive numeric ordering on first paint.
    courses.sort(
        key=lambda course: [
            int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", course.code)
        ]
    )

    # Build a set of course owners for badge differentiation

    owner_stmt = (
        select(CourseMembership.course_id, User.gitlab_username, User.username)
        .join(User, CourseMembership.user_id == User.id)
        .where(CourseMembership.role == "owner")
    )
    owner_result = await db.execute(owner_stmt)
    course_owners: dict[object, set[str]] = {}
    for cid, gl_uname, uname in owner_result.all():
        course_owners.setdefault(cid, set()).add((gl_uname or uname or "").lower())

    # Collect admin usernames - admins have implicit access,
    # so hide them from the teacher badges in the table.
    admin_q = await db.execute(
        select(User.gitlab_username, User.username).where(
            User.role == "admin", User.is_active.is_(True)
        )
    )
    admin_usernames: set[str] = set()
    for gl, un in admin_q.all():
        if gl:
            admin_usernames.add(gl.lower())
        if un:
            admin_usernames.add(un.lower())

    # Build course_id -> list of teacher/owner usernames from CourseMembership
    _staff_stmt = (
        select(
            CourseMembership.course_id,
            User.gitlab_username,
            User.username,
        )
        .join(User, CourseMembership.user_id == User.id)
        .where(CourseMembership.role.in_(("owner", "teacher")))
    )
    _staff_result = await db.execute(_staff_stmt)
    course_teacher_map: dict[object, list[str]] = {}
    for _cid, _gl_u, _u in _staff_result.all():
        uname = _gl_u or _u or ""
        if uname:
            course_teacher_map.setdefault(_cid, []).append(uname)

    return _templates(request).TemplateResponse(
        request,
        "admin_courses.html",
        {
            "request": request,
            "courses": courses,
            "period_scope": period_scope,
            "course_owners": course_owners,
            "course_teacher_map": course_teacher_map,
            "admin_usernames": admin_usernames,
            "csrf_token": _csrf_token(auth),
            **role_ctx,
        },
    )


@router.post("/admin/courses/{course_id}/teachers")
@router.post("/courses/{course_id}/teachers")
async def update_course_teachers(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    auth: TeacherAuth,
    _rate: RateLimitDep,
    _csrf: CSRFCheck,
) -> Response:
    """Update teacher assignments for a course using CourseMembership."""
    from app.security.course_roles import (
        remove_course_membership,
        set_course_membership,
    )

    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")

    if not await _can_manage_course(course, auth, db):
        raise_not_found("Course not found")

    # Teacher assignment is course configuration, so an archived course refuses
    # it like any other write. Reactivate, reassign, archive again.
    from app.services.courses import ensure_course_active

    await ensure_course_active(db, course_id)

    form = await request.form()
    # The Teachers page applies each change as it is made and asks for the
    # outcome as JSON; a plain form post still gets the redirect.
    wants_json = "application/json" in request.headers.get("accept", "")

    # -- Optimistic lock --
    expected_ts = _parse_form_timestamp(form, "expected_updated_at")
    try:
        check_optimistic_lock(course, expected_ts, label="Course")
    except HTTPException:
        if wants_json:
            return JSONResponse({"error": "conflict"}, status_code=409)
        return _conflict_redirect(f"/dashboard/courses/{course_id}/teachers")

    # -- Parse teacher data (JSON format with roles) --
    from app.models.course_membership import COURSE_ROLES, CourseMembership

    teachers_json_str = str(form.get("teachers_json", "[]"))
    try:
        teachers_data: list[dict[str, str]] = json.loads(teachers_json_str)
    except (ValueError, TypeError):
        return JSONResponse(
            {"error": "Invalid teacher data format"},
            status_code=400,
        )

    # Validate roles
    valid_roles = {r for r in COURSE_ROLES if r != "student"}  # student not assignable via this UI
    for item in teachers_data:
        if item.get("role", "teacher") not in valid_roles:
            item["role"] = "teacher"

    # Validate: submitted usernames must belong to active users
    submitted_usernames = [
        item.get("username", "") for item in teachers_data if item.get("username")
    ]
    valid_user_map: dict[str, uuid.UUID] = {}
    if submitted_usernames:
        valid_stmt = select(User.id, User.gitlab_username, User.username).where(
            User.is_active.is_(True),
        )
        valid_result = await db.execute(valid_stmt)
        for row in valid_result:
            if row.gitlab_username:
                valid_user_map[row.gitlab_username.lower()] = row.id
            if row.username:
                valid_user_map[row.username.lower()] = row.id

    # Resolve each teacher to a user_id
    desired: dict[uuid.UUID, dict[str, str]] = {}  # user_id -> {username, role}
    unresolved_usernames: list[str] = []  # usernames not yet in Users table (pre-provisioned)
    for item in teachers_data:
        uname = item.get("username", "").strip()[:100]
        if not uname:
            continue
        uid = valid_user_map.get(uname.lower())
        if uid is None:
            # Keep unresolved usernames - they get access once they log in
            unresolved_usernames.append(uname)
            continue
        desired[uid] = {"username": uname, "role": item.get("role", "teacher")}

    # Admins can be assigned as either 'owner' or 'teacher' - keep all roles.

    # -- Last-owner protection: at least one owner must remain --
    owner_count = sum(1 for info in desired.values() if info["role"] == "owner")
    if owner_count == 0 and desired:
        if wants_json:
            return JSONResponse({"error": "no_owner"}, status_code=422)
        return Response(
            status_code=303,
            headers={"Location": f"/dashboard/courses/{course_id}/teachers?error=no_owner"},
        )

    # Capture pre-existing staff for notification dedup
    # Load existing memberships for this course (staff roles only)
    existing_stmt = select(CourseMembership).where(
        CourseMembership.course_id == course_id,
        CourseMembership.role.in_(("owner", "teacher")),
    )
    existing_rows = list((await db.execute(existing_stmt)).scalars().all())
    existing_by_uid = {m.user_id: m for m in existing_rows}

    # Diff: add / update / remove
    for uid, info in desired.items():
        await set_course_membership(db, uid, course_id, info["role"])

    for uid in set(existing_by_uid) - set(desired):
        await remove_course_membership(db, uid, course_id)

    await db.flush()
    await db.commit()

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="course_teachers_updated",
        actor=str(auth.get("user_id", auth.get("user", ""))),
        entity_type="course",
        entity_id=course_id,
        detail={
            "memberships": [
                {"username": v["username"], "role": v["role"]} for v in desired.values()
            ],
            "removed": [str(uid) for uid in set(existing_by_uid) - set(desired)],
        },
    )

    # Detect newly added teachers for notification
    old_uids = set(existing_by_uid)
    admin_user = auth.get("user", "")
    for uid, info in desired.items():
        if uid not in old_uids and info["username"] != admin_user:
            _push_notification(
                info["username"],
                f"You were assigned as {info['role']} to {course.code} by {admin_user}",
            )

    # -- Email notifications for teacher changes --
    from app.services.email_notifications import notify_teacher_assigned_to_course

    # Lookup emails for affected users
    affected_uids = set(desired) - old_uids
    _email_map: dict[uuid.UUID, str] = {}
    if affected_uids:
        _email_stmt = select(User.id, User.email).where(User.id.in_(affected_uids))
        _email_map = {_uid: _em for _uid, _em in (await db.execute(_email_stmt)).all() if _em}

    for uid, info in desired.items():
        if uid not in old_uids:
            notify_teacher_assigned_to_course(
                teacher_username=info["username"],
                course_code=course.code,
                course_name=course.name,
                assigned_by=admin_user,
                course_id=course.id,
                to_email=_email_map.get(uid),
            )

    logger.info(
        "course_teachers_updated",
        course_id=str(course_id),
        course_code=course.code,
        memberships=[{"username": v["username"], "role": v["role"]} for v in desired.values()],
        admin_user=admin_user,
    )

    if wants_json:
        return JSONResponse({"ok": True})
    return Response(
        status_code=303,
        headers={"Location": f"/dashboard/courses/{course_id}/teachers"},
    )


@router.get("/courses/{course_id}/teachers", response_class=HTMLResponse)
async def course_teachers_page(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    auth: TeacherAuth,
) -> Response:
    """View and manage teachers for a specific course."""
    from app.models.course_membership import CourseMembership
    from app.security.course_roles import COURSE_ROLES

    course = await db.get(Course, course_id)
    if not course:
        return _not_found_response(request, "Course")

    role_ctx = _role_context(auth)
    if not await _can_manage_course(course, auth, db):
        return _not_found_response(request, "Course")

    course_role = await _membership_role(db, course_id, auth)

    # -- Load current memberships (staff roles: owner, teacher) --
    mem_stmt = (
        select(CourseMembership, User)
        .join(User, CourseMembership.user_id == User.id)
        .where(
            CourseMembership.course_id == course_id,
            CourseMembership.role.in_(("owner", "teacher")),
        )
        .order_by(CourseMembership.role)
    )
    mem_result = await db.execute(mem_stmt)
    memberships = list(mem_result.all())

    def _avatar(u: User) -> str:
        """Only stored photograph URLs are reliable; otherwise show initials."""
        return u.avatar_url or ""

    current_teachers_data = []
    assigned_user_ids: set[uuid.UUID] = set()
    assigned_usernames: set[str] = set()
    for membership, user in memberships:
        assigned_user_ids.add(user.id)
        uname = user.gitlab_username or user.username
        assigned_usernames.add(uname.lower())
        current_teachers_data.append(
            {
                "username": uname,
                "name": user.full_name or "",
                "role": membership.role,
                "global_role": user.role or "student",
                "avatar_url": _avatar(user),
            }
        )

    # Build a lookup from the all_users query (loaded below for available pool)
    users_stmt = (
        select(User)
        .where(
            User.is_active.is_(True),
        )
        .order_by(User.username)
    )
    users_result = await db.execute(users_stmt)
    all_users = list(users_result.scalars().all())

    # Map for resolving legacy teacher_usernames to real user data
    _user_by_name: dict[str, User] = {}
    for u in all_users:
        if u.gitlab_username:
            _user_by_name[u.gitlab_username.lower()] = u
        if u.username:
            _user_by_name[u.username.lower()] = u

    # -- Auto-inject all admin users into assigned list --
    # Admins have implicit access; show them in the admin section so
    # they can be assigned the Course Owner role.
    # Look up any existing CourseMembership for admin users in this course
    # so we can show the correct role instead of defaulting to teacher.
    admin_users_stmt = select(User).where(
        User.is_active.is_(True),
        User.role == "admin",
    )
    admin_result = await db.execute(admin_users_stmt)
    admin_users_list = list(admin_result.scalars())
    admin_ids = [au.id for au in admin_users_list]
    admin_mem_stmt = (
        (
            select(CourseMembership).where(
                CourseMembership.course_id == course_id,
                CourseMembership.user_id.in_(admin_ids),
            )
        )
        if admin_ids
        else None
    )
    admin_memberships: dict[uuid.UUID, str] = {}
    if admin_mem_stmt is not None:
        admin_mem_result = await db.execute(admin_mem_stmt)
        for am in admin_mem_result.scalars():
            admin_memberships[am.user_id] = am.role

    for au in admin_users_list:
        aname = au.gitlab_username or au.username
        if aname and aname.lower() not in assigned_usernames:
            assigned_usernames.add(aname.lower())
            assigned_user_ids.add(au.id)
            admin_role = admin_memberships.get(au.id, "teacher")
            current_teachers_data.append(
                {
                    "username": aname,
                    "name": au.full_name or "",
                    "role": admin_role,
                    "global_role": "admin",
                    "avatar_url": _avatar(au),
                }
            )

    # In the order the table opens in - by name, as its Teacher header says - so
    # the rows are where they belong in the first frame. (Owner-first order
    # was re-sorted by name in the browser, so the list reordered after paint.)
    current_teachers_data.sort(key=lambda x: (x["name"] or x["username"]).lower())

    # -- Build available users pool --
    # Admins have implicit access to all courses, so hide them from
    # non-admin/non-owner viewers.  Admins and course owners can see
    # admin users (for ownership transfer).
    is_admin = role_ctx.get("is_admin", False)
    current_user = (auth.get("user") or "").lower()
    is_owner = any(
        i["username"].lower() == current_user and i["role"] == "owner"
        for i in current_teachers_data
    )
    can_see_admins = is_admin or is_owner

    # Exclude already-assigned users
    exclude_ids = assigned_user_ids.copy()

    available_users = []
    seen: set[str] = set()
    for u in all_users:
        if u.id in exclude_ids:
            continue
        # Hide admin users from viewers who aren't admin or course owner
        if not can_see_admins and u.role == "admin":
            continue
        key = (u.gitlab_username or u.username or "").lower()
        if not key or key in seen or key in assigned_usernames:
            continue
        seen.add(key)
        if u.username and u.username.lower() != key:
            seen.add(u.username.lower())
        available_users.append(
            {
                "username": u.gitlab_username or u.username,
                "name": u.full_name or "",
                "role": u.role or "user",
                "avatar_url": _avatar(u),
            }
        )

    # Available course roles for the UI role selector
    assignable_roles = [r for r in COURSE_ROLES if r != "student"]

    ctx = {
        "request": request,
        "course": course,
        "course_role": course_role,
        "current_teachers": current_teachers_data,
        "available_users": available_users,
        "assignable_roles": assignable_roles,
        "current_username": auth.get("user", ""),
        "can_see_admins": can_see_admins,
        "csrf_token": _csrf_token(auth),
        **_role_context(auth),
    }

    return _templates(request).TemplateResponse(
        request,
        "course_teachers.html",
        ctx,
    )


# ===============================================================================
# ADMIN - SYSTEM SETTINGS
# ===============================================================================
