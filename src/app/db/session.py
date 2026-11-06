"""Async SQLAlchemy engine and session management."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import anyio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

_log = logging.getLogger(__name__)


def _install_db_timing(sync_engine: object) -> None:
    """Best-effort: a missing counter must never stop the app from starting."""
    with suppress(Exception):  # diagnostics are never load-bearing
        from app.observability.db_timing import install

        install(sync_engine)  # type: ignore[arg-type]


def init_engine(
    database_url: str,
    # The workers' size: a job holds one or two sessions at a time (its
    # gathers are GitLab fetches), and four of them share Postgres with the
    # API - see db_pool_size in config.py.
    pool_size: int = 2,
    max_overflow: int = 2,
    pool_recycle: int = 1800,
    pool_timeout: int = 5,
    echo: bool = False,
) -> AsyncEngine:
    """Create the global async engine. Called once at startup."""
    global _engine, _session_factory
    _engine = create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=pool_recycle,
        pool_timeout=pool_timeout,
        pool_use_lifo=True,
        echo=echo,
    )

    # Count statements and the time they take, per request. Read by the logging
    # middleware, which already writes a line per request - see observability
    # /db_timing.py for why a slow page needs this to be answerable at all.
    _install_db_timing(_engine.sync_engine)

    # Suppress noisy CancelledError warnings when the pool terminates
    # connections that were interrupted by Starlette/Uvicorn task cancellation.
    @event.listens_for(_engine.sync_engine, "close")
    def _on_close(dbapi_conn: object, connection_record: object) -> None:
        """Gracefully handle connections being discarded by the pool."""

    @event.listens_for(_engine.sync_engine, "close_detached")
    def _on_close_detached(dbapi_conn: object) -> None:
        """Suppress GC warnings for detached connections."""

    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Dependency-injection compatible session generator.

    Cancellation-safe: catches ``BaseException`` (including
    ``CancelledError``) and shields rollback / close with
    ``anyio.CancelScope(shield=True)`` so the underlying asyncpg
    connection is always returned to the pool - even when Starlette's
    middleware cancel scope fires on client disconnect.

    .. warning::

        This dependency **auto-commits** when the route returns without
        raising.  Routes that call :py:meth:`AsyncSession.commit` or
        :py:meth:`AsyncSession.rollback` themselves are fine - the
        auto-commit at exit is a no-op when there is nothing to flush -
        but a route that *intentionally* leaves the transaction open
        will have those uncommitted writes persisted at exit, which can
        mask logic errors.  When you need explicit transaction control,
        open a nested ``async with session.begin():`` block inside the route.
    """
    factory = _ensure_factory()
    session = factory()
    try:
        yield session
        with anyio.CancelScope(shield=True):
            await session.commit()
    except BaseException:
        with anyio.CancelScope(shield=True):
            try:
                await session.rollback()
            except Exception:
                _log.debug("DI session rollback failed during cleanup", exc_info=True)
        raise
    finally:
        with anyio.CancelScope(shield=True):
            try:
                await session.close()
            except Exception:
                _log.debug("DI session close failed during cleanup", exc_info=True)


def _ensure_factory() -> async_sessionmaker[AsyncSession]:
    """Lazily initialise the session factory and return it.

    Idempotent: when ``init_engine`` has already been called (the normal
    code path during the FastAPI lifespan), this function only returns
    the existing factory.  The lazy fallback below is reached only by
    standalone scripts and unit tests that bypass the lifespan.
    """
    global _session_factory
    if _session_factory is not None:
        return _session_factory
    if _engine is not None:
        # Engine was created out-of-band but the sessionmaker isn't -
        # wire one up against the existing engine instead of creating a
        # second engine.
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        return _session_factory
    try:
        from app.config import get_settings
    except Exception as exc:
        raise RuntimeError("Session factory not initialized.") from exc

    settings = get_settings()
    init_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
        pool_timeout=settings.db_pool_timeout,
        echo=settings.db_echo,
    )
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized.")
    return _session_factory


@asynccontextmanager
async def async_session_ctx() -> AsyncIterator[AsyncSession]:
    """Cancellation-safe async context manager for DB sessions.

    Unlike :func:`get_async_session` (an async-generator designed for
    FastAPI dependency injection), this context manager guarantees the
    connection is returned to the pool even when ``CancelledError``
    interrupts the caller - preventing the *"garbage collector cleaning
    up non-checked-in connection"* warning.
    """
    factory = _ensure_factory()
    session = factory()
    try:
        yield session
        with anyio.CancelScope(shield=True):
            await session.commit()
    except BaseException:
        with anyio.CancelScope(shield=True):
            try:
                await session.rollback()
            except Exception:
                _log.debug("session rollback failed during cleanup", exc_info=True)
        raise
    finally:
        with anyio.CancelScope(shield=True):
            try:
                await session.close()
            except Exception:
                _log.debug("session close failed during cleanup", exc_info=True)


async def dispose_engine() -> None:
    """Dispose engine on shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
