"""Multi-scope webhook configuration management API.

Mounted under ``/api/v1`` (no prefix - full paths are declared on each
route) - see ``app.api.router``.

Endpoints:

* ``GET    /courses/{course_id}/webhook-configs``
        List all webhook configurations for a course.
* ``POST   /courses/{course_id}/webhook-configs``
        Create a new configuration.  Returns plaintext secret **once**.
* ``GET    /webhook-configs/{config_id}``
        Read a single configuration (no secret material).
* ``PATCH  /webhook-configs/{config_id}``
        Update mutable fields (name, description, scope payload, is_active).
* ``DELETE /webhook-configs/{config_id}``
        Revoke (default) or hard-delete a configuration.
* ``POST   /webhook-configs/{config_id}/rotate``
        Rotate the secret with 24 h grace.

Authorisation is delegated to ``check_course_access`` so behaviour
matches the rest of the courses API: course teachers, admins, and
API tokens with the right course scope are permitted.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Query, Request, status
from sqlalchemy import select as _select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import raise_forbidden, raise_not_found
from app.api.helpers.utils import check_course_access
from app.dependencies import ApiAuth, DbSession
from app.models.course import Course
from app.models.user import User
from app.models.webhook_configuration import WebhookConfiguration
from app.schemas.webhook_configs import (
    WebhookConfigCreate,
    WebhookConfigListResponse,
    WebhookConfigRead,
    WebhookConfigRevealResponse,
    WebhookConfigRevokeResponse,
    WebhookConfigUpdate,
)
from app.security.session_auth import get_current_session
from app.services import webhook_configs as wc_service
from app.services.courses import ensure_course_active

logger = structlog.get_logger(__name__)
router = APIRouter()


# -- Helpers ----------------------------------------------------------


async def _resolve_actor(
    request: Request, db: AsyncSession, auth_kind: str
) -> tuple[str, uuid.UUID | None]:
    """Return ``(actor_label, actor_user_id)`` for audit logging."""
    if auth_kind == "api_token":
        return "api_token", None

    from app.config import get_settings as _gs

    s = _gs()
    sess = get_current_session(
        request,
        s.secret_key,
        max_age=s.session_max_age_seconds,
        app_base_url=s.app_base_url,
        session_absolute_max_age=s.session_absolute_max_age_seconds,
    )
    if not sess:
        return "session", None
    username = sess.get("user", "session")
    gl_username = sess.get("gitlab_username", username)
    user = (
        await db.execute(
            _select(User)
            .where((User.gitlab_username == gl_username) | (User.username == username))
            .limit(1)
        )
    ).scalar_one_or_none()
    return username, (user.id if user else None)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _correlation_id(request: Request) -> uuid.UUID | None:
    cid = getattr(request.state, "correlation_id", None)
    if not cid:
        return None
    try:
        return uuid.UUID(str(cid))
    except (ValueError, TypeError):
        return None


def _base_url(request: Request) -> str:
    return f"{request.url.scheme}://{request.url.netloc}"


def _webhook_url(request: Request) -> str:
    return f"{_base_url(request)}/api/v1/webhooks/gitlab"


def _serialize_config(cfg: WebhookConfiguration) -> WebhookConfigRead:
    return WebhookConfigRead(
        id=cfg.id,
        course_id=cfg.course_id,
        name=cfg.name,
        description=cfg.description,
        scope_type=cfg.scope_type,  # type: ignore[arg-type]
        scope_summary=cfg.scope_summary(),
        gitlab_group_id=cfg.gitlab_group_id,
        gitlab_group_path=cfg.gitlab_group_path,
        gitlab_project_ids=list(cfg.gitlab_project_ids or []),
        is_active=cfg.is_active,
        created_at=cfg.created_at,
        rotated_at=cfg.rotated_at,
        last_used_at=cfg.last_used_at,
        previous_expires_at=cfg.previous_expires_at,
        has_previous_secret=bool(cfg.secret_hash_previous),
        has_secret=bool(cfg.secret_hash),
    )


def _build_setup_instructions(*, base: str, secret: str) -> dict[str, Any]:
    return {
        "url": f"{base}/api/v1/webhooks/gitlab",
        "secret": secret,
        "ssl_verification": True,
        "triggers": [
            "push_events",
            "tag_push_events",
            "issues_events",
            "confidential_issues_events",
            "merge_requests_events",
            "note_events",
            "confidential_note_events",
            "pipeline_events",
            "member_events",
            "subgroup_events",
        ],
        "steps": [
            "Open the relevant GitLab Group / Sub-group / Project -> Settings -> Webhooks.",
            "Paste the URL above into the URL field.",
            "Paste the secret token (shown only once).",
            "Enable ALL of the listed trigger events; leave SSL verification ON.",
            "Prefer configuring the webhook at the Group (or Sub-group) level: only "
            "group webhooks deliver Member and Subgroup events, which is how member "
            "add/remove and reassignment are captured automatically.",
            "Click Add webhook, then use the Test -> Push events button to verify.",
        ],
    }


def _grace_seconds(previous_expires_at: Any) -> int | None:
    if previous_expires_at is None:
        return None

    delta = previous_expires_at - datetime.now(UTC)
    secs = int(delta.total_seconds())
    return max(secs, 0)


async def _load_course(db: AsyncSession, course_id: uuid.UUID) -> Course:
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    return course


async def _load_config(db: AsyncSession, config_id: uuid.UUID) -> WebhookConfiguration:
    cfg = await wc_service.get_configuration(db, config_id)
    if not cfg:
        raise_not_found("Webhook configuration not found")
    return cfg


# -- Routes -----------------------------------------------------------


async def build_webhook_configs_payload(
    db: AsyncSession,
    course_id: uuid.UUID,
    request: Request,
    *,
    include_inactive: bool = True,
) -> WebhookConfigListResponse:
    """Public configuration data shared by the JSON API and settings table."""
    configs = await wc_service.list_configurations(
        db, course_id=course_id, include_inactive=include_inactive
    )
    return WebhookConfigListResponse(
        course_id=course_id,
        webhook_url=_webhook_url(request),
        configurations=[_serialize_config(c) for c in configs],
    )


@router.get(
    "/courses/{course_id}/webhook-configs",
    response_model=WebhookConfigListResponse,
)
async def list_course_webhook_configs(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: ApiAuth,
    request: Request,
    include_inactive: bool = Query(default=True),
) -> WebhookConfigListResponse:
    """List all webhook configurations attached to a course."""
    course = await _load_course(db, course_id)
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="view webhook configurations for courses you don't teach",
    )
    return await build_webhook_configs_payload(
        db, course_id, request, include_inactive=include_inactive
    )


@router.post(
    "/courses/{course_id}/webhook-configs",
    response_model=WebhookConfigRevealResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course_webhook_config(
    course_id: uuid.UUID,
    body: WebhookConfigCreate,
    db: DbSession,
    _auth: ApiAuth,
    request: Request,
) -> WebhookConfigRevealResponse:
    """Create a new webhook configuration with a fresh server-generated
    secret.  Returns the plaintext exactly once."""
    course = await _load_course(db, course_id)
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="manage webhook configurations for courses you don't teach",
    )
    # Issuing a live webhook secret is a write, and an archived course is
    # read-only - a direct API call must be refused, not just dimmed in the UI.
    await ensure_course_active(db, course_id)
    actor, actor_user_id = await _resolve_actor(request, db, _auth)
    try:
        result = await wc_service.create_configuration(
            db,
            course_id=course_id,
            name=body.name,
            scope_type=body.scope_type,
            gitlab_group_id=body.gitlab_group_id,
            gitlab_group_path=body.gitlab_group_path,
            gitlab_project_ids=body.gitlab_project_ids,
            description=body.description,
            actor_user_id=actor_user_id,
            actor_label=actor,
            actor_ip=_client_ip(request),
            correlation_id=_correlation_id(request),
        )
    except ValueError as exc:
        raise_forbidden(str(exc))
        raise  # unreachable, satisfies type checkers
    base = _base_url(request)
    return WebhookConfigRevealResponse(
        config=_serialize_config(result.config),
        webhook_secret=result.plaintext,
        first_time=result.first_time,
        rotated_at=result.config.rotated_at,
        previous_expires_at=result.previous_expires_at,
        grace_seconds=_grace_seconds(result.previous_expires_at),
        webhook_url=_webhook_url(request),
        setup_instructions=_build_setup_instructions(base=base, secret=result.plaintext),
    )


@router.get("/webhook-configs/{config_id}", response_model=WebhookConfigRead)
async def get_webhook_config(
    config_id: uuid.UUID,
    db: DbSession,
    _auth: ApiAuth,
    request: Request,
) -> WebhookConfigRead:
    cfg = await _load_config(db, config_id)
    course = await _load_course(db, cfg.course_id)
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="view webhook configurations for courses you don't teach",
    )
    return _serialize_config(cfg)


@router.patch("/webhook-configs/{config_id}", response_model=WebhookConfigRead)
async def update_webhook_config(
    config_id: uuid.UUID,
    body: WebhookConfigUpdate,
    db: DbSession,
    _auth: ApiAuth,
    request: Request,
) -> WebhookConfigRead:
    cfg = await _load_config(db, config_id)
    course = await _load_course(db, cfg.course_id)
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="manage webhook configurations for courses you don't teach",
    )
    actor, actor_user_id = await _resolve_actor(request, db, _auth)
    try:
        cfg = await wc_service.update_configuration(
            db,
            cfg,
            name=body.name,
            description=body.description,
            gitlab_group_id=body.gitlab_group_id,
            gitlab_group_path=body.gitlab_group_path,
            gitlab_project_ids=body.gitlab_project_ids,
            is_active=body.is_active,
            actor_user_id=actor_user_id,
            actor_label=actor,
            actor_ip=_client_ip(request),
            correlation_id=_correlation_id(request),
        )
    except ValueError as exc:
        raise_forbidden(str(exc))
        raise
    return _serialize_config(cfg)


@router.delete(
    "/webhook-configs/{config_id}",
    status_code=status.HTTP_200_OK,
    response_model=WebhookConfigRevokeResponse,
)
async def delete_webhook_config(
    config_id: uuid.UUID,
    db: DbSession,
    _auth: ApiAuth,
    request: Request,
    hard: bool = Query(
        default=False,
        description="When true, drop the row entirely. Default keeps it (audit-friendly).",
    ),
) -> WebhookConfigRevokeResponse:
    cfg = await _load_config(db, config_id)
    course = await _load_course(db, cfg.course_id)
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="manage webhook configurations for courses you don't teach",
    )
    actor, actor_user_id = await _resolve_actor(request, db, _auth)
    await wc_service.revoke_configuration(
        db,
        cfg,
        actor_user_id=actor_user_id,
        actor_label=actor,
        actor_ip=_client_ip(request),
        correlation_id=_correlation_id(request),
        delete=hard,
    )
    return WebhookConfigRevokeResponse(status="revoked", deleted=hard, config_id=config_id)


@router.post(
    "/webhook-configs/{config_id}/rotate",
    response_model=WebhookConfigRevealResponse,
)
async def rotate_webhook_config(
    config_id: uuid.UUID,
    db: DbSession,
    _auth: ApiAuth,
    request: Request,
) -> WebhookConfigRevealResponse:
    cfg = await _load_config(db, config_id)
    course = await _load_course(db, cfg.course_id)
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="manage webhook configurations for courses you don't teach",
    )
    actor, actor_user_id = await _resolve_actor(request, db, _auth)
    result = await wc_service.rotate_configuration(
        db,
        cfg,
        actor_user_id=actor_user_id,
        actor_label=actor,
        actor_ip=_client_ip(request),
        correlation_id=_correlation_id(request),
    )
    base = _base_url(request)
    return WebhookConfigRevealResponse(
        config=_serialize_config(result.config),
        webhook_secret=result.plaintext,
        first_time=result.first_time,
        rotated_at=result.config.rotated_at,
        previous_expires_at=result.previous_expires_at,
        grace_seconds=_grace_seconds(result.previous_expires_at),
        webhook_url=_webhook_url(request),
        setup_instructions=_build_setup_instructions(base=base, secret=result.plaintext),
    )
