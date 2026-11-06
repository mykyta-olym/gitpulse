"""The monitoring stack's state for the signed-in reader (app.observability.insights)."""

from fastapi import APIRouter, Depends, Request, Response

from app.dependencies import get_current_user
from app.i18n import translate_text
from app.models.user import User
from app.observability import insights
from app.schemas.observability import ObservabilityStatusResponse, ServiceNotice

router = APIRouter(prefix="/observability", tags=["Observability"])


@router.get(
    "/status",
    response_model=ObservabilityStatusResponse,
    response_model_exclude_none=True,
    summary="Service notices for the signed-in reader",
)
async def observability_status(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
) -> ObservabilityStatusResponse:
    """The notices of the alerts firing now that affect the reader's role.

    Polled by every page (core health-monitor.js) for shared service notices;
    the answer is cached in `insights`, so the poll costs Prometheus
    one read per process per 20 s whatever the number of open pages.
    """
    response.headers["Cache-Control"] = "no-store"
    snap = await insights.snapshot()
    if not snap.reachable:
        return ObservabilityStatusResponse(state="unknown", notices=[])
    locale = getattr(request.state, "locale", "sk")
    notices = [
        ServiceNotice(
            key=n["key"],
            text=translate_text(locale, n["text"]),
            action_href=n.get("action_href"),
            action_label=(
                translate_text(locale, n["action_label"]) if n.get("action_label") else None
            ),
        )
        for n in insights.notices_for(snap, current_user.role)
    ]
    return ObservabilityStatusResponse(state="degraded" if notices else "ok", notices=notices)
