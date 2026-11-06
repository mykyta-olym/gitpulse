"""Webhook receiver - ingests GitLab events with triple idempotency.

Deduplication layers:
  1. gitlab_delivery_id - X-Gitlab-Delivery header (if present)
  2. gitlab_event_uuid - X-Gitlab-Event-UUID header (or computed deterministic hash)
  3. payload_hash - SHA-256 of raw body (catches redelivery with same content but new UUID)

Raw payloads are stored immutably in the JSONB column and are never modified.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import (
    raise_payload_too_large,
    raise_service_unavailable,
    raise_unauthorized,
    raise_unprocessable,
)
from app.config import get_settings
from app.db.repositories.event_repo import EventRepository
from app.db.repositories.project_repo import ProjectRepository
from app.dependencies import DbSession
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.webhook_event import WebhookEvent
from app.observability.metrics import WEBHOOK_RECEIVED
from app.schemas.webhooks import WebhookAcceptedResponse, WebhookPayload
from app.security.webhook_auth import compute_webhook_lookup_key, verify_webhook_token
from app.services import webhook_configs
from app.services.events import enqueue_event_processing

logger = structlog.get_logger(__name__)

router = APIRouter()


def _compute_payload_hash(raw_body: bytes) -> str:
    """SHA-256 hash of the raw webhook body for content-based dedup."""
    return hashlib.sha256(raw_body).hexdigest()


def _inactive_project_webhook_response(project_id: uuid.UUID) -> WebhookAcceptedResponse:
    """Return the stable response for authenticated webhooks from unlinked projects."""
    return WebhookAcceptedResponse(
        status="ignored",
        event_id=str(project_id),
        message="Project is unlinked or inactive - webhook ignored",
    )


def _previous_secret_is_active(expires_at: datetime | None, now: datetime) -> bool:
    """Return True only while a rotated legacy secret is inside its grace window."""
    return expires_at is not None and expires_at >= now


async def _stamp_course_settings_last_used(
    db: AsyncSession, *, course_settings_id: uuid.UUID
) -> None:
    """Best-effort ``webhook_secret_last_used_at`` stamp on the legacy
    course-level secret. Throttled to one write per 60 s to avoid row
    thrash on bursty deliveries. Failures are swallowed by the caller.
    """
    cs = await db.get(CourseSettings, course_settings_id)
    if cs is None:
        return
    now = datetime.now(UTC)
    if (
        cs.webhook_secret_last_used_at is not None
        and (now - cs.webhook_secret_last_used_at).total_seconds() < 60
    ):
        return
    cs.webhook_secret_last_used_at = now
    await db.flush()


async def _stamp_last_used(
    db: AsyncSession, *, config_id: uuid.UUID | None, course_settings_id: uuid.UUID | None
) -> None:
    """``last_used_at`` on the secret that matched - a webhook configuration
    or a course's legacy secret. Best-effort: it must never block delivery."""
    try:
        if config_id is not None:
            await webhook_configs.record_last_used(db, config_id=config_id)
        elif course_settings_id is not None:
            await _stamp_course_settings_last_used(db, course_settings_id=course_settings_id)
    except Exception:
        logger.debug("webhook_last_used_stamp_failed", exc_info=True)


def _answer(event_type: str, status: str, event_id: str, message: str) -> WebhookAcceptedResponse:
    WEBHOOK_RECEIVED.labels(event_type=event_type).inc()
    return WebhookAcceptedResponse(status=status, event_id=event_id, message=message)


# -- The delivery -------------------------------------------------------------


async def _read(request: Request) -> tuple[bytes, dict[str, Any], WebhookPayload]:
    """The raw body, the parsed JSON, and the payload model - or a 413/422."""
    try:
        raw_body = await request.body()
        if len(raw_body) > get_settings().webhook_max_payload_bytes:
            raise_payload_too_large("Payload too large")
        payload_dict = json.loads(raw_body)
    except HTTPException:
        raise
    except Exception as exc:
        raise_unprocessable(f"Invalid JSON: {exc}")

    # "Permissive" is about EXTRA fields; the nested ids (`user.id`,
    # `project.id`, `object_attributes.id`) are still required, so a delivery
    # shaped even slightly differently raised a bare ValidationError here - a
    # 500, which the error boundary logs as an unhandled crash and GitLab
    # treats as "try again", redelivering the same unusable payload for 24
    # hours. A 422 naming the failing fields says what is wrong in GitLab's
    # own delivery log and stops the retries. The field NAMES only: the
    # values are student data.
    try:
        payload = WebhookPayload.model_validate(payload_dict)
    except ValidationError as exc:
        fields = ", ".join(
            ".".join(str(part) for part in error["loc"]) for error in exc.errors()[:5]
        )
        raise_unprocessable(f"Payload is not a GitLab webhook (bad or missing: {fields})")
    # The schema admits ``project: null`` - and ``{}.get`` on None was a 500.
    if payload.project is None:
        raise_unprocessable("Missing project.id in payload")
    return raw_body, payload_dict, payload


class _Delivery:
    """What identifies one delivery: its type, dedup keys and ids."""

    def __init__(
        self,
        request: Request,
        raw_body: bytes,
        payload_dict: dict[str, Any],
        payload: WebhookPayload,
        x_gitlab_event: str,
        x_gitlab_event_uuid: str | None,
        x_gitlab_delivery: str | None,
    ) -> None:
        assert payload.project is not None  # noqa: S101 - checked in _read
        self.payload_dict = payload_dict
        self.object_kind = payload.object_kind
        self.project_gitlab_id = payload.project.id
        self.path_with_namespace = payload.project.path_with_namespace
        self.delivery_id = x_gitlab_delivery
        self.event_type = payload.object_kind or x_gitlab_event.lower().replace(" hook", "")
        self.payload_hash = _compute_payload_hash(raw_body)
        self.attrs: dict[str, Any] = payload_dict.get("object_attributes", {})
        if x_gitlab_event_uuid:
            self.dedup_key = x_gitlab_event_uuid
        else:
            # A deterministic hash of the event's attributes.
            key = (
                f"{self.event_type}:{self.project_gitlab_id}:{self.attrs.get('id', '')}:"
                f"{self.attrs.get('action', '')}:{self.attrs.get('updated_at', '')}"
            )
            self.dedup_key = hashlib.sha256(key.encode()).hexdigest()
        correlation = getattr(request.state, "correlation_id", None)
        try:
            self.correlation_id = uuid.UUID(correlation) if correlation else None
        except ValueError:
            self.correlation_id = None

    def event(self, **extra: Any) -> WebhookEvent:
        """The event row: the raw payload stored immutably (the JSONB is never
        modified after insert)."""
        return WebhookEvent(
            gitlab_event_uuid=self.dedup_key,
            event_type=self.event_type,
            gitlab_object_kind=self.object_kind,
            gitlab_project_id=self.project_gitlab_id,
            gitlab_object_id=self.attrs.get("id"),
            action=self.attrs.get("action"),
            payload=self.payload_dict,
            payload_hash=self.payload_hash,
            gitlab_delivery_id=self.delivery_id,
            received_at=datetime.now(UTC),
            correlation_id=self.correlation_id,
            **extra,
        )


# -- A project GitPulse does not know (yet) -----------------------------------


async def _authenticate_orphan(db: AsyncSession, token: str, d: _Delivery) -> None:
    """The token must be one of the configured secrets of SOME course - a
    webhook configuration whose scope matches, or a course's legacy secret
    (current, or previous inside its grace window) - so a sender who knows no
    secret cannot inject events for unknown projects. 401 otherwise.

    Legacy secrets are found by their HMAC lookup digest through an index;
    rows set before the digest column existed (migration 037) are compared
    by bcrypt, so old installations authenticate while secrets are rotated.
    """
    config_id: uuid.UUID | None = None
    settings_id: uuid.UUID | None = None
    authed = False
    try:
        # course_id=None: any course's configuration; the scope check inside
        # authenticate() limits the reach.
        match = await webhook_configs.authenticate(
            db,
            token=token,
            project_gitlab_id=d.project_gitlab_id,
            path_with_namespace=d.path_with_namespace,
            course_id=None,
        )
    except Exception:
        logger.warning("webhook_config_orphan_lookup_failed", exc_info=True)
        match = None
    if match is not None:
        authed, config_id = True, match.config.id
    else:
        now = datetime.now(UTC)
        lookup = compute_webhook_lookup_key(token, get_settings().secret_key)
        settings_id = (
            await db.execute(
                select(CourseSettings.id)
                .where(
                    or_(
                        CourseSettings.webhook_secret_lookup == lookup,
                        and_(
                            CourseSettings.webhook_secret_lookup_previous == lookup,
                            CourseSettings.webhook_secret_previous_expires_at.is_not(None),
                            CourseSettings.webhook_secret_previous_expires_at >= now,
                        ),
                    )
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        authed = settings_id is not None
        if not authed:
            legacy = await db.execute(
                select(
                    CourseSettings.webhook_secret_hash,
                    CourseSettings.webhook_secret_hash_previous,
                    CourseSettings.webhook_secret_previous_expires_at,
                ).where(
                    CourseSettings.webhook_secret_hash.is_not(None),
                    CourseSettings.webhook_secret_lookup.is_(None),
                )
            )
            for current, previous, previous_expires_at in legacy.all():
                if current and await asyncio.to_thread(verify_webhook_token, token, current):
                    authed = True
                    break
                if (
                    previous
                    and _previous_secret_is_active(previous_expires_at, now)
                    and await asyncio.to_thread(verify_webhook_token, token, previous)
                ):
                    authed = True
                    break
    await _stamp_last_used(db, config_id=config_id, course_settings_id=settings_id)
    if not authed:
        logger.warning(
            "webhook_orphan_unauthenticated",
            gitlab_project_id=d.project_gitlab_id,
            event_type=d.event_type,
        )
        raise_unauthorized("Webhook token does not match any configured course secret")


def _rate_limit_orphan(request: Request, d: _Delivery) -> None:
    """10 per minute per client IP. The IP is request.client.host only:
    ProxyHeadersMiddleware already set it from a trusted proxy (Caddy), and
    reading x-forwarded-for here would let a sender rotate spoofed IPs past
    the bucket.

    FAILS CLOSED when Redis is unavailable: this path stores a full payload
    and is reachable by any authenticated source, so unbounded traffic during
    an outage would flood the deferred-event table. Registered projects take
    the other path and are not affected.
    """
    try:
        from app.redis_pool import get_redis
        from app.security.rate_limit import RateLimiter

        client_ip = request.client.host if request.client else ""
        if not client_ip:
            logger.warning("webhook_orphan_no_client_ip", gitlab_project_id=d.project_gitlab_id)
            raise_unauthorized("Cannot determine client IP for unregistered project webhook")
        # The shared pool, not a connection per webhook.
        allowed, _ = RateLimiter(get_redis(), prefix="rl:orphan").is_allowed(
            key=client_ip, max_requests=10, window_seconds=60
        )
        if not allowed:
            logger.warning(
                "webhook_orphan_rate_limited",
                gitlab_project_id=d.project_gitlab_id,
                client_ip=client_ip,
            )
            raise_unauthorized("Rate limit exceeded for unregistered project webhooks")
    except HTTPException:
        raise
    except Exception:
        logger.warning(
            "webhook_orphan_rate_limit_unavailable_blocking",
            gitlab_project_id=d.project_gitlab_id,
            exc_info=True,
        )
        raise_service_unavailable(
            "Rate limiter temporarily unavailable; "
            "unregistered-project webhooks are rejected until "
            "rate limiting is restored."
        )


async def _store_orphan(
    db: AsyncSession, request: Request, token: str, d: _Delivery
) -> WebhookAcceptedResponse:
    """A delivery for a project not registered (yet) - it can arrive before
    the registration completes. A 404 would have GitLab retry for 24 h and
    drop it, so it is stored, unprocessed, for manual review. Nothing
    reprocesses it automatically: once the project is registered, a manual
    sync pulls the current state, so no data is lost."""
    await _authenticate_orphan(db, token, d)
    if get_settings().feature_security_hardening:
        _rate_limit_orphan(request, d)
    logger.warning(
        "webhook_orphan_project",
        gitlab_project_id=d.project_gitlab_id,
        event_type=d.event_type,
        msg="Project not registered - storing webhook for deferred processing",
    )
    events = EventRepository(db)
    if await events.exists_by_uuid(d.dedup_key):
        return WebhookAcceptedResponse(
            status="duplicate", event_id=d.dedup_key, message="Already stored (orphan)"
        )
    event = d.event(processing_error="orphan_project:not_registered_at_receive_time")
    try:
        await events.create(event)
        await db.commit()
    except IntegrityError:
        await db.rollback()
    return _answer(
        d.event_type,
        "accepted",
        str(event.id),
        "Project not registered - stored for deferred processing",
    )


# -- A registered project -----------------------------------------------------


async def _authenticate(
    db: AsyncSession, token: str, project: GitLabProject, d: _Delivery
) -> Course | None:
    """Verify the token; return the project's course.

    In order: the project's own secret (owner-supplied at creation); a
    webhook configuration of the project's course whose scope matches
    (group / sub-group / project list / course-wide, each rotated, audited
    and revoked on its own) - tried BEFORE the legacy secret, so a new config
    wins and shows in its last_used_at; the course's legacy single secret.
    A legacy secret also accepts its previous value inside the rotation grace
    window. 401 when none matches.

    A token that is not the project's own secret goes on down the list. An
    imported project always has one - generated at import and never shown -
    so stopping at it would leave every course-wide secret unable to
    authenticate an imported project.
    """
    team = await db.get(Team, project.team_id)
    course = await db.get(Course, team.course_id) if team else None

    own_hash = project.webhook_secret_hash
    # The lookup digest, when the project keeps one, rules a token out
    # without paying for bcrypt.
    if (
        own_hash
        and project.webhook_secret_lookup in (None, compute_webhook_lookup_key(token))
        and await asyncio.to_thread(verify_webhook_token, token, own_hash)
    ):
        return course

    secret_hash: str | None = None
    previous_hash: str | None = None
    previous_expires_at: datetime | None = None
    settings_id: uuid.UUID | None = None
    config_id: uuid.UUID | None = None
    used_previous = False
    if course is not None:
        try:
            match = await webhook_configs.authenticate(
                db,
                token=token,
                project_gitlab_id=d.project_gitlab_id,
                path_with_namespace=d.path_with_namespace,
                course_id=course.id,
            )
            if match is not None:
                config_id, used_previous = match.config.id, match.used_previous
        except Exception:
            logger.warning("webhook_config_auth_lookup_failed", exc_info=True)
    if config_id is None and course is not None and course.settings:
        secret_hash = course.settings.webhook_secret_hash
        previous_hash = course.settings.webhook_secret_hash_previous
        previous_expires_at = course.settings.webhook_secret_previous_expires_at
        if secret_hash:
            settings_id = course.settings.id

    if not own_hash and not secret_hash and config_id is None:
        # Say WHY in the log. A rejected delivery used to leave only
        # `request_completed status=401` behind, and GitLab's delivery log the
        # generic "Authentication required" - so "the webhook stopped working"
        # had no first clue anywhere. These facts separate the real causes: no
        # secret anywhere, one configured elsewhere, a course that has none.
        # The token itself is never logged.
        logger.warning(
            "webhook_auth_no_secret",
            gitlab_project_id=d.project_gitlab_id,
            course_id=str(course.id) if course else None,
            project_has_own_secret=False,
            course_has_legacy_secret=bool(
                course is not None
                and course.settings is not None
                and course.settings.webhook_secret_hash
            ),
            msg=(
                "No webhook secret matched this project: no project secret, no "
                "webhook configuration for the token, and no course-level secret."
            ),
        )
        raise_unauthorized("Project has no webhook secret configured")

    # A matched configuration was verified inside authenticate() (bcrypt);
    # the project's own secret did not match, or this would not be reached.
    if config_id is None:
        valid = False
        if secret_hash:
            valid = await asyncio.to_thread(verify_webhook_token, token, secret_hash)
        # §3b: the previous secret too, for zero-downtime rotation.
        if (
            not valid
            and previous_hash
            and _previous_secret_is_active(previous_expires_at, datetime.now(UTC))
        ):
            valid = await asyncio.to_thread(verify_webhook_token, token, previous_hash)
            used_previous = True
        if not valid:
            logger.warning("webhook_auth_failed", gitlab_project_id=d.project_gitlab_id)
            raise_unauthorized("Invalid webhook token")
    if used_previous:
        logger.info(
            "webhook_auth_used_previous_secret",
            gitlab_project_id=d.project_gitlab_id,
            msg="Authenticated with previous webhook secret - rotation in progress",
        )
    await _stamp_last_used(db, config_id=config_id, course_settings_id=settings_id)
    return course


def _enqueue(event_id: str) -> str | None:
    """Queue the event for processing - unless backpressure sheds it: the
    high queue is overloaded, and the event, already stored, is retried by
    the 15-minute sweep. A failed backpressure check enqueues anyway."""
    settings = get_settings()
    if not settings.feature_backpressure:
        return enqueue_event_processing(event_id)
    try:
        from app.redis_pool import get_redis
        from app.services.backpressure import BackpressureConfig, QueueBackpressure

        backpressure = QueueBackpressure(
            get_redis(),
            BackpressureConfig(
                queue_high_watermark=settings.queue_high_watermark,
                queue_critical_watermark=settings.queue_critical_watermark,
            ),
        )
        if backpressure.should_accept_job("high", priority=2):
            return enqueue_event_processing(event_id)
        logger.warning(
            "webhook_backpressure_shed",
            event_id=event_id,
            queue_depth=backpressure.get_queue_depth("high"),
            msg="High queue overloaded - event persisted, sweep will retry",
        )
        return None
    except Exception:
        # Logged with the traceback, so a broken backpressure module or a
        # Redis outage does not silently lose the shedding.
        logger.warning("webhook_backpressure_check_failed", event_id=event_id, exc_info=True)
        return enqueue_event_processing(event_id)


async def _store(db: AsyncSession, d: _Delivery) -> WebhookAcceptedResponse:
    """Store the event once - checked by delivery id, event UUID and payload
    hash (a redelivery with a new UUID) - and queue it."""
    events = EventRepository(db)
    if d.delivery_id and await events.exists_by_delivery_id(d.delivery_id):
        logger.info("webhook_duplicate_delivery", delivery_id=d.delivery_id)
        return _answer(d.event_type, "duplicate", d.delivery_id, "Duplicate delivery ID")
    if await events.exists_by_uuid(d.dedup_key):
        logger.info("webhook_duplicate_uuid", dedup_key=d.dedup_key)
        return _answer(d.event_type, "duplicate", d.dedup_key, "Event already received")
    if await events.exists_by_payload_hash(d.payload_hash):
        logger.info("webhook_duplicate_hash", payload_hash=d.payload_hash[:16])
        return _answer(
            d.event_type, "duplicate", d.dedup_key, "Payload already received (hash match)"
        )
    try:
        event = await events.create(d.event())
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.info("webhook_duplicate_concurrent", dedup_key=d.dedup_key)
        return _answer(d.event_type, "duplicate", d.dedup_key, "Concurrent duplicate detected")

    if not _enqueue(str(event.id)):
        logger.warning("enqueue_returned_none", event_id=str(event.id))
    logger.info(
        "webhook_accepted",
        event_id=str(event.id),
        event_type=d.event_type,
        gitlab_project_id=d.project_gitlab_id,
        action=d.attrs.get("action"),
        payload_hash=d.payload_hash[:16],
    )
    return _answer(d.event_type, "accepted", str(event.id), "Event enqueued for processing")


@router.post("/gitlab", response_model=WebhookAcceptedResponse)
async def receive_gitlab_webhook(
    request: Request,
    db: DbSession,
    x_gitlab_token: str = Header(..., alias="X-Gitlab-Token"),
    x_gitlab_event: str = Header("", alias="X-Gitlab-Event"),
    x_gitlab_event_uuid: str | None = Header(None, alias="X-Gitlab-Event-UUID"),
    x_gitlab_delivery: str | None = Header(None, alias="X-Gitlab-Delivery"),
) -> WebhookAcceptedResponse:
    """Receive and store a GitLab webhook event.

    Triple idempotency:
    1. Check delivery ID (X-Gitlab-Delivery)
    2. Check event UUID (X-Gitlab-Event-UUID or deterministic hash)
    3. Check payload hash (SHA-256 of raw body)
    """
    raw_body, payload_dict, payload = await _read(request)
    d = _Delivery(
        request,
        raw_body,
        payload_dict,
        payload,
        x_gitlab_event,
        x_gitlab_event_uuid,
        x_gitlab_delivery,
    )
    project = await ProjectRepository(db).get_by_gitlab_id(d.project_gitlab_id)
    if project is None:
        return await _store_orphan(db, request, x_gitlab_token, d)

    course = await _authenticate(db, x_gitlab_token, project, d)
    if not project.is_active:
        logger.info(
            "webhook_inactive_project_ignored",
            gitlab_project_id=d.project_gitlab_id,
            project_id=str(project.id),
        )
        WEBHOOK_RECEIVED.labels(event_type=d.event_type).inc()
        return _inactive_project_webhook_response(project.id)
    # An archived course is read-only, so its data stops moving. GitLab keeps
    # delivering (the hook stays installed on purpose, so reactivating resumes
    # without touching GitLab), but ingesting would rewrite an archived
    # course's MRs/issues and fire "Live update" toasts on a page presented as
    # frozen. Acknowledged and dropped.
    if course is not None and not course.is_active:
        logger.info(
            "webhook_archived_course_ignored",
            gitlab_project_id=d.project_gitlab_id,
            project_id=str(project.id),
            course_id=str(course.id),
        )
        return _answer(
            d.event_type,
            "ignored",
            str(project.id),
            "Course is archived (read-only) - webhook ignored",
        )
    return await _store(db, d)
