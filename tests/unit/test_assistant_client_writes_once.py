"""The bot's GitLab client: reads are retried, writes are sent exactly once.

A comment POST that timed out may already be in the merge request; sending it
again would post it twice. So only a GET retries on a transient answer, and a
refusal comes back as a ``GitLabAPIError`` carrying GitLab's own reason, which
the teacher then reads on the Assistant page.

It is also not the read-only ``GitLabClient``: a 401 here must not poison the
shared token-health flag that pauses every sync.
"""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock

import httpx
import pytest
from pytest_httpx import HTTPXMock

from app.services.assistant.client import BotGitLabClient
from app.services.gitlab import token_health
from app.services.gitlab.client_types import GitLabAPIError

API = "https://gitlab.test/api/v4"


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.assistant.client.asyncio.sleep", AsyncMock())


def _bot() -> BotGitLabClient:
    return BotGitLabClient("https://gitlab.test/", "bot-token")


async def test_a_read_sends_the_bots_token(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{API}/user", json={"id": 9, "username": "bot"})
    async with _bot() as bot:
        assert await bot.current_user() == {"id": 9, "username": "bot"}
    assert httpx_mock.get_requests()[0].headers["PRIVATE-TOKEN"] == "bot-token"


async def test_a_read_retries_a_server_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{API}/projects/1", status_code=502)
    httpx_mock.add_response(url=f"{API}/projects/1", json={"id": 1})
    async with _bot() as bot:
        assert await bot.project(1) == {"id": 1}


async def test_a_read_gives_up_after_three_attempts(httpx_mock: HTTPXMock) -> None:
    for _ in range(3):
        httpx_mock.add_response(url=f"{API}/projects/1", status_code=503)
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError) as err:
            await bot.project(1)
    assert err.value.status_code == 503


async def test_a_missing_thing_is_none(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/repository/files/docs%2Fa.md/raw?ref=main", status_code=404
    )
    async with _bot() as bot:
        assert await bot.file_text(1, "docs/a.md", "main") is None


async def test_a_write_is_not_retried(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests/3/notes", method="POST", status_code=502
    )
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError) as err:
            await bot.comment_on_merge_request(1, 3, "hello")
    assert err.value.status_code == 502
    assert len(httpx_mock.get_requests()) == 1


async def test_a_write_that_never_arrived_is_reported_as_unreachable(
    httpx_mock: HTTPXMock,
) -> None:
    httpx_mock.add_exception(httpx.ConnectError("refused"))
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError) as err:
            await bot.comment_on_commit(1, "abc", "hello")
    assert err.value.status_code == 0
    assert len(httpx_mock.get_requests()) == 1


async def test_a_refusal_carries_gitlabs_reason(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests/3/merge",
        method="PUT",
        status_code=405,
        json={"message": "405 Method Not Allowed"},
    )
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError, match="405 Method Not Allowed"):
            await bot.merge(1, 3, "abc", when_pipeline=False)


async def test_a_401_leaves_the_sync_token_alone(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{API}/user", status_code=401, json={"message": "401"})
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError):
            await bot.current_user()
    assert token_health.cached_status() != "unauthorized"


async def test_a_file_revision_is_decoded_with_its_last_commit(httpx_mock: HTTPXMock) -> None:
    content = "Ahoj\nsvet\n"
    httpx_mock.add_response(
        url=f"{API}/projects/1/repository/files/README.md?ref=main",
        json={
            "content": base64.b64encode(content.encode()).decode(),
            "encoding": "base64",
            "last_commit_id": "c0ffee",
        },
    )
    async with _bot() as bot:
        assert await bot.file_revision(1, "README.md", "main") == (content, "c0ffee")


async def test_a_binary_file_is_no_text(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/repository/files/logo.png?ref=main",
        json={"content": base64.b64encode(b"\xff\xfe\x00").decode(), "last_commit_id": "1"},
    )
    async with _bot() as bot:
        assert await bot.file_revision(1, "logo.png", "main") is None


async def test_the_merge_base_names_both_refs(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json={"id": "base"})
    async with _bot() as bot:
        assert await bot.is_ancestor(1, "base", "head") is True
    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/api/v4/projects/1/repository/merge_base"
    assert request.url.params.get_list("refs[]") == ["base", "head"]


async def test_changed_paths_cover_renames_once(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests/2/changes",
        json={
            "changes": [
                {"old_path": "a.txt", "new_path": "a.txt"},
                {"old_path": "old.txt", "new_path": "new.txt"},
            ]
        },
    )
    async with _bot() as bot:
        assert await bot.changed_paths(1, 2) == ["a.txt", "old.txt", "new.txt"]


async def test_a_merge_request_is_read_once_gitlab_knows_if_it_can_merge(
    httpx_mock: HTTPXMock,
) -> None:
    """Right after a push GitLab is still checking; has_conflicts says nothing."""
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests/2?with_merge_status_recheck=true",
        json={"iid": 2, "detailed_merge_status": "checking", "has_conflicts": False},
    )
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests/2",
        json={"iid": 2, "detailed_merge_status": "conflict", "has_conflicts": True},
    )
    async with _bot() as bot:
        mr = await bot.merge_request(1, 2)
    assert mr is not None
    assert mr["has_conflicts"] is True


async def test_a_merge_request_gitlab_never_finishes_checking_is_read_anyway(
    httpx_mock: HTTPXMock,
) -> None:
    for _ in range(4):
        httpx_mock.add_response(json={"iid": 2, "detailed_merge_status": "unchecked"})
    async with _bot() as bot:
        mr = await bot.merge_request(1, 2)
    assert mr is not None
    assert len(httpx_mock.get_requests()) == 4, "the first read and three waits, no more"


async def test_the_merge_requests_of_a_commit(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/repository/commits/abc/merge_requests",
        json=[{"iid": 7, "state": "merged", "target_branch": "main"}],
    )
    async with _bot() as bot:
        assert await bot.merge_requests_of_commit(1, "abc") == [
            {"iid": 7, "state": "merged", "target_branch": "main"}
        ]


async def test_an_issue_is_assigned_to_the_student(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/issues", method="POST", json={"iid": 4, "web_url": "u"}
    )
    async with _bot() as bot:
        assert (await bot.create_issue(1, "T", "D", 77))["iid"] == 4
    body = httpx_mock.get_requests()[0].read()
    assert b'"assignee_ids":[77]' in body.replace(b" ", b"")


async def test_a_branch_name_is_one_path_segment(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests?source_branch=feature%2Fx&state=opened",
        json=[{"iid": 5}],
    )
    async with _bot() as bot:
        assert await bot.open_merge_request_for(1, "feature/x") == {"iid": 5}


async def test_a_401_on_one_action_is_not_a_dead_token(httpx_mock: HTTPXMock) -> None:
    """GitLab answers 401 to approving twice; ``GET /user`` then still works."""
    httpx_mock.add_response(
        url=f"{API}/projects/1/merge_requests/3/approve", method="POST", status_code=401
    )
    httpx_mock.add_response(url=f"{API}/user", json={"id": 9})
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError):
            await bot.approve(1, 3, "abc")
        assert bot.saw_unauthorized
        assert await bot.token_rejected() is False


async def test_a_token_gitlab_refuses_everywhere_is_dead(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{API}/projects/1", status_code=401)
    httpx_mock.add_response(url=f"{API}/user", status_code=401)
    async with _bot() as bot:
        with pytest.raises(GitLabAPIError):
            await bot.project(1)
        assert await bot.token_rejected() is True


async def test_no_401_asks_gitlab_nothing_more(httpx_mock: HTTPXMock) -> None:
    async with _bot() as bot:
        assert await bot.token_rejected() is False
    assert httpx_mock.get_requests() == []
