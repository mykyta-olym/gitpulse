"""Shared worker bootstrap - async context manager for DB lifecycle.

Every RQ worker job needs to init_engine -> get_async_session -> dispose_engine.
This module provides a single context manager that encapsulates the pattern,
eliminating ~16 repetitions of the same 6-line boilerplate across 10 workers.
"""

import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.config import Settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def worker_session() -> AsyncIterator[tuple["AsyncSession", "Settings"]]:
    """Bootstrap DB for an RQ worker job.

    Usage::

        async with worker_session() as (session, settings):
            project = await session.get(GitLabProject, project_id)
            ...
    """
    from app.config import get_settings
    from app.db.session import async_session_ctx, dispose_engine, init_engine

    settings = get_settings()
    init_engine(str(settings.database_url))
    try:
        async with async_session_ctx() as session:
            yield session, settings
    finally:
        with contextlib.suppress(Exception):
            await dispose_engine()
