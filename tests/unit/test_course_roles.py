"""Unit tests for the per-course RBAC core (``app.security.course_roles``).

These lock in the privilege ordering that every dashboard access guard
depends on: ``_can_view_team`` / ``_can_view_course`` /
``_filter_teams_for_user`` all funnel through ``role_gte(role, min_role)``.
If this ordering ever inverts, a course ``student`` would slip past a
``teacher`` gate (seeing other groups) or a ``teacher`` past an ``owner``
gate (managing a course they only teach) - the exact role-separation
invariants we care about. ``test_roles.py`` covers the *GitLab* access-level
hierarchy (``app.compliance.roles``); this file covers the *course* one.
"""

from app.models.course_membership import COURSE_ROLE_WEIGHT, COURSE_ROLES
from app.security.course_roles import (
    ROLE_EDIT_CONTENT,
    ROLE_MANAGE_COURSE,
    ROLE_VIEW_COURSE,
    ROLE_VIEW_STUDENTS,
    role_gte,
)


class TestCourseRoleWeights:
    def test_order_is_student_teacher_owner(self) -> None:
        assert COURSE_ROLES == ("student", "teacher", "owner")

    def test_weights_strictly_increasing(self) -> None:
        assert COURSE_ROLE_WEIGHT["student"] < COURSE_ROLE_WEIGHT["teacher"]
        assert COURSE_ROLE_WEIGHT["teacher"] < COURSE_ROLE_WEIGHT["owner"]


class TestRoleGteOrdering:
    def test_owner_outranks_everything(self) -> None:
        assert role_gte("owner", "owner")
        assert role_gte("owner", "teacher")
        assert role_gte("owner", "student")

    def test_teacher_meets_teacher_and_student_but_not_owner(self) -> None:
        assert role_gte("teacher", "teacher")
        assert role_gte("teacher", "student")
        assert not role_gte("teacher", "owner")

    def test_student_meets_only_student(self) -> None:
        assert role_gte("student", "student")
        # The key separation invariant: a course-student must NOT pass a
        # teacher gate (would otherwise see groups they don't teach).
        assert not role_gte("student", "teacher")
        assert not role_gte("student", "owner")


class TestRoleGteUnknownInputs:
    def test_unknown_role_is_denied(self) -> None:
        # Unknown actual role weighs -1, below every real min_role -> deny.
        assert not role_gte("bogus", "student")
        assert not role_gte("", "student")

    def test_known_role_passes_unknown_min_role(self) -> None:
        # Unknown min_role defaults to weight 0 (student level). min_role is
        # always a hard-coded constant in app code (never user input), so this
        # permissive default is safe; we pin the documented behaviour.
        assert role_gte("teacher", "bogus")
        assert role_gte("student", "bogus")


class TestRoleConstants:
    def test_view_course_is_student_level(self) -> None:
        assert ROLE_VIEW_COURSE == "student"

    def test_viewing_students_and_editing_require_teacher(self) -> None:
        assert ROLE_VIEW_STUDENTS == "teacher"
        assert ROLE_EDIT_CONTENT == "teacher"

    def test_managing_a_course_requires_owner(self) -> None:
        assert ROLE_MANAGE_COURSE == "owner"

    def test_constants_are_real_course_roles(self) -> None:
        for const in (ROLE_VIEW_COURSE, ROLE_VIEW_STUDENTS, ROLE_EDIT_CONTENT, ROLE_MANAGE_COURSE):
            assert const in COURSE_ROLE_WEIGHT
