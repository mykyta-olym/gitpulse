"""Comprehensive tests for the LLM module: schema validation, redaction, and service."""

import pytest
from pydantic import ValidationError

from app.schemas.llm import (
    LLMAnalysisResponse,
    LLMAnalysisResult,
    LLMEvidenceRef,
)
from app.services.llm.redaction import RedactionService


class TestLLMSchemaValidation:
    """Test that schema validation rejects non-conforming model output."""

    def test_valid_analysis_result(self) -> None:
        """A fully valid result should parse without error."""
        data = {
            "summary": "The MR discussion shows good collaboration.",
            "risk_flags": [
                {
                    "flag": "low_effort_review",
                    "description": "Reviewer only wrote 'LGTM'",
                    "severity": "medium",
                    "evidence": [{"source_type": "note", "source_id": "12345", "snippet": "LGTM"}],
                }
            ],
            "recommended_questions": ["Ask reviewer to elaborate on what they tested."],
            "grading_suggestion": "Consider minor deduction for low-effort review.",
            "confidence_score": 0.85,
            "explanation": "High confidence due to clear evidence of LGTM-only comment.",
        }
        result = LLMAnalysisResult(**data)
        assert result.confidence_score == 0.85
        assert len(result.risk_flags) == 1
        assert result.risk_flags[0].evidence[0].source_id == "12345"

    def test_missing_required_fields(self) -> None:
        """Missing confidence_score should fail validation."""
        data = {
            "summary": "Summary",
            "explanation": "Explanation",
            # Missing confidence_score
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMAnalysisResult(**data)
        assert "confidence_score" in str(exc_info.value)

    def test_confidence_score_out_of_range(self) -> None:
        """confidence_score must be 0.0 to 1.0."""
        data = {
            "summary": "Summary",
            "risk_flags": [],
            "recommended_questions": [],
            "confidence_score": 1.5,  # Invalid: > 1.0
            "explanation": "Explanation",
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMAnalysisResult(**data)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_invalid_severity_literal(self) -> None:
        """severity must be 'low', 'medium', or 'high'."""
        data = {
            "summary": "Summary",
            "risk_flags": [
                {
                    "flag": "test_flag",
                    "description": "Test",
                    "severity": "critical",  # Invalid
                    "evidence": [],
                }
            ],
            "recommended_questions": [],
            "confidence_score": 0.5,
            "explanation": "Test",
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMAnalysisResult(**data)
        assert "severity" in str(exc_info.value).lower()

    def test_invalid_source_type_literal(self) -> None:
        """Unknown source_type values are normalized to 'general' by the validator."""
        data = {
            "summary": "Summary",
            "risk_flags": [
                {
                    "flag": "test_flag",
                    "description": "Test",
                    "severity": "low",
                    "evidence": [
                        {
                            "source_type": "unknown_source",
                            "source_id": "abc123",
                        }  # Invalid source_type
                    ],
                }
            ],
            "recommended_questions": [],
            "confidence_score": 0.5,
            "explanation": "Test",
        }
        result = LLMAnalysisResult(**data)
        # Unknown source types get normalized to "general"
        assert result.risk_flags[0].evidence[0].source_type == "general"

    def test_evidence_ref_optional_fields(self) -> None:
        """source_id and snippet are optional."""
        evidence = LLMEvidenceRef(source_type="general")
        assert evidence.source_id is None
        assert evidence.snippet is None

    def test_response_model_with_urls(self) -> None:
        """Test the API response model that includes URL templates."""
        analysis = LLMAnalysisResult(
            summary="Test",
            risk_flags=[],
            recommended_questions=[],
            confidence_score=0.8,
            explanation="Test explanation",
        )
        response = LLMAnalysisResponse(
            analysis=analysis,
            gitlab_mr_url="https://gitlab.example.com/group/project/-/merge_requests/42",
            note_url_template="https://gitlab.example.com/group/project/-/merge_requests/42#note_{id}",
        )
        assert response.note_url_template is not None
        assert response.gitlab_mr_url is not None
        assert "{id}" in response.note_url_template
        assert response.gitlab_mr_url.endswith("/42")


class TestRedactionService:
    """Test that all sensitive data is properly redacted."""

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

    def test_redact_bearer_token(self) -> None:
        text = (
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        )
        redacted = RedactionService.redact(text)
        assert "<BEARER_TOKEN_REDACTED>" in redacted
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted

    def test_redact_generic_secret(self) -> None:
        text = "api_key = '12345678abcdef12345678abcdef12'"
        redacted = RedactionService.redact(text)
        assert "<GENERIC_SECRET_REDACTED>" in redacted
        assert "12345678abcdef12345678abcdef12" not in redacted

    def test_redact_long_hex(self) -> None:
        # SHA256-like hash
        text = "Commit hash: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        redacted = RedactionService.redact(text)
        assert "<LONG_HEX_REDACTED>" in redacted

    def test_minimize_mr_context_with_note_ids(self) -> None:
        """Test that context includes Note IDs for evidence tracking."""
        title = "Fix for issue #10"
        desc = "This fixes the bug reported by test@example.com"
        comments = [
            {
                "id": "98765",
                "body": "Here is the token: glpat_placeholder_token",
                "author": "User1",
                "created_at": "2026-01-31T10:00:00Z",
            },
            {
                "id": "98766",
                "body": "LGTM",
                "author": "User2",
                "created_at": "2026-01-31T11:00:00Z",
            },
        ]
        files = ["src/main.py", "README.md"]

        context = RedactionService.minimize_mr_context(title, desc, comments, files)

        # Check PII is redacted
        assert "test@example.com" not in context
        assert "token_prefix_" not in context

        # Check structure for evidence tracking
        assert "--- Note ID: 98765 ---" in context
        assert "--- Note ID: 98766 ---" in context
        assert "Author: Participant_1" in context  # Authors are anonymized for privacy
        assert "LGTM" in context  # Non-sensitive content preserved
        assert "src/main.py" in context

    def test_minimize_mr_context_empty_comments(self) -> None:
        """Handle MRs with no comments gracefully."""
        context = RedactionService.minimize_mr_context(
            title="Test MR", description="No description", comments=[], filenames=[]
        )
        assert "(No comments)" in context
        assert "MR Title: Test MR" in context


class TestLLMServiceSchemaEnforcement:
    """Test that the service properly rejects invalid LLM output."""

    def test_parse_valid_json_response(self) -> None:
        """Valid JSON matching schema should parse correctly."""
        # Note: We don't import LLMService here to avoid openai dependency in tests
        # Instead we just test the schema validation directly
        raw_json = """
        {
            "summary": "Good collaboration observed.",
            "risk_flags": [],
            "recommended_questions": ["How did you test this?"],
            "grading_suggestion": null,
            "confidence_score": 0.9,
            "explanation": "Clear communication throughout."
        }
        """
        import json

        parsed = json.loads(raw_json)
        result = LLMAnalysisResult(**parsed)
        assert result.confidence_score == 0.9

    def test_reject_invalid_json_structure(self) -> None:
        """Invalid JSON structure should raise ValidationError."""
        raw_json = """
        {
            "summary": "Test",
            "risk_flags": "should_be_array",
            "confidence_score": 0.5,
            "explanation": "Test"
        }
        """
        import json

        parsed = json.loads(raw_json)
        with pytest.raises(ValidationError):
            LLMAnalysisResult(**parsed)
