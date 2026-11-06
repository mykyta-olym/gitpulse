"""The page whose job is to configure a course refused to open and told you to
open it.

A course with no `CourseSettings` row answered 404 with, for an admin, "This
course needs to be configured. Go to course settings to set it up" - which is
the page that just refused. There was no other way to create that row from the
UI, so the course stayed unconfigurable.

Every column on the model has a default and the import path already creates a
bare row exactly this way, so the page creates one and renders. Two of the three
courses in a freshly seeded database were in that state.
"""

from __future__ import annotations

import os
import uuid
from datetime import date, timedelta
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from starlette.responses import Response

from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.custom_check import CustomCheck
from app.services import course_settings as configuration

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
    from app.db.session import get_async_session

    async for session in get_async_session():
        yield session
        await session.rollback()
        break


def _client(
    app: Any, role: str, *, user_id: uuid.UUID | None = None, username: str | None = None
) -> AsyncClient:
    from app.config import get_settings
    from app.security.csrf import generate_csrf_token
    from app.security.session_auth import SESSION_COOKIE_NAME, create_session_cookie

    secret = get_settings().secret_key
    secret = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    carrier = Response()
    username = username or f"settings-probe-{role}"
    create_session_cookie(
        carrier,
        secret_key=secret,
        user=username,
        role=role,
        user_id=str(user_id or uuid.uuid4()),
        gitlab_username=username,
        user_agent="pytest",
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
            "X-CSRF-Token": generate_csrf_token({"user": username}, secret),
        },
    )


async def _course_without_settings(db) -> Course:
    course = Course(
        code=f"NOSET-{uuid.uuid4().hex[:6]}",
        name="A course nobody configured",
        academic_year="2026/2027",
        semester="winter",
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    assert course.settings is None, "the fixture must start with no settings row"
    return course


async def test_the_settings_page_opens_and_creates_the_row_it_needs(app, db_session):
    course = await _course_without_settings(db_session)

    async with _client(app, "admin") as client:
        response = await client.get(f"/dashboard/courses/{course.id}/settings")

    assert response.status_code == 200, (
        "the page that configures a course refused to open for a course that "
        "has not been configured"
    )

    row = (
        await db_session.execute(
            select(CourseSettings).where(CourseSettings.course_id == course.id)
        )
    ).scalar_one_or_none()
    assert row is not None, "the page rendered but left the course unconfigured"


async def test_opening_it_twice_does_not_make_a_second_row(app, db_session):
    course = await _course_without_settings(db_session)

    async with _client(app, "admin") as client:
        first = await client.get(f"/dashboard/courses/{course.id}/settings")
        second = await client.get(f"/dashboard/courses/{course.id}/settings")

    assert first.status_code == 200
    assert second.status_code == 200
    rows = (
        (
            await db_session.execute(
                select(CourseSettings).where(CourseSettings.course_id == course.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1, f"a second visit added another settings row: {len(rows)}"


async def test_a_student_still_cannot_reach_it(app, db_session):
    """Creating the row must not have widened who may open the page."""
    course = await _course_without_settings(db_session)

    async with _client(app, "student") as client:
        response = await client.get(f"/dashboard/courses/{course.id}/settings")

    assert response.status_code in (403, 404), response.status_code
    row = (
        await db_session.execute(
            select(CourseSettings).where(CourseSettings.course_id == course.id)
        )
    ).scalar_one_or_none()
    assert row is None, "a student's refused visit created a settings row anyway"


@pytest.fixture
async def configured(db_session, monkeypatch):
    course = Course(
        code=uuid.uuid4().hex[:10], name="Before", academic_year="2026/2027", semester="winter"
    )
    course.settings = CourseSettings(
        semester_start_date=date(2026, 9, 21),
        semester_end_date=date(2027, 2, 12),
        llm_course_type="devops",
        llm_custom_prompt="Preserve this prompt",
        llm_resource_urls=[{"url": "https://example.org/course", "label": "Course"}],
    )
    db_session.add(course)
    await db_session.flush()
    custom = CustomCheck(
        course_id=course.id, check_code="C01", name="Custom", weight=0.2, is_active=True
    )
    db_session.add(custom)
    await db_session.commit()
    events = []
    monkeypatch.setattr(
        configuration, "publish_course_settings_changed", lambda *a, **kw: events.append((a, kw))
    )
    return course, custom, events


def _draft(course, custom):
    return {
        "course": {"name": "After", "expected_updated_at": course.updated_at.isoformat()},
        "settings": {
            "green_threshold": 0.9,
            "expected_updated_at": course.settings.updated_at.isoformat(),
        },
        "checks": {
            "R01": {
                "name": "First edited",
                "weight": 0.25,
                "expected_updated_at": course.settings.updated_at.isoformat(),
            },
            "R02": {
                "name": "Second edited",
                "weight": 0.15,
                "expected_updated_at": course.settings.updated_at.isoformat(),
            },
            "C01": {
                "weight": 0.3,
                "is_active": False,
                "expected_updated_at": custom.updated_at.isoformat(),
            },
        },
    }


async def test_one_save_applies_metadata_settings_and_multiple_check_rows(
    app, db_session, configured
):
    course, custom, events = configured
    async with _client(app, "admin") as client:
        response = await client.post(
            f"/dashboard/courses/{course.id}/settings", json=_draft(course, custom)
        )
    assert response.status_code == 200, response.text
    await db_session.refresh(course)
    await db_session.refresh(custom)
    cs = course.settings
    assert (
        course.name,
        cs.green_threshold,
        cs.weight_issue_ownership,
        cs.weight_branch_naming,
    ) == ("After", 0.9, 0.25, 0.15)
    assert cs.check_configs["R01"]["_name"] == "First edited"
    assert cs.check_configs["R02"]["_name"] == "Second edited"
    assert (custom.weight, custom.is_active) == (0.3, False)
    assert cs.llm_custom_prompt == "Preserve this prompt"
    assert len(events) == 1
    assert response.json()["check_updated_at"]["R01"] == response.json()["settings_updated_at"]


async def test_stale_custom_row_rolls_back_the_entire_draft(app, db_session, configured):
    course, custom, events = configured
    draft = _draft(course, custom)
    draft["checks"]["C01"]["expected_updated_at"] = (
        custom.updated_at - timedelta(days=1)
    ).isoformat()
    async with _client(app, "admin") as client:
        response = await client.post(f"/dashboard/courses/{course.id}/settings", json=draft)
    assert response.status_code == 409, response.text
    await db_session.refresh(course)
    await db_session.refresh(custom)
    assert (course.name, course.settings.green_threshold, custom.weight) == ("Before", 0.8, 0.2)
    assert not course.settings.check_configs
    assert not events


async def test_invalid_semester_cannot_partially_rename_course(app, db_session, configured):
    course, custom, events = configured
    draft = _draft(course, custom)
    draft["settings"]["semester_end_date"] = "2026-09-01"
    async with _client(app, "admin") as client:
        response = await client.post(f"/dashboard/courses/{course.id}/settings", json=draft)
    assert response.status_code == 422, response.text
    await db_session.refresh(course)
    assert course.name == "Before"
    assert course.settings.semester_end_date == date(2027, 2, 12)
    assert not events


async def test_invalid_single_check_payload_does_not_persist_valid_weight(
    app, db_session, configured
):
    course, _, events = configured
    before = course.settings.weight_issue_ownership
    async with _client(app, "admin") as client:
        response = await client.put(
            f"/dashboard/courses/{course.id}/checks/R01", json={"weight": 0.4, "is_active": "false"}
        )
    assert response.status_code == 422, response.text
    await db_session.refresh(course)
    assert course.settings.weight_issue_ownership == before
    assert not events


async def test_native_form_uses_same_validation_and_preserves_absent_optional_fields(
    app, db_session, configured
):
    course, custom, _ = configured
    async with _client(app, "admin") as client:
        response = await client.post(
            f"/dashboard/courses/{course.id}/settings",
            data={
                "course_name": "Native save",
                "expected_course_updated_at": course.updated_at.isoformat(),
                "expected_settings_updated_at": course.settings.updated_at.isoformat(),
                "checks_present": "1",
                "custom_check_codes": "C01",
                "check_updated_at_C01": custom.updated_at.isoformat(),
            },
        )
    assert response.status_code == 303, response.text
    await db_session.refresh(course)
    await db_session.refresh(custom)
    cs = course.settings
    assert course.name == "Native save"
    assert cs.enabled_checks == []
    assert not custom.is_active
    assert cs.llm_course_type == "devops"
    assert cs.llm_custom_prompt == "Preserve this prompt"
    assert cs.llm_resource_urls == [{"url": "https://example.org/course", "label": "Course"}]
    assert cs.semester_start_date == date(2026, 9, 21)
    assert cs.semester_end_date == date(2027, 2, 12)


async def test_settings_form_requires_its_version_and_archived_courses_remain_read_only(
    app, db_session, configured
):
    course, custom, events = configured
    async with _client(app, "admin") as client:
        missing = await client.post(
            f"/dashboard/courses/{course.id}/settings",
            json={"course": {"name": "After"}, "settings": {}},
        )
        assert missing.status_code == 409
        course.is_active = False
        await db_session.commit()
        archived = await client.post(
            f"/dashboard/courses/{course.id}/settings", json=_draft(course, custom)
        )
        assert archived.status_code == 409
    await db_session.refresh(course)
    assert course.name == "Before"
    assert not events


async def test_initial_html_and_refresh_contain_same_shared_rows(app, configured):
    import re

    course, _, _ = configured
    async with _client(app, "admin") as client:
        initial = await client.get(f"/dashboard/courses/{course.id}/settings")
        refreshed = await client.get(f"/dashboard/courses/{course.id}/checks/table")
    assert initial.status_code == refreshed.status_code == 200
    first = re.findall(r"<tr data-check-code=.*?</tr>", initial.text, re.DOTALL)
    second = re.findall(r"<tr data-check-code=.*?</tr>", refreshed.text, re.DOTALL)
    assert len(first) == len(second) == 14
    assert first == second
    builtin = next(row for row in first if 'data-check-code="R01"' in row)
    assert 'name="enabled_checks"' in builtin
    assert 'class="form-check ' in builtin
    assert "btn-icon-only" in builtin
    assert 'data-action="editCheck"' in builtin


async def test_concurrent_saves_from_one_version_cannot_overwrite_each_other(app, configured):
    import asyncio

    course, custom, events = configured
    first = _draft(course, custom)
    second = _draft(course, custom)
    second["course"]["name"] = "Another editor"
    async with _client(app, "admin") as client:
        responses = await asyncio.gather(
            client.post(f"/dashboard/courses/{course.id}/settings", json=first),
            client.post(f"/dashboard/courses/{course.id}/settings", json=second),
        )
    assert sorted(response.status_code for response in responses) == [200, 409]
    assert len(events) == 1


@pytest.mark.parametrize("scope", ["group", "subgroup", "projects", "course"])
@pytest.mark.parametrize("archived", [False, True])
async def test_webhook_initial_rows_and_refresh_share_the_projection(
    app, db_session, configured, scope, archived
):
    import re
    from datetime import UTC, datetime

    from app.models.webhook_configuration import WebhookConfiguration

    course, _, _ = configured
    course.is_active = not archived
    config = WebhookConfiguration(
        course_id=course.id,
        name='Webhook <script>alert("x")</script>',
        description="<description> & details",
        scope_type=scope,
        gitlab_group_path="teaching/demo" if scope in ("group", "subgroup") else None,
        gitlab_project_ids=[12, 34] if scope == "projects" else [],
        secret_hash="private-hash" if scope != "projects" else "",
        secret_lookup="private-lookup",
        secret_hash_previous="previous-private-hash" if scope == "subgroup" else None,
        previous_expires_at=datetime(2030, 1, 1, tzinfo=UTC) if scope == "subgroup" else None,
        is_active=scope != "course",
    )
    db_session.add(config)
    await db_session.commit()
    async with _client(app, "admin") as client:
        initial = await client.get(f"/dashboard/courses/{course.id}/settings")
        refreshed = await client.get(f"/dashboard/courses/{course.id}/webhooks/table")
        api = await client.get(f"/api/v1/courses/{course.id}/webhook-configs")
    assert initial.status_code == refreshed.status_code == api.status_code == 200
    first = re.findall(r"<tr data-config-id=.*?</tr>", initial.text, re.DOTALL)
    second = re.findall(r"<tr data-config-id=.*?</tr>", refreshed.text, re.DOTALL)
    assert len(first) == len(second) == 1
    assert first == second
    assert "&lt;script&gt;" in second[0]
    assert "<script>" not in second[0]
    assert "private-hash" not in refreshed.text
    assert "private-lookup" not in refreshed.text
    assert "data-localize-time" in second[0]
    assert second[0].count('data-archived-locked="1"') == (3 if archived else 0)
    assert second[0].count("btn-icon-only") == 3
    assert all(tag.count("data-tippy-content=") <= 1 for tag in re.findall(r"<[^>]+>", second[0]))
    scope_path = (
        "teaching/demo"
        if scope in ("group", "subgroup")
        else ("12,34" if scope == "projects" else "course")
    )
    assert f'data-sort-value="{scope}:{scope_path}"' in second[0]
    assert len(api.json()["configurations"]) == 1


async def test_webhook_table_rejects_a_student(app, configured):
    course, _, _ = configured
    async with _client(app, "student") as client:
        response = await client.get(f"/dashboard/courses/{course.id}/webhooks/table")
    assert response.status_code == 403


async def test_initial_webhook_order_is_newest_first(app, db_session, configured):
    import re
    from datetime import UTC, datetime

    from app.models.webhook_configuration import WebhookConfiguration

    course, _, _ = configured
    configs = [
        WebhookConfiguration(
            course_id=course.id,
            name=name,
            scope_type="course",
            secret_hash="private-hash",
            secret_lookup="private-lookup",
            created_at=datetime(2026, month, 1, tzinfo=UTC),
        )
        for name, month in [("AAA older", 1), ("ZZZ newer", 2)]
    ]
    db_session.add_all(configs)
    await db_session.commit()
    async with _client(app, "admin") as client:
        response = await client.get(f"/dashboard/courses/{course.id}/settings")
    assert response.status_code == 200
    assert re.findall(r'<tr data-config-id="([^"]+)"', response.text) == [
        str(configs[1].id),
        str(configs[0].id),
    ]


@pytest.mark.parametrize("course_role", ["owner", "teacher", "student", None])
async def test_only_course_staff_can_configure_a_course(app, db_session, configured, course_role):
    from app.models.course_membership import CourseMembership
    from app.models.user import User

    course, custom, events = configured
    user = User(
        username="config-teacher-" + uuid.uuid4().hex[:8], password_hash="unused", role="teacher"
    )
    user.gitlab_username = user.username
    db_session.add(user)
    await db_session.flush()
    if course_role is not None:
        db_session.add(CourseMembership(user_id=user.id, course_id=course.id, role=course_role))
    await db_session.commit()
    async with _client(app, "teacher", user_id=user.id, username=user.username) as client:
        page = await client.get(f"/dashboard/courses/{course.id}/settings")
        webhooks = await client.get(f"/dashboard/courses/{course.id}/webhooks/table")
        saved = await client.post(
            f"/dashboard/courses/{course.id}/settings", json=_draft(course, custom)
        )
        check = await client.put(f"/dashboard/courses/{course.id}/checks/R01", json={"weight": 0.3})
    if course_role in ("owner", "teacher"):
        assert (
            page.status_code
            == webhooks.status_code
            == saved.status_code
            == check.status_code
            == 200
        )
        assert len(events) == 2
    else:
        assert page.status_code in (403, 404)
        assert webhooks.status_code in (403, 404)
        assert saved.status_code in (403, 404)
        assert check.status_code in (403, 404)
        await db_session.refresh(course)
        assert course.name == "Before"
        assert not events
