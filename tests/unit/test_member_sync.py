"""Unit tests for member_sync - membership detection logic.

Tests the parsing, teacher detection, and sync result tracking
without requiring a real database or GitLab instance.
"""

import pytest

from app.compliance.roles import access_role_name as _access_role_name
from app.services.member_sync import (
    _parse_gitlab_member,
)
from app.services.member_sync_types import MemberSyncResult


class TestAccessRoleName:
    """Map numeric GitLab access levels to human-readable names."""

    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            (50, "owner"),
            (40, "maintainer"),
            (30, "developer"),
            (20, "reporter"),
            (10, "guest"),
            (5, "none"),
            (0, "none"),
        ],
    )
    def test_maps_levels(self, level: int, expected: str) -> None:
        assert _access_role_name(level) == expected


class TestParseGitlabMember:
    """Parse raw GitLab API member dicts into structured objects."""

    def test_valid_member(self) -> None:
        raw = {
            "id": 123,
            "username": "Alice",
            "name": "Alice Smith",
            "email": "alice@example.com",
            "access_level": 30,
        }
        result = _parse_gitlab_member(raw, source="direct")
        assert result is not None
        assert result.gitlab_user_id == 123
        assert result.username == "alice"  # lowercased
        assert result.full_name == "Alice Smith"
        assert result.email == "alice@example.com"
        assert result.access_level == 30
        assert result.access_role == "developer"
        assert result.source == "direct"

    def test_inherited_source(self) -> None:
        raw = {"id": 456, "username": "bob", "access_level": 40}
        result = _parse_gitlab_member(raw, source="inherited")
        assert result is not None
        assert result.source == "inherited"
        assert result.access_role == "maintainer"

    def test_missing_user_id_returns_none(self) -> None:
        assert _parse_gitlab_member({"username": "x", "access_level": 10}) is None

    def test_zero_user_id_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": 0, "username": "x", "access_level": 10}) is None

    def test_negative_user_id_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": -1, "username": "x", "access_level": 10}) is None

    def test_missing_username_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": 1, "access_level": 10}) is None

    def test_empty_username_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": 1, "username": "  ", "access_level": 10}) is None

    def test_zero_access_level_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": 1, "username": "x", "access_level": 0}) is None

    def test_negative_access_level_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": 1, "username": "x", "access_level": -5}) is None

    def test_missing_access_level_returns_none(self) -> None:
        assert _parse_gitlab_member({"id": 1, "username": "x"}) is None

    def test_none_email_and_name_become_none(self) -> None:
        raw = {"id": 1, "username": "x", "access_level": 10, "email": None, "name": None}
        result = _parse_gitlab_member(raw)
        assert result is not None
        assert result.full_name is None
        assert result.email is None

    def test_empty_email_and_name_become_none(self) -> None:
        raw = {"id": 1, "username": "x", "access_level": 10, "email": "  ", "name": "  "}
        result = _parse_gitlab_member(raw)
        assert result is not None
        assert result.full_name is None
        assert result.email is None

    def test_default_source_is_direct(self) -> None:
        raw = {"id": 1, "username": "x", "access_level": 10}
        result = _parse_gitlab_member(raw)
        assert result is not None
        assert result.source == "direct"


class TestMemberSyncResult:
    """MemberSyncResult tracking and total_changes computation."""

    def test_zero_changes_on_init(self) -> None:
        import uuid

        r = MemberSyncResult(team_id=uuid.uuid4(), team_name="test")
        assert r.total_changes == 0
        assert r.members_added == 0
        assert r.members_removed == 0
        assert r.roles_changed == 0
        assert r.members_reactivated == 0
        assert r.errors == []

    def test_total_changes_sums_all(self) -> None:
        import uuid

        r = MemberSyncResult(
            team_id=uuid.uuid4(),
            team_name="test",
            members_added=2,
            members_removed=1,
            members_reactivated=1,
            roles_changed=3,
        )
        assert r.total_changes == 7

    def test_members_unchanged_not_in_total(self) -> None:
        import uuid

        r = MemberSyncResult(
            team_id=uuid.uuid4(),
            team_name="test",
            members_unchanged=5,
        )
        assert r.total_changes == 0


class TestGitLabMemberInfoSource:
    """Validate source tracking (direct vs inherited)."""

    def test_direct_source_preserved(self) -> None:
        raw = {"id": 1, "username": "u1", "access_level": 30}
        result = _parse_gitlab_member(raw, source="direct")
        assert result is not None
        assert result.source == "direct"

    def test_inherited_source_preserved(self) -> None:
        raw = {"id": 1, "username": "u1", "access_level": 30}
        result = _parse_gitlab_member(raw, source="inherited")
        assert result is not None
        assert result.source == "inherited"


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_string_access_level_skipped(self) -> None:
        """Non-integer access_level should be skipped."""
        raw = {"id": 1, "username": "x", "access_level": "thirty"}
        result = _parse_gitlab_member(raw)
        assert result is None

    def test_bot_user_skipped_by_username(self) -> None:
        """Bot users identified by username suffix should be skipped."""
        raw = {"id": 99, "username": "project_42_bot", "access_level": 30}
        assert _parse_gitlab_member(raw) is None

    def test_bot_user_skipped_by_user_type(self) -> None:
        """Bot users identified by user_type field should be skipped."""
        raw = {
            "id": 99,
            "username": "legit_user",
            "access_level": 30,
            "user_type": "project_bot",
        }
        assert _parse_gitlab_member(raw) is None

    def test_blocked_user_skipped(self) -> None:
        """Blocked/deactivated GitLab users should be skipped."""
        raw = {"id": 50, "username": "blocked_user", "access_level": 30, "state": "blocked"}
        assert _parse_gitlab_member(raw) is None

    def test_deactivated_user_skipped(self) -> None:
        """Deactivated GitLab users should be skipped."""
        raw = {"id": 51, "username": "deact_user", "access_level": 30, "state": "deactivated"}
        assert _parse_gitlab_member(raw) is None

    def test_active_user_not_skipped(self) -> None:
        """Active users should pass through normally."""
        raw = {"id": 52, "username": "active_user", "access_level": 30, "state": "active"}
        result = _parse_gitlab_member(raw)
        assert result is not None
        assert result.username == "active_user"

    def test_missing_state_defaults_active(self) -> None:
        """Missing state field should default to active (not blocked)."""
        raw = {"id": 53, "username": "no_state_user", "access_level": 30}
        result = _parse_gitlab_member(raw)
        assert result is not None
