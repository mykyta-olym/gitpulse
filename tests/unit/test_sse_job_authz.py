"""Authorization for the job status/progress SSE endpoints.

`/jobs/{job_id}` and `/jobs/{job_id}/stream` use ``ApiAuth`` which only
*authenticates*. ``_can_view_job`` adds *authorization* so one course's
sync/import process can't be read by a member of another course who happens to
learn the (random) job id. These tests pin the branch behaviour with light
monkeypatching - no signed-cookie or DB fixtures required.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import app.api.dashboard._access as access
import app.api.sse as sse
import app.config as config


async def test_can_view_job_branches(monkeypatch) -> None:
    request = object()
    job = SimpleNamespace(course_id=uuid.uuid4(), team_id=None, project_id=None)
    db = AsyncMock()

    # get_settings is lazy-imported inside the helper; the value is only passed
    # to the (monkeypatched) session validator, so a stub is fine.
    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace())

    # 1. Bearer-token client (shared/per-user API token) -> always allowed.
    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: "tok")
    assert await sse._can_view_job(request, job, db) is True

    # No bearer token for the remaining (session) cases.
    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: None)

    # 2. Missing / invalid session -> denied.
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: None)
    assert await sse._can_view_job(request, job, db) is False

    # 3. Session admin -> allowed without resolving the course.
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "admin"})
    assert await sse._can_view_job(request, job, db) is True

    # 4. Session non-admin -> defers to _can_view_course on the job's course.
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "student"})
    db.get = AsyncMock(return_value=SimpleNamespace(id=job.course_id))

    monkeypatch.setattr(access, "_can_view_course", AsyncMock(return_value=False))
    assert await sse._can_view_job(request, job, db) is False  # foreign course

    monkeypatch.setattr(access, "_can_view_course", AsyncMock(return_value=True))
    assert await sse._can_view_job(request, job, db) is True  # own course


async def test_can_view_job_denies_unresolvable_course_for_non_admin(monkeypatch) -> None:
    request = object()
    # No course/team/project -> can't resolve an owner -> non-admin denied.
    job = SimpleNamespace(course_id=None, team_id=None, project_id=None)
    db = AsyncMock()
    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace())
    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: None)
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "teacher"})
    assert await sse._can_view_job(request, job, db) is False


async def test_can_manage_job_branches(monkeypatch) -> None:
    request = object()
    job = SimpleNamespace(course_id=uuid.uuid4(), team_id=None, project_id=None)
    db = AsyncMock()
    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace())

    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: "tok")
    assert await sse._can_manage_job(request, job, db) is True

    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: None)
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: None)
    assert await sse._can_manage_job(request, job, db) is False

    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "admin"})
    assert await sse._can_manage_job(request, job, db) is True

    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "teacher"})
    db.get = AsyncMock(return_value=SimpleNamespace(id=job.course_id))
    monkeypatch.setattr(access, "can_manage_via_request", AsyncMock(return_value=False))
    assert await sse._can_manage_job(request, job, db) is False
    monkeypatch.setattr(access, "can_manage_via_request", AsyncMock(return_value=True))
    assert await sse._can_manage_job(request, job, db) is True


async def test_can_view_dashboard_stream_branches(monkeypatch) -> None:
    request = object()
    team_id = uuid.uuid4()
    course_id = uuid.uuid4()
    db = AsyncMock()
    monkeypatch.setattr(config, "get_settings", lambda: SimpleNamespace())

    # 1. Bearer-token client -> allowed for both team and course channels.
    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: "tok")
    assert await sse._can_view_dashboard_stream(request, db, team_id=team_id) is True
    assert await sse._can_view_dashboard_stream(request, db, course_id=course_id) is True

    monkeypatch.setattr(sse, "_extract_bearer_token", lambda r: None)

    # 2. No session -> denied.
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: None)
    assert await sse._can_view_dashboard_stream(request, db, team_id=team_id) is False

    # 3. Admin -> allowed.
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "admin"})
    assert await sse._can_view_dashboard_stream(request, db, team_id=team_id) is True

    # 4. Non-admin -> defers to _can_view_team / _can_view_course.
    monkeypatch.setattr(sse, "_validate_session", lambda r, s: {"role": "student"})
    db.get = AsyncMock(return_value=SimpleNamespace())

    monkeypatch.setattr(access, "_can_view_team", AsyncMock(return_value=False))
    assert await sse._can_view_dashboard_stream(request, db, team_id=team_id) is False
    monkeypatch.setattr(access, "_can_view_team", AsyncMock(return_value=True))
    assert await sse._can_view_dashboard_stream(request, db, team_id=team_id) is True

    monkeypatch.setattr(access, "_can_view_course", AsyncMock(return_value=False))
    assert await sse._can_view_dashboard_stream(request, db, course_id=course_id) is False
    monkeypatch.setattr(access, "_can_view_course", AsyncMock(return_value=True))
    assert await sse._can_view_dashboard_stream(request, db, course_id=course_id) is True

    # 5. Neither team nor course given -> denied.
    assert await sse._can_view_dashboard_stream(request, db) is False
