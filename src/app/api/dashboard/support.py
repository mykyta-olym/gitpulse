"""Support pages: the request form, the ticket list and a ticket's thread.

The JSON side (submissions, comments, ticket updates) is in
``app.api.support``; this module renders the pages over it.
"""

import contextlib
import uuid
from typing import Any

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.api.dashboard._access import _filter_courses_for_user, _membership_role
from app.api.dashboard._helpers import (
    _csrf_token,
    _feature_disabled_response,
    _not_found_response,
    _role_context,
    _templates,
)
from app.config import get_settings
from app.dependencies import DashboardAuth, DbSession, TeacherAuth
from app.models.course import Course
from app.security.course_roles import role_gte

router = APIRouter()


@router.get("/support")
async def support_page(
    request: Request,
    db: DbSession,
    _auth: DashboardAuth,
    course_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> Response:
    """Render the support form as an integrated dashboard page.

    Three-step flow:
      1. If no course_id -> show course picker (user's accessible courses).
      2. If course_id but no category -> show category selection cards.
      3. If course_id + category -> show the ticket submission form.
    """
    settings = get_settings()
    if not settings.feature_support_forms:
        flag_hint = "FEATURE_SUPPORT_FORMS=true"
        return _feature_disabled_response(
            request,
            "Support Forms",
            "The support forms feature is currently disabled.",
            flag_hint,
            **_role_context(_auth),
        )

    # NOTE: Support form is just a form (no heavy data), so we skip the
    # lazy shell and render it eagerly - a flash of a loading state on
    # a static form looks worse than a ~50 ms render delay.

    # -- Full data path --

    # -- Step 1: list user's courses for the picker --
    stmt = (
        select(Course)
        .order_by(Course.academic_year.desc(), Course.semester, Course.code)
        .limit(500)
    )
    result = await db.execute(stmt)
    all_courses = list(result.scalars().all())
    user_courses = await _filter_courses_for_user(all_courses, _auth, db)

    # If a specific course was chosen, generate a token bound to it
    selected_course = None
    token = ""
    support_form = None
    selected_category = None
    valid_categories = {
        "bug",
        "feature_request",
        "question",
        "general",
        "dashboard",
        "cicd",
        "code_review",
        "evaluation",
        "reports",
        "repositories",
        "account",
        "grade",
    }
    if category and category in valid_categories:
        selected_category = category

    if course_id:
        selected_course = next((c for c in user_courses if str(c.id) == course_id), None)
        if selected_course and selected_category:
            unique_data = f"{course_id}:dashboard:{uuid.uuid4().hex}"
            token = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_data))

            # Load the active dynamic form (auto-creates default if needed).
            from app.services.support_forms import SupportFormService

            form_svc = SupportFormService(
                db,
                enabled=True,
                anonymize_text=settings.support_anonymize_free_text,
            )
            support_form = await form_svc.get_or_create_default_form(
                selected_course.id,
                category=selected_category,
                username=_auth.get("user", ""),
            )
            await db.commit()

    # Step 1 is the table Support Tickets opens with: scoped by the academic
    # period like every list of courses, and counting the reader's OWN
    # requests per course (a ticket names its author by the GitLab username,
    # or the GitPulse one - see _form_content.html) - one grouped query.
    period_scope: dict[str, Any] | None = None
    support_courses = user_courses
    my_ticket_stats: dict[str, dict[str, Any]] = {}
    if not selected_course and user_courses:
        from app.models.support_ticket import SupportTicket
        from app.services.academic_periods import (
            courses_in_scope,
            period_scope_context,
            requested_period,
        )

        period_scope = await period_scope_context(
            db, requested_period(request), include_none=False, visible_courses=user_courses
        )
        support_courses = courses_in_scope(user_courses, period_scope)
        my_names = {n for n in (_auth.get("gitlab_username"), _auth.get("user")) if n}
        if my_names and support_courses:
            mine_rows = await db.execute(
                select(
                    SupportTicket.course_id,
                    func.count(SupportTicket.id),
                    func.count(SupportTicket.id).filter(
                        SupportTicket.status.in_(("open", "in_progress"))
                    ),
                    func.max(SupportTicket.submitted_at),
                )
                .where(
                    SupportTicket.course_id.in_([c.id for c in support_courses]),
                    SupportTicket.submitted_by.in_(my_names),
                )
                .group_by(SupportTicket.course_id)
            )
            for cid, total, open_count, last in mine_rows.all():
                my_ticket_stats[str(cid)] = {
                    "total": int(total),
                    "open": int(open_count),
                    "last": last,
                }

    return _templates(request).TemplateResponse(
        request,
        "support_form.html",
        {
            "request": request,
            "token": token,
            "course_id": str(course_id) if selected_course else "",
            "selected_course": selected_course,
            "selected_category": selected_category,
            "user_courses": user_courses,
            "support_courses": support_courses,
            "my_ticket_stats": my_ticket_stats,
            "period_scope": period_scope,
            "support_form": support_form,
            "context_type": "dashboard",
            "csrf_token": _csrf_token(_auth),
            **_role_context(_auth),
        },
    )


@router.get("/support/tickets")
async def support_tickets_page(
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    course_id: str | None = Query(default=None),
    form_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=5000, ge=10, le=5000),
) -> Response:
    """Support tickets viewer - admin/teacher can browse submitted tickets."""
    settings = get_settings()
    if not settings.feature_support_forms:
        return _feature_disabled_response(
            request,
            "Support Forms",
            "The support forms feature is currently disabled.",
            "FEATURE_SUPPORT_FORMS=true",
            **_role_context(_auth),
        )

    # -- Full data path --
    # Courses the user may view
    stmt = (
        select(Course)
        .order_by(Course.academic_year.desc(), Course.semester, Course.code)
        .limit(500)
    )
    result = await db.execute(stmt)
    all_courses = list(result.scalars().all())
    user_courses = await _filter_courses_for_user(all_courses, _auth, db)

    from app.services.support_forms import SupportFormService

    selected_course = None
    if course_id:
        selected_course = next((c for c in user_courses if str(c.id) == course_id), None)

    svc = SupportFormService(db, enabled=True, anonymize_text=settings.support_anonymize_free_text)

    forms: list[Any] = []
    responses: list[Any] = []
    total_responses = 0
    active_form: Any = None

    if selected_course:
        cid = selected_course.id
        forms = await svc.list_forms(cid)

        target_fid = None
        if form_id:
            with contextlib.suppress(ValueError):
                target_fid = uuid.UUID(form_id)

        # `active_form` (field labels used when rendering a response) defaults to
        # the first form. But the ticket LIST must include EVERY ticket for the
        # course - it is only filtered by a form when one is explicitly requested
        # via ?form_id=. Previously the list filter itself defaulted to forms[0],
        # which silently hid every ticket belonging to any other form (or to no
        # form at all) - the "only ticket #5 shows, the other 4 are gone" bug.
        _display_fid = target_fid or (forms[0].id if forms else None)
        if _display_fid:
            active_form = await svc.get_form(_display_fid)

        # Status, priority and category are NOT filtered here: the table loads
        # the course's tickets and filters them in the browser, with its
        # dropdowns pre-set from the same parameters (tickets_filters). Filtered
        # here as well, "All Statuses" could not bring back the rows the server
        # had dropped - a link with ?status=open stranded the reader on them.
        responses, total_responses = await svc.get_responses(
            cid,
            target_fid,
            search=search,
            limit=per_page,
            offset=(page - 1) * per_page,
        )

    total_pages = max(1, (total_responses + per_page - 1) // per_page)
    page = min(page, total_pages)

    # The course overview (no course picked yet) is scoped by the academic
    # period like every other list of courses - Course Management, the
    # Dashboard: the same selector, the same remembered pick, "All periods" one
    # click away. It says, per course, how many tickets wait for an answer, how
    # many there are and when the last came in - one grouped query.
    ticket_stats: dict[str, dict[str, Any]] = {}
    period_scope: dict[str, Any] | None = None
    ticket_courses = user_courses
    if not selected_course and user_courses:
        from app.models.support_ticket import SupportTicket
        from app.services.academic_periods import (
            courses_in_scope,
            period_scope_context,
            requested_period,
        )

        period_scope = await period_scope_context(
            db, requested_period(request), include_none=False, visible_courses=user_courses
        )
        ticket_courses = courses_in_scope(user_courses, period_scope)

        stats_rows = await db.execute(
            select(
                SupportTicket.course_id,
                func.count(SupportTicket.id),
                func.count(SupportTicket.id).filter(
                    SupportTicket.status.in_(("open", "in_progress"))
                ),
                func.max(SupportTicket.submitted_at),
            )
            .where(SupportTicket.course_id.in_([c.id for c in ticket_courses]))
            .group_by(SupportTicket.course_id)
        )
        for cid, total, open_count, last in stats_rows.all():
            ticket_stats[str(cid)] = {"total": int(total), "open": int(open_count), "last": last}

    # Who submitted and who handles each ticket, as the same role badge the
    # Users page shows - a bare "@ab002zz" did not say teacher or student.
    from app.api.dashboard._helpers import people_by_name

    people = await people_by_name(
        db,
        [r.get("submitted_by") for r in responses] + [r.get("assigned_to") for r in responses],
    )

    return _templates(request).TemplateResponse(
        request,
        "support_tickets.html",
        {
            "request": request,
            "user_courses": user_courses,
            "selected_course": selected_course,
            "forms": forms,
            "active_form": active_form,
            "responses": responses,
            "people": people,
            "ticket_stats": ticket_stats,
            "ticket_courses": ticket_courses,
            "period_scope": period_scope,
            "total_responses": total_responses,
            "filter_status": status or "",
            "filter_priority": priority or "",
            "filter_category": category or "",
            "filter_search": search or "",
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "offset": (page - 1) * per_page,
            },
            "csrf_token": _csrf_token(_auth),
            **_role_context(_auth),
        },
    )


@router.get("/support/ticket/{ticket_id}")
async def support_ticket_detail_page(
    request: Request,
    db: DbSession,
    _auth: TeacherAuth,
    ticket_id: int,
) -> Response:
    """Individual ticket detail page with threaded comments (GitHub-style)."""
    settings = get_settings()
    if not settings.feature_support_forms:
        return _feature_disabled_response(
            request,
            "Support Forms",
            "The support forms feature is currently disabled.",
            "FEATURE_SUPPORT_FORMS=true",
            **_role_context(_auth),
        )

    from app.services.support_forms import SupportFormService

    svc = SupportFormService(db, enabled=True, anonymize_text=settings.support_anonymize_free_text)
    ticket_obj = await svc.get_ticket(ticket_id)
    if not ticket_obj:
        return RedirectResponse(url="/dashboard/support/tickets", status_code=303)
    # The same rule as the ticket API and its SSE stream: staff of the
    # ticket's course only. A 404, so the page does not reveal the ticket.
    if _auth.get("role") != "admin":
        mem_role = (
            await _membership_role(db, ticket_obj.course_id, _auth)
            if ticket_obj.course_id
            else None
        )
        if mem_role is None or not role_gte(mem_role, "teacher"):
            return _not_found_response(request, "Ticket")

    # NOTE: ticket detail is dominated by the comments thread + form, not
    # heavy table data, so we render eagerly instead of flashing a loading state.

    comments = await svc.list_comments(ticket_id, include_internal=True)
    course = None
    if ticket_obj.course_id:
        stmt = select(Course).where(Course.id == ticket_obj.course_id)
        result = await db.execute(stmt)
        course = result.scalar_one_or_none()

    # Load staff users for assignee search dropdown
    from app.models.user import User
    from app.services.support_forms import support_assignees

    staff_users = [
        {
            "username": u.gitlab_username or u.username,
            "name": u.full_name or "",
            "avatar_url": u.avatar_url or "",
        }
        for u in await support_assignees(db, ticket_obj.course_id)
    ]

    # Build ticket dict for template
    ticket = {
        "id": int(ticket_obj.id),
        "title": ticket_obj.title,
        "status": ticket_obj.status or "open",
        "priority": ticket_obj.priority or "medium",
        "category": ticket_obj.category or "general",
        "assigned_to": ticket_obj.assigned_to,
        "submitted_by": ticket_obj.submitted_by or None,
        "submitted_at": (ticket_obj.submitted_at.isoformat() if ticket_obj.submitted_at else None),
        "updated_at": (ticket_obj.updated_at.isoformat() if ticket_obj.updated_at else None),
        "resolved_at": (ticket_obj.resolved_at.isoformat() if ticket_obj.resolved_at else None),
        "responses": dict(ticket_obj.responses) if ticket_obj.responses else {},
        "form": {"questions": ticket_obj.form.questions} if ticket_obj.form else None,
    }

    # Fetch submitter profile (avatar, role) if submitted_by is set
    submitter_profile: dict[str, str] = {}
    if ticket_obj.submitted_by:
        sub_stmt = select(User).where(
            (User.gitlab_username == ticket_obj.submitted_by)
            | (User.username == ticket_obj.submitted_by)
        )
        sub_result = await db.execute(sub_stmt)
        sub_user = sub_result.scalars().first()
        if sub_user:
            submitter_profile = {
                "username": sub_user.gitlab_username or sub_user.username,
                "full_name": sub_user.full_name or "",
                "avatar_url": sub_user.avatar_url or "",
                "role": sub_user.role or "student",
            }

    # Query who assigned this ticket (most recent support.assign audit entry)
    assigned_by = ""
    if ticket_obj.assigned_to:
        try:
            from app.models.audit_log import AuditLog

            assign_stmt = (
                select(AuditLog)
                .where(
                    AuditLog.action == "support.assign",
                    AuditLog.detail["ticket_id"].astext == str(ticket_id),
                )
                .order_by(AuditLog.timestamp.desc())
                .limit(1)
            )
            assign_result = await db.execute(assign_stmt)
            assign_entry = assign_result.scalar_one_or_none()
            if assign_entry:
                assigned_by = assign_entry.actor or ""
        except Exception:  # noqa: S110 -- assignment-history lookup is decorative; missing audit row is fine.
            pass

    # The kind of person behind every name on the page - submitter, assignee,
    # each comment's author - for the role badge beside it.
    from app.api.dashboard._helpers import people_by_name

    people = await people_by_name(
        db,
        [ticket_obj.submitted_by, ticket_obj.assigned_to]
        + [getattr(c, "author", None) for c in comments],
    )

    _current_uname = _auth.get("gitlab_username") or _auth.get("user", "")
    _current_role = _auth.get("role", "student")
    _can_comment = _current_role == "admin" or (
        ticket_obj.assigned_to and ticket_obj.assigned_to == _current_uname
    )

    return _templates(request).TemplateResponse(
        request,
        "support_ticket_detail.html",
        {
            "request": request,
            "ticket": ticket,
            "comments": comments,
            "course": course,
            "staff_users": staff_users,
            "current_username": _current_uname,
            "assigned_by": assigned_by,
            "submitter_profile": submitter_profile,
            "people": people,
            "can_comment": _can_comment,
            "csrf_token": _csrf_token(_auth),
            **_role_context(_auth),
        },
    )
