"""Job History has cleared itself by age since it was built. The Event
Pipeline collects the same kind of rows and had no way to, so that table only
ever grew - the admin page offered Refresh, Replay and Resurrect and nothing
that removed anything.

Two things this pins beyond "it deletes":

* a PENDING event is never removed, whatever the age or scope. It has not been
  dealt with yet, so dropping it loses work rather than tidying up after it.
* "Everything" means everything. The UI sends the maximum (ten years) for that
  item, and a cutoff ten years back matches no row at all - which is how the
  jobs purge's own "Everything" came to delete nothing while promising, in its
  own comment, that it "truly clears all".
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from starlette.responses import Response

from app.models.webhook_event import WebhookEvent

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture
async def app() -> Any:
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    os.environ.setdefault("TEACHER_API_TOKEN", "test-token-12345678")
    os.environ.setdefault("APP_ENV", "test")
    os.environ["ALLOWED_HOSTS"] = '["test","localhost","127.0.0.1"]'

    from sqlalchemy import text

    from app.config import get_settings
    from app.db.session import dispose_engine, init_engine
    from app.main import create_app
    from app.models import Base

    get_settings.cache_clear()
    settings = get_settings()
    engine = init_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        echo=settings.db_echo,
    )
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    application = create_app()
    try:
        yield application
    finally:
        await dispose_engine()


@pytest.fixture
async def db_session(app: Any) -> Any:
    """A session on the same database the app is using."""
    from app.db.session import get_async_session

    async for session in get_async_session():
        # Start clean: another test's events would change every count here.
        from sqlalchemy import delete as sa_delete

        await session.execute(sa_delete(WebhookEvent))
        await session.commit()
        yield session
        await session.rollback()
        break


def _client_for(app: Any, role: str) -> AsyncClient:
    from app.config import get_settings
    from app.security.csrf import generate_csrf_token
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = get_settings().secret_key
    secret = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user=f"purge-probe-{role}",
        role=role,
        user_id=str(uuid.uuid4()),
        gitlab_username=f"purge-probe-{role}",
        allow_stateless_fallback=True,
    )
    raw = carrier.headers.get("set-cookie", "")
    token = raw.split(f"{SESSION_COOKIE_NAME}=", 1)[-1].split(";", 1)[0]
    assert token, "could not mint a session cookie"
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={SESSION_COOKIE_NAME: token},
        headers={
            "User-Agent": "pytest",
            "X-CSRF-Token": generate_csrf_token({"user": f"purge-probe-{role}"}, secret),
        },
    )


@pytest.fixture
async def admin_client(app: Any) -> Any:
    async with _client_for(app, "admin") as client:
        yield client


@pytest.fixture
async def teacher_client(app: Any) -> Any:
    async with _client_for(app, "teacher") as client:
        yield client


async def _event(db, *, age_hours: float, processed: bool = False, dlq: bool = False):
    received = datetime.now(UTC) - timedelta(hours=age_hours)
    event = WebhookEvent(
        gitlab_event_uuid=str(uuid.uuid4()),
        event_type="push",
        gitlab_project_id=1,
        payload={},
        received_at=received,
        processed=processed,
        processed_at=received if processed else None,
        dead_letter_at=received if dlq else None,
        dead_letter_reason="gave up" if dlq else None,
    )
    db.add(event)
    await db.flush()
    return event


async def _remaining(db) -> int:
    return int((await db.execute(select(func.count(WebhookEvent.id)))).scalar() or 0)


async def test_an_old_handled_event_is_removed_and_a_pending_one_is_kept(admin_client, db_session):
    await _event(db_session, age_hours=100, processed=True)
    await _event(db_session, age_hours=100, dlq=True)
    pending = await _event(db_session, age_hours=100)
    await db_session.commit()

    response = await admin_client.post("/api/v1/events/purge", json={"hours": 24, "scope": "all"})
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 2, response.json()

    left = (await db_session.execute(select(WebhookEvent.id))).scalars().all()
    assert left == [pending.id], "a pending event must survive a purge"


async def test_a_recent_event_is_left_alone(admin_client, db_session):
    await _event(db_session, age_hours=1, processed=True)
    await db_session.commit()

    response = await admin_client.post("/api/v1/events/purge", json={"hours": 24, "scope": "all"})
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 0
    assert await _remaining(db_session) == 1


async def test_everything_clears_every_handled_event_whatever_its_age(admin_client, db_session):
    """The maximum is a sentinel for "no age limit", not a real age."""
    await _event(db_session, age_hours=0.1, processed=True)
    await _event(db_session, age_hours=0.1, dlq=True)
    pending = await _event(db_session, age_hours=0.1)
    await db_session.commit()

    response = await admin_client.post(
        "/api/v1/events/purge", json={"hours": 87600, "scope": "all"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 2, (
        "'Everything' matched nothing - a ten-year-old cutoff never does"
    )

    left = (await db_session.execute(select(WebhookEvent.id))).scalars().all()
    assert left == [pending.id]


async def test_the_scope_says_what_may_go(admin_client, db_session):
    processed = await _event(db_session, age_hours=100, processed=True)
    dead = await _event(db_session, age_hours=100, dlq=True)
    await db_session.commit()

    response = await admin_client.post("/api/v1/events/purge", json={"hours": 24, "scope": "dlq"})
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 1

    left = (await db_session.execute(select(WebhookEvent.id))).scalars().all()
    assert left == [processed.id], "only the dead-letter row was in scope"
    assert dead.id not in left


@pytest.mark.parametrize(
    "body",
    [
        {"hours": 0, "scope": "all"},
        {"hours": 999999, "scope": "all"},
        {"hours": 24, "scope": "nonsense"},
        {"hours": "soon", "scope": "all"},
    ],
)
async def test_rubbish_input_is_refused(admin_client, body):
    response = await admin_client.post("/api/v1/events/purge", json=body)
    assert response.status_code == 400, response.text


async def test_only_an_admin_may_clear_the_pipeline(teacher_client, db_session):
    await _event(db_session, age_hours=100, processed=True)
    await db_session.commit()

    response = await teacher_client.post("/api/v1/events/purge", json={"hours": 24, "scope": "all"})
    assert response.status_code == 403, response.text
    assert await _remaining(db_session) == 1, "a refused purge must remove nothing"


# -- Deleting the rows the reader ticked ---------------------------------------
#
# Purging by age answers "clear the old ones"; this answers "clear THESE", which
# is the question a reader looking at a table actually has. Job History has had
# both since it was built and the pipeline had neither.


async def test_the_ticked_events_are_removed(admin_client, db_session):
    keep = await _event(db_session, age_hours=1, processed=True)
    doomed = await _event(db_session, age_hours=1, processed=True)
    await db_session.commit()

    response = await admin_client.post("/api/v1/events/delete", json={"ids": [str(doomed.id)]})
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 1

    left = (await db_session.execute(select(WebhookEvent.id))).scalars().all()
    assert left == [keep.id]


async def test_a_ticked_pending_event_is_kept(admin_client, db_session):
    """Same rule as the age purge: it has not been handled, so it is not litter.

    The count in the reply is what the page uses to say "removed 1 of 2 -
    pending events are kept", so it has to report what actually went.
    """
    pending = await _event(db_session, age_hours=1)
    handled = await _event(db_session, age_hours=1, processed=True)
    await db_session.commit()

    response = await admin_client.post(
        "/api/v1/events/delete", json={"ids": [str(pending.id), str(handled.id)]}
    )
    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 1, "it reported removing the pending one too"

    left = (await db_session.execute(select(WebhookEvent.id))).scalars().all()
    assert left == [pending.id]


@pytest.mark.parametrize(
    "body",
    [{"ids": []}, {"ids": "all"}, {"ids": ["not-a-uuid"]}, {}],
)
async def test_a_delete_with_rubbish_ids_is_refused(admin_client, db_session, body):
    await _event(db_session, age_hours=1, processed=True)
    await db_session.commit()

    response = await admin_client.post("/api/v1/events/delete", json=body)
    assert response.status_code == 400, response.text
    assert await _remaining(db_session) == 1


async def test_only_an_admin_may_delete_the_ticked_events(teacher_client, db_session):
    doomed = await _event(db_session, age_hours=1, processed=True)
    await db_session.commit()

    response = await teacher_client.post("/api/v1/events/delete", json={"ids": [str(doomed.id)]})
    assert response.status_code == 403, response.text
    assert await _remaining(db_session) == 1
