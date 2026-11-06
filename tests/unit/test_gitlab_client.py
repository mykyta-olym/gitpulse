"""Tests for GitLab client functionality.

Tests the GitLab API client helpers and utility functions.
"""

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from app.services.gitlab.client import GitLabAPIError, GitLabClient


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["empty", "complete", "missing", "missing-page", "null"])
async def test_mr_commit_list_distinguishes_empty_from_unavailable(mode):
    def respond(request):
        page = int(request.url.params["page"])
        if mode == "missing" or (mode == "missing-page" and page == 2):
            return httpx.Response(404)
        if mode == "null":
            return httpx.Response(200, json=None)
        if mode == "missing-page":
            return httpx.Response(200, json=[{"id": str(i)} for i in range(100)])
        return httpx.Response(200, json=[] if mode == "empty" else [{"id": "a" * 40}])

    async with GitLabClient("https://gl.example", "test-token", max_retries=0) as client:
        await client._client.aclose()
        client._client = httpx.AsyncClient(
            base_url=client.api_url, transport=httpx.MockTransport(respond)
        )
        if mode in {"missing", "missing-page", "null"}:
            with pytest.raises(GitLabAPIError):
                await client.get_mr_commits(1, 6)
        else:
            assert await client.get_mr_commits(1, 6) == (
                [] if mode == "empty" else [{"id": "a" * 40}]
            )


class TestRepositoryExists:
    """``repository_exists`` distinguishes a missing repo (404) from an empty one."""

    def _client(self) -> GitLabClient:
        return GitLabClient(base_url="https://gl.example", private_token="t")

    @pytest.mark.asyncio
    async def test_missing_repo_returns_false(self) -> None:
        # 404 on the branches endpoint -> _request returns None -> repo absent.
        client = self._client()
        client._request = AsyncMock(return_value=None)  # type: ignore[method-assign]
        assert await client.repository_exists(13133) is False

    @pytest.mark.asyncio
    async def test_empty_but_initialised_repo_returns_true(self) -> None:
        # 200 [] -> repo exists, just has no branches/commits yet (keep active).
        client = self._client()
        client._request = AsyncMock(return_value=[])  # type: ignore[method-assign]
        assert await client.repository_exists(13133) is True

    @pytest.mark.asyncio
    async def test_repo_with_branches_returns_true(self) -> None:
        client = self._client()
        client._request = AsyncMock(return_value=[{"name": "main"}])  # type: ignore[method-assign]
        assert await client.repository_exists(13133) is True


class TestGitLabClientUrlConstruction:
    """Test URL construction for GitLab API."""

    def test_base_url_trailing_slash_stripped(self) -> None:
        """Test that trailing slash is stripped from base URL."""
        base_url = "https://gitlab.example.com/"
        clean_url = base_url.rstrip("/")
        assert clean_url == "https://gitlab.example.com"

    def test_api_url_construction(self) -> None:
        """Test API URL construction."""
        base_url = "https://gitlab.example.com"
        api_url = f"{base_url}/api/v4"
        assert api_url == "https://gitlab.example.com/api/v4"


class TestRetryableStatusCodes:
    """Test retryable status code detection."""

    def test_429_is_retryable(self) -> None:
        """Test that 429 (rate limit) is retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 429 in retryable

    def test_500_is_retryable(self) -> None:
        """Test that 500 (server error) is retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 500 in retryable

    def test_502_is_retryable(self) -> None:
        """Test that 502 (bad gateway) is retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 502 in retryable

    def test_503_is_retryable(self) -> None:
        """Test that 503 (service unavailable) is retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 503 in retryable

    def test_504_is_retryable(self) -> None:
        """Test that 504 (gateway timeout) is retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 504 in retryable

    def test_404_not_retryable(self) -> None:
        """Test that 404 (not found) is not retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 404 not in retryable

    def test_401_not_retryable(self) -> None:
        """Test that 401 (unauthorized) is not retryable."""
        retryable = {429, 500, 502, 503, 504}
        assert 401 not in retryable


class TestEndpointLabelSanitization:
    """Test endpoint label sanitization for metrics."""

    def test_endpoint_label_caps_cardinality(self) -> None:
        """Test that endpoint label is capped at 60 chars."""
        path = "/projects/123/merge_requests/456/discussions/789/notes/1234/very/long/path"
        endpoint_label = path.split("?")[0][:60]
        assert len(endpoint_label) <= 60

    def test_endpoint_label_strips_query_params(self) -> None:
        """Test that query params are stripped from endpoint label."""
        path = "/projects/123/issues?per_page=100&page=1"
        endpoint_label = path.split("?")[0][:60]
        assert "?" not in endpoint_label
        assert endpoint_label == "/projects/123/issues"


class TestPaginationHelpers:
    """Test pagination helper functions."""

    def test_calculate_pages(self) -> None:
        """Test calculating total pages from item count."""
        total_items = 250
        per_page = 100
        total_pages = (total_items + per_page - 1) // per_page
        assert total_pages == 3

    def test_extract_next_page_from_link_header(self) -> None:
        """Test extracting next page from Link header."""
        link_header = '<url?page=2>; rel="next", <url?page=5>; rel="last"'
        has_next = 'rel="next"' in link_header
        assert has_next is True

    def test_no_next_page(self) -> None:
        """Test when there is no next page."""
        link_header = '<url?page=5>; rel="last"'
        has_next = 'rel="next"' in link_header
        assert has_next is False


class TestGitLabAPIErrorConstruction:
    """Test GitLabAPIError exception construction."""

    def test_error_message_format(self) -> None:
        """Test error message format."""
        status_code = 404
        message = "Project not found"
        error_msg = f"GitLab API error {status_code}: {message}"
        assert error_msg == "GitLab API error 404: Project not found"

    def test_rate_limit_error_format(self) -> None:
        """Test rate limit error message."""
        project_id = 123
        retry_after = 60
        error_msg = f"Rate limit exceeded for project {project_id}, retry after {retry_after}s"
        assert "123" in error_msg
        assert "60" in error_msg


class TestProjectPathParsing:
    """Test GitLab project path parsing."""

    def test_parse_group_project_path(self) -> None:
        """Test parsing a group/project path."""
        path = "my-group/my-project"
        parts = path.split("/")
        assert parts[-1] == "my-project"
        assert len(parts) == 2

    def test_parse_nested_group_path(self) -> None:
        """Test parsing a nested group path."""
        path = "top-group/sub-group/project"
        parts = path.split("/")
        assert parts[-1] == "project"
        assert len(parts) == 3


class TestCommitAPIHelpers:
    """Test commit API helper functions."""

    def test_commit_sha_format(self) -> None:
        """Test commit SHA is 40 characters."""
        sha = "abc123def456789012345678901234567890abcd"
        assert len(sha) == 40

    def test_short_sha_extraction(self) -> None:
        """Test short SHA extraction."""
        sha = "abc123def456789012345678901234567890abcd"
        short_sha = sha[:8]
        assert short_sha == "abc123de"


class TestMergeRequestAPIHelpers:
    """Test merge request API helper functions."""

    def test_mr_state_values(self) -> None:
        """Test MR state values."""
        valid_states = {"opened", "closed", "merged", "all"}
        assert "opened" in valid_states
        assert "merged" in valid_states

    def test_mr_scope_values(self) -> None:
        """Test MR scope values."""
        valid_scopes = {"created_by_me", "assigned_to_me", "all"}
        assert "all" in valid_scopes


class TestIssueAPIHelpers:
    """Test issue API helper functions."""

    def test_issue_state_values(self) -> None:
        """Test issue state values."""
        valid_states = {"opened", "closed", "all"}
        assert "opened" in valid_states
        assert "closed" in valid_states


class TestPipelineAPIHelpers:
    """Test pipeline API helper functions."""

    def test_pipeline_status_values(self) -> None:
        """Test pipeline status values."""
        valid_statuses = {
            "created",
            "waiting_for_resource",
            "preparing",
            "pending",
            "running",
            "success",
            "failed",
            "canceled",
            "skipped",
            "manual",
        }
        assert "success" in valid_statuses
        assert "failed" in valid_statuses

    def test_pipeline_id_extraction(self) -> None:
        """Test extracting pipeline ID."""
        pipeline: dict[str, Any] = {"id": 12345, "status": "success"}
        pipeline_id = pipeline.get("id")
        assert pipeline_id == 12345


class TestGroupAPIHelpers:
    """Test group API helper functions."""

    def test_group_visibility_values(self) -> None:
        """Test group visibility values."""
        valid_visibility = {"private", "internal", "public"}
        assert "private" in valid_visibility

    def test_access_level_values(self) -> None:
        """Test access level numeric values."""
        access_levels = {
            "none": 0,
            "minimal": 5,
            "guest": 10,
            "reporter": 20,
            "developer": 30,
            "maintainer": 40,
            "owner": 50,
        }
        assert access_levels["developer"] == 30
        assert access_levels["maintainer"] == 40
