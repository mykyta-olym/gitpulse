"""Tests for base repository module."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestBaseRepositoryClass:
    """Tests for BaseRepository class."""

    def test_base_repository_class_exists(self) -> None:
        from app.db.repositories.base import BaseRepository

        assert BaseRepository is not None

    def test_base_repository_init(self) -> None:
        from app.db.repositories.base import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)

        assert repo.session is mock_session
        assert repo.model_class is mock_model


class TestBaseRepositoryGetById:
    """Tests for BaseRepository.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_entity(self):
        from app.db.repositories.base import BaseRepository

        mock_session = AsyncMock()
        mock_model = MagicMock()
        entity_id = uuid4()
        expected_entity = MagicMock()

        mock_session.get.return_value = expected_entity

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)
        result = await repo.get_by_id(entity_id)

        assert result is expected_entity
        mock_session.get.assert_called_once_with(mock_model, entity_id)

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self):
        from app.db.repositories.base import BaseRepository

        mock_session = AsyncMock()
        mock_model = MagicMock()
        entity_id = uuid4()

        mock_session.get.return_value = None

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)
        result = await repo.get_by_id(entity_id)

        assert result is None


class TestBaseRepositoryGetAll:
    """Tests for BaseRepository.get_all method."""

    def test_get_all_method_exists(self) -> None:
        from app.db.repositories.base import BaseRepository

        mock_session = MagicMock()
        mock_model = MagicMock()
        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)

        assert hasattr(repo, "get_all")
        assert callable(repo.get_all)


class TestBaseRepositoryCreate:
    """Tests for BaseRepository.create method."""

    @pytest.mark.asyncio
    async def test_create_adds_entity(self):
        from app.db.repositories.base import BaseRepository

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_model = MagicMock()
        new_entity = MagicMock()

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)
        result = await repo.create(new_entity)

        assert result is new_entity
        mock_session.add.assert_called_once_with(new_entity)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_returns_entity(self):
        from app.db.repositories.base import BaseRepository

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_model = MagicMock()
        new_entity = MagicMock()
        new_entity.id = uuid4()

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)
        result = await repo.create(new_entity)

        assert result.id == new_entity.id


class TestBaseRepositoryDelete:
    """Tests for BaseRepository.delete method."""

    @pytest.mark.asyncio
    async def test_delete_removes_entity(self):
        from app.db.repositories.base import BaseRepository

        mock_session = AsyncMock()
        mock_model = MagicMock()
        entity = MagicMock()

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)
        await repo.delete(entity)

        mock_session.delete.assert_called_once_with(entity)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_returns_none(self):
        from app.db.repositories.base import BaseRepository

        mock_session = AsyncMock()
        mock_model = MagicMock()
        entity = MagicMock()

        repo: BaseRepository[Any] = BaseRepository(mock_session, mock_model)
        await repo.delete(entity)
