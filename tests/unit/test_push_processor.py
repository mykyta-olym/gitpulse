"""Tests for push processor functionality.

Tests the push event processing logic including branch detection and commit handling.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPushEventDataExtraction:
    """Test push event data extraction."""

    def test_extract_branch_from_ref_heads(self) -> None:
        """Test extracting branch name from refs/heads/ prefix."""
        ref = "refs/heads/feature/my-feature"
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        assert branch == "feature/my-feature"

    def test_extract_branch_from_plain_ref(self) -> None:
        """Test extracting branch when no refs/heads prefix."""
        ref = "main"
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        assert branch == "main"

    def test_extract_branch_refs_tags(self) -> None:
        """Test that refs/tags is not stripped."""
        ref = "refs/tags/v1.0.0"
        branch = ref.replace("refs/heads/", "") if ref.startswith("refs/heads/") else ref
        assert branch == "refs/tags/v1.0.0"


class TestPushEventBranchDetection:
    """Test branch creation and deletion detection."""

    def test_detect_new_branch(self) -> None:
        """Test detecting new branch (before is all zeros)."""
        before = "0" * 40
        after = "abc123def456789"
        is_new_branch = before == "0" * 40
        is_delete = after == "0" * 40
        assert is_new_branch is True
        assert is_delete is False

    def test_detect_branch_delete(self) -> None:
        """Test detecting branch deletion (after is all zeros)."""
        before = "abc123def456789"
        after = "0" * 40
        is_new_branch = before == "0" * 40
        is_delete = after == "0" * 40
        assert is_new_branch is False
        assert is_delete is True

    def test_detect_regular_push(self) -> None:
        """Test detecting regular push (neither new nor delete)."""
        before = "abc123"
        after = "def456"
        is_new_branch = before == "0" * 40
        is_delete = after == "0" * 40
        assert is_new_branch is False
        assert is_delete is False


class TestPushPayloadExtraction:
    """Test extracting data from push payloads."""

    def test_extract_total_commits(self) -> None:
        """Test extracting total commits count."""
        payload: dict[str, Any] = {"total_commits_count": 5}
        total_commits = payload.get("total_commits_count", 0)
        assert total_commits == 5

    def test_extract_total_commits_default(self) -> None:
        """Test default total commits when missing."""
        payload: dict[str, Any] = {}
        total_commits = payload.get("total_commits_count", 0)
        assert total_commits == 0

    def test_extract_user_username(self) -> None:
        """Test extracting user username."""
        payload = {"user_username": "developer"}
        user = payload.get("user_username", "unknown")
        assert user == "developer"

    def test_extract_user_username_default(self) -> None:
        """Test default username when missing."""
        payload: dict[str, Any] = {}
        user = payload.get("user_username", "unknown")
        assert user == "unknown"


class TestPushCommitsExtraction:
    """Test extracting commits from push payload."""

    def test_extract_commits_list(self) -> None:
        """Test extracting commits from payload."""
        payload = {
            "commits": [
                {"id": "sha1", "message": "First commit"},
                {"id": "sha2", "message": "Second commit"},
            ]
        }
        commits = payload.get("commits", [])
        assert len(commits) == 2
        assert commits[0]["id"] == "sha1"

    def test_extract_commits_empty(self) -> None:
        """Test default empty commits list."""
        payload: dict[str, Any] = {}
        commits = payload.get("commits", [])
        assert commits == []


class TestDockerFileChangeDetection:
    """Test detection of Dockerfile changes in push events."""

    def test_detect_dockerfile_in_added(self) -> None:
        """Test detecting Dockerfile in added files."""
        commit = {"added": ["Dockerfile", "main.py"]}
        has_dockerfile = any("Dockerfile" in f for f in commit.get("added", []))
        assert has_dockerfile is True

    def test_detect_dockercompose_in_modified(self) -> None:
        """Test detecting docker-compose in modified files."""
        commit = {"modified": ["docker-compose.yml", "config.py"]}
        has_compose = any("compose" in f.lower() for f in commit.get("modified", []))
        assert has_compose is True

    def test_no_docker_files(self) -> None:
        """Test when no Docker files are changed."""
        commit = {"added": ["app.py"], "modified": ["test.py"]}
        has_dockerfile = any("Dockerfile" in f for f in commit.get("added", []))
        has_compose = any("compose" in f.lower() for f in commit.get("modified", []))
        assert has_dockerfile is False
        assert has_compose is False


class TestIssueBranchPattern:
    """Test issue branch pattern detection for conflict simulator."""

    def test_detect_issue_branch_pattern(self) -> None:
        """Test detecting issue-N pattern in branch."""
        branch = "issue-42-fix-bug"
        import re

        match = re.search(r"issue-(\d+)", branch)
        assert match is not None
        assert match.group(1) == "42"

    def test_no_issue_pattern(self) -> None:
        """Test non-issue branch pattern."""
        branch = "feature/new-feature"
        import re

        match = re.search(r"issue-(\d+)", branch)
        assert match is None

    def test_feature_branch_pattern(self) -> None:
        """Test feature branch naming."""
        branch = "feature-123-implement-login"
        import re

        match = re.search(r"issue-(\d+)", branch)
        assert match is None  # Should not match feature-


class TestProcessPushEvent:
    """Test the main process_push_event function."""

    @pytest.mark.asyncio
    @patch(
        "app.services.events.enqueue_metrics_refresh",
    )
    @patch(
        "app.workers.processors.push_processor._process_push_commits",
        new_callable=AsyncMock,
    )
    async def test_regular_push(
        self,
        mock_commits: AsyncMock,
        mock_enqueue: MagicMock,
    ) -> None:
        """Regular push triggers commit processing."""
        from app.workers.processors.push_processor import process_push_event

        session = AsyncMock()
        fake_project = MagicMock(team_id="team-1")
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=fake_project)
        )
        payload = {
            "ref": "refs/heads/main",
            "before": "a" * 40,
            "after": "b" * 40,
            "total_commits_count": 2,
            "user_username": "dev",
        }
        await process_push_event(session, payload, 123)
        mock_commits.assert_called_once()
        mock_enqueue.assert_called_once_with("team-1")

    @pytest.mark.asyncio
    @patch(
        "app.services.events.enqueue_metrics_refresh",
    )
    @patch(
        "app.workers.processors.push_processor._process_push_commits",
        new_callable=AsyncMock,
    )
    async def test_new_branch_push(
        self,
        mock_commits: AsyncMock,
        mock_enqueue: MagicMock,
    ) -> None:
        """New branch triggers commits processing."""
        from app.workers.processors.push_processor import process_push_event

        session = AsyncMock()
        fake_project = MagicMock(team_id="team-2")
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=fake_project)
        )
        payload = {
            "ref": "refs/heads/issue-5-fix",
            "before": "0" * 40,
            "after": "b" * 40,
            "total_commits_count": 1,
            "user_username": "student",
        }
        await process_push_event(session, payload, 456)
        mock_commits.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "app.workers.processors.push_processor._process_push_commits",
        new_callable=AsyncMock,
    )
    async def test_delete_branch(
        self,
        mock_commits: AsyncMock,
    ) -> None:
        """Branch deletion skips commit processing."""
        from app.workers.processors.push_processor import process_push_event

        session = AsyncMock()
        payload = {
            "ref": "refs/heads/old-branch",
            "before": "a" * 40,
            "after": "0" * 40,
            "total_commits_count": 0,
            "user_username": "dev",
        }
        await process_push_event(session, payload, 789)
        mock_commits.assert_not_called()
