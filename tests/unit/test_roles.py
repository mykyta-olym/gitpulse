"""Unit tests for the GitLab role hierarchy module (app.compliance.roles)."""

import pytest

from app.compliance.roles import (
    ACCESS_DEVELOPER,
    ACCESS_GUEST,
    ACCESS_LEVEL_NAMES,
    ACCESS_MAINTAINER,
    ACCESS_OWNER,
    ACCESS_REPORTER,
    MIN_CONTRIBUTING_LEVEL,
    access_role_name,
    is_contributing_role,
    role_priority,
)

# --- Constants -----------------------------------------------


class TestAccessLevelConstants:
    def test_guest_is_10(self) -> None:
        assert ACCESS_GUEST == 10

    def test_reporter_is_20(self) -> None:
        assert ACCESS_REPORTER == 20

    def test_developer_is_30(self) -> None:
        assert ACCESS_DEVELOPER == 30

    def test_maintainer_is_40(self) -> None:
        assert ACCESS_MAINTAINER == 40

    def test_owner_is_50(self) -> None:
        assert ACCESS_OWNER == 50

    def test_min_contributing_is_developer(self) -> None:
        assert MIN_CONTRIBUTING_LEVEL == ACCESS_DEVELOPER

    def test_access_level_names_complete(self) -> None:
        assert set(ACCESS_LEVEL_NAMES.keys()) == {10, 20, 30, 40, 50}
        assert ACCESS_LEVEL_NAMES[10] == "guest"
        assert ACCESS_LEVEL_NAMES[50] == "owner"


# --- access_role_name ----------------------------------------


class TestAccessRoleName:
    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            (10, "guest"),
            (15, "guest"),  # between guest and reporter
            (20, "reporter"),
            (25, "reporter"),
            (30, "developer"),
            (40, "maintainer"),
            (50, "owner"),
            (60, "owner"),  # above owner
        ],
    )
    def test_maps_level_to_name(self, level: int, expected: str) -> None:
        assert access_role_name(level) == expected

    def test_below_guest_returns_none_label(self) -> None:
        assert access_role_name(5) == "none"

    def test_zero_returns_none_label(self) -> None:
        assert access_role_name(0) == "none"


# --- is_contributing_role ------------------------------------


class TestIsContributingRole:
    def test_guest_is_not_contributing(self) -> None:
        assert is_contributing_role(ACCESS_GUEST) is False

    def test_reporter_is_not_contributing(self) -> None:
        assert is_contributing_role(ACCESS_REPORTER) is False

    def test_developer_is_contributing(self) -> None:
        assert is_contributing_role(ACCESS_DEVELOPER) is True

    def test_maintainer_is_contributing(self) -> None:
        assert is_contributing_role(ACCESS_MAINTAINER) is True

    def test_owner_is_contributing(self) -> None:
        assert is_contributing_role(ACCESS_OWNER) is True

    def test_none_defaults_to_contributing(self) -> None:
        """Unknown access level -> assume contributing (safe default)."""
        assert is_contributing_role(None) is True

    def test_below_developer_not_contributing(self) -> None:
        assert is_contributing_role(29) is False

    def test_at_developer_contributing(self) -> None:
        assert is_contributing_role(30) is True

    def test_above_owner_contributing(self) -> None:
        assert is_contributing_role(100) is True


# --- role_priority -------------------------------------------


class TestRolePriority:
    @pytest.mark.parametrize(
        ("role", "expected"),
        [
            ("owner", 50),
            ("maintainer", 40),
            ("developer", 30),
            ("reporter", 20),
            ("guest", 10),
        ],
    )
    def test_known_roles(self, role: str, expected: int) -> None:
        assert role_priority(role) == expected

    def test_case_insensitive(self) -> None:
        assert role_priority("Owner") == 50
        assert role_priority("DEVELOPER") == 30

    def test_none_returns_zero(self) -> None:
        assert role_priority(None) == 0

    def test_unknown_returns_zero(self) -> None:
        assert role_priority("external") == 0

    def test_empty_string_returns_zero(self) -> None:
        assert role_priority("") == 0

    def test_priority_ordering(self) -> None:
        """Owner > Maintainer > Developer > Reporter > Guest."""
        roles = ["guest", "reporter", "developer", "maintainer", "owner"]
        priorities = [role_priority(r) for r in roles]
        assert priorities == sorted(priorities)
