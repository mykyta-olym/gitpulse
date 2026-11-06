"""Support Tickets was the last admin surface that could not clear itself.

Job History purges by age and the Event Pipeline does now too, while a resolved
ticket stayed in the table for good - there was no delete route for a ticket at
all, only one that updated it.

What this pins is what may NEVER go: an open or in-progress ticket is somebody
waiting for an answer, and no age makes deleting it safe. Only `resolved` and
`closed` are eligible, and the server decides that rather than the menu.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select
from starlette.responses import Response

from app.models.support_ticket import SupportTicket

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_PURGE = "/api/v1/support/tickets/purge"
_DELETE = "/api/v1/support/tickets/delete"


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
    from app.db.session import get_async_session

    async for session in get_async_session():
        await session.execute(delete(SupportTicket))
        # The purge and delete routes load the session's User row
        # (get_current_admin / get_current_teacher); without one every request
        # here answered 404 "User not found" before reaching the rule under test.
        from app.models.user import User

        for role in ("admin", "teacher"):
            name = f"ticket-purge-{role}"
            if (await session.execute(select(User).where(User.username == name))).scalar() is None:
                session.add(User(username=name, password_hash="!", role=role))
        await session.commit()
        yield session
        await session.rollback()
        break


def _client(app: Any, role: str) -> AsyncClient:
    from app.config import get_settings
    from app.security.csrf import generate_csrf_token
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = get_settings().secret_key
    secret = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    carrier = Response()
    create_session_cookie(
        carrier,
        secret_key=secret,
        user=f"ticket-purge-{role}",
        role=role,
        user_id=str(uuid.uuid4()),
        gitlab_username=f"ticket-purge-{role}",
        allow_stateless_fallback=True,
    )
    raw = carrier.headers.get("set-cookie", "")
    token = raw.split(f"{SESSION_COOKIE_NAME}=", 1)[-1].split(";", 1)[0]
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={SESSION_COOKIE_NAME: token},
        headers={
            "User-Agent": "pytest",
            "X-CSRF-Token": generate_csrf_token({"user": f"ticket-purge-{role}"}, secret),
        },
    )


async def _ticket(db, title: str, status: str, *, days_ago: float, course_id=None):
    when = datetime.now(UTC) - timedelta(days=days_ago)
    ticket = SupportTicket(
        course_id=course_id,
        feedback_token=str(uuid.uuid4()),
        feedback_type="general",
        title=title,
        status=status,
        resolved_at=when if status in ("resolved", "closed") else None,
        updated_at=when,
    )
    db.add(ticket)
    await db.flush()
    return ticket


async def _titles(db) -> list[str]:
    rows = (await db.execute(select(SupportTicket.title).order_by(SupportTicket.title))).scalars()
    return sorted(rows.all())


async def test_assignment_rejects_people_who_cannot_open_the_ticket(app, db_session, monkeypatch):
    from app.config import get_settings
    from app.models.course import Course

    monkeypatch.setattr(get_settings(), "feature_support_forms", True)
    course = Course(
        code="ASSIGN-API", name="Assignment API", academic_year="2026/2027", semester="winter"
    )
    db_session.add(course)
    await db_session.flush()
    ticket = await _ticket(db_session, "assignment", "open", days_ago=0, course_id=course.id)
    await db_session.commit()
    async with _client(app, "admin") as client:
        path = f"/api/v1/support/tickets/{ticket.id}"
        rejected = await client.put(path, json={"assigned_to": "ticket-purge-teacher"})
        assert rejected.status_code == 400, rejected.text
        accepted = await client.put(path, json={"assigned_to": "ticket-purge-admin"})
        assert accepted.status_code == 200, accepted.text
        unassigned = await client.put(path, json={"assigned_to": None})
        assert unassigned.status_code == 200, unassigned.text


@pytest.mark.parametrize("field", ["status", "priority", "category"])
async def test_null_ticket_metadata_is_validation_error(app, db_session, field):
    ticket = await _ticket(db_session, "null-metadata", "open", days_ago=0)
    await db_session.commit()
    async with _client(app, "admin") as client:
        response = await client.put(f"/api/v1/support/tickets/{ticket.id}", json={field: None})
    assert response.status_code == 422, response.text


async def test_assignees_include_course_staff_and_exclude_other_teachers(app, db_session):
    from app.models.course import Course
    from app.models.course_membership import CourseMembership
    from app.models.user import User
    from app.services.support_forms import support_assignees

    course = Course(
        code="ASSIGN", name="Assignment scope", academic_year="2026/2027", semester="winter"
    )
    other = Course(code="OTHER", name="Other scope", academic_year="2026/2027", semester="winter")
    db_session.add_all([course, other])
    await db_session.flush()
    prefix = f"assignee-{uuid.uuid4().hex}"
    users = [
        User(username=f"{prefix}-{key}", password_hash="!", role=role, is_active=active, is_bot=bot)
        for key, role, active, bot in [
            ("course-teacher", "student", True, False),
            ("other-teacher", "teacher", True, False),
            ("inactive", "admin", False, False),
            ("bot", "admin", True, True),
            ("admin", "admin", True, False),
        ]
    ]
    db_session.add_all(users)
    await db_session.flush()
    db_session.add_all(
        [
            CourseMembership(user_id=users[0].id, course_id=course.id, role="teacher"),
            CourseMembership(user_id=users[1].id, course_id=other.id, role="teacher"),
        ]
    )
    await db_session.flush()
    eligible = {
        u.username
        for u in await support_assignees(db_session, course.id)
        if u.username.startswith(prefix)
    }
    assert eligible == {f"{prefix}-course-teacher", f"{prefix}-admin"}


async def _seed_one_of_each(db) -> None:
    await _ticket(db, "open-old", "open", days_ago=200)
    await _ticket(db, "in-progress-old", "in_progress", days_ago=200)
    await _ticket(db, "resolved-old", "resolved", days_ago=200)
    await _ticket(db, "closed-old", "closed", days_ago=200)
    await _ticket(db, "resolved-today", "resolved", days_ago=0.05)
    await db.commit()


async def test_only_finished_tickets_past_the_age_are_removed(app, db_session):
    await _seed_one_of_each(db_session)

    async with _client(app, "admin") as client:
        response = await client.post(_PURGE, json={"hours": 720})

    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 2, response.json()
    assert await _titles(db_session) == ["in-progress-old", "open-old", "resolved-today"]


async def test_an_unfinished_ticket_survives_even_a_full_purge(app, db_session):
    """No age makes deleting somebody's open question safe."""
    await _seed_one_of_each(db_session)

    async with _client(app, "admin") as client:
        response = await client.post(_PURGE, json={"hours": 87600})

    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 3
    assert await _titles(db_session) == ["in-progress-old", "open-old"]


async def test_a_purge_from_one_course_clears_only_that_course(app, db_session):
    """The menu sits on ONE course's ticket list. It used to clear the finished
    tickets of every course of every term."""
    from app.models.course import Course

    this = Course(
        code=f"PRG-{uuid.uuid4().hex[:6]}",
        name="This",
        academic_year="2025/2026",
        semester="summer",
    )
    other = Course(
        code=f"PRG-{uuid.uuid4().hex[:6]}",
        name="Other",
        academic_year="2024/2025",
        semester="summer",
    )
    db_session.add_all([this, other])
    await db_session.commit()
    await _ticket(db_session, "this-resolved-old", "resolved", days_ago=200, course_id=this.id)
    await _ticket(db_session, "other-resolved-old", "resolved", days_ago=200, course_id=other.id)
    await db_session.commit()

    try:
        async with _client(app, "admin") as client:
            response = await client.post(_PURGE, json={"hours": 720, "course_id": str(this.id)})

        assert response.status_code == 200, response.text
        assert response.json()["deleted"] == 1, response.json()
        assert await _titles(db_session) == ["other-resolved-old"]
    finally:
        await db_session.execute(delete(Course).where(Course.id.in_([this.id, other.id])))
        await db_session.commit()


@pytest.mark.parametrize(
    "body",
    [{"hours": 0}, {"hours": 999999}, {"hours": "soon"}, {"hours": 720, "course_id": "nope"}],
)
async def test_rubbish_input_is_refused(app, db_session, body):
    await _ticket(db_session, "resolved-old", "resolved", days_ago=200)
    await db_session.commit()

    async with _client(app, "admin") as client:
        response = await client.post(_PURGE, json=body)

    assert response.status_code == 400, response.text
    assert await _titles(db_session) == ["resolved-old"]


async def test_a_teacher_may_answer_tickets_but_not_erase_them(app, db_session):
    await _seed_one_of_each(db_session)

    async with _client(app, "teacher") as client:
        response = await client.post(_PURGE, json={"hours": 720})

    assert response.status_code == 403, response.text
    assert len(await _titles(db_session)) == 5, "a refused purge must remove nothing"


# -- Deleting the tickets the reader ticked -------------------------------------
#
# The age purge answers "clear the old ones"; this answers "clear THESE". The
# same rule decides what may go, because it is about the ticket's state and not
# about how it was chosen.


async def test_the_ticked_tickets_are_removed(app, db_session):
    await _seed_one_of_each(db_session)
    doomed = (
        await db_session.execute(
            select(SupportTicket.id).where(SupportTicket.title == "resolved-old")
        )
    ).scalar_one()

    async with _client(app, "admin") as client:
        response = await client.post(_DELETE, json={"ids": [doomed]})

    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 1
    assert "resolved-old" not in await _titles(db_session)


async def test_a_ticked_open_ticket_is_kept(app, db_session):
    """Somebody is waiting on it; ticking a box does not change that."""
    await _seed_one_of_each(db_session)
    rows = (
        await db_session.execute(
            select(SupportTicket.id, SupportTicket.title).where(
                SupportTicket.title.in_(("open-old", "resolved-old"))
            )
        )
    ).all()
    ids = [r[0] for r in rows]

    async with _client(app, "admin") as client:
        response = await client.post(_DELETE, json={"ids": ids})

    assert response.status_code == 200, response.text
    assert response.json()["deleted"] == 1, "it reported removing the open one too"
    assert "open-old" in await _titles(db_session)


@pytest.mark.parametrize("body", [{"ids": []}, {"ids": ["nope"]}, {}])
async def test_a_ticket_delete_with_rubbish_ids_is_refused(app, db_session, body):
    await _ticket(db_session, "resolved-old", "resolved", days_ago=200)
    await db_session.commit()

    async with _client(app, "admin") as client:
        response = await client.post(_DELETE, json=body)

    assert response.status_code == 400, response.text
    assert await _titles(db_session) == ["resolved-old"]


async def test_only_an_admin_may_delete_ticked_tickets(app, db_session):
    await _seed_one_of_each(db_session)
    doomed = (
        await db_session.execute(
            select(SupportTicket.id).where(SupportTicket.title == "resolved-old")
        )
    ).scalar_one()

    async with _client(app, "teacher") as client:
        response = await client.post(_DELETE, json={"ids": [doomed]})

    assert response.status_code == 403, response.text
    assert len(await _titles(db_session)) == 5
