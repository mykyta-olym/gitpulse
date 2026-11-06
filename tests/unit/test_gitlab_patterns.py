"""Tests for app.utils.gitlab_patterns module."""


class TestExtractLinkedIssueIids:
    """Tests for extract_linked_issue_iids function."""

    def test_none_input(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids(None)
        assert result == []

    def test_empty_string(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("")
        assert result == []

    def test_closes_hash_pattern(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("Closes #123")
        assert 123 in result

    def test_fixes_hash_pattern(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("Fixes #456")
        assert 456 in result

    def test_resolves_hash_pattern(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("Resolves #789")
        assert 789 in result

    def test_bare_hash_reference(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("Related to #42")
        assert 42 in result

    def test_multiple_references(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("Closes #1, fixes #2, #3")
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_case_insensitive(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("CLOSES #99")
        assert 99 in result

    def test_closed_variant(self) -> None:
        from app.utils.gitlab_patterns import extract_linked_issue_iids

        result = extract_linked_issue_iids("Closed #100")
        assert 100 in result


class TestValidateBranchName:
    """Tests for validate_branch_name function."""

    def test_matching_pattern(self) -> None:
        from app.utils.gitlab_patterns import validate_branch_name

        result = validate_branch_name("feature-123", r"^feature-\d+$")
        assert result is True

    def test_non_matching_pattern(self) -> None:
        from app.utils.gitlab_patterns import validate_branch_name

        result = validate_branch_name("bugfix-abc", r"^feature-\d+$")
        assert result is False

    def test_invalid_regex(self) -> None:
        from app.utils.gitlab_patterns import validate_branch_name

        result = validate_branch_name("test", r"[invalid(")
        assert result is False


class TestExtractIssueIidFromBranch:
    """Tests for extract_issue_iid_from_branch function."""

    def test_default_pattern_match(self) -> None:
        from app.utils.gitlab_patterns import extract_issue_iid_from_branch

        result = extract_issue_iid_from_branch("issue-42-add-feature")
        assert result == 42

    def test_no_match(self) -> None:
        from app.utils.gitlab_patterns import extract_issue_iid_from_branch

        result = extract_issue_iid_from_branch("feature-branch")
        assert result is None

    def test_custom_pattern(self) -> None:
        from app.utils.gitlab_patterns import extract_issue_iid_from_branch

        result = extract_issue_iid_from_branch("feat/123-new", pattern=r"^feat/(\d+)-.+$")
        assert result == 123

    def test_invalid_regex_pattern(self) -> None:
        from app.utils.gitlab_patterns import extract_issue_iid_from_branch

        result = extract_issue_iid_from_branch("test", pattern=r"[invalid(")
        assert result is None


class TestExtractCommitRefs:
    """Tests for extract_commit_refs function."""

    def test_none_input(self) -> None:
        from app.utils.gitlab_patterns import extract_commit_refs

        result = extract_commit_refs(None)
        assert result == []

    def test_empty_string(self) -> None:
        from app.utils.gitlab_patterns import extract_commit_refs

        result = extract_commit_refs("")
        assert result == []

    def test_short_sha(self) -> None:
        from app.utils.gitlab_patterns import extract_commit_refs

        result = extract_commit_refs("See commit abc1234")
        assert "abc1234" in result

    def test_full_sha(self) -> None:
        from app.utils.gitlab_patterns import extract_commit_refs

        sha = "abc1234567890abcdef1234567890abcdef1234"
        result = extract_commit_refs(f"Fixed in {sha}")
        assert sha in result

    def test_multiple_shas(self) -> None:
        from app.utils.gitlab_patterns import extract_commit_refs

        result = extract_commit_refs("Compare abc1234 with def5678")
        assert "abc1234" in result
        assert "def5678" in result


class TestCheckTemplateSections:
    """Tests for check_template_sections function."""

    def test_none_description(self) -> None:
        from app.utils.gitlab_patterns import check_template_sections

        compliant, missing = check_template_sections(None, ["Summary", "Testing"])
        assert compliant is False
        assert missing == ["Summary", "Testing"]

    def test_all_sections_present(self) -> None:
        from app.utils.gitlab_patterns import check_template_sections

        desc = "## Summary\nThis is a summary.\n## Testing\nUnit tests added."
        compliant, missing = check_template_sections(desc, ["Summary", "Testing"])
        assert compliant is True
        assert missing == []

    def test_missing_section(self) -> None:
        from app.utils.gitlab_patterns import check_template_sections

        desc = "## Summary\nThis is a summary."
        compliant, missing = check_template_sections(desc, ["Summary", "Testing"])
        assert compliant is False
        assert "Testing" in missing

    def test_case_insensitive(self) -> None:
        from app.utils.gitlab_patterns import check_template_sections

        desc = "## summary\nContent here"
        compliant, _missing = check_template_sections(desc, ["Summary"])
        assert compliant is True


class TestIsTestFile:
    """Tests for is_test_file function."""

    def test_matched_by_pattern(self) -> None:
        from app.utils.gitlab_patterns import is_test_file

        result = is_test_file("test_foo.py", ["test_*.py"])
        assert result is True

    def test_not_matched_by_pattern(self) -> None:
        from app.utils.gitlab_patterns import is_test_file

        result = is_test_file("foo.py", ["test_*.py"])
        assert result is False

    def test_heuristic_test_prefix(self) -> None:
        from app.utils.gitlab_patterns import is_test_file

        result = is_test_file("src/test_module.py", [])
        assert result is True

    def test_heuristic_test_suffix(self) -> None:
        from app.utils.gitlab_patterns import is_test_file

        result = is_test_file("module_test.py", [])
        assert result is True

    def test_heuristic_test_directory(self) -> None:
        from app.utils.gitlab_patterns import is_test_file

        result = is_test_file("src/test/conftest.py", [])
        # Contains '/test' pattern
        assert result is True

    def test_non_test_file(self) -> None:
        from app.utils.gitlab_patterns import is_test_file

        result = is_test_file("src/main.py", [])
        assert result is False

    def test_substring_false_positives_are_not_tests(self) -> None:
        """Ordinary files whose names merely contain the letters 'test' must
        NOT be classified as test files (regression for R03 inflation)."""
        from app.utils.gitlab_patterns import is_test_file

        for path in (
            "latest_data.py",
            "latest_release.json",
            "contest_results.py",
            "src/testimonials/quote.py",
            "protest_form.py",
            "greatest_hits.md",
        ):
            assert is_test_file(path, []) is False, path

    def test_js_test_naming_conventions(self) -> None:
        """JS/TS `.test.`/`.spec.` files are still detected."""
        from app.utils.gitlab_patterns import is_test_file

        assert is_test_file("src/button.test.ts", []) is True
        assert is_test_file("src/button.spec.js", []) is True
        assert is_test_file("tests/e2e/login.py", []) is True


class TestCountTestFiles:
    """Tests for count_test_files function."""

    def test_count_test_files(self) -> None:
        from app.utils.gitlab_patterns import count_test_files

        files = ["test_a.py", "test_b.py", "main.py", "config.py"]
        result = count_test_files(files, ["test_*.py"])
        assert result == 2

    def test_empty_list(self) -> None:
        from app.utils.gitlab_patterns import count_test_files

        result = count_test_files([], ["test_*.py"])
        assert result == 0

    def test_no_test_files(self) -> None:
        from app.utils.gitlab_patterns import count_test_files

        result = count_test_files(["main.py", "config.py"], ["test_*.py"])
        assert result == 0
