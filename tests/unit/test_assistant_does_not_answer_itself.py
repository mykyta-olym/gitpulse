"""Which events reach which tool - and the bot never answers its own actions.

Every comment, commit and approval of the bot comes back as a webhook. Handled,
they would loop: a comment answering a comment. So everything the bot account
did is dropped - except GitLab's merge event, which is how the exercise learns
that the merge it asked for (or the auto-merge it set) happened. A course
without the feature, without a connected bot, or without the tool costs no
work at all.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import get_settings
from app.models.assistant import CourseAssistant
from app.services.assistant import events
from app.workers import event_processor

BOT_ID = 900
STUDENT = SimpleNamespace(id=uuid.uuid4(), gitlab_username="jana")


class _Bot:
    rejected = False

    async def __aenter__(self) -> _Bot:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def token_rejected(self) -> bool:
        return self.rejected


def _assistant(**fields: Any) -> CourseAssistant:
    values = {
        "id": uuid.uuid4(),
        "bot_token": "enc:v1:x",
        "bot_user_id": BOT_ID,
        "push_review_enabled": True,
        "conflict_enabled": True,
        "mr_review_enabled": True,
    }
    return CourseAssistant(**{**values, **fields})


@pytest.fixture
def bot() -> _Bot:
    return _Bot()


@pytest.fixture
def tools(monkeypatch: pytest.MonkeyPatch, bot: _Bot) -> dict[str, AsyncMock]:
    """The feature on, a connected assistant with every tool, the tools spied on."""
    monkeypatch.setattr(get_settings(), "feature_classroom_assistant", True)
    project = SimpleNamespace(
        id=uuid.uuid4(), default_branch="main", gitlab_project_path="zsi/a", gitlab_project_id=1
    )
    course = SimpleNamespace(id=uuid.uuid4(), settings=None)
    monkeypatch.setattr(events, "_load", AsyncMock(return_value=(course, project, _assistant())))
    monkeypatch.setattr(events, "decrypt_token", lambda *_a: "bot-token")
    monkeypatch.setattr(events, "acting_student", AsyncMock(return_value=STUDENT))
    monkeypatch.setattr(events, "BotGitLabClient", lambda *_a: bot)
    spies = {
        "push": AsyncMock(),
        "conflict": AsyncMock(),
        "mr": AsyncMock(),
        "note": AsyncMock(),
        "rejected": AsyncMock(),
    }
    monkeypatch.setattr(events.account, "mark_token_rejected", spies["rejected"])
    monkeypatch.setattr(events.push_review, "handle", spies["push"])
    monkeypatch.setattr(events.conflict, "handle", spies["conflict"])
    monkeypatch.setattr(events.mr_review, "on_merge_request", spies["mr"])
    monkeypatch.setattr(events.mr_review, "on_note", spies["note"])
    return spies


def _event(kind: str, payload: dict[str, Any]) -> Any:
    return SimpleNamespace(gitlab_object_kind=kind, payload=payload, gitlab_project_id=1)


async def test_a_students_push_reaches_both_push_tools(tools: dict[str, AsyncMock]) -> None:
    await events.handle(MagicMock(), _event("push", {"user_id": 5, "user_username": "jana"}))
    tools["push"].assert_awaited_once()
    tools["conflict"].assert_awaited_once()
    assert tools["push"].await_args.args[4] is STUDENT


async def test_the_bots_own_push_is_dropped(tools: dict[str, AsyncMock]) -> None:
    await events.handle(MagicMock(), _event("push", {"user_id": BOT_ID}))
    tools["push"].assert_not_awaited()
    tools["conflict"].assert_not_awaited()


async def test_a_push_by_someone_who_is_not_a_student_is_dropped(
    tools: dict[str, AsyncMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(events, "acting_student", AsyncMock(return_value=None))
    await events.handle(MagicMock(), _event("push", {"user_id": 6, "user_username": "teacher"}))
    tools["push"].assert_not_awaited()


async def test_a_merge_request_event_says_whether_the_bot_caused_it(
    tools: dict[str, AsyncMock],
) -> None:
    await events.handle(MagicMock(), _event("merge_request", {"user": {"id": BOT_ID}}))
    assert tools["mr"].await_args.kwargs == {"by_bot": True}
    await events.handle(MagicMock(), _event("merge_request", {"user": {"id": 5}}))
    assert tools["mr"].await_args.kwargs == {"by_bot": False}


async def test_the_bots_own_comment_is_dropped(tools: dict[str, AsyncMock]) -> None:
    await events.handle(MagicMock(), _event("note", {"user": {"id": BOT_ID}}))
    tools["note"].assert_not_awaited()
    await events.handle(MagicMock(), _event("note", {"user": {"id": 5, "username": "jana"}}))
    tools["note"].assert_awaited_once()


async def test_a_tool_that_is_off_is_not_run(
    tools: dict[str, AsyncMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = await events._load(MagicMock(), 1)
    loaded[2].conflict_enabled = False
    await events.handle(MagicMock(), _event("push", {"user_id": 5}))
    tools["push"].assert_awaited_once()
    tools["conflict"].assert_not_awaited()


async def test_an_unreadable_token_stops_quietly(
    tools: dict[str, AsyncMock], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(events, "decrypt_token", lambda *_a: None)
    await events.handle(MagicMock(), _event("push", {"user_id": 5}))
    tools["push"].assert_not_awaited()


async def test_the_feature_off_asks_the_database_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "feature_classroom_assistant", False)
    session = MagicMock()
    session.execute = AsyncMock()
    assert await events.wants(session, 1, "push") is False
    await events.handle(session, _event("push", {"user_id": 5}))
    session.execute.assert_not_awaited()


async def test_other_kinds_are_not_wanted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "feature_classroom_assistant", True)
    session = MagicMock()
    session.execute = AsyncMock()
    assert await events.wants(session, 1, "pipeline") is False
    session.execute.assert_not_awaited()


@pytest.mark.parametrize(
    ("kind", "flags", "wanted"),
    [
        ("push", {"push_review_enabled": True}, True),
        ("push", {"conflict_enabled": True}, True),
        ("push", {"mr_review_enabled": True}, False),
        ("merge_request", {"mr_review_enabled": True}, True),
        ("note", {"push_review_enabled": True}, False),
    ],
)
async def test_an_event_is_wanted_when_its_tool_is_on(
    monkeypatch: pytest.MonkeyPatch, kind: str, flags: dict[str, bool], wanted: bool
) -> None:
    monkeypatch.setattr(get_settings(), "feature_classroom_assistant", True)
    assistant = _assistant(
        **{"push_review_enabled": False, "conflict_enabled": False, "mr_review_enabled": False}
        | flags
    )
    monkeypatch.setattr(events, "_load", AsyncMock(return_value=(None, None, assistant)))
    assert await events.wants(MagicMock(), 1, kind) is wanted


@pytest.mark.parametrize(
    "fields",
    [
        {"token_expires_at": datetime.now(UTC) - timedelta(minutes=1)},
        {"token_rejected_at": datetime.now(UTC)},
    ],
    ids=["expired", "rejected"],
)
async def test_a_token_that_cannot_act_stops_every_tool(
    tools: dict[str, AsyncMock], monkeypatch: pytest.MonkeyPatch, fields: dict[str, Any]
) -> None:
    course = SimpleNamespace(id=uuid.uuid4(), settings=None)
    project = SimpleNamespace(id=uuid.uuid4(), default_branch="main", gitlab_project_path="a")
    monkeypatch.setattr(
        events, "_load", AsyncMock(return_value=(course, project, _assistant(**fields)))
    )
    assert await events.wants(MagicMock(), 1, "push") is False
    await events.handle(MagicMock(), _event("push", {"user_id": 5}))
    tools["push"].assert_not_awaited()


async def test_a_token_gitlab_refuses_is_recorded(tools: dict[str, AsyncMock], bot: Any) -> None:
    bot.rejected = True
    await events.handle(MagicMock(), _event("push", {"user_id": 5}))
    tools["push"].assert_awaited_once()
    tools["rejected"].assert_awaited_once()
    assert tools["rejected"].await_args.args[2] == "enc:v1:x", "only the token that was used"


async def test_a_token_gitlab_still_takes_is_left_alone(tools: dict[str, AsyncMock]) -> None:
    await events.handle(MagicMock(), _event("push", {"user_id": 5}))
    tools["rejected"].assert_not_awaited()


async def test_the_event_pipeline_queues_the_assistant_only_when_wanted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enqueue = MagicMock()
    monkeypatch.setattr("app.services.events.enqueue_assistant_event", enqueue)
    event = SimpleNamespace(id=uuid.uuid4(), gitlab_project_id=1)

    monkeypatch.setattr(events, "wants", AsyncMock(return_value=False))
    await event_processor._enqueue_assistant(MagicMock(), event, "push")
    enqueue.assert_not_called()

    monkeypatch.setattr(events, "wants", AsyncMock(return_value=True))
    await event_processor._enqueue_assistant(MagicMock(), event, "push")
    enqueue.assert_called_once_with(str(event.id))
