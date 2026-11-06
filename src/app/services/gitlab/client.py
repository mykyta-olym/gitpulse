"""Typed GitLab API v4 client with retries and caching."""

import asyncio
import logging
import time as _time
import urllib.parse
from typing import TYPE_CHECKING, Any, Self, cast

import httpx

from app.observability.metrics import GITLAB_API_DURATION, GITLAB_API_REQUESTS
from app.services.gitlab.client_types import GitLabAPIError, GitLabPaginationTruncatedError
from app.services.gitlab.token_health import mark_ok as _token_ok
from app.services.gitlab.token_health import mark_unauthorized as _token_unauthorized

if TYPE_CHECKING:
    from app.services.gitlab.cache import GitLabAPICache

logger = logging.getLogger(__name__)

__all__ = ["GitLabAPIError", "GitLabClient", "GitLabPaginationTruncatedError"]

# Status codes that warrant a retry
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
JsonDict = dict[str, Any]


class GitLabClient:
    """Async GitLab API v4 client with retry logic and caching."""

    def __init__(
        self,
        base_url: str,
        private_token: str,
        timeout: int = 30,
        max_retries: int = 3,
        cache: "GitLabAPICache | None" = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v4"
        self.max_retries = max_retries
        self._cache = cache
        self._client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={
                "PRIVATE-TOKEN": private_token,
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(timeout=timeout, connect=5.0),
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Any:
        """Make an API request with retry, backoff, and optional caching."""
        last_error: Exception | None = None
        endpoint_label = path.split("?")[0][:60]  # cap cardinality

        # Check cache for GET requests
        cached_response = None
        etag = None
        if method == "GET" and use_cache and self._cache:
            cached_response, etag = await self._cache.get_cached_response(path, params)
            if cached_response is not None and etag is None:
                # Have cached data without ETag, return immediately
                return cached_response

        for attempt in range(self.max_retries + 1):
            try:
                # Add ETag header for conditional request
                headers = {}
                if etag:
                    headers["If-None-Match"] = etag

                t0 = _time.monotonic()
                response = await self._client.request(
                    method, path, params=params, json=json_body, headers=headers
                )
                GITLAB_API_DURATION.labels(endpoint=endpoint_label).observe(_time.monotonic() - t0)
                GITLAB_API_REQUESTS.labels(
                    endpoint=endpoint_label, status=str(response.status_code)
                ).inc()

                # Handle 304 Not Modified
                if response.status_code == 304 and cached_response is not None:
                    # A 304 means the token was accepted - clear any stale poison.
                    _token_ok()
                    return cached_response

                if response.status_code == 404:
                    return None

                if response.status_code == 429:
                    # Rate limited - read Retry-After header
                    try:
                        retry_after = int(response.headers.get("Retry-After", "60"))
                    except (ValueError, TypeError):
                        retry_after = 60
                    logger.warning(
                        "GitLab API rate limited, waiting %ds (attempt %d/%d)",
                        retry_after,
                        attempt + 1,
                        self.max_retries + 1,
                    )
                    if attempt >= self.max_retries:
                        # Do NOT return None - callers treat None as "not found"
                        # which would silently drop rate-limited results and
                        # mark sync jobs as successful with missing data.
                        raise GitLabAPIError(
                            429,
                            f"rate limited after {self.max_retries + 1} attempts "
                            f"(Retry-After={retry_after}s)",
                        )
                    await asyncio.sleep(retry_after)
                    continue

                if response.status_code in RETRYABLE_STATUS_CODES:
                    wait = 2**attempt  # 1, 2, 4 seconds
                    logger.warning(
                        "GitLab API returned %d, retrying in %.1fs (attempt %d/%d)",
                        response.status_code,
                        wait,
                        attempt + 1,
                        self.max_retries + 1,
                    )
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
                # Reached here => 2xx: the token is currently accepted. Clear
                # any stale "unauthorized" poison so work resumes automatically
                # after a token rotation without a restart.
                _token_ok()
                if response.status_code == 204 or not response.content:
                    return None
                data = response.json()

                # Cache successful GET responses
                if method == "GET" and use_cache and self._cache:
                    response_etag = response.headers.get("ETag")
                    await self._cache.store_response(path, params, data, response_etag)

                return data

            except httpx.TimeoutException as exc:
                last_error = exc
                wait = 2**attempt
                logger.warning(
                    "GitLab API timeout, retrying in %.1fs (attempt %d/%d)",
                    wait,
                    attempt + 1,
                    self.max_retries + 1,
                )
                await asyncio.sleep(wait)
            except httpx.HTTPStatusError as exc:
                # 401/403 => the token is dead. Poison the shared flag so every
                # other entrypoint and background job short-circuits instead of
                # each independently hammering GitLab and spawning retry storms.
                if exc.response.status_code in (401, 403):
                    _token_unauthorized()
                raise GitLabAPIError(exc.response.status_code, str(exc)) from exc

        raise GitLabAPIError(0, f"Max retries exceeded: {last_error}")

    # Analytics reads only; the classroom assistant has a separate write client.
    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        per_page: int = 100,
        max_pages: int = 100,
        missing_is_error: bool = False,
    ) -> list[JsonDict]:
        """Fetch all pages of a paginated endpoint.

        ``max_pages`` caps the number of pages fetched to prevent unbounded
        memory growth and API quota exhaustion for unexpectedly large results.
        """
        all_items: list[JsonDict] = []
        page = 1
        p = dict(params or {})
        p["per_page"] = per_page

        while page <= max_pages:
            p["page"] = page
            items = cast(list[JsonDict] | None, await self._get(path, params=p))
            if items is None and missing_is_error:
                raise GitLabAPIError(404, f"GitLab list is unavailable: {path}")
            if items is None or not items:
                # No (more) data - return whatever we have so far. An
                # empty first page is a legitimate "this project has
                # zero items" answer, NOT a pagination truncation.
                return all_items
            all_items.extend(items)
            if len(items) < per_page:
                # Last page was partial - we have everything.
                return all_items
            page += 1

        # Reached here only if every one of ``max_pages`` pages was FULL
        # (len == per_page), meaning GitLab almost certainly has more
        # data we did not fetch.  Silent truncation would mark a sync
        # as successful with missing data - raise instead so the
        # per-project try/except fails that one project loudly and the
        # sweep can retry later.
        logger.error(
            "gitlab_pagination_truncated",
            extra={
                "path": path,
                "max_pages": max_pages,
                "per_page": per_page,
                "items_fetched": len(all_items),
            },
        )
        raise GitLabPaginationTruncatedError(
            path=path,
            items_fetched=len(all_items),
            max_pages=max_pages,
            per_page=per_page,
        )

    async def _get_dict(self, path: str, params: dict[str, Any] | None = None) -> JsonDict | None:
        return cast(JsonDict | None, await self._get(path, params=params))

    async def _get_list(self, path: str, params: dict[str, Any] | None = None) -> list[JsonDict]:
        return await self._get_paginated(path, params=params)

    # -- Groups --

    async def get_group(self, group_id_or_path: int | str) -> JsonDict | None:
        """Fetch a GitLab group by numeric ID or full path."""

        if isinstance(group_id_or_path, int):
            return await self._get_dict(f"/groups/{group_id_or_path}")
        encoded = urllib.parse.quote(group_id_or_path, safe="")
        return await self._get_dict(f"/groups/{encoded}")

    async def get_group_subgroups(self, group_id: int) -> list[JsonDict]:
        """List direct subgroups for a group."""
        return await self._get_list(f"/groups/{group_id}/subgroups")

    async def get_group_projects(
        self,
        group_id: int,
        include_subgroups: bool = True,
        include_archived: bool = False,
    ) -> list[JsonDict]:
        """List projects in a group, optionally including subgroup projects."""
        return await self._get_list(
            f"/groups/{group_id}/projects",
            params={
                "include_subgroups": include_subgroups,
                "archived": include_archived,
                "simple": True,
            },
        )

    async def get_group_members(
        self,
        group_id: int,
        include_inherited: bool = True,
    ) -> list[JsonDict]:
        """List group members.

        include_inherited=True uses `/members/all`, otherwise `/members` (direct members only).
        """
        endpoint = (
            f"/groups/{group_id}/members/all"
            if include_inherited
            else f"/groups/{group_id}/members"
        )
        return await self._get_list(endpoint)

    # -- Projects --

    async def get_project(self, project_id: int) -> JsonDict | None:
        return await self._get_dict(f"/projects/{project_id}")

    async def get_project_by_path(self, project_path: str) -> JsonDict | None:
        """Fetch a GitLab project by its full path (e.g., 'namespace/project')."""

        encoded = urllib.parse.quote(project_path, safe="")
        return await self._get_dict(f"/projects/{encoded}")

    async def get_project_members(
        self,
        project_id: int,
        include_inherited: bool = True,
    ) -> list[JsonDict]:
        """List project members.

        include_inherited=True uses `/members/all`, otherwise `/members`.
        """
        endpoint = (
            f"/projects/{project_id}/members/all"
            if include_inherited
            else f"/projects/{project_id}/members"
        )
        return await self._get_list(endpoint)

    # -- Issues --

    async def get_project_issues(
        self,
        project_id: int,
        state: str = "all",
        updated_after: str | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {"state": state}
        if updated_after:
            params["updated_after"] = updated_after
        return await self._get_list(f"/projects/{project_id}/issues", params=params)

    async def get_issue_notes(self, project_id: int, issue_iid: int) -> list[JsonDict]:
        return await self._get_list(
            f"/projects/{project_id}/issues/{issue_iid}/notes",
            params={"sort": "asc", "order_by": "created_at"},
        )

    async def get_issue(self, project_id: int, issue_iid: int) -> JsonDict | None:
        return await self._get_dict(f"/projects/{project_id}/issues/{issue_iid}")

    # -- Merge Requests --

    async def get_project_merge_requests(
        self,
        project_id: int,
        state: str = "all",
        updated_after: str | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {"state": state}
        if updated_after:
            params["updated_after"] = updated_after
        return await self._get_list(f"/projects/{project_id}/merge_requests", params=params)

    async def get_merge_request(self, project_id: int, mr_iid: int) -> JsonDict | None:
        return await self._get_dict(f"/projects/{project_id}/merge_requests/{mr_iid}")

    async def get_mr_commits(self, project_id: int, mr_iid: int) -> list[JsonDict]:
        """Get commits belonging to an MR via the MR commits endpoint.

        This endpoint works even after the source branch is deleted, making it
        more reliable than fetching the source branch ref directly.
        """
        return await self._get_paginated(
            f"/projects/{project_id}/merge_requests/{mr_iid}/commits", missing_is_error=True
        )

    async def get_mr_changes(self, project_id: int, mr_iid: int) -> JsonDict | None:
        """Get MR diff metadata (file list, not content)."""
        return await self._get_dict(f"/projects/{project_id}/merge_requests/{mr_iid}/changes")

    async def get_mr_approvals(self, project_id: int, mr_iid: int) -> JsonDict | None:
        """Get MR approval state. May fail on CE without approvals feature."""
        try:
            return await self._get_dict(f"/projects/{project_id}/merge_requests/{mr_iid}/approvals")
        except GitLabAPIError as exc:
            if exc.status_code in (403, 404):
                logger.info(
                    "Approvals API not available for project %d MR %d (CE?)",
                    project_id,
                    mr_iid,
                )
                return None
            raise

    # -- Notes --

    async def get_mr_notes(self, project_id: int, mr_iid: int) -> list[JsonDict]:
        return await self._get_list(
            f"/projects/{project_id}/merge_requests/{mr_iid}/notes",
            params={"sort": "asc", "order_by": "created_at"},
        )

    # -- Pipelines --

    async def get_project_pipelines(
        self,
        project_id: int,
        ref: str | None = None,
        updated_after: str | None = None,
    ) -> list[JsonDict]:
        params: dict[str, Any] = {}
        if ref:
            params["ref"] = ref
        if updated_after:
            params["updated_after"] = updated_after
        return await self._get_list(f"/projects/{project_id}/pipelines", params=params)

    async def get_pipeline(self, project_id: int, pipeline_id: int) -> JsonDict | None:
        return await self._get_dict(f"/projects/{project_id}/pipelines/{pipeline_id}")

    async def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> list[JsonDict]:
        return await self._get_list(f"/projects/{project_id}/pipelines/{pipeline_id}/jobs")

    # -- Commits --

    async def get_commits(
        self,
        project_id: int,
        ref_name: str | None = None,
        since: str | None = None,
        until: str | None = None,
        per_page: int = 100,
        all_pages: bool = True,
    ) -> list[JsonDict]:
        """Get commits from a project.

        Args:
            project_id: GitLab project ID
            ref_name: Branch or tag name (optional, defaults to default branch)
            since: ISO 8601 date string for commits after this date
            until: ISO 8601 date string for commits before this date
            per_page: Number of commits per page
            all_pages: Whether to fetch all pages
        """
        params: dict[str, str | int] = {"per_page": per_page}
        if ref_name:
            params["ref_name"] = ref_name
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        if all_pages:
            return await self._get_list(f"/projects/{project_id}/repository/commits", params=params)

        # Single page only
        endpoint = f"/projects/{project_id}/repository/commits"
        data = await self._request("GET", endpoint, params=params)
        if isinstance(data, list):
            return data
        return []

    async def get_commit(self, project_id: int, sha: str) -> JsonDict | None:
        """Get a single commit with stats."""
        endpoint = f"/projects/{project_id}/repository/commits/{sha}"
        return await self._get_dict(endpoint, params={"stats": "true"})

    async def repository_exists(self, project_id: int) -> bool:
        """Return True if the project's git repository actually exists.

        The project object reports ``empty_repo: true`` for BOTH a fresh
        initialised-but-empty repo (awaiting the first push) and a project whose
        repository does not exist at all ("The repository for this project does
        not exist"). They are indistinguishable on the project payload, but the
        branches endpoint tells them apart: an empty-but-initialised repo returns
        ``200 []`` while a non-existent repo returns ``404`` (``_request`` maps
        that to ``None``). Use this to deactivate genuinely-missing repos without
        punishing teams that simply have not pushed yet.
        """
        endpoint = f"/projects/{project_id}/repository/branches"
        data = await self._request("GET", endpoint, params={"per_page": 1})
        return data is not None

    # -- Users --

    async def get_user(self, user_id: int) -> JsonDict | None:
        return await self._get_dict(f"/users/{user_id}")

    async def search_users(self, username: str) -> list[JsonDict]:
        """Search users by username."""
        return await self._get_list("/users", params={"username": username})

    # -- Project Hooks --

    # -- Branches (write) --

    # -- Files (write) --

    # -- Merge Requests (write) --

    # -- Notes (write) --

    # -- Protected branches --

    async def get_protected_branches(self, project_id: int) -> list[JsonDict]:
        """List protected branches for a project."""
        return await self._get_list(f"/projects/{project_id}/protected_branches")

    # -- Repository contributors --

    async def get_contributors(self, project_id: int, *, ref: str | None = None) -> list[JsonDict]:
        """List repository contributors with commit counts."""
        params: dict[str, Any] = {}
        if ref:
            params["ref"] = ref
        return await self._get_list(
            f"/projects/{project_id}/repository/contributors",
            params=params or None,
        )

    # -- Project statistics --

    async def get_project_statistics(self, project_id: int) -> JsonDict | None:
        """Get project with statistics (repo size, commit count, etc)."""
        return await self._get_dict(
            f"/projects/{project_id}",
            params={"statistics": "true"},
        )

    # -- Milestones --

    async def get_project_milestones(self, project_id: int, state: str = "all") -> list[JsonDict]:
        """List project milestones."""
        return await self._get_list(
            f"/projects/{project_id}/milestones",
            params={"state": state},
        )

    # -- Releases --

    async def get_project_releases(self, project_id: int) -> list[JsonDict]:
        """List project releases (tags with release notes)."""
        return await self._get_list(f"/projects/{project_id}/releases")

    # -- Labels --

    async def get_project_labels(self, project_id: int) -> list[JsonDict]:
        """List project labels."""
        return await self._get_list(f"/projects/{project_id}/labels")

    # -- CI Lint --
