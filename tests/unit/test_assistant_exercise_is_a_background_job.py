"""Prepare exercise runs as a BackgroundJob, the way a sync does.

The top bar follows the job to its end and Admin -> System's Job History
lists it with its duration. A run that cannot start - the course archived,
the bot gone, its token refused since the click - fails its job at once and
says why on the page, instead of "Preparing" until it goes stale a quarter of
an hour later. A finished run tells the course's live stream, so an open
Assistant page redraws its activity card.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.workers import assistant_job

COURSE_ID = uuid.uuid4()
JOB_ID = str(uuid.uuid4())


class _Result:
    def __init__(self, value: Any) -> None:
        self.value = value

    def scalar_one_or_none(self) -> Any:
        return self.value


class _Session:
    def __init__(self, course: Any, assistant: Any) -> None:
        self.rows = {
            Course: course,
            BackgroundJob: SimpleNamespace(
                status="enqueued",
                started_at=None,
                enqueued_at=datetime.now(UTC),
                completed_at=None,
                duration_ms=None,
                result_summary=None,
                error_message=None,
            ),
        }
        self.assistant = assistant

    async def get(self, model: Any, _id: Any) -> Any:
        return self.rows.get(model)

    async def execute(self, _stmt: Any) -> _Result:
        return _Result(self.assistant)

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass

    @property
    def job(self) -> Any:
        return self.rows[BackgroundJob]


def _assistant(*, usable: bool = True) -> SimpleNamespace:
    assistant = SimpleNamespace(
        id=uuid.uuid4(),
        bot_token="enc",
        comment_language="sk",
        last_exercise_run={"status": "running", "at": datetime.now(UTC).isoformat()},
    )
    assistant.can_act = lambda _now: usable
    return assistant


@pytest.fixture
def run(monkeypatch: pytest.MonkeyPatch) -> Any:
    published = MagicMock()
    announced = MagicMock()
    monkeypatch.setattr(assistant_job, "init_engine", lambda *_a, **_k: None)
    monkeypatch.setattr(assistant_job, "dispose_engine", AsyncMock())
    monkeypatch.setattr(assistant_job, "decrypt_token", lambda *_a: "token")
    monkeypatch.setattr(assistant_job, "publish_progress", published)
    monkeypatch.setattr(assistant_job, "publish_dashboard_update", announced)

    async def _run(session: _Session) -> SimpleNamespace:
        @asynccontextmanager
        async def _ctx() -> Any:
            yield session

        monkeypatch.setattr(assistant_job, "async_session_ctx", _ctx)
        await assistant_job._prepare_exercise(str(COURSE_ID), [], "teacher", JOB_ID)
        return SimpleNamespace(published=published, announced=announced)

    return _run


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("course", "assistant", "reason"),
    [
        (
            SimpleNamespace(id=COURSE_ID, is_active=False),
            _assistant(),
            "This course is archived and read-only. Reactivate it to make changes.",
        ),
        (
            SimpleNamespace(id=COURSE_ID, is_active=True),
            _assistant(usable=False),
            "The bot token does not work. Connect a new one first.",
        ),
    ],
)
async def test_a_run_that_cannot_start_fails_its_job_and_says_why(
    run: Any, course: Any, assistant: Any, reason: str
) -> None:
    session = _Session(course, assistant)
    out = await run(session)
    assert session.job.status == "failed"
    assert session.job.error_message == reason
    assert session.job.duration_ms is not None
    assert assistant.last_exercise_run["error"] == reason
    assert "status" not in assistant.last_exercise_run, "no longer 'running'"
    assert out.published.call_args_list[-1].args[:2] == (JOB_ID, "failed")


@pytest.mark.asyncio
async def test_a_finished_run_completes_its_job_and_tells_the_page(
    run: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _Session(SimpleNamespace(id=COURSE_ID, is_active=True), _assistant())
    monkeypatch.setattr(assistant_job, "_course_projects", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        assistant_job.exercise,
        "prepare",
        AsyncMock(return_value=[{"path": "zsi/a", "created": 2, "skipped": 0}]),
    )
    bot = MagicMock()
    bot.token_rejected = AsyncMock(return_value=False)

    @asynccontextmanager
    async def _bot(*_a: Any) -> Any:
        yield bot

    monkeypatch.setattr(assistant_job, "BotGitLabClient", _bot)
    out = await run(session)
    assert session.job.status == "completed"
    assert session.job.result_summary == "Exercise prepared"
    assert session.job.started_at is not None
    first, last = out.published.call_args_list[0], out.published.call_args_list[-1]
    assert first.args[:2] == (JOB_ID, "running")
    assert last.args[:2] == (JOB_ID, "completed")
    out.announced.assert_called_once_with("course", str(COURSE_ID), "assistant_activity")
