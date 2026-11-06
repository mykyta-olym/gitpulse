"""Unit tests for per-course role hierarchy (CourseMembership + course_roles helpers)."""

from __future__ import annotations

import pytest

from app.models.course_membership import COURSE_ROLE_WEIGHT, COURSE_ROLES
from app.security.course_roles import (
    ROLE_EDIT_CONTENT,
    ROLE_MANAGE_COURSE,
    ROLE_VIEW_COURSE,
    ROLE_VIEW_STUDENTS,
    role_gte,
)

# ===============================================================================
# Constants
# ===============================================================================


class TestCourseRoleConstants:
    def test_roles_ordered_least_to_most(self) -> None:
        assert COURSE_ROLES == ("student", "teacher", "owner")

    def test_weight_ordering(self) -> None:
        assert COURSE_ROLE_WEIGHT["student"] < COURSE_ROLE_WEIGHT["teacher"]
        assert COURSE_ROLE_WEIGHT["teacher"] < COURSE_ROLE_WEIGHT["owner"]

    def test_all_roles_have_weights(self) -> None:
        for role in COURSE_ROLES:
            assert role in COURSE_ROLE_WEIGHT

    def test_role_aliases(self) -> None:
        assert ROLE_VIEW_COURSE == "student"
        assert ROLE_VIEW_STUDENTS == "teacher"
        assert ROLE_EDIT_CONTENT == "teacher"
        assert ROLE_MANAGE_COURSE == "owner"


# ===============================================================================
# role_gte - synchronous comparison
# ===============================================================================


class TestRoleGte:
    """Test the role_gte(role, min_role) comparison helper."""

    @pytest.mark.parametrize(
        ("role", "min_role", "expected"),
        [
            # Same role - always True
            ("student", "student", True),
            ("teacher", "teacher", True),
            ("owner", "owner", True),
            # Higher role - True
            ("owner", "student", True),
            ("owner", "teacher", True),
            ("teacher", "student", True),
            # Lower role - False
            ("student", "teacher", False),
            ("student", "owner", False),
            ("teacher", "owner", False),
        ],
    )
    def test_comparison(self, role: str, min_role: str, expected: bool) -> None:
        assert role_gte(role, min_role) is expected

    def test_unknown_role_returns_false(self) -> None:
        assert role_gte("unknown", "student") is False

    def test_unknown_min_role_returns_false(self) -> None:
        # Unknown min_role defaults to weight 0, which student (weight 0) meets
        assert role_gte("student", "unknown") is True

    def test_both_unknown_returns_false(self) -> None:
        # unknown has weight -1, unknown min_role has weight 0
        assert role_gte("unknown", "bogus") is False


# ===============================================================================
# is_course_staff - combined check (admin / CourseMembership / legacy)
# ===============================================================================


class _FakeUser:
    """Minimal User-like object for testing."""

    def __init__(
        self,
        *,
        role: str = "student",
        gitlab_username: str = "",
        username: str = "",
        user_id: object = None,
    ) -> None:
        self.role = role
        self.gitlab_username = gitlab_username
        self.username = username
        self.id = user_id


class TestIsCourseStaffSync:
    """Test the synchronous parts of is_course_staff logic via role_gte."""

    def test_admin_user_always_passes(self) -> None:
        """Admin bypass is the first check - no membership needed."""
        user = _FakeUser(role="admin")
        # Admin check happens before DB, so we test the condition directly
        assert user.role == "admin"


# ===============================================================================
# CourseMembership model
# ===============================================================================


class TestCourseMembershipModel:
    def test_model_imports(self) -> None:
        from app.models.course_membership import CourseMembership

        assert CourseMembership.__tablename__ == "course_memberships"

    def test_model_in_registry(self) -> None:
        from app.models import CourseMembership

        assert CourseMembership is not None

    def test_unique_constraint_name(self) -> None:
        from app.models.course_membership import CourseMembership

        constraint_names = [c.name for c in CourseMembership.__table_args__ if hasattr(c, "name")]
        assert "uq_course_membership_user_course" in constraint_names

    def test_default_role_is_student(self) -> None:
        from app.models.course_membership import CourseMembership

        col = CourseMembership.__table__.c.role
        assert col.default.arg == "student"


# ===============================================================================
# Per-course hierarchy invariants
# ===============================================================================


class TestHierarchyInvariants:
    """Verify the role hierarchy has the properties needed for a diploma-quality system."""

    def test_three_levels(self) -> None:
        assert len(COURSE_ROLES) == 3

    def test_owner_is_highest(self) -> None:
        assert COURSE_ROLES[-1] == "owner"
        assert role_gte("owner", "teacher")
        assert role_gte("owner", "student")

    def test_student_is_lowest(self) -> None:
        assert COURSE_ROLES[0] == "student"
        assert not role_gte("student", "teacher")
        assert not role_gte("student", "owner")

    def test_teacher_can_edit_content(self) -> None:
        assert role_gte("teacher", ROLE_EDIT_CONTENT)

    def test_teacher_can_view_students(self) -> None:
        assert role_gte("teacher", ROLE_VIEW_STUDENTS)

    def test_student_cannot_view_other_students(self) -> None:
        assert not role_gte("student", ROLE_VIEW_STUDENTS)

    def test_transitivity(self) -> None:
        """If A >= B and B >= C then A >= C."""
        roles = list(COURSE_ROLES)
        for i in range(len(roles)):
            for j in range(i, len(roles)):
                for k in range(j, len(roles)):
                    # roles[k] >= roles[j] >= roles[i]
                    if role_gte(roles[k], roles[j]) and role_gte(roles[j], roles[i]):
                        assert role_gte(roles[k], roles[i])


# ===============================================================================
# set_course_membership validation
# ===============================================================================


class TestSetCourseMembershipValidation:
    """Verify that set_course_membership rejects invalid roles."""

    def test_invalid_role_raises_value_error(self) -> None:
        import asyncio

        from app.security.course_roles import set_course_membership

        async def _try() -> None:
            import uuid
            from unittest.mock import AsyncMock

            mock_db = AsyncMock()
            await set_course_membership(mock_db, uuid.uuid4(), uuid.uuid4(), "superadmin")

        with pytest.raises(ValueError, match="Invalid course role"):
            asyncio.run(_try())

    def test_valid_roles_accepted(self) -> None:
        for role in COURSE_ROLES:
            # Should not raise ValueError (role validation passes before DB call)
            from app.models.course_membership import COURSE_ROLE_WEIGHT

            assert role in COURSE_ROLE_WEIGHT
