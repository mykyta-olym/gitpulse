"""What keeps the assistant from acting is decided once, in account.problems().

The Assistant page's top alerts and the dashboard's "Items that need your
attention" both read it, so the two never disagree. And a configuration
file's ``assistant`` section is checked as strictly as the tools form.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.models.assistant import CourseAssistant
from app.services.assistant import account


def _assistant(**fields: object) -> CourseAssistant:
    base: dict[str, object] = {
        "course_id": uuid.uuid4(),
        "push_review_enabled": False,
        "conflict_enabled": False,
        "mr_review_enabled": False,
        "min_commit_title_length": 10,
        "conflict_file_path": "README.md",
        "mr_bot_merges": False,
        "exercise_file_template": "ulohy/{username}.txt",
        "comment_language": "sk",
    }
    return CourseAssistant(**{**base, **fields})


def _connected(**fields: object) -> CourseAssistant:
    return _assistant(bot_token="x", bot_user_id=1, bot_username="bot", **fields)


def test_nothing_stops_a_connected_assistant() -> None:
    assert account.problems(_connected(push_review_enabled=True)) == []
    assert account.problems(None) == []
    assert account.problems(_assistant()) == [], "no tool on, no bot: nothing to say"


def test_one_stopping_problem_at_most_the_first_that_holds() -> None:
    now = datetime.now(UTC)
    both = _connected(token_rejected_at=now, token_expires_at=now - timedelta(days=1))
    assert account.problems(both) == ["token_rejected"]
    assert account.problems(_connected(token_expires_at=now - timedelta(days=1))) == [
        "token_expired"
    ]
    assert account.problems(_assistant(mr_review_enabled=True)) == ["no_bot"]


def test_what_will_stop_it_soon() -> None:
    now = datetime.now(UTC)
    assert account.problems(_connected(token_expires_at=now + timedelta(days=3))) == [
        "token_expiring"
    ]
    stale = {"at": (now - timedelta(hours=1)).isoformat(), "by": "t", "status": "running"}
    assert account.problems(_connected(last_exercise_run=stale)) == ["run_stale"]


def test_a_configuration_file_is_checked_like_the_form() -> None:
    current = _connected(push_review_enabled=True)
    tools, bad = account.tools_from_config(current, {"conflict_enabled": True})
    assert bad == []
    assert tools is not None
    assert tools.push_review_enabled is True, "a field the file leaves out stays"
    assert tools.conflict_enabled is True

    assert account.tools_from_config(current, {"mr_bot_merges": 1}) == (None, ["mr_bot_merges"])
    assert account.tools_from_config(current, {"comment_language": "xx"}) == (
        None,
        ["comment_language"],
    )
    tools, bad = account.tools_from_config(current, {"bot_token": "glpat_placeholder_token"})
    assert bad == []
    assert tools is not None, "an unknown key - a token included - is not a tool"
