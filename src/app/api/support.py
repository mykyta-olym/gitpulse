"""Support form / ticket / link endpoints."""

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.api.dashboard._access import _can_view_course
from app.api.errors import (
    raise_bad_request,
    raise_forbidden,
    raise_internal_error,
    raise_not_found,
    raise_service_unavailable,
)
from app.api.helpers.support_deps import get_support_form_service
from app.api.helpers.utils import course_staff_emails, lookup_user_email, require_course_staff
from app.config import get_settings
from app.dependencies import (
    CSRFCheck,
    DbSession,
    RateLimitDep,
    get_current_admin,
    get_current_teacher,
    get_current_user,
)
from app.models.course import Course
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.schemas.common import StatusIdResponse
from app.schemas.support import (
    SupportAttachmentUploadResponse,
    SupportCommentCreate,
    SupportCommentListResponse,
    SupportCommentResponse,
    SupportCreate,
    SupportFormResponse,
    SupportResponseItem,
    SupportResponsesPage,
    SupportStatsResponse,
    SupportTicketUpdate,
    TicketPurgeResponse,
)
from app.services.support_forms import SupportFormService, support_assignees
from app.template_cache import TEMPLATE_DIR

logger = structlog.get_logger(__name__)

# The value the UI sends for "everything": ten years, used as a sentinel for
# "no age limit" rather than as a real age - the same contract as the events
# and jobs purges.
_PURGE_MAX_HOURS = 87600
router = APIRouter()


def _publish_ticket_event(course_id: Any, ticket_id: Any, event: str = "ticket_created") -> None:
    """Publish a course-scoped SSE event so an open tickets list live-updates the
    moment a ticket is created OR changed (status / priority / assignment) -
    including via API - instead of needing a manual refresh. Reuses the
    ``dashboard:course:<id>`` channel the course SSE stream already serves; the
    tickets list subscribes and reloads on any ``ticket_*`` event.
    """
    if not course_id:
        return
    try:
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update(
            "course",
            str(course_id),
            event,
            extra={"ticket_id": ticket_id},
        )
    except Exception:
        logger.debug("ticket_sse_publish_failed", exc_info=True)


# ===============================================================================
# SUPPORT ENDPOINTS
# ===============================================================================


async def _notify_staff_new_ticket(
    *,
    db: AsyncSession,
    course_id: uuid.UUID | None,
    ticket_id: int,
    title: str,
    category: str,
    submitted_by: str,
    exclude_email: str | None,
) -> None:
    """Email all owner/teacher members of the course about a new ticket.

    Best-effort: never raises. Skips ``exclude_email`` (typically the
    submitter, who already received the confirmation email).
    """
    if course_id is None:
        return
    try:
        from app.services.email_notifications import notify_ticket_new_to_staff

        _course = await db.get(Course, course_id)
        _course_code = _course.code if _course else "course"

        _emails = set(await course_staff_emails(db, course_id))
        if exclude_email:
            _emails.discard(exclude_email)
        for _em in _emails:
            await asyncio.to_thread(
                notify_ticket_new_to_staff,
                ticket_id=ticket_id,
                title=title,
                category=category,
                submitted_by=submitted_by,
                course_code=_course_code,
                to_email=_em,
            )
    except Exception:
        logger.debug("staff_ticket_notify_failed", exc_info=True)


async def _send_ticket_notifications(
    *,
    db: AsyncSession,
    ticket_id: int,
    title: str | None,
    category: str | None,
    submitted_by: str | None,
    course_id: uuid.UUID | None,
) -> None:
    """Best-effort email notifications for a newly-created support ticket.

    Sends confirmation to the submitter and alerts course staff.
    """
    if not title:
        return
    try:
        from app.services.email_notifications import notify_ticket_created

        submitter_email = await lookup_user_email(db, submitted_by) if submitted_by else None
        await asyncio.to_thread(
            notify_ticket_created,
            ticket_id=ticket_id,
            title=title,
            category=category or "general",
            to_email=submitter_email,
        )
        await _notify_staff_new_ticket(
            db=db,
            course_id=course_id,
            ticket_id=ticket_id,
            title=title,
            category=category or "general",
            submitted_by=submitted_by or "unknown",
            exclude_email=submitter_email,
        )
    except Exception:
        logger.debug("ticket_email_notify_failed", exc_info=True)


# NOTE: this fixed-path route MUST be declared BEFORE ``/support/{token}`` below.
# Otherwise ``POST /support/upload`` matches the ``{token}`` param route
# (submit_support_ticket, a JSON-body endpoint) with token="upload", and every
# multipart upload 422s with "Input should be a valid dictionary or object to
# extract fields from" (the raw multipart body fed into a Pydantic model).
@router.post(
    "/support/upload",
    summary="Upload ticket attachment",
)
async def upload_support_attachment(
    _csrf: CSRFCheck,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> SupportAttachmentUploadResponse:
    """Upload a file attachment for a support ticket.
    Max file size: 50 MB.
    Saves to src/app/templates/static/uploads/
    """
    if not get_settings().feature_support_forms:
        raise_service_unavailable("Support feature is disabled")
    max_size = 50 * 1024 * 1024
    # Read the file size by seeking
    try:
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
    except Exception:
        # Fallback if seek not supported
        file_size = 0

    if file_size > max_size:
        raise_bad_request("File too large. Maximum size is 50 MB.")

    # Generate unique filename to avoid collision
    ext = os.path.splitext(file.filename or "")[1]
    unique_filename = f"{uuid.uuid4()}{ext}"

    # Target directory
    # The app's one templates directory, not a path counted up from this
    # module: a module move would write uploads somewhere nothing serves.
    uploads_dir = TEMPLATE_DIR / "static" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    file_path = uploads_dir / unique_filename

    try:
        import asyncio

        content = await file.read()

        def save_file_sync(path: Path, data: bytes) -> None:
            with open(path, "wb") as f:
                f.write(data)

        await asyncio.to_thread(save_file_sync, file_path, content)
    except Exception as e:
        logger.error("file_upload_failed", error=str(e), filename=file.filename)
        raise_internal_error("Failed to save uploaded file")

    return SupportAttachmentUploadResponse(
        url=f"/static/uploads/{unique_filename}",
        filename=file.filename or unique_filename,
    )


@router.post(
    "/support/{token}",
    status_code=status.HTTP_201_CREATED,
    response_model=StatusIdResponse,
    summary="Submit support ticket",
)
async def submit_support_ticket(
    token: uuid.UUID,
    data: SupportCreate,
    _csrf: CSRFCheck,
    _rate_limit: RateLimitDep,
    service: SupportFormService = Depends(get_support_form_service),
    current_user: User = Depends(get_current_user),
) -> StatusIdResponse:
    """Submit the active course form as the signed-in author."""
    if not service.enabled:
        raise_service_unavailable("Support feature is disabled")
    form = await service.get_form(data.form_id)
    if not form or not form.is_active or form.course_id != data.course_id:
        raise_not_found("Support form not found")
    course = await service.db.get(Course, data.course_id)
    auth = {
        "role": current_user.role,
        "user": current_user.username,
        "gitlab_username": current_user.gitlab_username or "",
    }
    if not course or not await _can_view_course(course, auth, service.db):
        raise_not_found("Course not found")
    author = current_user.gitlab_username or current_user.username
    support_type = "student" if current_user.role == "student" else "teacher"
    try:
        ticket_id = await service.submit_dynamic(
            token=str(token),
            form_id=form.id,
            course_id=course.id,
            support_type=support_type,
            context_type=data.context_type,
            responses=data.responses,
            title=data.title,
            priority=data.priority,
            category=form.category or "general",
            submitted_by=author,
        )
        from app.services.audit import write_audit

        await write_audit(
            service.db,
            action="support.create",
            actor=author,
            entity_type="support_ticket",
            detail={"ticket_id": ticket_id, "course_id": str(course.id), "form_id": str(form.id)},
        )
        await service.db.commit()
    except Exception:
        await service.db.rollback()
        raise_internal_error("Failed to submit support ticket")
    if data.title:
        await _send_ticket_notifications(
            db=service.db,
            ticket_id=ticket_id,
            title=data.title,
            category=form.category or "general",
            submitted_by=author,
            course_id=course.id,
        )
    _publish_ticket_event(course.id, ticket_id, "ticket_created")
    return StatusIdResponse(status="submitted", id=ticket_id)


# ===============================================================================
# SUPPORT RESPONSES
# ===============================================================================


@router.get(
    "/support/{course_id}/responses",
    response_model=SupportResponsesPage,
    summary="Get support tickets",
)
async def get_support_responses(
    course_id: uuid.UUID,
    db: DbSession,
    form_id: uuid.UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    priority_filter: str | None = Query(default=None, alias="priority"),
    category_filter: str | None = Query(default=None, alias="category"),
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    svc: SupportFormService = Depends(get_support_form_service),
    current_user: User = Depends(get_current_teacher),
) -> SupportResponsesPage:
    """Return support tickets for a course with optional filtering."""
    if not svc.enabled:
        raise_service_unavailable("Support forms feature is disabled")
    await require_course_staff(db, course_id, current_user)
    items, total = await svc.get_responses(
        course_id,
        form_id,
        status=status_filter,
        priority=priority_filter,
        category=category_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    form_obj = None
    if form_id:
        f = await svc.get_form(form_id)
        if f:
            form_obj = SupportFormResponse.model_validate(f)
    return SupportResponsesPage(
        items=[SupportResponseItem.model_validate(i) for i in items],
        total=total,
        form=form_obj,
    )


@router.get(
    "/support/{course_id}/stats",
    response_model=SupportStatsResponse,
    summary="Get support response statistics",
)
async def get_support_stats(
    course_id: uuid.UUID,
    db: DbSession,
    form_id: uuid.UUID | None = None,
    svc: SupportFormService = Depends(get_support_form_service),
    current_user: User = Depends(get_current_teacher),
) -> SupportStatsResponse:
    """Return aggregated per-question statistics including distributions,
    averages, NPS score, and sentiment analysis for text responses."""
    if not svc.enabled:
        raise_service_unavailable("Support forms feature is disabled")
    await require_course_staff(db, course_id, current_user)
    data = await svc.get_response_stats(course_id, form_id)
    return SupportStatsResponse(**data)


# ===============================================================================
# TICKET MANAGEMENT (status, priority, assignment, comments)
# ===============================================================================


@router.put(
    "/support/tickets/{ticket_id}",
    response_model=StatusIdResponse,
    summary="Update support ticket",
)
async def update_support_ticket(
    ticket_id: int,
    payload: SupportTicketUpdate,
    db: DbSession,
    _csrf: CSRFCheck,
    svc: SupportFormService = Depends(get_support_form_service),
    current_user: User = Depends(get_current_teacher),
) -> StatusIdResponse:
    """Update ticket metadata - status, priority, category, assignment."""
    if not svc.enabled:
        raise_service_unavailable("Support forms feature is disabled")
    ticket = await svc.get_ticket(ticket_id)
    if ticket is None:
        raise_not_found("Ticket not found")
    await require_course_staff(db, ticket.course_id, current_user)

    fields = payload.model_dump(exclude_unset=True)
    if fields.get("assigned_to"):
        assignees = await support_assignees(db, ticket.course_id)
        if fields["assigned_to"] not in {u.gitlab_username or u.username for u in assignees}:
            raise_bad_request("Assignee must be an active administrator or staff of this course")
    old_assigned = getattr(ticket, "assigned_to", None)
    old_status = getattr(ticket, "status", None)
    old_priority = getattr(ticket, "priority", None)
    updated = await svc.update_ticket(ticket_id, **fields)
    if updated is None:
        raise_not_found("Ticket not found")

    # Audit log for support ticket updates
    try:
        from app.services.audit import write_audit

        _actor = current_user.gitlab_username or current_user.username
        if "assigned_to" in fields:
            await write_audit(
                db,
                action="support.assign",
                actor=_actor,
                entity_type="support_ticket",
                detail={
                    "ticket_id": ticket_id,
                    "assigned_to": fields["assigned_to"],
                    "previous": old_assigned,
                },
            )
        if "status" in fields:
            _new_status = fields["status"]
            _action = (
                "support.resolve"
                if _new_status == "resolved"
                else (
                    "support.reopen"
                    if _new_status == "open" and old_status == "resolved"
                    else "support.status"
                )
            )
            await write_audit(
                db,
                action=_action,
                actor=_actor,
                entity_type="support_ticket",
                detail={"ticket_id": ticket_id, "status": _new_status, "previous": old_status},
            )
    except Exception:
        logger.debug("audit_log_failed", exc_info=True)
    await db.commit()

    # Publish SSE event for real-time ticket updates
    try:
        import json as _json
        from datetime import datetime

        from app.redis_pool import get_redis as _pool_get_redis

        _r = _pool_get_redis()
        _r.publish(  # type: ignore[attr-defined]
            f"support:ticket:{ticket_id}",
            _json.dumps(
                {
                    "_event": "update",
                    "ticket_id": ticket_id,
                    "fields": fields,
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            ),
        )
    except Exception:
        logger.debug("sse_publish_failed", exc_info=True)

    # Also live-update the course-scoped tickets LIST (the per-ticket channel
    # above only reaches the open ticket-detail page). A status / priority /
    # assignment change now reflects in the list without a manual refresh.
    _publish_ticket_event(getattr(ticket, "course_id", None), ticket_id, "ticket_updated")

    # Email notification for status changes
    if "status" in fields and fields["status"] != old_status:
        try:
            from app.services.email_notifications import notify_ticket_status_change

            _actor = current_user.gitlab_username or current_user.username
            _notified_status: set[str] = set()

            # Notify the assigned teacher (if different from actor)
            _assigned = getattr(ticket, "assigned_to", None) or ""
            if _assigned and _assigned != _actor:
                _u_row = await lookup_user_email(db, _assigned)
                if _u_row:
                    await asyncio.to_thread(
                        notify_ticket_status_change,
                        ticket_id,
                        getattr(ticket, "title", ""),
                        fields["status"],
                        _u_row,
                    )
                    _notified_status.add(_u_row)

            # Also notify the submitter (if different from actor and not already notified)
            _submitter = getattr(ticket, "submitted_by", None) or ""
            if _submitter and _submitter != _actor:
                _s_row = await lookup_user_email(db, _submitter)
                if _s_row and _s_row not in _notified_status:
                    await asyncio.to_thread(
                        notify_ticket_status_change,
                        ticket_id,
                        getattr(ticket, "title", ""),
                        fields["status"],
                        _s_row,
                    )
        except Exception:
            logger.debug("status_email_notify_failed", exc_info=True)

    # Email notification for priority changes (was previously silent - only
    # status changes emailed the user). Same recipients as a status change:
    # the assigned teacher and/or the submitter, when different from the actor.
    if "priority" in fields and fields["priority"] != old_priority:
        try:
            from app.services.email_notifications import notify_ticket_priority_change

            _actor_p = current_user.gitlab_username or current_user.username
            _notified_prio: set[str] = set()
            for _who in (
                getattr(ticket, "assigned_to", None) or "",
                getattr(ticket, "submitted_by", None) or "",
            ):
                if _who and _who != _actor_p:
                    _em = await lookup_user_email(db, _who)
                    if _em and _em not in _notified_prio:
                        await asyncio.to_thread(
                            notify_ticket_priority_change,
                            ticket_id,
                            getattr(ticket, "title", ""),
                            fields["priority"],
                            _em,
                        )
                        _notified_prio.add(_em)
        except Exception:
            logger.debug("priority_email_notify_failed", exc_info=True)

    # Email notification for assignment changes
    if fields.get("assigned_to"):
        try:
            from app.services.email_notifications import notify_ticket_assignment

            _new_assignee = fields["assigned_to"]
            _assigner = current_user.gitlab_username or current_user.username
            _au_row = await lookup_user_email(db, _new_assignee)
            if _au_row:
                await asyncio.to_thread(
                    notify_ticket_assignment,
                    ticket_id,
                    getattr(ticket, "title", ""),
                    _assigner,
                    _au_row,
                )
        except Exception:
            logger.debug("assignment_email_notify_failed", exc_info=True)

    return StatusIdResponse(status="updated", id=ticket_id)


@router.get(
    "/support/tickets/{ticket_id}/comments",
    response_model=SupportCommentListResponse,
    summary="List ticket comments",
)
async def list_ticket_comments(
    ticket_id: int,
    db: DbSession,
    svc: SupportFormService = Depends(get_support_form_service),
    current_user: User = Depends(get_current_teacher),
) -> SupportCommentListResponse:
    """List comments on a support ticket. Staff sees internal notes."""
    if not svc.enabled:
        raise_service_unavailable("Support forms feature is disabled")
    ticket = await svc.get_ticket(ticket_id)
    if ticket is None:
        raise_not_found("Ticket not found")
    await require_course_staff(db, ticket.course_id, current_user)
    comments = await svc.list_comments(ticket_id, include_internal=True)
    return SupportCommentListResponse(
        items=[SupportCommentResponse.model_validate(c) for c in comments],
        total=len(comments),
    )


@router.post(
    "/support/tickets/{ticket_id}/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=SupportCommentResponse,
    summary="Add ticket comment",
)
async def add_ticket_comment(
    ticket_id: int,
    payload: SupportCommentCreate,
    db: DbSession,
    _csrf: CSRFCheck,
    svc: SupportFormService = Depends(get_support_form_service),
    current_user: User = Depends(get_current_teacher),
) -> SupportCommentResponse:
    """Add a comment to a support ticket."""
    if not svc.enabled:
        raise_service_unavailable("Support forms feature is disabled")
    ticket = await svc.get_ticket(ticket_id)
    if ticket is None:
        raise_not_found("Ticket not found")
    await require_course_staff(db, ticket.course_id, current_user)

    # Only admins or the assigned teacher can comment
    _uname = current_user.gitlab_username or current_user.username
    _is_admin = current_user.role == "admin"
    _is_assigned = (
        getattr(ticket, "assigned_to", None) and getattr(ticket, "assigned_to", None) == _uname
    )
    if not _is_admin and not _is_assigned:
        raise_forbidden("Only admins or the assigned teacher can comment")

    comment = await svc.add_comment(
        ticket_id,
        author=current_user.gitlab_username or current_user.username,
        content=payload.content,
        is_internal=payload.is_internal,
    )
    if comment is None:
        raise_not_found("Ticket not found")

    # Touch ticket updated_at so "Last updated" reflects comment activity

    _now = datetime.now(UTC)
    ticket.updated_at = _now

    try:
        from app.services.audit import write_audit

        await write_audit(
            db,
            action="support.comment",
            actor=current_user.gitlab_username or current_user.username,
            entity_type="support_ticket",
            detail={
                "ticket_id": ticket_id,
                "comment_id": str(comment.id),
                "is_internal": payload.is_internal,
            },
        )
    except Exception:
        await db.rollback()
    await db.commit()

    # Publish SSE event for real-time comment streaming
    try:
        import json as _json

        from app.redis_pool import get_redis as _pool_get_redis

        _r = _pool_get_redis()
        _r.publish(  # type: ignore[attr-defined]
            f"support:ticket:{ticket_id}",
            _json.dumps(
                {
                    "_event": "comment",
                    "ticket_id": ticket_id,
                    "updated_at": _now.isoformat(),
                    "comment": {
                        "id": str(comment.id),
                        "author": comment.author,
                        # Who wrote it, for the avatar and role badge the page
                        # draws beside every comment it was served with.
                        "author_avatar_url": current_user.avatar_url or "",
                        "author_role": current_user.role or "",
                        "author_is_bot": bool(current_user.is_bot),
                        "content": comment.content,
                        "is_internal": comment.is_internal,
                        "created_at": comment.created_at.isoformat()
                        if comment.created_at
                        else None,
                    },
                }
            ),
        )
    except Exception:
        logger.debug("sse_publish_failed", exc_info=True)

    # Email notification for new comment
    try:
        from app.services.email_notifications import notify_ticket_comment

        _assigned = getattr(ticket, "assigned_to", None) or ""
        _author = comment.author or ""
        _submitter = getattr(ticket, "submitted_by", None) or ""

        _notified: set[str] = set()

        # Notify the assigned teacher (if different from author)
        if _assigned and _assigned != _author:
            _u_row = await lookup_user_email(db, _assigned)
            if _u_row:
                await asyncio.to_thread(
                    notify_ticket_comment,
                    ticket_id,
                    getattr(ticket, "title", ""),
                    _author,
                    comment.content,
                    _u_row,
                )
                _notified.add(_u_row)

        # Also notify the submitter (if different from author and not already notified).
        # Internal comments are staff-only - never email submitter for those.
        if _submitter and _submitter != _author and not payload.is_internal:
            _s_row = await lookup_user_email(db, _submitter)
            if _s_row and _s_row not in _notified:
                await asyncio.to_thread(
                    notify_ticket_comment,
                    ticket_id,
                    getattr(ticket, "title", ""),
                    _author,
                    comment.content,
                    _s_row,
                )
                _notified.add(_s_row)

        # If the ticket is unassigned and the comment is from the student, notify all course staff
        if not _assigned and _author == _submitter and not payload.is_internal:
            _course_id = getattr(ticket, "course_id", None)
            if _course_id:
                _staff_emails = await course_staff_emails(db, _course_id)
                for _sem in _staff_emails:
                    if _sem not in _notified:
                        await asyncio.to_thread(
                            notify_ticket_comment,
                            ticket_id,
                            getattr(ticket, "title", ""),
                            _author,
                            comment.content,
                            _sem,
                        )
                        _notified.add(_sem)
    except Exception:
        logger.debug("comment_email_notification_failed", ticket_id=ticket_id, exc_info=True)

    return SupportCommentResponse.model_validate(comment)


# ===============================================================================
# SUPPORT LINKS CRUD (persisted shareable links)


@router.post(
    "/support/tickets/purge",
    response_model=TicketPurgeResponse,
    summary="Purge finished support tickets",
)
async def purge_support_tickets(
    request: Request,
    db: DbSession,
    _csrf: CSRFCheck,
    _admin: User = Depends(get_current_admin),
    _rate: RateLimitDep = None,
) -> TicketPurgeResponse:
    """Delete resolved and closed tickets older than N hours. Admin only.

    Tickets were the last admin surface with no way to clear itself: Job History
    and the Event Pipeline both purge by age, while a resolved ticket stayed in
    the table for good. Only FINISHED tickets are eligible - an open or
    in-progress ticket is somebody waiting for an answer, and no age makes it
    safe to delete. Comments go with their ticket through the FK's own cascade.

    ``course_id`` limits it to one course. The page offers the purge on ONE
    course's ticket list, and without it that menu cleared every course of every
    term while the dialog named none.
    """
    body = await request.json()
    try:
        hours = int(body.get("hours", 720))
    except (TypeError, ValueError):
        raise_bad_request("hours must be an integer")
    if not (1 <= hours <= _PURGE_MAX_HOURS):
        raise_bad_request(f"hours must be between 1 and {_PURGE_MAX_HOURS}")
    course_id: uuid.UUID | None = None
    if body.get("course_id"):
        try:
            course_id = uuid.UUID(str(body["course_id"]))
        except ValueError:
            raise_bad_request("course_id must be a UUID")

    # The maximum means "every finished ticket", not "older than ten years" - a
    # cutoff that far back matches nothing, which is how the jobs purge's own
    # "Everything" came to delete nothing.
    where: list[ColumnElement[bool]] = [SupportTicket.status.in_(("resolved", "closed"))]
    if course_id is not None:
        where.append(SupportTicket.course_id == course_id)
    if hours < _PURGE_MAX_HOURS:
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        # `resolved_at` is set when a ticket reaches either terminal status; fall
        # back to when it last changed for rows that predate that column.
        where.append(func.coalesce(SupportTicket.resolved_at, SupportTicket.updated_at) < cutoff)

    deleted = int(
        (await db.execute(select(func.count(SupportTicket.id)).where(*where))).scalar() or 0
    )
    if deleted:
        await db.execute(delete(SupportTicket).where(*where))
        await db.commit()

    logger.info(
        "support_tickets_purged", hours=hours, course_id=str(course_id or ""), deleted=deleted
    )
    return TicketPurgeResponse(deleted=deleted, hours=hours)


@router.post(
    "/support/tickets/delete",
    response_model=TicketPurgeResponse,
    summary="Delete selected support tickets",
)
async def delete_support_tickets(
    request: Request,
    db: DbSession,
    _csrf: CSRFCheck,
    _admin: User = Depends(get_current_admin),
    _rate: RateLimitDep = None,
) -> TicketPurgeResponse:
    """Delete the tickets the reader ticked. Admin only.

    The age purge beside this answers "clear the old ones"; this answers "clear
    THESE". Same rule decides what may go: only `resolved` and `closed`, because
    an open ticket is somebody waiting for an answer. The count in the reply is
    what actually went, so a reader who ticked an open one is told it was kept.
    """
    body = await request.json()
    ids = body.get("ids")
    if not isinstance(ids, list) or not ids:
        raise_bad_request("ids must be a non-empty list")
    if len(ids) > 1000:
        raise_bad_request("too many ids (max 1000)")

    parsed: list[int] = []
    for raw in ids:
        try:
            parsed.append(int(raw))
        except (TypeError, ValueError):
            raise_bad_request(f"not a ticket id: {raw!r}")

    where: list[ColumnElement[bool]] = [
        SupportTicket.id.in_(parsed),
        SupportTicket.status.in_(("resolved", "closed")),
    ]
    deleted = int(
        (await db.execute(select(func.count(SupportTicket.id)).where(*where))).scalar() or 0
    )
    if deleted:
        await db.execute(delete(SupportTicket).where(*where))
        await db.commit()

    logger.info("support_tickets_deleted", requested=len(parsed), deleted=deleted)
    return TicketPurgeResponse(deleted=deleted, hours=0)
