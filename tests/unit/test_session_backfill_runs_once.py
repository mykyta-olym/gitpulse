"""The one-shot repair runs once, not once per request.

`_require_dashboard_session` fires a background task that writes
`users.gitlab_user_id` when the session carries an id the row is missing. It is
a repair for sessions minted before login started writing that id - there is
nothing for it to do afterwards - and it was firing on EVERY dashboard request.

Each firing opened its own database session, so a request already holding a pool
connection took a second one, and the dashboard opens five fragments at once
(stats, badges, attention items, activity, notifications). Five writes then
raced for the same row lock, five times per page.

Measured on production during one such burst, from the request log:

    /dashboard/sidebar-badges  total=128991ms  db=76880ms
        worst 36417ms: UPDATE users SET gitlab_user_id=... WHERE gitlab_username=...
    /dashboard/stats           total=128965ms  db=87053ms
    /dashboard/attention-items total=107442ms  db=0ms  q=0
    /dashboard/activity        total=108795ms  db=0ms  q=0

The last two are the tell: 107 seconds without running a single query, because
no connection was free to run one.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app import dependencies


@pytest.fixture(autouse=True)
def _clean_slate() -> Any:
    dependencies._BACKFILL_TRIED.clear()
    yield
    dependencies._BACKFILL_TRIED.clear()


@pytest.fixture
def scheduled(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Records who a backfill was scheduled for, without touching a database."""
    fired: list[str] = []

    async def _fake(username: str, user_id: int) -> None:
        fired.append(username)

    monkeypatch.setattr(dependencies, "_backfill_gitlab_user_id", _fake)
    return fired


def _session(username: str = "ada") -> dict[str, str]:
    return {"gitlab_username": username, "gitlab_user_id": "4242", "user": username}


async def _visit(monkeypatch: pytest.MonkeyPatch, session: dict[str, str], times: int) -> None:
    monkeypatch.setattr(dependencies, "_validate_session", lambda *_a, **_k: session)
    for _ in range(times):
        dependencies._require_dashboard_session(object(), object())  # type: ignore[arg-type]
    # let the created tasks run
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_five_fragments_of_one_page_write_once(
    monkeypatch: pytest.MonkeyPatch, scheduled: list[str]
) -> None:
    """The dashboard's five parallel fragments are what turned this into a
    five-way race for one row lock."""
    await _visit(monkeypatch, _session(), times=5)
    assert scheduled == ["ada"], f"scheduled {len(scheduled)} writes for one page"


@pytest.mark.asyncio
async def test_it_does_not_come_back_on_the_next_page(
    monkeypatch: pytest.MonkeyPatch, scheduled: list[str]
) -> None:
    await _visit(monkeypatch, _session(), times=3)
    await _visit(monkeypatch, _session(), times=3)
    assert len(scheduled) == 1, "the repair is running again on later requests"


@pytest.mark.asyncio
async def test_a_different_user_still_gets_their_repair(
    monkeypatch: pytest.MonkeyPatch, scheduled: list[str]
) -> None:
    await _visit(monkeypatch, _session("ada"), times=2)
    await _visit(monkeypatch, _session("linus"), times=2)
    assert scheduled == ["ada", "linus"]


@pytest.mark.asyncio
async def test_a_session_without_the_id_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, scheduled: list[str]
) -> None:
    await _visit(monkeypatch, {"gitlab_username": "ada", "gitlab_user_id": ""}, times=3)
    assert scheduled == []
