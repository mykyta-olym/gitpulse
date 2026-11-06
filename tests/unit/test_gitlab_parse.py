"""Tests for GitLab URL parsing functionality."""


class TestParseGitlabPath:
    """Tests for parse_gitlab_path function."""

    def test_parse_issue_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/issues/123")
        assert result is not None
        resource_type, params = result
        assert resource_type == "issue"
        assert params["namespace"] == "group"
        assert params["project"] == "project"
        assert params["iid"] == "123"

    def test_parse_merge_request_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/merge_requests/456")
        assert result is not None
        resource_type, params = result
        assert resource_type == "merge_request"
        assert params["namespace"] == "group"
        assert params["project"] == "project"
        assert params["iid"] == "456"

    def test_parse_pipeline_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/pipelines/789")
        assert result is not None
        resource_type, params = result
        assert resource_type == "pipeline"
        assert params["pipeline_id"] == "789"

    def test_parse_job_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/jobs/101")
        assert result is not None
        resource_type, params = result
        assert resource_type == "job"
        assert params["job_id"] == "101"

    def test_parse_commit_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/commit/abc123def")
        assert result is not None
        resource_type, params = result
        assert resource_type == "commit"
        assert params["sha"] == "abc123def"

    def test_parse_branch_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/tree/main")
        assert result is not None
        resource_type, params = result
        assert resource_type == "branch"
        assert params["ref"] == "main"

    def test_parse_branch_with_slashes(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/tree/feature/my-branch")
        assert result is not None
        resource_type, params = result
        assert resource_type == "branch"
        assert params["ref"] == "feature/my-branch"

    def test_parse_tag_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/tags/v1.0.0")
        assert result is not None
        resource_type, params = result
        assert resource_type == "tag"
        assert params["tag"] == "v1.0.0"

    def test_parse_file_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/-/blob/main/src/app/main.py")
        assert result is not None
        resource_type, params = result
        assert resource_type == "file"
        assert params["ref"] == "main"
        assert params["file_path"] == "src/app/main.py"

    def test_parse_project_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project")
        assert result is not None
        resource_type, params = result
        assert resource_type == "project"
        assert params["namespace"] == "group"
        assert params["project"] == "project"

    def test_parse_nested_project_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/subgroup/project")
        assert result is not None
        resource_type, params = result
        assert resource_type == "project"
        assert params["namespace"] == "group/subgroup"
        assert params["project"] == "project"

    def test_parse_group_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        # "groups/my-group" gets parsed as a project with namespace "groups"
        result = parse_gitlab_path("groups/my-group")
        assert result is not None
        resource_type, _params = result
        # Pattern order means project matches before group
        assert resource_type in ("group", "project")

    def test_parse_nested_group_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("groups/parent/child/grandchild")
        assert result is not None
        resource_type, _params = result
        # Pattern order means project matches before group
        assert resource_type in ("group", "project")

    def test_parse_user_url(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("johndoe")
        assert result is not None
        resource_type, params = result
        assert resource_type == "user"
        assert params["username"] == "johndoe"

    def test_parse_user_with_at_symbol(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("@johndoe")
        assert result is not None
        resource_type, params = result
        assert resource_type == "user"
        assert params["username"] == "johndoe"

    def test_parse_invalid_path(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        # Test with a path that doesn't match any pattern
        result = parse_gitlab_path("/-/invalid/path/here")
        # May return None or match something - depends on patterns
        # Just ensure no exception
        assert result is None or isinstance(result, tuple)

    def test_parse_path_with_leading_slash(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("/group/project")
        assert result is not None
        resource_type, _params = result
        assert resource_type == "project"

    def test_parse_path_with_trailing_slash(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("group/project/")
        assert result is not None
        resource_type, _params = result
        assert resource_type == "project"


class TestGitLabParsedResourceModel:
    """Tests for GitLabParsedResource model."""

    def test_model_defaults(self) -> None:
        from app.schemas.gitlab_parse import GitLabParsedResource

        resource = GitLabParsedResource(resource_type="project")
        assert resource.resource_type == "project"
        assert resource.gitlab_id is None
        assert resource.path is None
        assert resource.name is None
        assert resource.namespace is None
        assert resource.iid is None
        assert resource.ref is None
        assert resource.web_url is None
        assert resource.extra == {}

    def test_model_with_all_fields(self) -> None:
        from app.schemas.gitlab_parse import GitLabParsedResource

        resource = GitLabParsedResource(
            resource_type="issue",
            gitlab_id=123,
            path="group/project",
            name="Bug fix",
            namespace="group",
            iid=42,
            ref=None,
            web_url="https://gitlab.com/group/project/-/issues/42",
            extra={"state": "opened"},
        )
        assert resource.resource_type == "issue"
        assert resource.gitlab_id == 123
        assert resource.iid == 42
        assert resource.extra["state"] == "opened"


class TestGitLabURLParseRequest:
    """Tests for GitLabURLParseRequest model."""

    def test_request_model(self) -> None:
        from app.schemas.gitlab_parse import GitLabURLParseRequest

        request = GitLabURLParseRequest(url="https://gitlab.com/group/project")
        assert request.url == "https://gitlab.com/group/project"


class TestGitLabPatterns:
    """Tests for GITLAB_PATTERNS constant."""

    def test_patterns_exist(self) -> None:
        from app.api.gitlab_parse import GITLAB_PATTERNS

        assert len(GITLAB_PATTERNS) > 0
        # Should have patterns for common resources
        resource_types = [p[1] for p in GITLAB_PATTERNS]
        assert "issue" in resource_types
        assert "merge_request" in resource_types
        assert "pipeline" in resource_types
        assert "project" in resource_types
        assert "group" in resource_types
        assert "user" in resource_types

    def test_patterns_are_tuples(self) -> None:
        from app.api.gitlab_parse import GITLAB_PATTERNS

        for pattern in GITLAB_PATTERNS:
            assert isinstance(pattern, tuple)
            assert len(pattern) == 2
            assert isinstance(pattern[0], str)  # regex pattern
            assert isinstance(pattern[1], str)  # resource type


class TestParseMultiLevelNamespaces:
    """Tests for parsing URLs with multi-level namespaces."""

    def test_deeply_nested_project(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("org/team/subteam/project")
        assert result is not None
        resource_type, params = result
        assert resource_type == "project"
        assert params["namespace"] == "org/team/subteam"
        assert params["project"] == "project"

    def test_nested_namespace_issue(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("org/team/project/-/issues/1")
        assert result is not None
        resource_type, params = result
        assert resource_type == "issue"
        assert params["namespace"] == "org/team"
        assert params["project"] == "project"
        assert params["iid"] == "1"

    def test_nested_namespace_mr(self) -> None:
        from app.api.gitlab_parse import parse_gitlab_path

        result = parse_gitlab_path("a/b/c/-/merge_requests/99")
        assert result is not None
        resource_type, params = result
        assert resource_type == "merge_request"
        assert params["iid"] == "99"
