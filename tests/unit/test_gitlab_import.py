"""Unit tests for GitLab group import helpers."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.schemas.courses import GitLabGroupImportResponse
from app.services.gitlab_import.helpers import (
    extract_group_path_from_input,
    is_bot_user,
    match_team_group_path,
    select_team_group_records,
)
from app.services.gitlab_import.normalize import (
    _normalize_nonempty,
    _normalize_optional,
    _to_int,
    _to_positive_int,
)
from app.services.gitlab_import.persistence import (
    _deactivate_missing_projects_for_course,
    _derive_team_name,
    _is_teacher_access_level,
    _is_teacher_member,
    _project_namespace_path,
    _role_priority,
    gitlab_access_role_name,
)


class TestExtractGroupPathFromInput:
    """Validate URL/path normalization for group imports."""

    def test_full_groups_url(self) -> None:
        path = extract_group_path_from_input(
            "https://gitlab.example.com/groups/zsi-labs/assignments-2025",
            "https://gitlab.example.com",
        )
        assert path == "zsi-labs/assignments-2025"

    def test_plain_group_path(self) -> None:
        path = extract_group_path_from_input(
            "zsi-labs/assignments-2025",
            "https://gitlab.example.com",
        )
        assert path == "zsi-labs/assignments-2025"

    def test_groups_prefix_path(self) -> None:
        path = extract_group_path_from_input(
            "groups/zsi-labs/assignments-2025",
            "https://gitlab.example.com",
        )
        assert path == "zsi-labs/assignments-2025"

    def test_strips_resource_suffix(self) -> None:
        path = extract_group_path_from_input(
            "https://gitlab.example.com/groups/zsi-labs/assignments-2025/-/group_members",
            "https://gitlab.example.com",
        )
        assert path == "zsi-labs/assignments-2025"

    def test_rejects_empty_input(self) -> None:
        with pytest.raises(ValueError, match="required"):
            extract_group_path_from_input("   ", "https://gitlab.example.com")

    def test_accepts_single_segment_path(self) -> None:
        """Single-segment paths are valid (could be a project namespace)."""
        path = extract_group_path_from_input("assignments-2025", "https://gitlab.example.com")
        assert path == "assignments-2025"

    def test_rejects_non_ascii_path(self) -> None:
        with pytest.raises(ValueError, match="valid GitLab"):
            extract_group_path_from_input("ф", "https://gitlab.example.com")

    def test_rejects_path_with_spaces(self) -> None:
        with pytest.raises(ValueError, match="valid GitLab"):
            extract_group_path_from_input("zsi labs/assignments", "https://gitlab.example.com")

    def test_rejects_url_without_path(self) -> None:
        with pytest.raises(ValueError, match="Could not determine"):
            extract_group_path_from_input(
                "https://gitlab.example.com/", "https://gitlab.example.com"
            )

    def test_strips_git_suffix(self) -> None:
        path = extract_group_path_from_input(
            "https://github.com/mykyta-olym/test-diplomova.git",
            "https://gitlab.example.com",
        )
        assert path == "mykyta.olym/test-diplomova"

    def test_strips_git_suffix_plain_path(self) -> None:
        path = extract_group_path_from_input(
            "mykyta.olym/test-diplomova.git",
            "https://gitlab.example.com",
        )
        assert path == "mykyta.olym/test-diplomova"


class TestMatchTeamGroupPath:
    """Validate namespace -> team mapping strategy."""

    def test_prefers_longest_prefix_match(self) -> None:
        matched = match_team_group_path(
            namespace_path="zsi-labs/assignments-2025/team-01",
            team_group_paths=[
                "zsi-labs",
                "zsi-labs/assignments-2025",
                "zsi-labs/assignments-2025/team-01",
            ],
        )
        assert matched == "zsi-labs/assignments-2025/team-01"

    def test_returns_none_when_no_match(self) -> None:
        matched = match_team_group_path(
            namespace_path="another-group/course-x",
            team_group_paths=["zsi-labs/assignments-2025/team-01"],
        )
        assert matched is None


class TestGitLabAccessRoleName:
    """Validate GitLab numeric access level -> role mapping."""

    @pytest.mark.parametrize(
        ("access_level", "expected_role"),
        [
            (50, "owner"),
            (45, "maintainer"),
            (40, "maintainer"),
            (30, "developer"),
            (20, "reporter"),
            (10, "guest"),
            (5, "minimal_access"),
            (0, "unknown"),
        ],
    )
    def test_maps_access_levels_to_roles(self, access_level: int, expected_role: str) -> None:
        assert gitlab_access_role_name(access_level) == expected_role


class TestSelectTeamGroupRecords:
    """Validate dynamic team group selection for nested hierarchies."""

    def test_prefers_groups_that_directly_host_projects(self) -> None:
        root_id = 10
        records = [
            {"id": 10, "full_path": "zsi-labs/assignments-2025"},
            {"id": 11, "full_path": "zsi-labs/assignments-2025/a"},
            {"id": 12, "full_path": "zsi-labs/assignments-2025/a/a7"},
            {"id": 13, "full_path": "zsi-labs/assignments-2025/a/a8"},
        ]
        selected = select_team_group_records(
            records,
            root_group_id=root_id,
            project_namespace_paths={
                "zsi-labs/assignments-2025/a/a7",
                "zsi-labs/assignments-2025/a/a8",
            },
        )
        assert [r["id"] for r in selected] == [12, 13]

    def test_falls_back_to_non_root_groups_without_project_namespaces(self) -> None:
        root_id = 10
        records = [
            {"id": 10, "full_path": "zsi-labs/assignments-2025"},
            {"id": 11, "full_path": "zsi-labs/assignments-2025/km-1"},
            {"id": 12, "full_path": "zsi-labs/assignments-2025/km-2"},
        ]
        selected = select_team_group_records(
            records,
            root_group_id=root_id,
            project_namespace_paths=set(),
        )
        assert [r["id"] for r in selected] == [11, 12]

    def test_keeps_root_when_it_is_the_only_group(self) -> None:
        selected = select_team_group_records(
            [{"id": 10, "full_path": "zsi-labs/assignments-2025"}],
            root_group_id=10,
            project_namespace_paths=set(),
        )
        assert [r["id"] for r in selected] == [10]


class TestIsTeacherMember:
    """Validate role classification during team/project member import."""

    def test_treats_discovered_username_as_teacher(self) -> None:
        assert _is_teacher_member(
            username="sulir",
            discovered_teachers={"sulir"},
        )

    def test_does_not_treat_owner_as_teacher_by_default(self) -> None:
        """Owners are often students in their own repos - access level alone
        should NOT classify them as teachers."""
        assert not _is_teacher_member(
            username="project-manager",
            discovered_teachers=set(),
        )

    def test_does_not_treat_maintainer_as_teacher_by_default(self) -> None:
        assert not _is_teacher_member(
            username="vd453gx",
            discovered_teachers=set(),
        )

    def test_discovered_owner_is_teacher(self) -> None:
        assert _is_teacher_member(
            username="teacher1",
            discovered_teachers={"teacher1"},
        )

    def test_root_group_member_with_high_subgroup_access_is_teacher(self) -> None:
        """Layer 2: root group member with Owner access in subgroup -> teacher."""
        assert _is_teacher_member(
            username="ta-user",
            discovered_teachers=set(),
            access_level=50,
            is_group_member=True,
            root_group_usernames={"ta-user", "admin-user"},
        )

    def test_root_group_member_with_maintainer_access_not_teacher(self) -> None:
        """Root group member with Maintainer access is NOT automatically teacher."""
        assert not _is_teacher_member(
            username="ta-user",
            discovered_teachers=set(),
            access_level=40,
            is_group_member=True,
            root_group_usernames={"ta-user", "admin-user"},
        )

    def test_root_group_member_with_low_subgroup_access_not_teacher(self) -> None:
        """Root group member with Developer access is NOT automatically teacher."""
        assert not _is_teacher_member(
            username="ta-user",
            discovered_teachers=set(),
            access_level=30,
            is_group_member=True,
            root_group_usernames={"ta-user"},
        )

    def test_high_access_without_root_membership_not_teacher(self) -> None:
        """High access alone (without root membership) -> NOT teacher (student project lead)."""
        assert not _is_teacher_member(
            username="student-leader",
            discovered_teachers=set(),
            access_level=50,
            is_group_member=True,
            root_group_usernames={"teacher1"},
        )

    def test_project_member_not_detected_via_layer2_maintainer(self) -> None:
        """Layer 2a only applies to group members (is_group_member=True) for Maintainer."""
        assert not _is_teacher_member(
            username="ta-user",
            discovered_teachers=set(),
            access_level=40,
            is_group_member=False,
            root_group_usernames={"ta-user"},
        )

    def test_root_group_member_owner_in_project_not_detected(self) -> None:
        """Layer 2b fix: root group member with Owner in a *project* -> NOT teacher.

        Students frequently own their project (they created it).  Only flag
        as teacher when the Owner access is on a *group* (subgroup).
        """
        assert not _is_teacher_member(
            username="gurbal",
            discovered_teachers=set(),
            access_level=50,
            is_group_member=False,
            root_group_usernames={"gurbal", "other-teacher"},
        )

    def test_root_group_member_owner_in_subgroup_detected(self) -> None:
        """Layer 2b: root group member with Owner access in a *subgroup* -> teacher."""
        assert _is_teacher_member(
            username="gurbal",
            discovered_teachers=set(),
            access_level=50,
            is_group_member=True,
            root_group_usernames={"gurbal", "other-teacher"},
        )

    def test_non_root_owner_in_project_not_detected(self) -> None:
        """Owner access alone without root membership -> NOT teacher."""
        assert not _is_teacher_member(
            username="student-owner",
            discovered_teachers=set(),
            access_level=50,
            is_group_member=False,
            root_group_usernames={"teacher1"},
        )


class TestIsBotUser:
    """Validate bot / service-account detection."""

    # -- user_type field (most reliable) --

    @pytest.mark.parametrize(
        "user_type",
        [
            "project_bot",
            "group_bot",
            "service_account",
            "alert_bot",
            "placeholder",
            "admin_bot",
        ],
    )
    def test_detects_bot_by_user_type(self, user_type: str) -> None:
        assert is_bot_user("some-user", user_type=user_type)

    def test_ignores_normal_user_type(self) -> None:
        assert not is_bot_user("student", user_type="human")

    def test_none_user_type_falls_through(self) -> None:
        assert not is_bot_user("student", user_type=None)

    # -- exact username matches --

    @pytest.mark.parametrize(
        "username",
        [
            "ghost",
            "alert-bot",
            "support-bot",
            "admin",
            "root",
        ],
    )
    def test_detects_exact_bot_usernames(self, username: str) -> None:
        assert is_bot_user(username)

    def test_exact_match_is_case_insensitive(self) -> None:
        assert is_bot_user("Ghost")
        assert is_bot_user("ALERT-BOT")

    # -- prefix heuristics --

    @pytest.mark.parametrize(
        "username",
        [
            "project_123_bot",
            "project_99_bot1",
            "group_42_bot",
            "group_1_bot2",
        ],
    )
    def test_detects_bot_by_prefix(self, username: str) -> None:
        assert is_bot_user(username)

    # -- suffix heuristics --

    @pytest.mark.parametrize(
        "username",
        [
            "deploy_bot",
            "ci-bot",
            "merge_bot1",
            "release_bot2",
        ],
    )
    def test_detects_bot_by_suffix(self, username: str) -> None:
        assert is_bot_user(username)

    # -- normal users must NOT be flagged --

    @pytest.mark.parametrize(
        "username",
        [
            "vd453gx",
            "john.doe",
            "sulir",
            "student-123",
            "my_project",
            "botticelli",
            "robotics",
        ],
    )
    def test_normal_users_not_flagged(self, username: str) -> None:
        assert not is_bot_user(username)


class TestRolePriority:
    """Validate role priority ordering."""

    @pytest.mark.parametrize(
        ("role", "expected"),
        [
            ("student", 0),
            ("teacher", 2),
            ("admin", 3),
            ("unknown", 0),
        ],
    )
    def test_role_priorities(self, role: str, expected: int) -> None:
        assert _role_priority(role) == expected


class TestIsTeacherAccessLevel:
    """Validate access-level threshold."""

    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            (50, True),
            (40, True),
            (39, False),
            (30, False),
            (0, False),
        ],
    )
    def test_access_threshold(self, level: int, expected: bool) -> None:
        assert _is_teacher_access_level(level) == expected


class TestDeriveTeamName:
    """Validate team name derivation from GitLab group records."""

    def test_uses_explicit_name(self) -> None:
        assert _derive_team_name({"name": "Team Alpha", "full_path": "org/alpha"}) == "Team Alpha"

    def test_uses_leaf_of_full_path(self) -> None:
        assert _derive_team_name({"name": None, "full_path": "org/sub/team-01"}) == "team-01"

    def test_falls_back_to_id(self) -> None:
        assert _derive_team_name({"name": None, "full_path": None, "id": 42}) == "team-42"

    def test_whitespace_name_falls_through(self) -> None:
        assert _derive_team_name({"name": "   ", "full_path": "org/team-x"}) == "team-x"


class TestProjectNamespacePath:
    """Validate project namespace path extraction."""

    def test_uses_namespace_dict(self) -> None:
        project = {
            "namespace": {"full_path": "org/course"},
            "path_with_namespace": "org/course/proj",
        }
        assert _project_namespace_path(project) == "org/course"

    def test_falls_back_to_path_with_namespace(self) -> None:
        project = {"namespace": {}, "path_with_namespace": "org/course/proj"}
        assert _project_namespace_path(project) == "org/course"

    def test_returns_none_for_missing_data(self) -> None:
        assert _project_namespace_path({}) is None

    def test_returns_none_for_single_segment(self) -> None:
        assert _project_namespace_path({"path_with_namespace": "proj"}) is None


class TestNormalizeNonempty:
    """Validate non-empty string normalization."""

    def test_strips_whitespace(self) -> None:
        assert _normalize_nonempty("  hello  ") == "hello"

    def test_uses_fallback(self) -> None:
        assert _normalize_nonempty("   ", fallback="default") == "default"

    def test_raises_without_fallback(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            _normalize_nonempty("   ")

    def test_converts_to_string(self) -> None:
        assert _normalize_nonempty(42) == "42"


class TestNormalizeOptional:
    """Validate optional string normalization."""

    def test_returns_none_for_none(self) -> None:
        assert _normalize_optional(None) is None

    def test_returns_none_for_empty(self) -> None:
        assert _normalize_optional("") is None

    def test_returns_none_for_whitespace(self) -> None:
        assert _normalize_optional("   ") is None

    def test_strips_and_returns(self) -> None:
        assert _normalize_optional("  test  ") == "test"


class TestToInt:
    """Validate integer conversion helper."""

    def test_converts_int(self) -> None:
        assert _to_int(42) == 42

    def test_converts_string(self) -> None:
        assert _to_int("50") == 50

    def test_returns_zero_for_none(self) -> None:
        assert _to_int(None) == 0

    def test_returns_zero_for_invalid(self) -> None:
        assert _to_int("abc") == 0


class TestToPositiveInt:
    """Validate positive integer conversion."""

    def test_valid_positive(self) -> None:
        assert _to_positive_int(10, "test") == 10

    def test_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="Invalid test"):
            _to_positive_int(0, "test")

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="Invalid test"):
            _to_positive_int(-5, "test")

    def test_rejects_none(self) -> None:
        with pytest.raises(ValueError, match="Invalid id"):
            _to_positive_int(None, "id")


class TestGitLabGroupImportReconciliationContract:
    """Validate course/group imports deactivate projects missing from GitLab."""

    def test_missing_project_reconciliation_is_part_of_group_import(self) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        src = (root / "src" / "app" / "services" / "gitlab_import" / "service.py").read_text(
            encoding="utf-8"
        )

        assert "_deactivate_missing_projects_for_course" in src
        # Every project seen live is reported, so the rest can be deactivated.
        assert "observed.add(project_id)" in src
        assert "live_gitlab_project_ids=observed" in src
        assert "projects_deactivated=projects_deactivated" in src
        assert "Deactivated {deactivated} project(s) missing from GitLab." in src

    def test_reconciliation_helper_is_transaction_scoped(self) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        src = (root / "src" / "app" / "services" / "gitlab_import" / "persistence.py").read_text(
            encoding="utf-8"
        )
        helper_src = src.split("async def _deactivate_missing_projects_for_course", 1)[1].split(
            "\n\nasync def _transfer_memberships_on_reassign", 1
        )[0]

        assert _deactivate_missing_projects_for_course is not None
        assert "GitLabProject.gitlab_project_id.notin_(live_gitlab_project_ids)" in helper_src
        assert 'GitLabProject.gitlab_project_path.like(f"{root_path}/%")' in helper_src
        assert "await db.flush()" in helper_src
        assert "await db.commit()" not in helper_src

    async def test_an_empty_live_list_deactivates_nothing(self) -> None:
        """GitLab answers 200 [] for a group whose projects the token cannot
        see. That is not a list of what is gone: with nothing observed the
        helper must not touch the database, let alone deactivate the course's
        every project (which it used to)."""

        class _Db:
            executed = 0

            async def execute(self, *a: object, **k: object) -> None:
                self.executed += 1
                raise AssertionError("no query may run for an empty live list")

        db = _Db()
        result = await _deactivate_missing_projects_for_course(
            db,  # type: ignore[arg-type]
            course_id=uuid4(),
            root_group_path="kpi/2026/dp",
            live_gitlab_project_ids=set(),
        )
        assert result == (0, 0)
        assert db.executed == 0

    def test_import_response_exposes_deactivated_project_count(self) -> None:
        response = GitLabGroupImportResponse(
            course_id=uuid4(),
            course_code="ZSI",
            course_name="Software Engineering",
            group_path="zsi-labs/assignments",
            created_course=False,
            teams_created=0,
            teams_updated=1,
            students_created=0,
            students_updated=0,
            memberships_created=0,
            projects_created=0,
            projects_updated=4,
            projects_deactivated=1,
            teachers_detected=[],
        )

        assert response.projects_deactivated == 1
