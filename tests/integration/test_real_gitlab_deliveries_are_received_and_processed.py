"""What GitLab 19.4 really sends is received and processed.

The fixtures in ``tests/fixtures/payloads/gitlab_19_4`` are deliveries a
GitLab CE 19.4.2 sent to GitPulse in a local end-to-end run of the
classroom assistant. Two of them failed before: every merge request event
(its ``object_attributes.source`` is the source project, not a word, so the
receiver refused it with 422) and every pipeline outside a merge request
(``"merge_request": null`` crashed the processor). The hand-written payloads
the other tests use had neither shape.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

FIXTURES = Path(__file__).parents[1] / "fixtures" / "payloads" / "gitlab_19_4"
SECRET = "whsec_" + "e" * 48


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
    engine = init_engine(str(settings.database_url), pool_size=5, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    application = create_app()
    try:
        yield application
    finally:
        await dispose_engine()


@pytest.fixture
async def project_id(app: Any) -> Any:
    """A registered project with its own webhook secret; its GitLab id."""
    from app.db.session import async_session_ctx
    from app.models.course import Course
    from app.models.course_settings import CourseSettings
    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.security.webhook_auth import compute_webhook_lookup_key, hash_webhook_secret

    gitlab_id = 870_000_000 + uuid.uuid4().int % 1_000_000
    suffix = uuid.uuid4().hex[:8]
    async with async_session_ctx() as session:
        course = Course(code=f"R{suffix[:6]}", name="Real payloads", academic_year="2026/2027")
        session.add(course)
        await session.flush()
        session.add(CourseSettings(course_id=course.id))
        team = Team(course_id=course.id, name=f"Team {suffix}")
        session.add(team)
        await session.flush()
        session.add(
            GitLabProject(
                team_id=team.id,
                gitlab_project_id=gitlab_id,
                gitlab_project_path=f"kurz/{suffix}",
                default_branch="main",
                webhook_secret_hash=hash_webhook_secret(SECRET),
                webhook_secret_lookup=compute_webhook_lookup_key(SECRET),
            )
        )
        await session.commit()
        course_id = course.id
    try:
        yield gitlab_id
    finally:
        async with async_session_ctx() as session:
            await session.execute(delete(Course).where(Course.id == course_id))
            await session.commit()


def _fixture(name: str, gitlab_id: int) -> tuple[str, dict[str, Any]]:
    """The delivery's event header and its payload, moved to ``gitlab_id``."""
    body = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    payload = body["payload"]
    payload["project"]["id"] = gitlab_id
    if "project_id" in payload:
        payload["project_id"] = gitlab_id
    return body["event"], payload


@pytest.mark.parametrize("name", sorted(p.stem for p in FIXTURES.glob("*.json")))
async def test_the_delivery_is_received_and_processed(app: Any, project_id: int, name: str) -> None:
    from app.db.session import async_session_ctx
    from app.models.webhook_event import WebhookEvent
    from app.workers.event_processor import _process_async

    event_header, payload = _fixture(name, project_id)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/webhooks/gitlab",
            json=payload,
            headers={
                "X-Gitlab-Token": SECRET,
                "X-Gitlab-Event": event_header,
                "X-Gitlab-Event-UUID": str(uuid.uuid4()),
            },
        )
    assert response.status_code == 200, response.text
    event_id = response.json()["event_id"]

    await _process_async(event_id)

    async with async_session_ctx() as session:
        event = await session.get(WebhookEvent, uuid.UUID(event_id))
        assert event is not None
        assert event.processing_error is None
        assert event.processed is True
