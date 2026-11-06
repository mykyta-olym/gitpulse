"""Email persistence must not borrow an asyncpg pool from another event loop."""

from __future__ import annotations

import asyncio
import gc
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models import Base
from app.models.email_log import EmailLog
from app.models.user import User
from app.services.email_notifications import enqueue_email

pytestmark = pytest.mark.integration


@pytest.fixture
async def mail_db(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "feature_email_notifications", True)
    monkeypatch.setattr(settings, "smtp_host", "unused.invalid")
    engine = create_async_engine(str(settings.database_url))
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    queued = MagicMock()
    monkeypatch.setattr("rq.Queue.enqueue", queued)
    recipient = f"mail-loop-{uuid.uuid4().hex}@example.test"
    try:
        yield factory, queued, recipient
    finally:
        async with factory() as session:
            await session.execute(delete(EmailLog).where(EmailLog.to_email == recipient))
            await session.execute(delete(User).where(User.email == recipient))
            await session.commit()
        await engine.dispose()


@pytest.mark.parametrize("in_thread", [True, False])
@pytest.mark.parametrize("opted_out", [True, False])
async def test_enqueue_respects_preferences_on_every_loop(mail_db, recwarn, in_thread, opted_out):
    factory, queued, recipient = mail_db
    async with factory() as session:
        session.add(
            User(
                username=recipient,
                email=recipient,
                password_hash="unused",
                notify_tickets=not opted_out,
            )
        )
        await session.commit()
    payload = {
        "to_email": recipient,
        "subject": "Loop ownership regression",
        "html_body": "<p>Request received</p>",
        "text_body": "Request received",
        "category": "ticket",
        "idempotency_key": uuid.uuid4().hex,
    }
    for attempt in range(2):
        log_id = (
            await asyncio.to_thread(enqueue_email, **payload)
            if in_thread
            else enqueue_email(**payload)
        )
        assert (log_id is not None) is (not opted_out and attempt == 0)
    async with factory() as session:
        rows = (await session.scalars(select(EmailLog).where(EmailLog.to_email == recipient))).all()
        assert len(rows) == (0 if opted_out else 1)
    assert queued.call_count == (0 if opted_out else 1)
    gc.collect()
    assert not [w for w in recwarn if issubclass(w.category, RuntimeWarning)]


async def test_concurrent_enqueues_keep_one_delivery(mail_db):
    factory, queued, recipient = mail_db
    payload = {
        "to_email": recipient,
        "subject": "Concurrent delivery",
        "html_body": "<p>Request received</p>",
        "text_body": "Request received",
        "category": "ticket",
        "idempotency_key": uuid.uuid4().hex,
    }
    results = await asyncio.gather(*(asyncio.to_thread(enqueue_email, **payload) for _ in range(6)))
    assert sum(result is not None for result in results) == 1
    assert queued.call_count == 1
    async with factory() as session:
        assert (
            len(
                (
                    await session.scalars(select(EmailLog).where(EmailLog.to_email == recipient))
                ).all()
            )
            == 1
        )
