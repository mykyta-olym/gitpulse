"""The Assistant page's actions answer JSON, and every refusal names its reason.

The page script turns the reason into the toast the teacher reads, so each one
must arrive as a code, not as a 500 or a bare 400: the feature off, no such
course, an archived course, a token GitLab will not back, a form with a path
outside the repository, an exercise with nothing to prepare.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dashboard.courses import assistant as routes
from app.config import get_settings
from app.dependencies import CSRFCheck, DbSession, RateLimitDep, TeacherAuth

COURSE_ID = uuid.uuid4()
PROJECT_ID = str(uuid.uuid4())
BASE = f"/dashboard/courses/{COURSE_ID}/assistant"


def _override(app: FastAPI, annotated: Any, value: Any) -> None:
    app.dependency_overrides[annotated.__metadata__[0].dependency] = lambda: value


class _Db:
    def __init__(self, course: Any) -> None:
        self.course = course
        self.commits = 0
        self.added: list[Any] = []

    async def get(self, _model: Any, _id: Any) -> Any:
        return self.course

    def add(self, row: Any) -> None:
        self.added.append(row)

    async def flush(self) -> None:
        for row in self.added:
            if getattr(row, "id", None) is None:
                row.id = uuid.uuid4()

    async def commit(self) -> None:
        self.commits += 1


@pytest.fixture
def course() -> SimpleNamespace:
    return SimpleNamespace(id=COURSE_ID, is_active=True)


@pytest.fixture
def db(course: SimpleNamespace) -> _Db:
    return _Db(course)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, course: SimpleNamespace, db: _Db) -> TestClient:
    monkeypatch.setattr(get_settings(), "feature_classroom_assistant", True)
    monkeypatch.setattr(routes, "_membership_role", AsyncMock(return_value="teacher"))
    app = FastAPI()
    app.include_router(routes.router, prefix="/dashboard")
    _override(app, DbSession, db)
    _override(app, TeacherAuth, {"role": "teacher", "user": "t", "gitlab_username": "teach"})
    _override(app, CSRFCheck, None)
    _override(app, RateLimitDep, None)
    return TestClient(app)


def _assistant(*, usable: bool = True, **fields: Any) -> SimpleNamespace:
    values = {
        "is_connected": True,
        "mr_review_enabled": True,
        "bot_username": "bot",
        "last_exercise_run": None,
    }
    assistant = SimpleNamespace(**{**values, **fields})
    assistant.can_act = lambda _now: usable
    return assistant


def test_the_feature_off_refuses_every_action(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "feature_classroom_assistant", False)
    for action in ("token", "disconnect", "tools", "exercise"):
        response = client.post(f"{BASE}/{action}")
        assert response.status_code == 404
        assert response.json()["error"] == "feature_disabled"


@pytest.mark.parametrize("course_role", [None, "student"])
def test_a_course_the_teacher_does_not_run(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, course_role: str | None
) -> None:
    """Seeing a course (a mentor in one of its teams) is not running it: no
    course role of owner or teacher, no action - nor the page."""
    monkeypatch.setattr(routes, "_membership_role", AsyncMock(return_value=course_role))
    for action in ("token", "disconnect", "tools", "exercise"):
        response = client.post(f"{BASE}/{action}")
        assert response.status_code == 404
        assert response.json()["error"] == "not_found"


def test_an_admin_runs_every_course(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routes, "_membership_role", AsyncMock(return_value=None))
    client.app.dependency_overrides[TeacherAuth.__metadata__[0].dependency] = lambda: {
        "role": "admin",
        "user": "a",
    }
    monkeypatch.setattr(routes.account, "assistant_for", AsyncMock(return_value=None))
    assert client.post(f"{BASE}/disconnect").json() == {"ok": True}


def test_an_archived_course_is_read_only(client: TestClient, course: SimpleNamespace) -> None:
    course.is_active = False
    for action in ("token", "disconnect", "tools", "exercise"):
        assert client.post(f"{BASE}/{action}").status_code == 409


def test_a_rejected_token_names_why(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        routes.account, "connect", AsyncMock(side_effect=routes.account.TokenRejectedError("scope"))
    )
    response = client.post(f"{BASE}/token", data={"token": "glpat_placeholder_token"})
    assert response.status_code == 422
    assert response.json() == {"ok": False, "error": "scope"}


def test_a_connected_token_answers_who_the_bot_is(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    connect = AsyncMock(return_value=_assistant(bot_username="group_7_bot"))
    monkeypatch.setattr(routes.account, "connect", connect)
    response = client.post(f"{BASE}/token", data={"token": "glpat_placeholder_token"})
    assert response.json() == {"ok": True, "bot_username": "group_7_bot"}
    assert connect.await_args.args[1:] == (COURSE_ID, "glpat_placeholder_token")
    assert connect.await_args.kwargs == {"actor": "teach"}


def test_disconnecting(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    disconnect = AsyncMock()
    monkeypatch.setattr(routes.account, "assistant_for", AsyncMock(return_value=_assistant()))
    monkeypatch.setattr(routes.account, "disconnect", disconnect)
    assert client.post(f"{BASE}/disconnect").json() == {"ok": True}
    disconnect.assert_awaited_once()


def test_an_invalid_tools_form_names_its_fields(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    save = AsyncMock()
    monkeypatch.setattr(routes.account, "save_tools", save)
    response = client.post(
        f"{BASE}/tools",
        data={
            "min_commit_title_length": "10",
            "conflict_file_path": "../etc",
            "exercise_file_template": "x.txt",
        },
    )
    assert response.status_code == 422
    assert response.json()["fields"] == ["conflict_file_path", "exercise_file_template"]
    save.assert_not_awaited()


def test_a_good_tools_form_is_saved(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    save = AsyncMock()
    monkeypatch.setattr(routes.account, "ensure_assistant", AsyncMock(return_value=MagicMock()))
    monkeypatch.setattr(routes.account, "save_tools", save)
    response = client.post(
        f"{BASE}/tools",
        data={
            "conflict_enabled": "true",
            "mr_bot_merges": "true",
            "min_commit_title_length": "12",
            "conflict_file_path": "docs/zadanie.md",
            "exercise_file_template": "ulohy/{username}.md",
        },
    )
    assert response.json() == {"ok": True}
    tools = save.await_args.args[2]
    assert tools.conflict_enabled is True
    assert tools.push_review_enabled is False
    assert tools.min_commit_title_length == 12
    assert tools.mr_bot_merges is True
    assert tools.mr_review_enabled is False


@pytest.mark.parametrize(
    ("assistant", "chosen", "error", "status"),
    [
        (None, [PROJECT_ID], "not_connected", 409),
        (_assistant(is_connected=False), [PROJECT_ID], "not_connected", 409),
        (_assistant(usable=False), [PROJECT_ID], "token_unusable", 409),
        (_assistant(mr_review_enabled=False), [PROJECT_ID], "tool_off", 409),
        (
            _assistant(
                last_exercise_run={"status": "running", "at": datetime.now(UTC).isoformat()}
            ),
            [PROJECT_ID],
            "already_running",
            409,
        ),
        (_assistant(), [str(uuid.uuid4())], "no_projects", 422),
        (_assistant(), [], "no_projects", 422),
    ],
)
def test_an_exercise_that_cannot_be_prepared(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    assistant: Any,
    chosen: list[str],
    error: str,
    status: int,
) -> None:
    monkeypatch.setattr(routes.account, "assistant_for", AsyncMock(return_value=assistant))
    monkeypatch.setattr(
        routes.account, "course_projects", AsyncMock(return_value=[{"id": PROJECT_ID}])
    )
    response = client.post(f"{BASE}/exercise", data={"project_ids": chosen})
    assert response.status_code == status
    assert response.json()["error"] == error


def test_the_exercise_is_queued_for_the_courses_projects_only(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, db: _Db
) -> None:
    """...as a BackgroundJob of the course, which the top bar follows."""
    enqueue = MagicMock(return_value="job-1")
    started = AsyncMock(return_value=None)
    monkeypatch.setattr(routes, "enqueue_assistant_exercise", enqueue)
    monkeypatch.setattr(routes.account, "start_exercise_run", started)
    monkeypatch.setattr(routes.account, "assistant_for", AsyncMock(return_value=_assistant()))
    monkeypatch.setattr(
        routes.account, "course_projects", AsyncMock(return_value=[{"id": PROJECT_ID}])
    )
    stranger = str(uuid.uuid4())
    response = client.post(f"{BASE}/exercise", data={"project_ids": [PROJECT_ID, stranger]})
    (job,) = db.added
    assert (job.job_type, job.course_id, job.rq_job_id) == (
        "assistant_exercise",
        COURSE_ID,
        "job-1",
    )
    assert response.json() == {"ok": True, "projects": 1, "job_id": str(job.id)}
    enqueue.assert_called_once_with(str(COURSE_ID), [PROJECT_ID], "teach", str(job.id))
    started.assert_awaited_once()


def test_a_queue_that_is_down_is_said(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, db: _Db
) -> None:
    """...the run it marked as started is put back the way it was, and its
    job reads failed in Job History."""
    earlier = {"at": "2026-10-01T10:00:00+00:00", "by": "t", "projects": []}
    assistant = _assistant(last_exercise_run=earlier)
    monkeypatch.setattr(routes, "enqueue_assistant_exercise", MagicMock(return_value=None))
    monkeypatch.setattr(routes.account, "assistant_for", AsyncMock(return_value=assistant))
    monkeypatch.setattr(routes.account, "start_exercise_run", AsyncMock(return_value=earlier))
    monkeypatch.setattr(
        routes.account, "course_projects", AsyncMock(return_value=[{"id": PROJECT_ID}])
    )
    response = client.post(f"{BASE}/exercise", data={"project_ids": [PROJECT_ID]})
    assert response.status_code == 503
    assert response.json()["error"] == "queue_unavailable"
    assert db.added[0].status == "failed"
    assert assistant.last_exercise_run == earlier


def test_the_activity_card_alone_is_for_whoever_runs_the_course(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """What the card's Refresh and the live stream redraw: the card, nothing
    around it - and no card for a teacher who only sees the course."""
    monkeypatch.setattr(routes.account, "activity", AsyncMock(return_value=[]))
    response = client.get(f"{BASE}/activity")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.text.count('id="assistantActivityCard"') == 1
    assert "<html" not in response.text
    monkeypatch.setattr(routes, "_membership_role", AsyncMock(return_value=None))
    assert client.get(f"{BASE}/activity").status_code == 404
