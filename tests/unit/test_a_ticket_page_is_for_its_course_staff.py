"""The ticket page answers only the staff of the ticket's course.

The ticket API and its SSE stream have always required course staff, but the
page itself checked nothing past "is a teacher": any teacher could open any
course's ticket by its number - internal notes included - while the page's own
live stream was refused with a 403. The page now applies the API's rule and
answers a 404, so it does not reveal that the ticket exists.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dashboard import support as support_routes
from app.dependencies import DbSession, TeacherAuth

COURSE_ID = uuid.uuid4()


def _override(app: FastAPI, annotated: Any, value: Any) -> None:
    app.dependency_overrides[annotated.__metadata__[0].dependency] = lambda: value


class _Service:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def get_ticket(self, ticket_id: int) -> Any:
        return SimpleNamespace(id=ticket_id, course_id=COURSE_ID)

    async def list_comments(self, ticket_id: int, include_internal: bool = False) -> list[Any]:
        raise AssertionError("the thread of a ticket the reader may not see was loaded")


def _client(monkeypatch: pytest.MonkeyPatch, role: str, membership: str | None) -> TestClient:
    from app.services import support_forms

    async def membership_role(db: Any, course_id: Any, session: Any) -> str | None:
        assert course_id == COURSE_ID
        return membership

    monkeypatch.setattr(support_forms, "SupportFormService", _Service)
    monkeypatch.setattr(support_routes, "_membership_role", membership_role)
    monkeypatch.setattr(
        support_routes,
        "get_settings",
        lambda: SimpleNamespace(feature_support_forms=True, support_anonymize_free_text=False),
    )
    app = FastAPI()
    app.include_router(support_routes.router, prefix="/dashboard")
    _override(app, DbSession, None)
    _override(app, TeacherAuth, {"role": role, "user": "t", "gitlab_username": "t"})
    return TestClient(app, follow_redirects=False)


@pytest.mark.parametrize("membership", [None, "student"])
def test_a_teacher_outside_the_course_gets_a_404(
    monkeypatch: pytest.MonkeyPatch, membership: str | None
) -> None:
    resp = _client(monkeypatch, "teacher", membership).get("/dashboard/support/ticket/7")

    assert resp.status_code == 404


def test_the_course_staff_are_let_through(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(AssertionError, match="thread"):
        _client(monkeypatch, "teacher", "teacher").get("/dashboard/support/ticket/7")
