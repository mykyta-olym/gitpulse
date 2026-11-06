"""Tests for audit service module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


def _mock_session() -> AsyncMock:
    session = AsyncMock()
    session.add = MagicMock()
    return session


class TestWriteAuditFunction:
    """Tests for write_audit function."""

    def test_write_audit_function_exists(self) -> None:
        from app.services.audit import write_audit

        assert callable(write_audit)

    @pytest.mark.asyncio
    async def test_write_audit_creates_entry(self):
        from app.services.audit import write_audit

        mock_session = _mock_session()

        await write_audit(
            mock_session,
            action="user.login",
            actor="user@example.com",
        )

        # Session.add should be called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_audit_with_all_params(self):
        from app.services.audit import write_audit

        mock_session = _mock_session()
        entity_id = uuid4()
        correlation_id = uuid4()

        await write_audit(
            mock_session,
            action="entity.updated",
            actor="admin",
            actor_ip="192.168.1.1",
            entity_type="Course",
            entity_id=entity_id,
            detail={"field": "name", "old": "A", "new": "B"},
            correlation_id=correlation_id,
        )

        mock_session.add.assert_called_once()
        added_entry = mock_session.add.call_args[0][0]

        assert added_entry.action == "entity.updated"
        assert added_entry.actor == "admin"
        assert added_entry.actor_ip == "192.168.1.1"
        assert added_entry.entity_type == "Course"
        assert added_entry.entity_id == entity_id
        assert added_entry.detail == {"field": "name", "old": "A", "new": "B"}
        assert added_entry.correlation_id == correlation_id

    @pytest.mark.asyncio
    async def test_write_audit_default_actor(self):
        from app.services.audit import write_audit

        mock_session = _mock_session()

        await write_audit(mock_session, action="system.event")

        added_entry = mock_session.add.call_args[0][0]
        assert added_entry.actor == "system"

    @pytest.mark.asyncio
    async def test_write_audit_empty_detail_becomes_dict(self):
        from app.services.audit import write_audit

        mock_session = _mock_session()

        await write_audit(mock_session, action="test", detail=None)

        added_entry = mock_session.add.call_args[0][0]
        assert added_entry.detail == {}

    @pytest.mark.asyncio
    async def test_write_audit_sets_timestamp(self):
        from app.services.audit import write_audit

        mock_session = _mock_session()

        before = datetime.now(UTC)
        await write_audit(mock_session, action="test")
        after = datetime.now(UTC)

        added_entry = mock_session.add.call_args[0][0]
        assert before <= added_entry.timestamp <= after

    @pytest.mark.asyncio
    async def test_write_audit_returns_audit_log(self):
        from app.models.audit_log import AuditLog
        from app.services.audit import write_audit

        mock_session = _mock_session()

        result = await write_audit(mock_session, action="test")

        assert isinstance(result, AuditLog)

    @pytest.mark.asyncio
    async def test_write_audit_with_none_optional_fields(self):
        from app.services.audit import write_audit

        mock_session = _mock_session()

        await write_audit(
            mock_session,
            action="test",
            actor_ip=None,
            entity_type=None,
            entity_id=None,
            correlation_id=None,
        )

        added_entry = mock_session.add.call_args[0][0]
        assert added_entry.actor_ip is None
        assert added_entry.entity_type is None
        assert added_entry.entity_id is None
        assert added_entry.correlation_id is None
