"""Connecting the assistant's bot - its own token, checked before it is kept.

The sync token stays read-only, so the assistant refuses it; a token GitLab
rejects, or one without the ``api`` scope, is refused with a reason the page
can name; an accepted one is stored encrypted, never as typed. The tools form
accepts only paths inside the repository.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import get_settings
from app.models.assistant import CourseAssistant
from app.security.token_encryption import decrypt_token, is_encrypted
from app.services.assistant import account
from app.services.gitlab.client_types import GitLabAPIError


class _Bot:
    """GitLab as the token sees it."""

    def __init__(self, user: Any = None, info: Any = None, error: Exception | None = None):
        self._user, self._info, self._error = user, info, error

    async def __aenter__(self) -> _Bot:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def current_user(self) -> Any:
        if self._error:
            raise self._error
        return self._user

    async def token_info(self) -> Any:
        return self._info


def _session(assistant: CourseAssistant | None = None) -> Any:
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = assistant
    session.execute = AsyncMock(return_value=result)
    return session


def _gitlab(monkeypatch: pytest.MonkeyPatch, bot: _Bot) -> None:
    monkeypatch.setattr(account, "BotGitLabClient", lambda *_a, **_k: bot)


@pytest.mark.parametrize(
    ("bot", "reason"),
    [
        (_Bot(error=GitLabAPIError(401, "401 Unauthorized")), "invalid"),
        (_Bot(error=GitLabAPIError(0, "GitLab unreachable")), "unreachable"),
        (_Bot(user=None), "invalid"),
        (_Bot(user={"id": 5, "username": "bot"}, info={"scopes": ["read_api"]}), "scope"),
    ],
)
async def test_a_token_gitlab_does_not_back_is_refused(
    monkeypatch: pytest.MonkeyPatch, bot: _Bot, reason: str
) -> None:
    _gitlab(monkeypatch, bot)
    session = _session()
    with pytest.raises(account.TokenRejectedError) as err:
        await account.connect(session, uuid.uuid4(), "glpat_placeholder_token", actor="teacher")
    assert err.value.reason == reason
    session.commit.assert_not_awaited()


async def test_an_empty_token_is_refused_without_asking_gitlab(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gitlab(monkeypatch, _Bot(error=AssertionError("GitLab must not be asked")))
    with pytest.raises(account.TokenRejectedError) as err:
        await account.connect(_session(), uuid.uuid4(), "   ", actor="teacher")
    assert err.value.reason == "empty"


async def test_the_sync_token_is_not_the_bots(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "gitlab_api_token", "glpat_placeholder_token")
    _gitlab(monkeypatch, _Bot(error=AssertionError("GitLab must not be asked")))
    with pytest.raises(account.TokenRejectedError) as err:
        await account.connect(_session(), uuid.uuid4(), "glpat_placeholder_token", actor="teacher")
    assert err.value.reason == "read_token"


async def test_an_accepted_token_is_stored_encrypted_with_who_it_is(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gitlab(
        monkeypatch,
        _Bot(
            user={"id": 42, "username": "group_7_bot_ab", "name": "Assistant", "avatar_url": "a"},
            info={"scopes": ["api"], "expires_at": "2026-12-31"},
        ),
    )
    course_id = uuid.uuid4()
    existing = CourseAssistant(course_id=course_id)
    session = _session(existing)
    assistant = await account.connect(session, course_id, " glpat_placeholder_token ", actor="teacher")
    assert assistant is existing
    assert is_encrypted(assistant.bot_token)
    assert decrypt_token(assistant.bot_token, get_settings().secret_key) == "glpat_placeholder_token"
    assert (assistant.bot_user_id, assistant.bot_username) == (42, "group_7_bot_ab")
    assert assistant.token_expires_at == datetime(2026, 12, 31, tzinfo=UTC)
    assert assistant.connected_by == "teacher"
    session.commit.assert_awaited_once()


async def test_disconnecting_forgets_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant = CourseAssistant(
        course_id=uuid.uuid4(), bot_token="enc:v1:x", bot_user_id=1, bot_username="bot"
    )
    session = _session(assistant)
    await account.disconnect(session, assistant, actor="teacher")
    assert not assistant.is_connected
    assert assistant.bot_user_id is None
    session.commit.assert_awaited_once()


def _tools(**values: str) -> account.Tools:
    form = {
        "push_review_enabled": "true",
        "min_commit_title_length": "10",
        "conflict_file_path": "README.md",
        "exercise_file_template": "ulohy/{username}.txt",
        **values,
    }
    return account.read_tools(form)


class TestTheToolsForm:
    def test_a_good_form(self) -> None:
        tools = _tools()
        assert tools.errors() == []
        assert tools.push_review_enabled is True
        assert tools.conflict_enabled is False

    @pytest.mark.parametrize(
        "path", ["", "/etc/passwd", "../x", "a/../b", "a//b", "a\\b", "x" * 301]
    )
    def test_a_path_outside_the_repository_is_refused(self, path: str) -> None:
        assert _tools(conflict_file_path=path).errors() == ["conflict_file_path"]

    def test_the_template_needs_the_username(self) -> None:
        assert _tools(exercise_file_template="ulohy/all.txt").errors() == ["exercise_file_template"]

    @pytest.mark.parametrize("value", ["0", "73", "ten"])
    def test_the_title_length_is_bounded(self, value: str) -> None:
        assert _tools(min_commit_title_length=value).errors() == ["min_commit_title_length"]

    def test_a_course_without_a_row_shows_the_defaults(self) -> None:
        tools = account.tools_of(None)
        assert tools.errors() == []
        assert not tools.push_review_enabled
        assert not tools.conflict_enabled
        assert not tools.mr_review_enabled
        assert not tools.mr_bot_merges


class TestWhatThePageSays:
    def test_the_token_expiry(self) -> None:
        assert account.token_state(None) is None
        soon = CourseAssistant(token_expires_at=datetime.now(UTC) + timedelta(days=3))
        later = CourseAssistant(token_expires_at=datetime.now(UTC) + timedelta(days=90))
        gone = CourseAssistant(token_expires_at=datetime.now(UTC) - timedelta(days=1))
        assert account.token_state(soon) == "expiring"
        assert account.token_state(later) == "ok"
        assert account.token_state(gone) == "expired"

    def test_the_last_exercise_run_reads_its_time(self) -> None:
        run = {"at": "2026-10-19T10:00:00+00:00", "by": "t", "projects": []}
        shown = account.last_exercise_run(CourseAssistant(last_exercise_run=run))
        assert shown is not None
        assert shown["at"] == datetime(2026, 10, 19, 10, tzinfo=UTC)
        assert account.last_exercise_run(CourseAssistant()) is None


class TestWhenTheBotCanAct:
    NOW = datetime(2026, 10, 19, 12, tzinfo=UTC)

    def test_a_connected_token(self) -> None:
        assert CourseAssistant(bot_token="enc:v1:x").can_act(self.NOW)

    def test_no_token(self) -> None:
        assert not CourseAssistant().can_act(self.NOW)

    def test_past_its_expiry(self) -> None:
        bot = CourseAssistant(bot_token="enc:v1:x", token_expires_at=self.NOW - timedelta(hours=1))
        assert not bot.can_act(self.NOW)

    def test_refused_by_gitlab(self) -> None:
        bot = CourseAssistant(bot_token="enc:v1:x", token_rejected_at=self.NOW)
        assert not bot.can_act(self.NOW)


class TestTheExerciseRunState:
    def _state(self, run: dict[str, Any]) -> str:
        shown = account.last_exercise_run(CourseAssistant(last_exercise_run=run))
        assert shown is not None
        return str(shown["state"])

    def test_a_finished_run(self) -> None:
        assert self._state({"at": datetime.now(UTC).isoformat(), "projects": []}) == "done"

    def test_a_run_in_progress(self) -> None:
        run = {"status": "running", "at": datetime.now(UTC).isoformat()}
        assert self._state(run) == "running"

    def test_a_run_that_died(self) -> None:
        run = {"status": "running", "at": (datetime.now(UTC) - timedelta(hours=1)).isoformat()}
        assert self._state(run) == "stale"

    async def test_starting_a_run_keeps_what_it_replaces(self) -> None:
        earlier = {"at": "2026-10-01T10:00:00+00:00", "projects": []}
        assistant = CourseAssistant(last_exercise_run=earlier)
        session = _session(assistant)
        previous = await account.start_exercise_run(session, assistant, actor="teacher")
        assert previous == earlier
        assert assistant.last_exercise_run is not None
        assert assistant.last_exercise_run["status"] == "running"
        session.commit.assert_awaited_once()


def test_the_comment_language_must_be_one_the_app_speaks() -> None:
    assert _tools(comment_language="en").errors() == []
    assert _tools(comment_language="de").errors() == ["comment_language"]
    assert _tools().comment_language == "sk", "an empty choice is the default language"
