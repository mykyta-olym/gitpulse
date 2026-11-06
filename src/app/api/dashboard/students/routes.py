"""Student detail page (`/dashboard/students/{student_id}/team/{team_id}`).

This module decides WHO may see the page and delivers it (the short content
cache, full page or HTMX fragment); what the page shows is built section by
section in `profile.py`.
"""

import contextlib
import uuid

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.dashboard._access import _can_manage_team, _can_view_team, _membership_role
from app.api.dashboard._helpers import (
    _csrf_token,
    _is_own_student_profile,
    _not_found_response,
    _role_context,
    _templates,
)
from app.api.dashboard.students.profile import build_profile_context
from app.dependencies import DashboardAuth, DbSession
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.services.page_cache import (
    CSP_NONCE_PLACEHOLDER,
    CSRF_PLACEHOLDER,
    build_cache_render_ctx,
    cacheable_role_ctx,
    get_cached,
    make_role_variant,
    render_inline,
    set_cached,
)

router = APIRouter()

_ROLE_LABELS = {"admin": "Admin", "teacher": "Teacher"}


async def _resolve_member(db: DbSession, student_id: uuid.UUID) -> tuple[Student | None, str]:
    """The Student behind the id, and the role badge the page gives them.

    The id may be a User.id - a synthetic member who reached the team through
    inherited GitLab access. Their Student record is found by username, or
    created so the profile can display.
    """
    student = await db.get(Student, student_id)
    if student:
        conditions = []
        if student.gitlab_user_id:
            conditions.append(User.gitlab_user_id == student.gitlab_user_id)
        if student.gitlab_username:
            conditions.append(User.gitlab_username == student.gitlab_username)
        role = None
        if conditions:
            role = (
                await db.execute(select(User.role).where(or_(*conditions)).limit(1))
            ).scalar_one_or_none()
        return student, _ROLE_LABELS.get(role or "", "Student")

    user = await db.get(User, student_id)
    if user and user.gitlab_username:
        student = (
            await db.execute(select(Student).where(Student.gitlab_username == user.gitlab_username))
        ).scalar_one_or_none()
    if not student and user:
        student = Student(
            id=user.id,
            gitlab_user_id=user.gitlab_user_id,
            gitlab_username=user.gitlab_username or user.username or "",
            full_name=user.full_name,
            email=user.email,
        )
        db.add(student)
        await db.flush()
    return student, _ROLE_LABELS.get(user.role or "", "Student") if user else "Student"


@router.get("/students/{student_id}/team/{team_id}", response_class=HTMLResponse)
async def student_detail(
    student_id: uuid.UUID,
    team_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
) -> Response:
    student, member_role_label = await _resolve_member(db, student_id)
    if not student:
        return _not_found_response(request, "Member")

    team = (
        await db.execute(
            select(Team).where(Team.id == team_id).options(selectinload(Team.projects))
        )
    ).scalar_one_or_none()
    if not team:
        return _not_found_response(request, "Group")

    if member_role_label == "Student":
        is_mentor = (
            await db.execute(
                select(TeamMember.is_mentor).where(
                    TeamMember.team_id == team_id, TeamMember.student_id == student.id
                )
            )
        ).scalar()
        if is_mentor is True:
            member_role_label = "Mentor"

    if not await _can_view_team(team, _auth, db):
        return _not_found_response(
            request,
            "Student",
            message="You don't have access to this student's data.",
            suggestion="You can only view data for students in your own group.",
        )
    # _can_view_team lets a team MEMBER through so a student can open their own
    # page - not a teammate's. Staff (global admin/teacher, or a course
    # teacher/owner) see every member; everyone else only themselves.
    is_own_profile = _is_own_student_profile(student, _auth)
    if _auth.get("role", "student") not in ("admin", "teacher") and not is_own_profile:
        course_role = await _membership_role(db, team.course_id, _auth)
        if course_role not in ("admin", "owner", "teacher"):
            return _not_found_response(
                request,
                "Student",
                message="You can only open your own profile.",
                suggestion="Students can view only their own student page.",
            )

    course = await db.get(Course, team.course_id)
    from_project = None
    if from_project_id := request.query_params.get("from_project"):
        with contextlib.suppress(ValueError, AttributeError):
            from_project = await db.get(GitLabProject, uuid.UUID(from_project_id))

    page_ctx = {
        "student": student,
        "team": team,
        "course": course,
        "from_project": from_project,
        "is_own_profile": is_own_profile,
        "member_role_label": member_role_label,
    }
    role_ctx = {**_role_context(_auth), "can_edit": await _can_manage_team(team, _auth, db)}

    def deliver(fragment: str) -> Response:
        return render_inline(
            request=request,
            fragment=fragment,
            csrf_token=_csrf_token(_auth),
            role_ctx=role_ctx,
            templates=_templates(request),
            page_template="student_detail.html",
            page_ctx=page_ctx,
        )

    # The content body runs a few dozen queries (0.5-2s), so it is cached for a
    # minute per locale, viewer role and own-profile flag; the CSRF token and
    # the CSP nonce are placeholders filled on the way out.
    variant = make_role_variant(request, role_ctx, int(is_own_profile), str(team_id))
    cached = get_cached("student", student_id, variant)
    if cached is not None:
        return deliver(cached)

    content = await build_profile_context(
        db, student=student, student_id=student_id, team_id=team_id, course=course, auth=_auth
    )
    rendered = (
        _templates(request)
        .get_template("partials/student/_detail_content.html")
        .render(
            {
                **build_cache_render_ctx(request),
                "request": request,
                # Not `from_project`: the cached body is shared by every entry path.
                **{k: v for k, v in page_ctx.items() if k != "from_project"},
                **content,
                "csrf_token": CSRF_PLACEHOLDER,
                "csp_nonce": CSP_NONCE_PLACEHOLDER,
                **cacheable_role_ctx(role_ctx),
            }
        )
    )
    set_cached("student", student_id, variant, rendered)
    return deliver(rendered)
