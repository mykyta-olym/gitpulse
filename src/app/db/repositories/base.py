"""Base repository with common CRUD operations."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic repository providing basic CRUD."""

    def __init__(self, session: AsyncSession, model_class: type[ModelT]) -> None:
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        return await self.session.get(self.model_class, entity_id)

    async def get_all(self, **filters: Any) -> list[ModelT]:
        stmt = select(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                stmt = stmt.where(getattr(self.model_class, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()
