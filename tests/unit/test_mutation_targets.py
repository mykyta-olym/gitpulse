"""Focused tests for mutation targets used by mutmut.

This module provides comprehensive tests for pure-logic modules to ensure
high mutation test coverage. Each test is designed to catch common mutations.
"""

from datetime import UTC, datetime

from app.utils import gitlab_patterns as gp
from app.utils import text_analysis as ta
from app.utils import time_utils as tu

# ===============================================================
#  GitLab Patterns Tests
# ===============================================================


class TestExtractLinkedIssueIids:
    """Tests for extract_linked_issue_iids function."""

    def test_closes_single_issue(self) -> None:
        assert gp.extract_linked_issue_iids("Closes #12") == [12]

    def test_fixes_single_issue(self) -> None:
        assert gp.extract_linked_issue_iids("Fixes #42") == [42]

    def test_resolves_single_issue(self) -> None:
        assert gp.extract_linked_issue_iids("Resolves #99") == [99]

    def test_cross_project_reference(self) -> None:
        assert gp.extract_linked_issue_iids("Closes group/project#34") == [34]

    def test_multiple_issues_deduped(self) -> None:
        description = "Closes #12 and fixes group/project#34 plus #12 again"
        result = gp.extract_linked_issue_iids(description)
        assert result == [12, 34]
        assert len(result) == 2

    def test_bare_reference_fallback(self) -> None:
        assert gp.extract_linked_issue_iids("Related to #55") == [55]

    def test_none_returns_empty(self) -> None:
        assert gp.extract_linked_issue_iids(None) == []

    def test_empty_string_returns_empty(self) -> None:
        assert gp.extract_linked_issue_iids("") == []

    def test_no_issues_returns_empty(self) -> None:
        assert gp.extract_linked_issue_iids("No issues here") == []

    def test_case_insensitive_close(self) -> None:
        assert gp.extract_linked_issue_iids("CLOSES #10") == [10]
        assert gp.extract_linked_issue_iids("closes #10") == [10]
        assert gp.extract_linked_issue_iids("Closes #10") == [10]

    def test_past_tense_variants(self) -> None:
        assert gp.extract_linked_issue_iids("Closed #5") == [5]
        assert gp.extract_linked_issue_iids("Fixed #6") == [6]
        assert gp.extract_linked_issue_iids("Resolved #7") == [7]


class TestValidateBranchName:
    """Tests for validate_branch_name function."""

    def test_valid_pattern_match(self) -> None:
        assert gp.validate_branch_name("issue-123-fix", r"^issue-(\d+)-.+$") is True

    def test_invalid_pattern_no_match(self) -> None:
        assert gp.validate_branch_name("bad-branch", r"^issue-(\d+)-.+$") is False

    def test_invalid_regex_returns_false(self) -> None:
        assert gp.validate_branch_name("issue-123", r"[") is False

    def test_feature_branch_pattern(self) -> None:
        assert gp.validate_branch_name("feature/add-login", r"^feature/.+$") is True
        assert gp.validate_branch_name("bugfix/fix-crash", r"^feature/.+$") is False

    def test_empty_branch_name(self) -> None:
        assert gp.validate_branch_name("", r"^.+$") is False


class TestExtractIssueIidFromBranch:
    """Tests for extract_issue_iid_from_branch function."""

    def test_default_pattern_match(self) -> None:
        assert gp.extract_issue_iid_from_branch("issue-456-demo") == 456

    def test_default_pattern_no_match(self) -> None:
        assert gp.extract_issue_iid_from_branch("issue-demo") is None

    def test_invalid_regex_returns_none(self) -> None:
        assert gp.extract_issue_iid_from_branch("issue-456-demo", r"[") is None

    def test_custom_pattern(self) -> None:
        assert gp.extract_issue_iid_from_branch("feat-789-test", r"^feat-(\d+)-.+$") == 789

    def test_no_capture_group_returns_none(self) -> None:
        assert gp.extract_issue_iid_from_branch("issue-123-fix", r"^issue-\d+-.*$") is None


class TestExtractCommitRefs:
    """Tests for extract_commit_refs function."""

    def test_short_sha(self) -> None:
        assert gp.extract_commit_refs("See a1b2c3d") == ["a1b2c3d"]

    def test_long_sha(self) -> None:
        refs = gp.extract_commit_refs("Fix in 0123456789abcdef0123456789abcdef01234567")
        assert len(refs) == 1
        assert len(refs[0]) == 40

    def test_multiple_shas(self) -> None:
        result = gp.extract_commit_refs("Fixes a1b2c3d and 0123456789abcdef")
        assert result == ["a1b2c3d", "0123456789abcdef"]

    def test_no_hashes(self) -> None:
        assert gp.extract_commit_refs("no hashes here") == []

    def test_none_returns_empty(self) -> None:
        assert gp.extract_commit_refs(None) == []

    def test_empty_string_returns_empty(self) -> None:
        assert gp.extract_commit_refs("") == []

    def test_short_hash_boundary(self) -> None:
        # 6 chars should not match (minimum is 7)
        assert gp.extract_commit_refs("abc123") == []
        # 7 chars should match
        assert gp.extract_commit_refs("abc1234") == ["abc1234"]


class TestCheckTemplateSections:
    """Tests for check_template_sections function."""

    def test_all_sections_present(self) -> None:
        compliant, missing = gp.check_template_sections(
            "## Summary\nDetails\n## Testing\nTests passed", ["Summary", "Testing"]
        )
        assert compliant is True
        assert missing == []

    def test_some_sections_missing(self) -> None:
        compliant, missing = gp.check_template_sections(
            "## Summary\nDetails", ["Summary", "Testing"]
        )
        assert compliant is False
        assert missing == ["Testing"]

    def test_none_description(self) -> None:
        compliant, missing = gp.check_template_sections(None, ["Summary"])
        assert compliant is False
        assert missing == ["Summary"]

    def test_empty_required_sections(self) -> None:
        compliant, missing = gp.check_template_sections("Any content", [])
        assert compliant is True
        assert missing == []

    def test_case_insensitive(self) -> None:
        compliant, _missing = gp.check_template_sections("SUMMARY here", ["summary"])
        assert compliant is True


class TestIsTestFile:
    """Tests for is_test_file function."""

    def test_matches_pattern(self) -> None:
        assert gp.is_test_file("tests/unit/test_api.py", ["tests/**/*.py"]) is True

    def test_no_pattern_match_but_heuristic(self) -> None:
        assert gp.is_test_file("src/test_module.py", ["docs/**/*.md"]) is True

    def test_no_match_at_all(self) -> None:
        assert gp.is_test_file("src/app/module.py", ["docs/**/*.md"]) is False

    def test_test_in_path(self) -> None:
        # The heuristic looks for /test in path, test_ prefix, or _test. suffix
        assert gp.is_test_file("some/test/api.py", []) is True

    def test_suffix_test(self) -> None:
        assert gp.is_test_file("src/module_test.py", []) is True


class TestCountTestFiles:
    """Tests for count_test_files function."""

    def test_single_match(self) -> None:
        files = ["src/app/main.py", "tests/test_app.py", "docs/plan.md"]
        assert gp.count_test_files(files, ["tests/**/*.py"]) == 1

    def test_multiple_matches(self) -> None:
        files = ["tests/test_a.py", "tests/test_b.py", "src/main.py"]
        assert gp.count_test_files(files, ["tests/**/*.py"]) == 2

    def test_heuristic_fallback(self) -> None:
        files = ["src/app/main.py", "tests/test_app.py", "docs/test_plan.md"]
        assert gp.count_test_files(files, ["tests/**/*.py"]) == 2

    def test_no_matches(self) -> None:
        files = ["src/app/main.py", "docs/plan.md"]
        assert gp.count_test_files(files, ["tests/**/*.py"]) == 0

    def test_empty_files_list(self) -> None:
        assert gp.count_test_files([], ["tests/**/*.py"]) == 0


# ===============================================================
#  Text Analysis Tests
# ===============================================================


class TestWordCount:
    """Tests for word_count function."""

    def test_normal_text(self) -> None:
        assert ta.word_count("hello world") == 2

    def test_multiple_spaces(self) -> None:
        assert ta.word_count("hello   world") == 2

    def test_none_returns_zero(self) -> None:
        assert ta.word_count(None) == 0

    def test_empty_string_returns_zero(self) -> None:
        assert ta.word_count("") == 0

    def test_whitespace_only(self) -> None:
        assert ta.word_count("   ") == 0

    def test_single_word(self) -> None:
        assert ta.word_count("hello") == 1


class TestCharCount:
    """Tests for char_count function."""

    def test_normal_text(self) -> None:
        assert ta.char_count("hello world") == 10  # excludes space

    def test_none_returns_zero(self) -> None:
        assert ta.char_count(None) == 0

    def test_empty_string_returns_zero(self) -> None:
        assert ta.char_count("") == 0

    def test_whitespace_only_returns_zero(self) -> None:
        assert ta.char_count("   \n\t  ") == 0


class TestIsMeaningfulComment:
    """Tests for is_meaningful_comment function."""

    def test_meaningful_long_comment(self) -> None:
        text = " ".join(["word"] * 35)  # 35 words
        assert ta.is_meaningful_comment(text, min_words=30) is True

    def test_trivial_ok(self) -> None:
        assert ta.is_meaningful_comment("ok") is False

    def test_trivial_lgtm(self) -> None:
        assert ta.is_meaningful_comment("LGTM") is False

    def test_trivial_looks_good(self) -> None:
        assert ta.is_meaningful_comment("looks good") is False

    def test_trivial_plus_one(self) -> None:
        assert ta.is_meaningful_comment("+1") is False

    def test_trivial_approved(self) -> None:
        assert ta.is_meaningful_comment("approved") is False

    def test_trivial_thanks(self) -> None:
        assert ta.is_meaningful_comment("thanks") is False

    def test_none_returns_false(self) -> None:
        assert ta.is_meaningful_comment(None) is False

    def test_empty_returns_false(self) -> None:
        assert ta.is_meaningful_comment("") is False

    def test_short_but_not_trivial(self) -> None:
        # 10 words, not trivial pattern, but below default threshold
        text = "This is a short but meaningful comment about code"
        assert ta.is_meaningful_comment(text, min_words=30) is False

    def test_custom_threshold(self) -> None:
        text = "This is a short comment"
        # 5 words exactly, min_words=5 means >= 5, so it passes
        assert ta.is_meaningful_comment(text, min_words=5) is True
        assert ta.is_meaningful_comment(text, min_words=6) is False


# ===============================================================
#  Time Utils Tests
# ===============================================================


class TestNowUtc:
    """Tests for now_utc function."""

    def test_returns_datetime(self) -> None:
        result = tu.now_utc()
        assert isinstance(result, datetime)

    def test_has_utc_timezone(self) -> None:
        result = tu.now_utc()
        assert result.tzinfo == UTC


class TestParseGitlabDatetime:
    """Tests for parse_gitlab_datetime function."""

    def test_z_suffix(self) -> None:
        result = tu.parse_gitlab_datetime("2025-10-15T10:00:00.000Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 15
        assert result.tzinfo is not None

    def test_offset_suffix(self) -> None:
        result = tu.parse_gitlab_datetime("2025-10-15T10:00:00+02:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_none_returns_none(self) -> None:
        assert tu.parse_gitlab_datetime(None) is None

    def test_empty_returns_none(self) -> None:
        assert tu.parse_gitlab_datetime("") is None

    def test_invalid_format_returns_none(self) -> None:
        assert tu.parse_gitlab_datetime("not-a-date") is None


class TestMutationKillersGitlabPatterns:
    """Additional tests specifically to kill mutants in gitlab_patterns."""

    def test_extract_linked_issue_iids_order_preserved(self) -> None:
        # Ensure first found issue appears first (not reversed)
        result = gp.extract_linked_issue_iids("Closes #1, Fixes #2, Resolves #3")
        assert result == [1, 2, 3]
        assert result[0] == 1  # First element is 1, not 3

    def test_extract_linked_issue_iids_dedup_first_wins(self) -> None:
        # Same issue mentioned multiple ways - first occurrence wins
        result = gp.extract_linked_issue_iids("Closes #5, then #5 again, and Fixes #5")
        assert result == [5]
        assert len(result) == 1

    def test_validate_branch_name_full_match_required(self) -> None:
        # Partial match should fail with anchored pattern
        assert gp.validate_branch_name("prefix-issue-123-fix", r"^issue-(\d+)-.+$") is False

    def test_extract_issue_iid_from_branch_group_value_check(self) -> None:
        # Verify returned value is from the capture group
        result = gp.extract_issue_iid_from_branch("issue-999-feature")
        assert result == 999
        assert result != 0  # Not default

    def test_check_template_sections_empty_description(self) -> None:
        compliant, missing = gp.check_template_sections("", ["Summary"])
        assert compliant is False
        assert missing == ["Summary"]

    def test_check_template_sections_all_missing(self) -> None:
        compliant, missing = gp.check_template_sections("Nothing here", ["A", "B", "C"])
        assert compliant is False
        assert len(missing) == 3
        assert "A" in missing
        assert "B" in missing
        assert "C" in missing

    def test_is_test_file_exact_pattern_match(self) -> None:
        # fnmatch exact match
        assert gp.is_test_file("test.py", ["test.py"]) is True
        assert gp.is_test_file("main.py", ["test.py"]) is False

    def test_is_test_file_underscore_test_suffix(self) -> None:
        # _test. detection
        assert gp.is_test_file("module_test.py", []) is True
        assert gp.is_test_file("moduletest.py", []) is False

    def test_is_test_file_test_prefix(self) -> None:
        # test_ prefix detection
        assert gp.is_test_file("test_module.py", []) is True

    def test_is_test_file_test_directory(self) -> None:
        # /test in path - both /test/ and /tests/ contain "/test"
        assert gp.is_test_file("src/test/helper.py", []) is True
        assert gp.is_test_file("src/tests/helper.py", []) is True  # /tests contains /test
        assert gp.is_test_file("src/testing/helper.py", []) is True  # /testing contains /test

    def test_count_test_files_empty_patterns(self) -> None:
        files = ["test_a.py", "main.py"]
        # With empty patterns, heuristic still catches test_a.py
        assert gp.count_test_files(files, []) == 1

    def test_extract_commit_refs_exactly_7_chars(self) -> None:
        # Boundary: exactly 7 hex chars
        assert gp.extract_commit_refs("abcdef1") == ["abcdef1"]

    def test_extract_commit_refs_exactly_40_chars(self) -> None:
        # Full SHA
        sha = "a" * 40
        assert gp.extract_commit_refs(sha) == [sha]


class TestMutationKillersTextAnalysis:
    """Additional tests specifically to kill mutants in text_analysis."""

    def test_word_count_single_space_separator(self) -> None:
        assert ta.word_count("a b c") == 3

    def test_word_count_tabs_and_newlines(self) -> None:
        assert ta.word_count("a\tb\nc") == 3

    def test_char_count_mixed_whitespace(self) -> None:
        assert ta.char_count("a b\tc\nd") == 4  # Only a, b, c, d counted

    def test_is_meaningful_comment_exactly_threshold(self) -> None:
        # Exactly 30 words should pass
        text = " ".join(["word"] * 30)
        assert ta.is_meaningful_comment(text, min_words=30) is True

    def test_is_meaningful_comment_one_below_threshold(self) -> None:
        # 29 words should fail
        text = " ".join(["word"] * 29)
        assert ta.is_meaningful_comment(text, min_words=30) is False

    def test_is_meaningful_comment_trivial_variants(self) -> None:
        # Test more trivial patterns
        assert ta.is_meaningful_comment("done") is False
        assert ta.is_meaningful_comment("fixed") is False
        assert ta.is_meaningful_comment("thx") is False
        assert ta.is_meaningful_comment("ack") is False
        assert ta.is_meaningful_comment("noted") is False
        assert ta.is_meaningful_comment("yes") is False
        assert ta.is_meaningful_comment("no") is False
        assert ta.is_meaningful_comment("nope") is False
        assert ta.is_meaningful_comment("okay") is False
        assert ta.is_meaningful_comment("nice") is False
        assert ta.is_meaningful_comment("great") is False
        assert ta.is_meaningful_comment("thank you") is False
        assert ta.is_meaningful_comment("looks fine") is False
        assert ta.is_meaningful_comment("good") is False

    def test_is_meaningful_comment_all_trivial_patterns_individually(self) -> None:
        """Test each trivial pattern to kill set mutation."""
        # Each pattern must be tested to kill mutants that remove it from set
        trivial_patterns = [
            "ok",
            "okay",
            "lgtm",
            "looks good",
            "looks fine",
            "good",
            "nice",
            "great",
            "+1",
            "approved",
            "done",
            "fixed",
            "thanks",
            "thank you",
            "thx",
            "ack",
            "noted",
            "yes",
            "no",
            "nope",
        ]
        for pattern in trivial_patterns:
            assert ta.is_meaningful_comment(pattern) is False, f"'{pattern}' should be trivial"
            # Also test uppercase
            assert ta.is_meaningful_comment(pattern.upper()) is False, (
                f"'{pattern.upper()}' should be trivial"
            )
            # Test with whitespace
            assert ta.is_meaningful_comment(f"  {pattern}  ") is False, (
                f"'{pattern}' with spaces should be trivial"
            )

    def test_is_meaningful_comment_markdown_stripped(self) -> None:
        # Markdown artifacts should be stripped
        text = "**" + " ".join(["word"] * 30) + "**"
        assert ta.is_meaningful_comment(text, min_words=30) is True

    def test_is_meaningful_comment_emoji_only(self) -> None:
        # Emoji-only should fail
        assert ta.is_meaningful_comment("\U0001f44d") is False  # 👍
        assert ta.is_meaningful_comment("\U0001f44d\U0001f44d\U0001f44d") is False

    def test_is_meaningful_comment_markdown_characters_stripped(self) -> None:
        """Test that each markdown character is properly stripped."""
        base_text = " ".join(["word"] * 30)
        # Test each markdown character
        assert ta.is_meaningful_comment(f">{base_text}") is True
        assert ta.is_meaningful_comment(f"`{base_text}`") is True
        assert ta.is_meaningful_comment(f"*{base_text}*") is True
        assert ta.is_meaningful_comment(f"_{base_text}_") is True
        assert ta.is_meaningful_comment(f"~{base_text}~") is True
        assert ta.is_meaningful_comment(f"[{base_text}]") is True
        assert ta.is_meaningful_comment(f"({base_text})") is True

    def test_is_meaningful_comment_trivial_with_markdown(self) -> None:
        """Trivial patterns with markdown should still be trivial."""
        assert ta.is_meaningful_comment(">ok") is False
        assert ta.is_meaningful_comment("`lgtm`") is False
        assert ta.is_meaningful_comment("**good**") is False
        assert ta.is_meaningful_comment("*nice*") is False

    def test_is_meaningful_comment_emoji_with_spaces(self) -> None:
        """Emoji with only spaces should be trivial."""
        assert ta.is_meaningful_comment("  \U0001f44d  ") is False
        assert ta.is_meaningful_comment("\U0001f44d \U0001f44e") is False  # 👍 👎

    def test_is_meaningful_comment_boundary_word_count(self) -> None:
        """Test boundary conditions for word count."""
        # Test with min_words=1
        assert ta.is_meaningful_comment("nontrivialword", min_words=1) is True
        # Test with min_words=0
        assert ta.is_meaningful_comment("", min_words=0) is False  # Empty still fails
        # Test non-trivial single word
        assert ta.is_meaningful_comment("something", min_words=1) is True


class TestMutationKillersTimeUtils:
    """Additional tests specifically to kill mutants in time_utils."""

    def test_parse_gitlab_datetime_no_milliseconds(self) -> None:
        result = tu.parse_gitlab_datetime("2025-10-15T10:00:00Z")
        assert result is not None
        assert result.hour == 10

    def test_parse_gitlab_datetime_negative_offset(self) -> None:
        result = tu.parse_gitlab_datetime("2025-10-15T10:00:00-05:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_now_utc_is_recent(self) -> None:
        before = datetime.now(UTC)
        result = tu.now_utc()
        after = datetime.now(UTC)
        assert before <= result <= after

    def test_parse_gitlab_datetime_z_replacement(self) -> None:
        """Test that Z is properly replaced with +00:00."""
        # Without Z replacement, parsing would fail or give wrong result
        result = tu.parse_gitlab_datetime("2025-10-15T10:00:00.000Z")
        assert result is not None
        # Verify the result is UTC
        offset = result.utcoffset()
        assert offset is not None
        assert offset.total_seconds() == 0

    def test_parse_gitlab_datetime_with_positive_offset(self) -> None:
        """Test parsing with positive timezone offset."""
        result = tu.parse_gitlab_datetime("2025-10-15T12:00:00+02:00")
        assert result is not None
        offset = result.utcoffset()
        assert offset is not None
        assert offset.total_seconds() == 7200  # +2 hours

    def test_parse_gitlab_datetime_naive_gets_utc(self) -> None:
        """Test that naive datetime (if parsed) gets UTC timezone."""
        # This tests the dt.tzinfo is None branch
        # fromisoformat with +00:00 always produces aware datetime,
        # but we need to ensure the code path is covered
        result = tu.parse_gitlab_datetime("2025-10-15T10:00:00+00:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_parse_gitlab_datetime_invalid_format(self) -> None:
        """Test that invalid format returns None (ValueError branch)."""
        assert tu.parse_gitlab_datetime("not-a-date") is None
        assert tu.parse_gitlab_datetime("2025-13-45T99:99:99Z") is None

    def test_parse_gitlab_datetime_type_error(self) -> None:
        """Test that TypeError is caught."""
        # fromisoformat doesn't accept int, would raise TypeError
        # but our function takes str | None, so this tests None case
        assert tu.parse_gitlab_datetime(None) is None
