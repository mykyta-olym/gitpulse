"""Service layer for multi-scope webhook configurations.

Lifecycle - rotate / revoke / authenticate / match / status.

Design rules:

* Plaintext secrets exist **only** in the response of the rotate call
  (one-time reveal).  They are *never* written to logs, audit trails,
  or any database column.
* Each configuration carries an HMAC-SHA256(SECRET_KEY, plaintext)
  *lookup* digest stored separately from the bcrypt hash.  Lookup is
  used for indexed authentication; the hash is used for verification.
* Rotation keeps the *previous* secret valid for ``ROTATION_GRACE``
  (24 h) so teachers can update GitLab without dropping deliveries.
* Audit events are written for ``webhook_config.create``,
  ``webhook_config.rotate``, ``webhook_config.revoke``,
  ``webhook_config.update``, ``webhook_config.activate``,
  ``webhook_config.deactivate``.
* Receiver matching is split into two phases for defence-in-depth:
  1. **Pool query** by HMAC lookup -> narrows the candidate set to
     rows that *could* hold this token (O(1) on indexed column).
  2. **Scope check** via :py:meth:`WebhookConfiguration.matches_payload`
     -> ensures the token may authenticate this specific payload.
  An attacker who steals one team's secret cannot replay it for
  projects outside that scope.
"""

from __future__ import annotations

import asyncio
import contextlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_configuration import WebhookConfiguration, WebhookScope
from app.security.webhook_auth import (
    compute_webhook_lookup_key,
    hash_webhook_secret,
    verify_webhook_token,
)
from app.services.audit import write_audit

logger = structlog.get_logger(__name__)

# -- Constants --------------------------------------------------------
ROTATION_GRACE = timedelta(hours=24)
"""How long the previous secret stays valid after a rotation."""

LAST_USED_RATE_LIMIT_SECONDS = 60
"""Minimum interval between ``last_used_at`` writes for one row.

Webhooks can fire dozens of times per second per project; updating the
row that often would create lock contention and WAL churn for no
operational gain.  60 s gives accurate "is it alive?" telemetry.
"""

SECRET_PLAINTEXT_PREFIX = "whsec_"  # noqa: S105 - non-secret format prefix
"""GitPulse webhook secret format: ``whsec_<48 hex chars>``.

The prefix lets log-scrubbers and secret-detection tools spot a leaked
token without false positives on hex strings.
"""


# -- Helpers ----------------------------------------------------------


def _new_plaintext() -> str:
    """Return a freshly-generated plaintext secret (192 bits of entropy)."""
    # 24 bytes = 48 hex chars = 192 bits, well above the 128-bit
    # threshold recommended by NIST SP 800-131A.
    return f"{SECRET_PLAINTEXT_PREFIX}{secrets.token_hex(24)}"


def _normalize_path(value: str | None) -> str | None:
    """Trim slashes / whitespace and lower-case GitLab paths."""
    if value is None:
        return None
    cleaned = value.strip().strip("/")
    return cleaned.lower() or None


def _validate_scope_payload(
    *,
    scope_type: str,
    gitlab_group_path: str | None,
    gitlab_project_ids: list[int] | None,
) -> None:
    """Raise ``ValueError`` if the scope payload is inconsistent.

    Mirrors the DB CHECK constraint so we surface a friendly error
    *before* hitting Postgres.
    """
    try:
        scope = WebhookScope(scope_type)
    except ValueError as exc:
        raise ValueError(f"Unknown scope_type '{scope_type}'") from exc

    if scope is WebhookScope.PROJECTS:
        if not gitlab_project_ids:
            raise ValueError("scope='projects' requires at least one project id")
        if any((not isinstance(i, int) or i <= 0) for i in gitlab_project_ids):
            raise ValueError("gitlab_project_ids must contain positive integers")
        if len(set(gitlab_project_ids)) != len(gitlab_project_ids):
            raise ValueError("gitlab_project_ids must be unique")
    elif scope in (WebhookScope.GROUP, WebhookScope.SUBGROUP):
        if not gitlab_group_path:
            raise ValueError(f"scope='{scope.value}' requires gitlab_group_path")


# -- Result types -----------------------------------------------------


@dataclass(slots=True)
class RotateResult:
    """Returned by :func:`rotate_configuration` and :func:`create_configuration`."""

    config: WebhookConfiguration
    plaintext: str
    first_time: bool
    previous_expires_at: datetime | None


@dataclass(slots=True)
class AuthMatch:
    """Returned by :func:`authenticate`."""

    config: WebhookConfiguration
    used_previous: bool


# -- CRUD -------------------------------------------------------------


async def create_configuration(
    db: AsyncSession,
    *,
    course_id: uuid.UUID,
    name: str,
    scope_type: str,
    gitlab_group_id: int | None = None,
    gitlab_group_path: str | None = None,
    gitlab_project_ids: list[int] | None = None,
    description: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    actor_label: str = "system",
    actor_ip: str | None = None,
    correlation_id: uuid.UUID | None = None,
) -> RotateResult:
    """Create a new webhook configuration with a freshly generated secret.

    Returns the newly persisted row plus the **one-time** plaintext
    secret - caller must surface it to the user immediately.
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("name is required")
    if len(name) > 120:
        raise ValueError("name is too long (max 120 chars)")

    gitlab_project_ids = sorted({int(i) for i in (gitlab_project_ids or [])})
    gitlab_group_path = _normalize_path(gitlab_group_path)
    _validate_scope_payload(
        scope_type=scope_type,
        gitlab_group_path=gitlab_group_path,
        gitlab_project_ids=gitlab_project_ids,
    )

    plaintext = _new_plaintext()
    config = WebhookConfiguration(
        course_id=course_id,
        name=name,
        description=description,
        scope_type=scope_type,
        gitlab_group_id=gitlab_group_id,
        gitlab_group_path=gitlab_group_path,
        gitlab_project_ids=gitlab_project_ids,
        secret_hash=await asyncio.to_thread(hash_webhook_secret, plaintext),
        secret_lookup=compute_webhook_lookup_key(plaintext),
        created_by=actor_user_id,
        is_active=True,
    )
    db.add(config)
    await db.flush()

    await write_audit(
        db,
        action="webhook_config.create",
        actor=actor_label,
        actor_ip=actor_ip,
        entity_type="webhook_configuration",
        entity_id=config.id,
        detail={
            "course_id": str(course_id),
            "name": name,
            "scope": config.scope_summary(),
            "scope_type": scope_type,
            "project_ids_count": len(gitlab_project_ids),
        },
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(config)

    logger.info(
        "webhook_config_created",
        config_id=str(config.id),
        course_id=str(course_id),
        scope=config.scope_summary(),
    )
    return RotateResult(
        config=config,
        plaintext=plaintext,
        first_time=True,
        previous_expires_at=None,
    )


async def update_configuration(
    db: AsyncSession,
    config: WebhookConfiguration,
    *,
    name: str | None = None,
    description: str | None = None,
    gitlab_group_id: int | None = None,
    gitlab_group_path: str | None = None,
    gitlab_project_ids: list[int] | None = None,
    is_active: bool | None = None,
    actor_user_id: uuid.UUID | None = None,
    actor_label: str = "system",
    actor_ip: str | None = None,
    correlation_id: uuid.UUID | None = None,
) -> WebhookConfiguration:
    """Update mutable fields on an existing configuration.

    Scope **type** is intentionally immutable - change of scope_type
    requires creating a new configuration so the audit trail stays
    coherent and the secret cannot accidentally inherit a wider blast
    radius.
    """
    changes: dict[str, Any] = {}
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("name cannot be empty")
        if len(name) > 120:
            raise ValueError("name is too long (max 120 chars)")
        if name != config.name:
            changes["name"] = {"old": config.name, "new": name}
            config.name = name
    if description is not None and description != config.description:
        changes["description"] = {"changed": True}
        config.description = description or None

    new_path = (
        _normalize_path(gitlab_group_path)
        if gitlab_group_path is not None
        else config.gitlab_group_path
    )
    new_ids = (
        sorted({int(i) for i in gitlab_project_ids})
        if gitlab_project_ids is not None
        else list(config.gitlab_project_ids or [])
    )
    new_group_id = gitlab_group_id if gitlab_group_id is not None else config.gitlab_group_id

    _validate_scope_payload(
        scope_type=config.scope_type,
        gitlab_group_path=new_path,
        gitlab_project_ids=new_ids,
    )

    if new_path != config.gitlab_group_path:
        changes["gitlab_group_path"] = {"old": config.gitlab_group_path, "new": new_path}
        config.gitlab_group_path = new_path
    if new_group_id != config.gitlab_group_id:
        changes["gitlab_group_id"] = {"old": config.gitlab_group_id, "new": new_group_id}
        config.gitlab_group_id = new_group_id
    if new_ids != list(config.gitlab_project_ids or []):
        changes["gitlab_project_ids"] = {
            "old_count": len(config.gitlab_project_ids or []),
            "new_count": len(new_ids),
        }
        config.gitlab_project_ids = new_ids

    if is_active is not None and is_active != config.is_active:
        changes["is_active"] = {"old": config.is_active, "new": is_active}
        config.is_active = is_active

    if not changes:
        return config

    await db.flush()

    action = "webhook_config.update"
    if "is_active" in changes:
        action = "webhook_config.activate" if config.is_active else "webhook_config.deactivate"
    await write_audit(
        db,
        action=action,
        actor=actor_label,
        actor_ip=actor_ip,
        entity_type="webhook_configuration",
        entity_id=config.id,
        detail={
            "course_id": str(config.course_id),
            "scope": config.scope_summary(),
            "changes": changes,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
        },
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(config)
    return config


async def rotate_configuration(
    db: AsyncSession,
    config: WebhookConfiguration,
    *,
    actor_user_id: uuid.UUID | None = None,
    actor_label: str = "system",
    actor_ip: str | None = None,
    correlation_id: uuid.UUID | None = None,
) -> RotateResult:
    """Generate a new secret and demote the current one to *previous*.

    The previous secret remains valid for :data:`ROTATION_GRACE` so
    GitLab can be updated without dropping deliveries.
    """
    plaintext = _new_plaintext()
    new_hash = await asyncio.to_thread(hash_webhook_secret, plaintext)
    new_lookup = compute_webhook_lookup_key(plaintext)

    previous_expires_at: datetime | None = None
    if config.secret_hash:
        # Demote current -> previous.
        config.secret_hash_previous = config.secret_hash
        config.secret_lookup_previous = config.secret_lookup
        previous_expires_at = datetime.now(UTC) + ROTATION_GRACE
        config.previous_expires_at = previous_expires_at

    config.secret_hash = new_hash
    config.secret_lookup = new_lookup
    config.rotated_at = datetime.now(UTC)
    config.is_active = True

    await db.flush()
    await write_audit(
        db,
        action="webhook_config.rotate",
        actor=actor_label,
        actor_ip=actor_ip,
        entity_type="webhook_configuration",
        entity_id=config.id,
        detail={
            "course_id": str(config.course_id),
            "scope": config.scope_summary(),
            "previous_expires_at": previous_expires_at.isoformat() if previous_expires_at else None,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
        },
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(config)

    logger.info(
        "webhook_config_rotated",
        config_id=str(config.id),
        course_id=str(config.course_id),
        scope=config.scope_summary(),
    )
    return RotateResult(
        config=config,
        plaintext=plaintext,
        first_time=False,
        previous_expires_at=previous_expires_at,
    )


async def revoke_configuration(
    db: AsyncSession,
    config: WebhookConfiguration,
    *,
    actor_user_id: uuid.UUID | None = None,
    actor_label: str = "system",
    actor_ip: str | None = None,
    correlation_id: uuid.UUID | None = None,
    delete: bool = False,
) -> None:
    """Invalidate the secret immediately.

    By default the row is **kept** with cleared secret material and
    ``is_active=False`` so the audit trail (``created_at``,
    ``rotated_at``, ``last_used_at``) is preserved.  Pass
    ``delete=True`` to also drop the row.
    """
    config.secret_hash = ""
    config.secret_lookup = ""
    config.secret_hash_previous = None
    config.secret_lookup_previous = None
    config.previous_expires_at = None
    config.is_active = False

    await write_audit(
        db,
        action="webhook_config.revoke",
        actor=actor_label,
        actor_ip=actor_ip,
        entity_type="webhook_configuration",
        entity_id=config.id,
        detail={
            "course_id": str(config.course_id),
            "scope": config.scope_summary(),
            "deleted": delete,
            "actor_user_id": str(actor_user_id) if actor_user_id else None,
        },
        correlation_id=correlation_id,
    )

    if delete:
        await db.delete(config)
    else:
        await db.flush()
    await db.commit()

    logger.info(
        "webhook_config_revoked",
        config_id=str(config.id),
        course_id=str(config.course_id),
        deleted=delete,
    )


# -- Listing & status ------------------------------------------------


async def list_configurations(
    db: AsyncSession, *, course_id: uuid.UUID, include_inactive: bool = True
) -> list[WebhookConfiguration]:
    """Return all configurations for a course, newest-first."""
    stmt = select(WebhookConfiguration).where(WebhookConfiguration.course_id == course_id)
    if not include_inactive:
        stmt = stmt.where(WebhookConfiguration.is_active.is_(True))
    stmt = stmt.order_by(WebhookConfiguration.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return list(rows)


async def get_configuration(db: AsyncSession, config_id: uuid.UUID) -> WebhookConfiguration | None:
    """Fetch a single configuration by id (or None)."""
    return await db.get(WebhookConfiguration, config_id)


# -- Authentication --------------------------------------------------


async def authenticate(
    db: AsyncSession,
    *,
    token: str,
    project_gitlab_id: int | None,
    path_with_namespace: str | None,
    course_id: uuid.UUID | None = None,
) -> AuthMatch | None:
    """Look up a webhook configuration that authenticates ``token``
    AND whose scope matches the given payload context.

    * ``project_gitlab_id`` and ``path_with_namespace`` come from the
      GitLab payload's ``project`` object.  Either may be missing for
      malformed payloads - the function then degrades gracefully:
      project-list scope requires ``project_gitlab_id``;
      group/subgroup scope requires ``path_with_namespace``;
      ``course`` scope only matches when ``course_id`` is provided.
    * ``course_id``: when known (registered project), restrict the
      authentication pool to configurations belonging to that course.
      For orphan webhooks this is None and we authenticate against the
      *global* pool - the scope check still ensures payload eligibility.
    """
    if not token:
        return None

    lookup = compute_webhook_lookup_key(token)

    stmt = select(WebhookConfiguration).where(
        WebhookConfiguration.is_active.is_(True),
        or_(
            WebhookConfiguration.secret_lookup == lookup,
            WebhookConfiguration.secret_lookup_previous == lookup,
        ),
    )
    if course_id is not None:
        stmt = stmt.where(WebhookConfiguration.course_id == course_id)
    candidates = (await db.execute(stmt)).scalars().all()
    if not candidates:
        return None

    now = datetime.now(UTC)
    for cfg in candidates:
        # Scope check first (cheap) - reject configs that aren't
        # authorised to authenticate this payload before paying the
        # bcrypt cost.
        if not cfg.matches_payload(
            project_id=project_gitlab_id, path_with_namespace=path_with_namespace
        ):
            continue

        # Try current secret.
        if cfg.secret_hash and await asyncio.to_thread(
            verify_webhook_token,  # type: ignore[arg-type]
            token,
            cfg.secret_hash,
        ):
            return AuthMatch(config=cfg, used_previous=False)

        # Try previous secret if still within grace window.
        if (
            cfg.secret_hash_previous
            and cfg.previous_expires_at is not None
            and cfg.previous_expires_at >= now
            and await asyncio.to_thread(verify_webhook_token, token, cfg.secret_hash_previous)
        ):
            return AuthMatch(config=cfg, used_previous=True)

    return None


async def record_last_used(db: AsyncSession, *, config_id: uuid.UUID) -> None:
    """Update ``last_used_at`` for a configuration.

    Rate-limited to once per :data:`LAST_USED_RATE_LIMIT_SECONDS`.
    All errors are swallowed - telemetry must never block delivery.
    """
    try:
        cfg = await db.get(WebhookConfiguration, config_id)
        if cfg is None:
            return
        now = datetime.now(UTC)
        if cfg.last_used_at is not None:
            delta = (now - cfg.last_used_at).total_seconds()
            if delta < LAST_USED_RATE_LIMIT_SECONDS:
                return
        cfg.last_used_at = now
        await db.commit()
    except Exception:
        logger.debug("webhook_config_record_last_used_failed", exc_info=True)
        with contextlib.suppress(Exception):
            await db.rollback()
