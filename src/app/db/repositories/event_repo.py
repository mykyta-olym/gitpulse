"""Repository for webhook events: dedup, DLQ, and replay operations."""

import uuid as _uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_event import WebhookEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # -- Dedup checks (triple idempotency) --

    async def exists_by_uuid(self, gitlab_event_uuid: str) -> bool:
        """Check if event with this UUID already exists."""
        stmt = select(WebhookEvent.id).where(WebhookEvent.gitlab_event_uuid == gitlab_event_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_delivery_id(self, delivery_id: str) -> bool:
        """Check if event with this GitLab delivery ID already exists."""
        stmt = select(WebhookEvent.id).where(WebhookEvent.gitlab_delivery_id == delivery_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def exists_by_payload_hash(self, payload_hash: str) -> bool:
        """Check if event with this SHA-256 payload hash already exists."""
        stmt = select(WebhookEvent.id).where(WebhookEvent.payload_hash == payload_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # -- CRUD --

    async def create(self, event: WebhookEvent) -> WebhookEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_id(self, event_id: UUID) -> WebhookEvent | None:
        return await self.session.get(WebhookEvent, event_id)

    # -- Dead-letter queue --

    async def get_recent_events(
        self, limit: int = 50, event_type: str | None = None
    ) -> list[WebhookEvent]:
        """Most recently received events, whatever their outcome.

        The pipeline page only ever showed the dead-letter queue, so a working
        system looked identical to one receiving nothing at all. This is the
        feed that shows the normal flow, with failures still distinguishable by
        their dead_letter_at / processing_error.
        """
        stmt = select(WebhookEvent).order_by(WebhookEvent.received_at.desc()).limit(limit)
        if event_type:
            stmt = stmt.where(WebhookEvent.event_type == event_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_dead_letter_events(
        self, limit: int = 100, event_type: str | None = None
    ) -> list[WebhookEvent]:
        """List events in the dead-letter queue."""
        stmt = (
            select(WebhookEvent)
            .where(WebhookEvent.dead_letter_at.isnot(None))
            .order_by(WebhookEvent.dead_letter_at.desc())
            .limit(limit)
        )
        if event_type:
            stmt = stmt.where(WebhookEvent.event_type == event_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def resurrect_from_dead_letter(self, event_id: UUID) -> None:
        """Remove event from DLQ and reset for reprocessing."""
        stmt = (
            update(WebhookEvent)
            .where(WebhookEvent.id == event_id)
            .values(
                dead_letter_at=None,
                dead_letter_reason=None,
                processed=False,
                processed_at=None,
                processing_error=None,
                retry_count=0,
            )
        )
        await self.session.execute(stmt)

    # -- Replay --

    async def get_events_for_replay(
        self,
        start: datetime,
        end: datetime,
        project_id: int | None = None,
        event_type: str | None = None,
        limit: int = 1000,
    ) -> list[WebhookEvent]:
        """Select events in a time range for replay."""
        stmt = (
            select(WebhookEvent)
            .where(
                WebhookEvent.received_at >= start,
                WebhookEvent.received_at <= end,
            )
            .order_by(WebhookEvent.received_at)
            .limit(limit)
        )
        if project_id:
            stmt = stmt.where(WebhookEvent.gitlab_project_id == project_id)
        if event_type:
            stmt = stmt.where(WebhookEvent.event_type == event_type)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_events_by_ids(self, event_ids: list[UUID]) -> list[WebhookEvent]:
        """Select specific events for replay.

        Replaying by id is what the events table offers: you tick the rows you
        can see and act on exactly those. A time range can only describe them
        indirectly, and silently sweeps in everything else that happens to fall
        inside it.
        """
        if not event_ids:
            return []
        stmt = (
            select(WebhookEvent)
            .where(WebhookEvent.id.in_(event_ids))
            .order_by(WebhookEvent.received_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_replay_event(self, original: WebhookEvent) -> WebhookEvent:
        """Create a replay copy of an event. Original is marked as replayed."""
        replay = WebhookEvent(
            gitlab_event_uuid=f"replay-{_uuid.uuid4().hex[:16]}-{original.gitlab_event_uuid[:40]}",
            event_type=original.event_type,
            gitlab_object_kind=original.gitlab_object_kind,
            gitlab_project_id=original.gitlab_project_id,
            gitlab_object_id=original.gitlab_object_id,
            action=original.action,
            payload=original.payload,  # immutable - same JSONB data
            payload_hash=original.payload_hash,
            gitlab_delivery_id=None,  # replay has no delivery ID
            received_at=datetime.now(UTC),
            replay_of_id=original.id,
        )
        self.session.add(replay)

        # Mark original as replayed
        stmt = update(WebhookEvent).where(WebhookEvent.id == original.id).values(is_replayed=True)
        await self.session.execute(stmt)
        await self.session.flush()
        return replay
