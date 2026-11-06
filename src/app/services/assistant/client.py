"""The assistant's GitLab client - the bot account's token, and the writes.

Deliberately not ``GitLabClient``. That one is GET-only because GitPulse's
analytics never write, and it reports every 401 to the shared token-health flag
that pauses all syncing: a teacher's bot token expiring must not stop the
course's sync, and a sync token must never be able to comment or merge.

Writes are sent once. A timeout after GitLab already applied a comment would,
retried, post it twice - so only reads are retried, and the tools record each
write in their task row the moment it succeeds.

A 401 is remembered (``saw_unauthorized``) for :meth:`token_rejected` to
confirm: GitLab also answers 401 to approving a merge request twice, so one
401 alone does not say the token is dead.
"""

import asyncio
import base64
import urllib.parse
from typing import Any, Self, cast

import httpx

from app.services.gitlab.client_types import GitLabAPIError

JsonDict = dict[str, Any]

_RETRYABLE = frozenset({429, 500, 502, 503, 504})
_READ_ATTEMPTS = 3
# GitLab works out on its own time whether a merge request can merge.
_MERGEABILITY_PENDING = frozenset({"unchecked", "checking", "preparing", "approvals_syncing"})
_MERGEABILITY_WAITS = (1, 2, 4)


def _quote(value: str) -> str:
    """A file path or branch name as one URL path segment."""
    return urllib.parse.quote(value, safe="")


def _reason(response: httpx.Response) -> str:
    """GitLab's own words for a refusal (``message`` or ``error``)."""
    try:
        body = response.json()
    except ValueError:
        return response.text[:200]
    if isinstance(body, dict):
        message = body.get("message") or body.get("error") or body
        return str(message)[:200]
    return str(body)[:200]


class BotGitLabClient:
    """GitLab API v4 as the course's bot account."""

    def __init__(self, base_url: str, token: str, timeout: float = 20.0) -> None:
        self.saw_unauthorized = False
        self._client = httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}/api/v4",
            headers={"PRIVATE-TOKEN": token, "Accept": "application/json"},
            timeout=httpx.Timeout(timeout=timeout, connect=5.0),
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self._client.aclose()

    async def _read(self, path: str, params: Any = None, *, raw: bool = False) -> Any:
        """GET, retried on a transient failure; ``None`` for a 404."""
        for attempt in range(_READ_ATTEMPTS):
            last = attempt == _READ_ATTEMPTS - 1
            try:
                response = await self._client.get(path, params=params)
            except httpx.TransportError as exc:
                if last:
                    raise GitLabAPIError(0, f"GitLab unreachable: {exc}") from exc
                await asyncio.sleep(2**attempt)
                continue
            if response.status_code == 404:
                return None
            if response.status_code in _RETRYABLE and not last:
                await asyncio.sleep(2**attempt)
                continue
            if response.is_error:
                raise self._refusal(response)
            return response.text if raw else response.json()
        raise AssertionError("unreachable")  # pragma: no cover

    async def _write(self, method: str, path: str, body: JsonDict) -> JsonDict:
        """POST / PUT, sent once."""
        try:
            response = await self._client.request(method, path, json=body)
        except httpx.TransportError as exc:
            raise GitLabAPIError(0, f"GitLab unreachable: {exc}") from exc
        if response.is_error:
            raise self._refusal(response)
        return cast(JsonDict, response.json()) if response.content else {}

    def _refusal(self, response: httpx.Response) -> GitLabAPIError:
        if response.status_code == 401:
            self.saw_unauthorized = True
        return GitLabAPIError(response.status_code, _reason(response))

    async def token_rejected(self) -> bool:
        """After a 401: does GitLab refuse the token itself (not one action)?"""
        if not self.saw_unauthorized:
            return False
        try:
            await self.current_user()
        except GitLabAPIError as exc:
            return exc.status_code == 401
        return False

    # -- Who the bot is --

    async def current_user(self) -> JsonDict | None:
        return cast(JsonDict | None, await self._read("/user"))

    async def token_info(self) -> JsonDict | None:
        """The token's scopes and expiry (GitLab 15.5+; None where missing)."""
        return cast(JsonDict | None, await self._read("/personal_access_tokens/self"))

    # -- Repository --

    async def project(self, project_id: int) -> JsonDict | None:
        return cast(JsonDict | None, await self._read(f"/projects/{project_id}"))

    async def file_text(self, project_id: int, path: str, ref: str) -> str | None:
        """A file's content at ``ref``, or None when it is not there."""
        return cast(
            str | None,
            await self._read(
                f"/projects/{project_id}/repository/files/{_quote(path)}/raw",
                {"ref": ref},
                raw=True,
            ),
        )

    async def file_revision(self, project_id: int, path: str, ref: str) -> tuple[str, str] | None:
        """A text file at ``ref`` and the last commit that changed it - which a
        later update names, so GitLab refuses it if the file moved meanwhile."""
        data = await self._read(
            f"/projects/{project_id}/repository/files/{_quote(path)}", {"ref": ref}
        )
        if not data:
            return None
        try:
            content = base64.b64decode(data["content"]).decode("utf-8")
        except (KeyError, ValueError):
            return None  # not a text file
        return content, str(data["last_commit_id"])

    async def merge_base(self, project_id: int, first: str, second: str) -> str | None:
        data = await self._read(
            f"/projects/{project_id}/repository/merge_base",
            [("refs[]", first), ("refs[]", second)],
        )
        return str(data["id"]) if data else None

    async def is_ancestor(self, project_id: int, ancestor: str, descendant: str) -> bool:
        """Whether ``ancestor`` is in ``descendant``'s history."""
        return await self.merge_base(project_id, ancestor, descendant) == ancestor

    async def commit(
        self, project_id: int, branch: str, message: str, actions: list[JsonDict]
    ) -> JsonDict:
        """One commit of file actions (create / update) on ``branch``."""
        return await self._write(
            "POST",
            f"/projects/{project_id}/repository/commits",
            {"branch": branch, "commit_message": message, "actions": actions},
        )

    async def comment_on_commit(self, project_id: int, sha: str, note: str) -> JsonDict:
        return await self._write(
            "POST", f"/projects/{project_id}/repository/commits/{sha}/comments", {"note": note}
        )

    # -- Issues --

    async def create_issue(
        self, project_id: int, title: str, description: str, assignee_id: int
    ) -> JsonDict:
        return await self._write(
            "POST",
            f"/projects/{project_id}/issues",
            {"title": title, "description": description, "assignee_ids": [assignee_id]},
        )

    async def find_issue(self, project_id: int, text: str) -> JsonDict | None:
        """The issue whose description contains ``text``."""
        found = await self._read(
            f"/projects/{project_id}/issues", {"search": text, "in": "description"}
        )
        return cast(JsonDict, found[0]) if found else None

    async def issue(self, project_id: int, iid: int) -> JsonDict | None:
        return cast(JsonDict | None, await self._read(f"/projects/{project_id}/issues/{iid}"))

    async def close_issue(self, project_id: int, iid: int) -> JsonDict:
        return await self._write(
            "PUT", f"/projects/{project_id}/issues/{iid}", {"state_event": "close"}
        )

    # -- Merge requests --

    async def merge_request(self, project_id: int, iid: int) -> JsonDict | None:
        """The merge request - once GitLab has decided whether it can merge.

        Right after a push GitLab is still "checking", and ``has_conflicts``
        says nothing yet: a review then would approve a conflict.
        """
        path = f"/projects/{project_id}/merge_requests/{iid}"
        mr = await self._read(path, {"with_merge_status_recheck": "true"})
        for wait in _MERGEABILITY_WAITS:
            if mr is None or mr.get("detailed_merge_status") not in _MERGEABILITY_PENDING:
                break
            await asyncio.sleep(wait)
            mr = await self._read(path)
        return cast(JsonDict | None, mr)

    async def changed_paths(self, project_id: int, iid: int) -> list[str]:
        """Every path the merge request adds, edits, renames or deletes."""
        data = await self._read(f"/projects/{project_id}/merge_requests/{iid}/changes")
        paths: list[str] = []
        for change in (data or {}).get("changes") or []:
            for key in ("old_path", "new_path"):
                path = change.get(key)
                if path and path not in paths:
                    paths.append(path)
        return paths

    async def merge_requests_of_commit(self, project_id: int, sha: str) -> list[JsonDict]:
        """The merge requests a commit belongs to - its own commits, or the
        merge commit GitLab wrote for it."""
        found = await self._read(
            f"/projects/{project_id}/repository/commits/{_quote(sha)}/merge_requests"
        )
        return list(found or [])

    async def open_merge_request_for(self, project_id: int, branch: str) -> JsonDict | None:
        found = await self._read(
            f"/projects/{project_id}/merge_requests",
            {"source_branch": branch, "state": "opened"},
        )
        return cast(JsonDict, found[0]) if found else None

    async def comment_on_merge_request(self, project_id: int, iid: int, body: str) -> JsonDict:
        return await self._write(
            "POST", f"/projects/{project_id}/merge_requests/{iid}/notes", {"body": body}
        )

    async def approve(self, project_id: int, iid: int, sha: str) -> JsonDict:
        return await self._write(
            "POST", f"/projects/{project_id}/merge_requests/{iid}/approve", {"sha": sha}
        )

    async def merge(self, project_id: int, iid: int, sha: str, *, when_pipeline: bool) -> JsonDict:
        return await self._write(
            "PUT",
            f"/projects/{project_id}/merge_requests/{iid}/merge",
            {"sha": sha, "merge_when_pipeline_succeeds": when_pipeline},
        )
