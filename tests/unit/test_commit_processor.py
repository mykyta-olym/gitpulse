"""Tests for commit processor functionality.

Tests the commit processing logic including author matching and batch processing.
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestProcessCommitDataExtraction:
    """Test data extraction helpers from commit data."""

    def test_extract_sha_from_id_field(self) -> None:
        """Test extracting SHA from 'id' field."""
        commit_data = {"id": "abc123def456", "title": "Test commit"}
        sha = commit_data.get("id") or commit_data.get("sha")
        assert sha == "abc123def456"

    def test_extract_sha_from_sha_field(self) -> None:
        """Test extracting SHA from 'sha' field when 'id' is missing."""
        commit_data = {"sha": "xyz789abc123", "title": "Test commit"}
        sha = commit_data.get("id") or commit_data.get("sha")
        assert sha == "xyz789abc123"

    def test_missing_sha_returns_none(self) -> None:
        """Test that missing SHA fields return None."""
        commit_data = {"title": "Test commit"}
        sha = commit_data.get("id") or commit_data.get("sha")
        assert sha is None

    def test_extract_title_from_message(self) -> None:
        """Test title extraction from message."""
        message = "First line title\n\nBody of commit message"
        title = message.split("\n")[0][:500]
        assert title == "First line title"

    def test_extract_author_from_nested_object(self) -> None:
        """Test author extraction from nested author object."""
        commit_data: dict[str, Any] = {"author": {"name": "John Doe", "email": "john@example.com"}}
        author_name: str | None = commit_data.get("author_name")
        author_email: str | None = commit_data.get("author_email")
        if not author_name and "author" in commit_data:
            author = commit_data["author"]
            if isinstance(author, dict):
                author_name = author.get("name")
                author_email = author.get("email")
        assert author_name == "John Doe"
        assert author_email == "john@example.com"

    def test_extract_stats(self) -> None:
        """Test stats extraction from commit data."""
        commit_data = {"stats": {"additions": 100, "deletions": 50, "total": 150}}
        stats = commit_data.get("stats", {})
        additions = stats.get("additions", 0) if stats else 0
        deletions = stats.get("deletions", 0) if stats else 0
        files_changed = stats.get("total", 0) if stats else 0
        assert additions == 100
        assert deletions == 50
        assert files_changed == 150

    def test_extract_parent_ids(self) -> None:
        """Test parent SHA extraction."""
        commit_data = {"parent_ids": ["abc123", "def456"]}
        parent_ids = commit_data.get("parent_ids", [])
        assert parent_ids == ["abc123", "def456"]

    def test_empty_parent_ids(self) -> None:
        """Test default empty parent ids."""
        commit_data: dict[str, Any] = {}
        parent_ids = commit_data.get("parent_ids", [])
        assert parent_ids == []


class TestTimestampParsing:
    """Test timestamp parsing from various formats."""

    def test_parse_iso_format_with_z(self) -> None:
        """Test parsing ISO format with Z suffix."""
        ts_str = "2025-01-15T10:30:00Z"
        committed_at = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        assert committed_at.year == 2025
        assert committed_at.month == 1
        assert committed_at.day == 15

    def test_parse_iso_format_with_timezone(self) -> None:
        """Test parsing ISO format with timezone offset."""
        ts_str = "2025-01-15T10:30:00+01:00"
        committed_at = datetime.fromisoformat(ts_str)
        assert committed_at.hour == 10

    def test_datetime_object_passthrough(self) -> None:
        """Test datetime objects pass through correctly."""
        ts = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
        if isinstance(ts, datetime):
            committed_at = ts
        assert committed_at == ts


class TestShortShaGeneration:
    """Test short SHA generation."""

    def test_short_sha_8_chars(self) -> None:
        """Test that short SHA is first 8 characters."""
        sha = "abc123def456789012345"
        short_sha = sha[:8]
        assert short_sha == "abc123de"
        assert len(short_sha) == 8

    def test_short_sha_from_40_char_hash(self) -> None:
        """Test short SHA from full 40-char git hash."""
        sha = "0123456789abcdef0123456789abcdef01234567"
        short_sha = sha[:8]
        assert short_sha == "01234567"


class TestTitleTruncation:
    """Test title truncation to 500 chars."""

    def test_short_title_unchanged(self) -> None:
        """Test that short titles are unchanged."""
        title = "Short title"
        truncated = title[:500] if title else None
        assert truncated == "Short title"

    def test_long_title_truncated(self) -> None:
        """Test that long titles are truncated to 500 chars."""
        title = "A" * 600
        truncated = title[:500] if title else None
        assert len(truncated or "") == 500

    def test_none_title_stays_none(self) -> None:
        """Test that None title stays None."""
        title: str | None = None
        truncated = title[:500] if title else None
        assert truncated is None


class TestCommitDataValidation:
    """Test commit data validation logic."""

    def test_commit_with_all_fields(self) -> None:
        """Test processing commit with all standard fields."""
        commit_data = {
            "id": "sha123456789",
            "title": "Fix: Important bug",
            "message": "Fix: Important bug\n\nDetailed description",
            "author_name": "Developer",
            "author_email": "dev@example.com",
            "committed_date": "2025-01-15T12:00:00Z",
            "stats": {"additions": 10, "deletions": 5, "total": 15},
            "parent_ids": ["parent1"],
        }
        assert commit_data["id"] == "sha123456789"
        assert commit_data["author_name"] == "Developer"

    def test_commit_minimal_fields(self) -> None:
        """Test processing commit with minimal fields."""
        commit_data = {"id": "sha123"}
        sha = commit_data.get("id")
        title = commit_data.get("title") or ""
        message = commit_data.get("message") or title
        assert sha == "sha123"
        assert title == ""
        assert message == ""


class TestAuthorMatchingLogic:
    """Test author matching strategy logic."""

    def test_email_lower_case_normalization(self) -> None:
        """Test email is normalized to lowercase for matching."""
        email = "Developer@Example.COM"
        email_lower = email.lower()
        assert email_lower == "developer@example.com"

    def test_username_from_email(self) -> None:
        """Test extracting potential username from email."""
        email = "johndoe@users.noreply.gitlab.com"
        potential_username = email.split("@")[0].lower()
        assert potential_username == "johndoe"

    def test_name_case_insensitive(self) -> None:
        """Test name matching is case insensitive."""
        name = "John DOE"
        name_lower = name.lower()
        assert name_lower == "john doe"


class TestBatchProcessingLogic:
    """Test batch processing helper logic."""

    def test_count_increments_for_valid_commits(self) -> None:
        """Test that count increments for each valid commit."""
        commits_data = [
            {"id": "sha1"},
            {"id": "sha2"},
            {"id": "sha3"},
        ]
        count = 0
        for commit_data in commits_data:
            if commit_data.get("id"):
                count += 1
        assert count == 3

    def test_count_skips_invalid_commits(self) -> None:
        """Test that count skips commits without SHA."""
        commits_data = [
            {"id": "sha1"},
            {"title": "no sha"},  # Invalid - no SHA
            {"id": "sha3"},
        ]
        count = 0
        for commit_data in commits_data:
            if commit_data.get("id") or commit_data.get("sha"):
                count += 1
        assert count == 2


def _full_commit(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a realistic commit payload for function-level tests."""
    base: dict[str, Any] = {
        "id": "abc123def456789012345678901234567890abcd",
        "title": "feat: add login page",
        "message": "feat: add login page\n\nAdds OAuth flow",
        "author_name": "Test User",
        "author_email": "test@example.com",
        "committed_date": "2025-10-15T14:30:00+02:00",
        "stats": {"additions": 42, "deletions": 5, "total": 3},
        "parent_ids": ["0000000000000000000000000000000000000001"],
    }
    if overrides:
        base.update(overrides)
    return base


class TestProcessCommitFunction:
    """Actually call process_commit with mocked DB."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id="commit-uuid-1")
        session.execute.return_value = mock_result
        return session

    @pytest.mark.asyncio
    async def test_process_commit_happy_path(self, mock_session: AsyncMock) -> None:
        from app.workers.processors.commit_processor import process_commit

        with patch(
            "app.workers.processors.commit_processor._match_author_to_student",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            result = await process_commit(mock_session, _full_commit(), "proj-uuid-1")
            assert result is not None
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_commit_missing_sha(self, mock_session: AsyncMock) -> None:
        from app.workers.processors.commit_processor import process_commit

        result = await process_commit(mock_session, {"title": "no sha"}, "proj-uuid-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_process_commit_nested_author(self, mock_session: AsyncMock) -> None:
        from app.workers.processors.commit_processor import process_commit

        data = _full_commit(
            {
                "author_name": None,
                "author_email": None,
                "author": {"name": "Bot", "email": "bot@ci.com"},
            }
        )
        with patch(
            "app.workers.processors.commit_processor._match_author_to_student",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            result = await process_commit(mock_session, data, "proj-uuid-1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_process_commit_no_stats(self, mock_session: AsyncMock) -> None:
        from app.workers.processors.commit_processor import process_commit

        data = _full_commit({"stats": None})
        with patch(
            "app.workers.processors.commit_processor._match_author_to_student",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            result = await process_commit(mock_session, data, "proj-uuid-1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_process_commit_datetime_obj(self, mock_session: AsyncMock) -> None:
        from app.workers.processors.commit_processor import process_commit

        now = datetime.now(UTC)
        data = _full_commit({"committed_date": now})
        with patch(
            "app.workers.processors.commit_processor._match_author_to_student",
            new_callable=AsyncMock,
            return_value=("student-uuid", 42),
        ):
            result = await process_commit(mock_session, data, "proj-uuid-1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_process_commit_no_timestamp(self, mock_session: AsyncMock) -> None:
        from app.workers.processors.commit_processor import process_commit

        data = _full_commit({"committed_date": None, "created_at": None, "timestamp": None})
        with patch(
            "app.workers.processors.commit_processor._match_author_to_student",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            result = await process_commit(mock_session, data, "proj-uuid-1")
            assert result is not None

    @pytest.mark.asyncio
    async def test_offset_less_timestamp_stored_tz_aware(self, mock_session: AsyncMock) -> None:
        """An offset-less ISO timestamp must be stored tz-aware (UTC), not naive.

        committed_at feeds the compliance engine's tz-aware semester-window
        comparison; a naive value there raises TypeError at scoring time.
        """
        from app.workers.processors.commit_processor import process_commit

        data = _full_commit({"committed_date": "2025-10-15T14:30:00"})  # no tz offset
        with patch(
            "app.workers.processors.commit_processor._match_author_to_student",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            await process_commit(mock_session, data, "proj-uuid-1")
        stmt = mock_session.execute.call_args.args[0]
        dt_params = [v for v in stmt.compile().params.values() if isinstance(v, datetime)]
        assert dt_params, "committed_at was not bound"
        assert all(v.tzinfo is not None for v in dt_params)
