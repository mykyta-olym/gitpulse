from app.services.llm.redaction import RedactionService


class TestRedactionService:
    def test_redact_email(self) -> None:
        text = "Contact me at student@university.edu regarding the issue."
        redacted = RedactionService.redact(text)
        assert "<EMAIL_REDACTED>" in redacted
        assert "student@university.edu" not in redacted

    def test_redact_ipv4(self) -> None:
        text = "Server is at 192.168.1.50 please check."
        redacted = RedactionService.redact(text)
        assert "<IPV4_REDACTED>" in redacted
        assert "192.168.1.50" not in redacted

    def test_redact_gitlab_token(self) -> None:
        token = "glpat_placeholder_token"
        text = f"I accidentally committed {token} in the file."
        redacted = RedactionService.redact(text)
        assert "<GITLAB_TOKEN_REDACTED>" in redacted
        assert token not in redacted

    def test_redact_generic_secret(self) -> None:
        text = "api_key = '12345678abcdef12345678abcdef12'"
        redacted = RedactionService.redact(text)
        assert "<GENERIC_SECRET_REDACTED>" in redacted
        assert "12345678abcdef12345678abcdef12" not in redacted

    def test_redact_empty_string(self) -> None:
        """Test redacting empty string returns empty string."""
        assert RedactionService.redact("") == ""

    def test_redact_no_sensitive_data(self) -> None:
        """Test text without sensitive data is unchanged."""
        text = "This is normal text without any secrets."
        redacted = RedactionService.redact(text)
        assert redacted == text

    def test_redact_bearer_token(self) -> None:
        """Test Bearer token redaction."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        redacted = RedactionService.redact(text)
        assert "<BEARER_TOKEN_REDACTED>" in redacted
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted

    def test_redact_long_hex_sha256(self) -> None:
        """Test long hex string (like SHA256) redaction."""
        sha = "a" * 64
        text = f"Commit hash: {sha}"
        redacted = RedactionService.redact(text)
        assert "<LONG_HEX_REDACTED>" in redacted
        assert sha not in redacted

    def test_redact_password_pattern(self) -> None:
        """Test password pattern redaction."""
        text = "password: supersecretpassword123"
        redacted = RedactionService.redact(text)
        assert "<GENERIC_SECRET_REDACTED>" in redacted

    def test_redact_multiple_patterns(self) -> None:
        """Test multiple patterns in same text."""
        text = "Email: test@example.com, IP: 10.0.0.1, Token: glpat_placeholder_token"
        redacted = RedactionService.redact(text)
        assert "<EMAIL_REDACTED>" in redacted
        assert "<IPV4_REDACTED>" in redacted
        assert "<GITLAB_TOKEN_REDACTED>" in redacted

    def test_minimize_context(self) -> None:
        title = "Fix for issue #10"
        desc = "This fixes the bug reported by test@example.com"
        comments = [
            {
                "id": "1",
                "body": "Here is the token: glpat_placeholder_token",
                "author": "User1",
                "created_at": "2026-01-31",
            },
            {"id": "2", "body": "LGTM", "author": "User2", "created_at": "2026-01-31"},
        ]
        files = ["src/main.py", "README.md"]

        context = RedactionService.minimize_mr_context(title, desc, comments, files)

        assert "test@example.com" not in context
        assert "token_prefix_" not in context
        assert "src/main.py" in context
        assert "LGTM" in context
        assert "--- Note ID: 1 ---" in context
        assert "Author: Participant_1" in context  # Authors are anonymized for privacy

    def test_minimize_context_no_comments(self) -> None:
        """Test minimize_mr_context with no comments."""
        context = RedactionService.minimize_mr_context(
            title="Test MR",
            description="Description",
            comments=[],
            filenames=["file.py"],
        )
        assert "(No comments)" in context
        assert "file.py" in context

    def test_minimize_context_with_metadata(self) -> None:
        """Test minimize_mr_context with metadata."""
        metadata = {
            "state": "merged",
            "source_branch": "feature/test",
            "target_branch": "main",
            "empty_value": None,  # Should be skipped
        }
        context = RedactionService.minimize_mr_context(
            title="Test MR",
            description="Desc",
            comments=[],
            filenames=[],
            metadata=metadata,
        )
        assert "MR Metadata:" in context
        assert "state: merged" in context
        assert "source_branch: feature/test" in context
        assert "empty_value" not in context  # None values are skipped

    def test_minimize_context_redacts_metadata_and_filenames(self) -> None:
        """PII in a branch name (metadata) or file path must be redacted."""
        context = RedactionService.minimize_mr_context(
            title="Test MR",
            description="Desc",
            comments=[],
            filenames=["src/jane.doe@uni.edu/secret.py"],
            metadata={"source_branch": "fix-for-jane.doe@uni.edu"},
        )
        assert "jane.doe@uni.edu" not in context
        assert "<EMAIL_REDACTED>" in context

    def test_minimize_context_with_diffs(self) -> None:
        """Test minimize_mr_context with diffs."""
        diffs = [
            {"file_path": "src/app.py", "diff": "+line1\n-line2"},
            {"file_path": "README.md", "diff": "+updated docs"},
        ]
        context = RedactionService.minimize_mr_context(
            title="Test",
            description="Desc",
            comments=[],
            filenames=[],
            diffs=diffs,
        )
        assert "Diffs (truncated):" in context
        assert "--- src/app.py ---" in context
        assert "+line1" in context

    def test_minimize_context_diff_truncation(self) -> None:
        """Test diff truncation when exceeding max_diff_chars."""
        long_diff = "x" * 10000
        diffs = [{"file_path": "large.py", "diff": long_diff}]
        context = RedactionService.minimize_mr_context(
            title="Test",
            description="Desc",
            comments=[],
            filenames=[],
            diffs=diffs,
            max_diff_chars=100,
        )
        assert "...[truncated]" in context
        assert len(context) < len(long_diff)

    def test_minimize_context_empty_diff(self) -> None:
        """Test handling of empty diffs."""
        diffs = [
            {"file_path": "empty.py", "diff": ""},
            {"file_path": "valid.py", "diff": "+code"},
        ]
        context = RedactionService.minimize_mr_context(
            title="Test",
            description="Desc",
            comments=[],
            filenames=[],
            diffs=diffs,
        )
        assert "--- valid.py ---" in context
        # empty.py should be skipped since it has no diff content

    def test_minimize_context_author_anonymization(self) -> None:
        """Test that same author gets same anonymous label."""
        comments = [
            {"id": "1", "body": "First", "author": "JohnDoe", "created_at": "2026-01-01"},
            {"id": "2", "body": "Second", "author": "JaneDoe", "created_at": "2026-01-02"},
            {"id": "3", "body": "Third", "author": "JohnDoe", "created_at": "2026-01-03"},
        ]
        context = RedactionService.minimize_mr_context(
            title="Test",
            description="Desc",
            comments=comments,
            filenames=[],
        )
        # JohnDoe appears twice, should get Participant_1 both times
        assert context.count("Participant_1") == 2
        assert context.count("Participant_2") == 1
        # Original names should not appear
        assert "JohnDoe" not in context
        assert "JaneDoe" not in context

    def test_minimize_context_redacts_diff_file_path(self) -> None:
        """A diff's file_path header can embed PII and must be redacted, like
        the standalone filenames list."""
        diffs = [{"file_path": "reports/jane.doe@uni.edu/answer.py", "diff": "+code"}]
        context = RedactionService.minimize_mr_context(
            title="Test",
            description="Desc",
            comments=[],
            filenames=[],
            diffs=diffs,
        )
        assert "jane.doe@uni.edu" not in context
        assert "<EMAIL_REDACTED>" in context
        assert "+code" in context

    def test_minimize_context_diff_with_secrets(self) -> None:
        """Test that secrets in diffs are also redacted."""
        diffs = [{"file_path": "config.py", "diff": "+API_KEY = 'secret12345678'"}]
        context = RedactionService.minimize_mr_context(
            title="Test",
            description="Desc",
            comments=[],
            filenames=[],
            diffs=diffs,
        )
        assert "secret12345678" not in context
