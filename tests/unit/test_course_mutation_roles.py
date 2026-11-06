"""Read access and a global teacher role do not grant course mutation rights."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.api.dashboard import _access
from app.models.course_membership import CourseMembership
from app.models.user import User


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [None, "student", "teacher", "owner"])
@pytest.mark.parametrize("scope", ["course", "team", "project"])
@pytest.mark.parametrize("linked", [False, True])
async def test_api_mutations_require_course_staff(monkeypatch, role, scope, linked):
    engine = create_engine("sqlite:///:memory:")
    User.__table__.create(engine)
    CourseMembership.__table__.create(engine)
    course_id = uuid.uuid4()
    team = SimpleNamespace(course_id=course_id)
    with Session(engine) as session:
        user = User(
            username="teacher",
            gitlab_username="teacher" if linked else None,
            role="teacher",
            password_hash="unused",
            is_active=True,
        )
        session.add(user)
        session.flush()
        if role:
            session.add(CourseMembership(user_id=user.id, course_id=course_id, role=role))
            session.flush()
        auth = {"role": "teacher", "user": "teacher", "gitlab_username": "teacher"}
        monkeypatch.setattr(_access, "_validate_session", lambda *args: auth)
        db = SimpleNamespace(
            execute=AsyncMock(side_effect=session.execute), get=AsyncMock(return_value=team)
        )
        obj = {
            "course": SimpleNamespace(id=course_id),
            "team": team,
            "project": SimpleNamespace(team_id=uuid.uuid4()),
        }[scope]
        permitted = await _access.can_manage_via_request(
            Request({"type": "http", "headers": []}), db, **{scope: obj}
        )
        assert permitted is (role in {"teacher", "owner"})
        if permitted:
            course = SimpleNamespace(id=course_id)
            assert await _access._filter_courses_for_user([course], auth, db) == [course]
            assert await _access._filter_teams_for_user([team], auth, db) == [team]
    engine.dispose()


@pytest.mark.asyncio
async def test_admin_keeps_cross_course_management_without_membership():
    assert await _access._can_manage_team(
        SimpleNamespace(course_id=uuid.uuid4()), {"role": "admin"}, None
    )
