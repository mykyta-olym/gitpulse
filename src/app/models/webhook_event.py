"""Raw webhook event storage for dedup, audit, replay, and dead-letter queue.

Deduplication strategy (triple idempotency):
  1. gitlab_event_uuid - X-Gitlab-Event-UUID header (UNIQUE)
  2. gitlab_delivery_id - X-Gitlab-Delivery header (indexed)
  3. payload_hash - SHA-256 of raw JSON body (indexed)

Dead-letter queue:
  Events that fail > max_retries are moved to DLQ by setting dead_letter_at.
  They are excluded from the recovery sweep and must be manually reviewed.

Replay:
  Replayed events reference the original via replay_of_id.
  The original is marked is_replayed=True for lineage tracking.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("idx_we_project_received", "gitlab_project_id", "received_at"),
        Index("idx_we_unprocessed", "received_at", postgresql_where="processed = false"),
        Index("idx_we_event_type", "event_type", "received_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    gitlab_event_uuid: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    gitlab_object_kind: Mapped[str | None] = mapped_column(String(50))
    gitlab_project_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gitlab_object_id: Mapped[int | None] = mapped_column(BigInteger)
    action: Mapped[str | None] = mapped_column(String(50))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # -- Triple idempotency (Patch 8) --
    payload_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    gitlab_delivery_id: Mapped[str | None] = mapped_column(String(100), index=True)

    # -- Dead-letter queue (Patch 11) --
    dead_letter_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dead_letter_reason: Mapped[str | None] = mapped_column(Text)

    # -- Replay lineage (Patch 9) --
    replay_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("webhook_events.id", ondelete="SET NULL")
    )
    is_replayed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
