"""The course settings save accepts only a body posted by the settings page.

Every blank field on that form means "clear", so an empty, truncated or
foreign POST used to answer 200 and wipe the semester dates, the deadlines
and the auto-archive flag the page never showed. The page always posts the
`expected_settings_updated_at` it was rendered from; a body without it is
turned away with the conflict redirect instead of applied.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dashboard.courses import settings as settings_routes
from app.dependencies import CSRFCheck, DbSession, RateLimitDep, TeacherAuth

COURSE_ID = uuid.uuid4()


def _override(app: FastAPI, annotated: Any, value: Any) -> None:
    app.dependency_overrides[annotated.__metadata__[0].dependency] = lambda: value


class _Db:
    def __init__(self, course: Any) -> None:
        self.course = course
        self.committed = False

    async def get(self, model: Any, key: Any) -> Any:
        return self.course if key == COURSE_ID else None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False

    async def refresh(self, entity: Any, **kwargs: Any) -> None:
        pass


def _course() -> Any:
    settings = SimpleNamespace(
        updated_at=datetime(2026, 9, 1, tzinfo=UTC),
        semester_start_date=date(2026, 9, 21),
        semester_end_date=date(2026, 12, 18),
        skip_auto_archive=True,
    )
    return SimpleNamespace(
        id=COURSE_ID, is_active=True, settings=settings, updated_at=None, code="X", name="X"
    )


def _client(monkeypatch: Any, db: _Db) -> TestClient:
    async def allow(course: Any, auth: Any, db_: Any) -> bool:
        return True

    monkeypatch.setattr(settings_routes, "_can_manage_course", allow)
    app = FastAPI()
    app.include_router(settings_routes.router, prefix="/dashboard")
    _override(app, DbSession, db)
    _override(app, TeacherAuth, {"role": "teacher", "sub": "t"})
    _override(app, CSRFCheck, None)
    _override(app, RateLimitDep, None)
    return TestClient(app, follow_redirects=False)


def test_a_body_without_the_render_timestamp_is_turned_away(monkeypatch: Any) -> None:
    course = _course()
    db = _Db(course)
    resp = _client(monkeypatch, db).post(f"/dashboard/courses/{COURSE_ID}/settings", data={})

    assert resp.status_code == 303
    assert "error=conflict" in resp.headers["location"]
    assert course.settings.semester_start_date == date(2026, 9, 21), "the dates must survive"
    assert course.settings.skip_auto_archive is True
    assert not db.committed
