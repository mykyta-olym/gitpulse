"""Tests for event repository module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestEventRepositoryClass:
    """Tests for EventRepository class."""

    def test_event_repository_class_exists(self) -> None:
        from app.db.repositories.event_repo import EventRepository

        assert EventRepository is not None

    def test_event_repository_init(self) -> None:
        from app.db.repositories.event_repo import EventRepository

        mock_session = MagicMock()
        repo = EventRepository(mock_session)

        assert repo.session is mock_session


class TestEventRepositoryDedupChecks:
    """Tests for deduplication check methods."""

    @pytest.mark.asyncio
    async def test_exists_by_uuid_returns_true(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.exists_by_uuid("test-uuid-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_uuid_returns_false(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.exists_by_uuid("non-existent-uuid")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_by_delivery_id_returns_true(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.exists_by_delivery_id("delivery-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_delivery_id_returns_false(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.exists_by_delivery_id("non-existent")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists_by_payload_hash_returns_true(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.exists_by_payload_hash("abc123hash")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_payload_hash_returns_false(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.exists_by_payload_hash("non-existent-hash")

        assert result is False


class TestEventRepositoryCRUD:
    """Tests for CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_adds_and_flushes(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_event = MagicMock()

        repo = EventRepository(mock_session)
        result = await repo.create(mock_event)

        mock_session.add.assert_called_once_with(mock_event)
        mock_session.flush.assert_called_once()
        assert result is mock_event

    @pytest.mark.asyncio
    async def test_get_by_id_returns_event(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_event = MagicMock()
        event_id = uuid4()
        mock_session.get.return_value = mock_event

        repo = EventRepository(mock_session)
        result = await repo.get_by_id(event_id)

        assert result is mock_event

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_session.get.return_value = None
        event_id = uuid4()

        repo = EventRepository(mock_session)
        result = await repo.get_by_id(event_id)

        assert result is None


class TestEventRepositoryDeadLetterQueue:
    """Tests for dead-letter queue operations."""

    @pytest.mark.asyncio
    async def test_get_dead_letter_events(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.get_dead_letter_events(limit=50)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_dead_letter_events_with_event_type(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        result = await repo.get_dead_letter_events(event_type="push")

        assert result == []

    @pytest.mark.asyncio
    async def test_resurrect_from_dead_letter(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        event_id = uuid4()

        repo = EventRepository(mock_session)
        await repo.resurrect_from_dead_letter(event_id)

        mock_session.execute.assert_called_once()


class TestEventRepositoryReplay:
    """Tests for replay operations."""

    @pytest.mark.asyncio
    async def test_get_events_for_replay(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [MagicMock(), MagicMock()]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        start = datetime.now(UTC)
        end = datetime.now(UTC)
        result = await repo.get_events_for_replay(start, end)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_events_for_replay_with_filters(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        repo = EventRepository(mock_session)
        start = datetime.now(UTC)
        end = datetime.now(UTC)
        result = await repo.get_events_for_replay(
            start, end, project_id=123, event_type="merge_request", limit=500
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_create_replay_event(self):
        from app.db.repositories.event_repo import EventRepository

        mock_session = AsyncMock()
        mock_session.add = MagicMock()

        # Create mock original event
        original = MagicMock()
        original.id = uuid4()
        original.gitlab_event_uuid = "original-uuid-1234567890"
        original.event_type = "push"
        original.gitlab_object_kind = "push"
        original.gitlab_project_id = 123
        original.gitlab_object_id = 456
        original.action = "create"
        original.payload = {"data": "test"}
        original.payload_hash = "abc123"

        repo = EventRepository(mock_session)
        await repo.create_replay_event(original)

        mock_session.add.assert_called_once()
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
