"""Authorization for the REST sync write endpoints.

``/api/v1/sync/teams/{id}/sync``, ``/projects/{id}/sync`` and
``/courses/{id}/sync-all`` authenticate with ``ApiTeacherAuth`` (the *global*
teacher/admin role). ``can_manage_via_request`` adds *course-scoped*
authorization so a teacher who does not belong to a course can't sync its teams
by UUID - mirroring the read endpoints and the dashboard write routes, which
already scope a non-admin teacher to the courses/teams they belong to.

These pin the branch behaviour with light monkeypatching - no signed-cookie or
DB fixtures required.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import app.api.dashboard._access as access


async def test_can_manage_via_request_branches(monkeypatch) -> None:
    request = object()
    db = AsyncMock()
    course = SimpleNamespace(id=uuid.uuid4())
    team = SimpleNamespace(id=uuid.uuid4(), course_id=uuid.uuid4())

    # get_settings result is only handed to the (monkeypatched) session
    # validator, so a stub keeps the real settings loader out of the test.
    monkeypatch.setattr(access, "get_settings", lambda: SimpleNamespace())

    # 1. Bearer-token client (shared OR per-user token) -> always allowed.
    monkeypatch.setattr(access, "_extract_bearer_token", lambda r: "tok")
    assert await access.can_manage_via_request(request, db, course=course) is True
    assert await access.can_manage_via_request(request, db, team=team) is True

    # No bearer token for the remaining (session) cases.
    monkeypatch.setattr(access, "_extract_bearer_token", lambda r: None)

    # 2. Missing / invalid session -> denied.
    monkeypatch.setattr(access, "_validate_session", lambda r, s: None)
    assert await access.can_manage_via_request(request, db, course=course) is False

    # 3. Session admin -> allowed without resolving the course.
    monkeypatch.setattr(access, "_validate_session", lambda r, s: {"role": "admin"})
    assert await access.can_manage_via_request(request, db, course=course) is True
    assert await access.can_manage_via_request(request, db, team=team) is True

    # 4. Session non-admin (global teacher) -> defers to _can_manage_course.
    monkeypatch.setattr(access, "_validate_session", lambda r, s: {"role": "teacher"})

    monkeypatch.setattr(access, "_can_manage_course", AsyncMock(return_value=False))
    assert await access.can_manage_via_request(request, db, course=course) is False  # foreign
    monkeypatch.setattr(access, "_can_manage_course", AsyncMock(return_value=True))
    assert await access.can_manage_via_request(request, db, course=course) is True  # own

    # 5. Team scope -> defers to _can_manage_team.
    monkeypatch.setattr(access, "_can_manage_team", AsyncMock(return_value=False))
    assert await access.can_manage_via_request(request, db, team=team) is False
    monkeypatch.setattr(access, "_can_manage_team", AsyncMock(return_value=True))
    assert await access.can_manage_via_request(request, db, team=team) is True


async def test_can_manage_via_request_project_resolves_to_team(monkeypatch) -> None:
    request = object()
    db = AsyncMock()
    team = SimpleNamespace(id=uuid.uuid4(), course_id=uuid.uuid4())
    monkeypatch.setattr(access, "get_settings", lambda: SimpleNamespace())
    monkeypatch.setattr(access, "_extract_bearer_token", lambda r: None)
    monkeypatch.setattr(access, "_validate_session", lambda r, s: {"role": "teacher"})

    # Project -> owning team -> _can_manage_team.
    project = SimpleNamespace(team_id=uuid.uuid4())
    db.get = AsyncMock(return_value=team)
    monkeypatch.setattr(access, "_can_manage_team", AsyncMock(return_value=True))
    assert await access.can_manage_via_request(request, db, project=project) is True
    monkeypatch.setattr(access, "_can_manage_team", AsyncMock(return_value=False))
    assert await access.can_manage_via_request(request, db, project=project) is False

    # Project with no owning team -> denied.
    assert (
        await access.can_manage_via_request(request, db, project=SimpleNamespace(team_id=None))
        is False
    )

    # Owning team row gone -> denied.
    db.get = AsyncMock(return_value=None)
    assert await access.can_manage_via_request(request, db, project=project) is False


async def test_can_manage_via_request_denies_when_nothing_supplied(monkeypatch) -> None:
    request = object()
    db = AsyncMock()
    monkeypatch.setattr(access, "get_settings", lambda: SimpleNamespace())
    monkeypatch.setattr(access, "_extract_bearer_token", lambda r: None)
    monkeypatch.setattr(access, "_validate_session", lambda r, s: {"role": "teacher"})
    # Non-admin session but no course/team/project to scope against -> denied.
    assert await access.can_manage_via_request(request, db) is False


def _result(first_val):
    """A stand-in for a SQLAlchemy Result whose .first() returns first_val."""
    return SimpleNamespace(first=lambda: first_val)


async def test_can_view_student_via_request_branches(monkeypatch) -> None:
    request = object()
    student = SimpleNamespace(id=uuid.uuid4())
    db = AsyncMock()
    monkeypatch.setattr(access, "get_settings", lambda: SimpleNamespace())

    # 1. Bearer token -> always allowed.
    monkeypatch.setattr(access, "_extract_bearer_token", lambda r: "tok")
    assert await access.can_view_student_via_request(request, db, student) is True

    monkeypatch.setattr(access, "_extract_bearer_token", lambda r: None)

    # 2. No session -> denied.
    monkeypatch.setattr(access, "_validate_session", lambda r, s: None)
    assert await access.can_view_student_via_request(request, db, student) is False

    # 3. Admin -> allowed.
    monkeypatch.setattr(access, "_validate_session", lambda r, s: {"role": "admin"})
    assert await access.can_view_student_via_request(request, db, student) is True

    # 4. Non-admin with no resolvable identity in the session -> denied.
    monkeypatch.setattr(access, "_validate_session", lambda r, s: {"role": "teacher"})
    assert await access.can_view_student_via_request(request, db, student) is False

    # Identity present for the DB-backed branches.
    monkeypatch.setattr(
        access, "_validate_session", lambda r, s: {"role": "teacher", "gitlab_username": "t1"}
    )

    # 5. Viewer user row not found -> denied.
    db.execute = AsyncMock(side_effect=[_result(None)])
    assert await access.can_view_student_via_request(request, db, student) is False

    # 6. Viewer found but shares no course with the student -> denied.
    db.execute = AsyncMock(side_effect=[_result(("viewer-id",)), _result(None)])
    assert await access.can_view_student_via_request(request, db, student) is False

    # 7. Viewer shares a course with the student -> allowed.
    db.execute = AsyncMock(side_effect=[_result(("viewer-id",)), _result(("shared",))])
    assert await access.can_view_student_via_request(request, db, student) is True
