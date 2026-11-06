"""Event pipeline admin API - replay, DLQ management, audit queries.

All endpoints require admin or teacher role.
Gated behind FEATURE_EVENT_PIPELINE flag.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, or_, select

from app.api.errors import raise_bad_request, raise_not_found, raise_service_unavailable
from app.db.repositories.event_repo import EventRepository
from app.dependencies import (
    AdminAuth,
    CSRFCheck,
    DbSession,
    RateLimitDep,
    SettingsDep,
    TeacherAuth,
)
from app.models.webhook_event import WebhookEvent
from app.schemas.events import (
    DLQEventSummary,
    DLQListResponse,
    PurgeResponse,
    RecentEventsResponse,
    RecentEventSummary,
    ReplayRequest,
    ReplayResponse,
    ResurrectResponse,
)
from app.services.audit import write_audit
from app.services.events import enqueue_event_processing

logger = structlog.get_logger(__name__)

router = APIRouter()

# The value the UI sends for "Everything": ten years, used as a sentinel for
# "no age limit" rather than as a real age.
_PURGE_MAX_HOURS = 87600


# -- Replay --


@router.post("/replay", response_model=ReplayResponse)
async def replay_events(
    body: ReplayRequest,
    db: DbSession,
    settings: SettingsDep,
    auth: AdminAuth,
    _csrf: CSRFCheck,
) -> ReplayResponse:
    """Replay events from a time range. Creates replay copies and enqueues them."""
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    repo = EventRepository(db)
    if body.event_ids:
        # An explicit selection from the events table: replay exactly the rows
        # the user ticked, not everything that shares their time window.
        originals = await repo.get_events_by_ids(body.event_ids)
    else:
        originals = await repo.get_events_for_replay(
            start=body.start,  # type: ignore[arg-type]  # validated as a pair
            end=body.end,  # type: ignore[arg-type]
            project_id=body.project_id,
            event_type=body.event_type,
            limit=body.limit,
        )

    replayed_ids: list[str] = []
    for original in originals:
        replay = await repo.create_replay_event(original)
        replayed_ids.append(str(replay.id))

    actor = auth.get("user", auth.get("role", "teacher"))
    await write_audit(
        db,
        action="event.replay",
        actor=actor,
        entity_type="webhook_event",
        detail={
            "start": body.start.isoformat() if body.start else None,
            "end": body.end.isoformat() if body.end else None,
            "project_id": body.project_id,
            "event_type": body.event_type,
            "selected_count": len(body.event_ids) if body.event_ids else None,
            "replayed_count": len(replayed_ids),
        },
    )
    await db.commit()

    for rid in replayed_ids:
        try:
            enqueue_event_processing(rid)
        except Exception:
            logger.warning("failed_to_enqueue_replay", event_id=rid)

    logger.info("events_replayed", count=len(replayed_ids))
    return ReplayResponse(replayed=len(replayed_ids), event_ids=replayed_ids)


# -- Dead-letter queue --


def _event_actor(payload: dict[str, Any] | None) -> str | None:
    """Who triggered the event, as GitLab reported them."""
    if not isinstance(payload, dict):
        return None
    user = payload.get("user")
    if isinstance(user, dict):
        name = user.get("username") or user.get("name")
        if name:
            return str(name)[:80]
    # Push events name the pusher at the top level instead.
    for key in ("user_username", "user_name"):
        value = payload.get(key)
        if value:
            return str(value)[:80]
    return None


def _event_summary(event_type: str, payload: dict[str, Any] | None) -> str | None:
    """One line describing what actually happened.

    "merge_request" alone does not tell a teacher whether something was opened,
    merged or closed, which is the part they care about.
    """
    if not isinstance(payload, dict):
        return None
    attrs = payload.get("object_attributes")
    attrs = attrs if isinstance(attrs, dict) else {}

    if event_type in ("merge_request", "issue", "confidential_issue"):
        action = attrs.get("action") or attrs.get("state") or ""
        title = attrs.get("title") or ""
        iid = attrs.get("iid")
        ref = f"!{iid}" if event_type == "merge_request" and iid else (f"#{iid}" if iid else "")
        return " ".join(x for x in (str(action), ref, str(title)[:80]) if x) or None
    if event_type == "pipeline":
        return f"{attrs.get('status', '')} {attrs.get('ref', '')}".strip() or None
    if event_type in ("note", "confidential_note"):
        return str(attrs.get("note", ""))[:80] or None
    if event_type in ("push", "tag_push"):
        commits = payload.get("total_commits_count")
        ref = str(payload.get("ref", "")).split("/")[-1]
        return f"{commits} commit(s) to {ref}".strip() if commits is not None else ref or None
    return None


async def _resolve_event_context(
    db: DbSession, project_ids: set[int]
) -> dict[int, dict[str, str | None]]:
    """Map GitLab project id -> human context (project path, group, course)."""
    if not project_ids:
        return {}

    from app.models.course import Course
    from app.models.project import GitLabProject
    from app.models.team import Team

    stmt = (
        select(
            GitLabProject.gitlab_project_id,
            GitLabProject.gitlab_project_path,
            Team.name,
            Course.code,
            Course.name,
            Course.academic_year,
            Course.semester,
        )
        .join(Team, GitLabProject.team_id == Team.id)
        .join(Course, Team.course_id == Course.id)
        .where(GitLabProject.gitlab_project_id.in_(project_ids))
    )
    rows = (await db.execute(stmt)).all()
    return {
        gid: {
            "project_path": path,
            "team_name": team,
            "course_code": code,
            "course_name": cname,
            # The course's term: the same code runs every year, and an event
            # from last summer's ZSI is not one from this summer's.
            "course_academic_year": year,
            "course_semester": semester,
        }
        for gid, path, team, code, cname, year, semester in rows
    }


@router.get("/{event_id}/payload")
async def get_event_payload(
    event_id: UUID,
    db: DbSession,
    settings: SettingsDep,
    auth: TeacherAuth,
) -> JSONResponse:
    """The raw delivered payload for one event.

    The pipeline page has always had a payload viewer, but the handler behind
    its Details button called a function that was never defined, so the modal
    could not be filled. This is what it needs.
    """
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    event = await db.get(WebhookEvent, event_id)
    if event is None:
        raise_not_found("Event not found")

    return JSONResponse(
        {
            "id": str(event.id),
            "event_type": event.event_type,
            "action": event.action,
            "gitlab_project_id": event.gitlab_project_id,
            "received_at": event.received_at.isoformat() if event.received_at else None,
            "processed": bool(event.processed),
            "processed_at": event.processed_at.isoformat() if event.processed_at else None,
            "dead_letter_at": event.dead_letter_at.isoformat() if event.dead_letter_at else None,
            "retry_count": event.retry_count,
            "processing_error": event.processing_error,
            "summary": _event_summary(event.event_type, event.payload),
            "actor": _event_actor(event.payload),
            "payload": event.payload,
        }
    )


async def build_recent_events_payload(
    db: Any, limit: int, event_type: str | None
) -> RecentEventsResponse:
    """Build the recent-events window. Shared by the /recent endpoint and the
    admin Events page, which inlines the first window into the HTML so the table
    renders on load with no fetch and no loader - the same instant-rows behaviour
    User Management has, instead of the async "Loading..." the page used to show.
    """
    repo = EventRepository(db)
    events = await repo.get_recent_events(limit=limit, event_type=event_type)

    # Resolve project -> team -> course once for the whole page rather than per
    # row, so the feed can say which course and group an event belongs to
    # instead of showing a bare GitLab project id.
    context = await _resolve_event_context(db, {e.gitlab_project_id for e in events})

    summaries = [
        RecentEventSummary(
            id=str(e.id),
            event_type=e.event_type,
            gitlab_project_id=e.gitlab_project_id,
            received_at=e.received_at,
            processed=bool(e.processed),
            processed_at=e.processed_at,
            retry_count=e.retry_count,
            dead_letter_at=e.dead_letter_at,
            processing_error=e.processing_error[:200] if e.processing_error else None,
            actor=_event_actor(e.payload),
            summary=_event_summary(e.event_type, e.payload),
            **context.get(e.gitlab_project_id, {}),
        )
        for e in events
    ]
    return RecentEventsResponse(count=len(summaries), events=summaries)


@router.get("/recent", response_model=RecentEventsResponse)
async def list_recent_events(
    db: DbSession,
    settings: SettingsDep,
    auth: TeacherAuth,
    limit: int = Query(50, ge=1, le=200),
    event_type: str | None = Query(None),
) -> RecentEventsResponse:
    """Most recent events regardless of outcome.

    The pipeline page only listed the dead-letter queue, so a healthy system was
    indistinguishable from one receiving nothing. This is the normal flow.
    """
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    return await build_recent_events_payload(db, limit, event_type)


async def build_dlq_payload(db: Any, limit: int, event_type: str | None) -> DLQListResponse:
    """Build the dead-letter-queue window. Shared by the /dlq endpoint and the
    admin Events page, which inlines it so the DLQ tab renders on load with no
    fetch and no loader - the same instant-rows behaviour as every other table."""
    repo = EventRepository(db)
    events = await repo.get_dead_letter_events(limit=limit, event_type=event_type)

    summaries = [
        DLQEventSummary(
            id=str(e.id),
            event_type=e.event_type,
            gitlab_project_id=e.gitlab_project_id,
            dead_letter_at=e.dead_letter_at,
            dead_letter_reason=e.dead_letter_reason,
            retry_count=e.retry_count,
            processing_error=e.processing_error[:200] if e.processing_error else None,
        )
        for e in events
    ]
    return DLQListResponse(count=len(summaries), events=summaries)


@router.get("/dlq", response_model=DLQListResponse)
async def list_dead_letter_events(
    db: DbSession,
    settings: SettingsDep,
    auth: TeacherAuth,
    limit: int = Query(100, ge=1, le=500),
    event_type: str | None = Query(None),
) -> DLQListResponse:
    """List events in the dead-letter queue."""
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    return await build_dlq_payload(db, limit, event_type)


@router.post("/dlq/{event_id}/resurrect", response_model=ResurrectResponse)
async def resurrect_event(
    event_id: UUID,
    db: DbSession,
    settings: SettingsDep,
    auth: AdminAuth,
    _csrf: CSRFCheck,
) -> ResurrectResponse:
    """Remove event from DLQ and re-enqueue for processing."""
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    repo = EventRepository(db)
    event = await repo.get_by_id(event_id)
    if event is None:
        raise_not_found("Event not found")
    if event.dead_letter_at is None:
        raise_bad_request("Event is not in the dead-letter queue")

    await repo.resurrect_from_dead_letter(event_id)

    actor = auth.get("user", auth.get("role", "teacher"))
    await write_audit(
        db,
        action="event.resurrect",
        actor=actor,
        entity_type="webhook_event",
        entity_id=event_id,
        detail={"previous_reason": event.dead_letter_reason},
    )
    await db.commit()

    try:
        enqueue_event_processing(str(event_id))
    except Exception:
        logger.warning("failed_to_enqueue_resurrected", event_id=str(event_id))

    return ResurrectResponse(event_id=str(event_id), status="resurrected")


# -- Purge --


@router.post("/purge", response_model=PurgeResponse)
async def purge_events(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
    auth: AdminAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> PurgeResponse:
    """Delete handled events older than N hours. Admin only.

    Job History has had this since it was built; the Event Pipeline collects the
    same kind of rows and had no way to clear them, so the table only ever grew.

    ``scope`` says what may go:
      ``processed`` - events that were handled, and are therefore finished with;
      ``dlq``       - events that were given up on, once they are old enough;
      ``all``       - both.
    A pending event is never removed whatever the scope: it has not been dealt
    with yet, and deleting it would drop work rather than tidy up after it.
    """
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    body = await request.json()
    try:
        hours = int(body.get("hours", 24))
    except (TypeError, ValueError):
        raise_bad_request("hours must be an integer")
    # Same bounds as the jobs purge, so "Everything" means the same thing here.
    if not (1 <= hours <= _PURGE_MAX_HOURS):
        raise_bad_request("hours must be between 1 and 87600")
    scope = str(body.get("scope", "processed"))
    if scope not in ("processed", "dlq", "all"):
        raise_bad_request("scope must be processed, dlq, or all")

    # `hours` at its maximum means "everything handled", not "older than ten
    # years" - a cutoff that far back matches no row at all, which is how the
    # jobs purge's own "Everything" came to delete nothing.
    unlimited = hours >= _PURGE_MAX_HOURS
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    handled = []
    if scope in ("processed", "all"):
        handled.append(WebhookEvent.processed.is_(True))
    if scope in ("dlq", "all"):
        handled.append(WebhookEvent.dead_letter_at.is_not(None))

    where = [or_(*handled)]
    if not unlimited:
        where.append(WebhookEvent.received_at < cutoff)

    # COUNT, then delete. `rowcount` on a bulk ORM delete came back 0 while the
    # rows really had gone, so the toast said "Removed 0 event(s)" after clearing
    # thirteen - the same count-first shape the jobs purge already uses.
    deleted = int(
        (await db.execute(select(func.count(WebhookEvent.id)).where(*where))).scalar() or 0
    )
    if deleted:
        await db.execute(delete(WebhookEvent).where(*where))

    await write_audit(
        db,
        action="event.purge",
        actor=auth.get("user", auth.get("role", "admin")),
        entity_type="webhook_event",
        entity_id=None,
        detail={"hours": hours, "scope": scope, "deleted": deleted},
    )
    await db.commit()

    logger.info("events_purged", hours=hours, scope=scope, deleted=deleted)
    return PurgeResponse(deleted=deleted, scope=scope, hours=hours)


@router.post("/delete", response_model=PurgeResponse)
async def delete_events(
    request: Request,
    db: DbSession,
    settings: SettingsDep,
    auth: AdminAuth,
    _csrf: CSRFCheck,
    _rate: RateLimitDep,
) -> PurgeResponse:
    """Delete the events the reader ticked. Admin only.

    Purging by age answers "clear the old ones"; this answers "clear THESE",
    which is the question a reader looking at a table actually has. Job History
    has had both since it was built and the pipeline had neither.

    A PENDING event is skipped even when ticked, for the same reason the age
    purge skips it: it has not been dealt with yet, so removing it drops work.
    The response says how many actually went, so a reader who ticked a pending
    row can see it was kept.
    """
    if not settings.feature_event_pipeline:
        raise_service_unavailable("Event pipeline feature is disabled")

    body = await request.json()
    ids = body.get("ids")
    if not isinstance(ids, list) or not ids:
        raise_bad_request("ids must be a non-empty list")
    if len(ids) > 1000:
        raise_bad_request("too many ids (max 1000)")

    parsed: list[UUID] = []
    for raw in ids:
        try:
            parsed.append(UUID(str(raw)))
        except (TypeError, ValueError):
            raise_bad_request(f"not an event id: {raw!r}")

    where = [
        WebhookEvent.id.in_(parsed),
        or_(WebhookEvent.processed.is_(True), WebhookEvent.dead_letter_at.is_not(None)),
    ]
    deleted = int(
        (await db.execute(select(func.count(WebhookEvent.id)).where(*where))).scalar() or 0
    )
    if deleted:
        await db.execute(delete(WebhookEvent).where(*where))

    await write_audit(
        db,
        action="event.delete",
        actor=auth.get("user", auth.get("role", "admin")),
        entity_type="webhook_event",
        entity_id=None,
        detail={"requested": len(parsed), "deleted": deleted},
    )
    await db.commit()

    logger.info("events_deleted", requested=len(parsed), deleted=deleted)
    return PurgeResponse(deleted=deleted, scope="selected", hours=0)
