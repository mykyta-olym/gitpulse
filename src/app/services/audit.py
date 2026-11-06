"""Thin helper for writing audit log entries."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def write_audit(
    session: AsyncSession,
    *,
    action: str,
    actor: str = "system",
    actor_ip: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    detail: dict[str, Any] | None = None,
    correlation_id: uuid.UUID | None = None,
) -> AuditLog:
    """Append an immutable audit log entry and flush."""
    entry = AuditLog(
        action=action,
        actor=actor,
        actor_ip=actor_ip,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail or {},
        correlation_id=correlation_id,
        timestamp=datetime.now(UTC),
    )
    session.add(entry)
    await session.flush()
    return entry
