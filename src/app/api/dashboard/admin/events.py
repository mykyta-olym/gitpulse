"""Administration: the Events page (`/dashboard/admin/events`)."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

from app.api.dashboard._helpers import (
    _csrf_token,
    _feature_disabled_response,
    _role_context,
    _templates,
)
from app.config import get_settings
from app.dependencies import AdminAuth, DbSession

router = APIRouter()


# -- Admin: Event Pipeline Management --


@router.get("/admin/events", response_class=HTMLResponse)
async def admin_events_page(
    request: Request,
    db: DbSession,
    auth: AdminAuth,
) -> Response:
    """Event pipeline admin page: DLQ and replay UI."""
    settings = get_settings()
    if not settings.feature_event_pipeline:
        return _feature_disabled_response(
            request,
            "Event Pipeline",
            "The event pipeline admin interface is currently disabled.",
            "FEATURE_EVENT_PIPELINE=true",
            **_role_context(auth),
        )

    from sqlalchemy import select

    from app.models.course import Course
    from app.services.webhook_activity import compute_webhook_activity

    # ACTIVE courses only. An archived course receives no events by design, so
    # counting it made "courses with inactive webhooks" permanent from the
    # day a term ended - a warning nobody could clear.
    active_courses = list(
        (
            await db.scalars(select(Course).where(Course.is_active.is_(True)).order_by(Course.code))
        ).all()
    )
    report = await compute_webhook_activity(db, [c.id for c in active_courses])
    has_webhook = bool(report.configured)
    silent_courses = [c for c in active_courses if c.id in report.silent]

    # Inline the first recent-events window so the table renders on load with no
    # fetch and no "Loading..." spinner - the instant-rows behaviour every
    # server-rendered table (e.g. User Management) has. The JS renders from this
    # and only fetches for refresh / type-filter / pagination. 200 = the same
    # window the client used to request.
    from app.api.events import build_dlq_payload, build_recent_events_payload

    recent_payload = await build_recent_events_payload(db, limit=200, event_type=None)
    # The DLQ tab is inlined too (500 = the client's _DLQ_FETCH_LIMIT), so both
    # tabs render on load with no fetch and no loader.
    dlq_payload = await build_dlq_payload(db, limit=500, event_type=None)

    return _templates(request).TemplateResponse(
        request,
        "admin_events.html",
        {
            "request": request,
            "csrf_token": _csrf_token(auth),
            "webhooks_configured": has_webhook,
            "silent_courses": silent_courses,
            "recent_events_json": recent_payload.model_dump(mode="json"),
            "dlq_json": dlq_payload.model_dump(mode="json"),
            **_role_context(auth),
        },
    )
