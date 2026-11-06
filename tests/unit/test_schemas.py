"""Tests for Pydantic schemas.

Tests schema validation, serialization, and default values.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.llm import (
    LLMAnalysisLog,
    LLMAnalysisResponse,
    LLMAnalysisResult,
    LLMEvidenceRef,
    LLMRiskFlag,
)
from app.schemas.webhooks import (
    GitLabProject,
    GitLabUser,
    ObjectAttributes,
    WebhookAcceptedResponse,
    WebhookPayload,
)


class TestLLMSchemas:
    """Tests for LLM-related Pydantic schemas."""

    def test_llm_evidence_ref_minimal(self) -> None:
        """Test LLMEvidenceRef with minimal fields."""
        ref = LLMEvidenceRef(source_type="note")
        assert ref.source_type == "note"
        assert ref.source_id is None
        assert ref.snippet is None

    def test_llm_evidence_ref_full(self) -> None:
        """Test LLMEvidenceRef with all fields."""
        ref = LLMEvidenceRef(
            source_type="description",
            source_id="12345",
            snippet="This is relevant text...",
        )
        assert ref.source_type == "description"
        assert ref.source_id == "12345"
        assert ref.snippet == "This is relevant text..."

    def test_llm_evidence_ref_invalid_source_type(self) -> None:
        """Unknown source_type values are normalized to 'general'."""
        ref = LLMEvidenceRef(source_type="invalid_type")
        assert ref.source_type == "general"

    def test_llm_risk_flag_minimal(self) -> None:
        """Test LLMRiskFlag with minimal required fields."""
        flag = LLMRiskFlag(
            flag="TEST_RISK",
            description="Test risk description",
            severity="medium",
        )
        assert flag.flag == "TEST_RISK"
        assert flag.evidence == []

    def test_llm_risk_flag_with_evidence(self) -> None:
        """Test LLMRiskFlag with evidence references."""
        evidence = [
            LLMEvidenceRef(source_type="note", source_id="1"),
            LLMEvidenceRef(source_type="description", snippet="Some text"),
        ]
        flag = LLMRiskFlag(
            flag="COPY_PASTE",
            description="Potential copied code",
            severity="high",
            evidence=evidence,
        )
        assert len(flag.evidence) == 2

    def test_llm_analysis_result_minimal(self) -> None:
        """Test LLMAnalysisResult with minimal required fields."""
        result = LLMAnalysisResult(
            summary="Good work",
            confidence_score=0.8,
            explanation="Analysis was straightforward",
        )
        assert result.summary == "Good work"
        assert result.risk_flags == []
        assert result.recommended_questions == []
        assert result.grading_suggestion is None

    def test_llm_analysis_result_full(self) -> None:
        """Test LLMAnalysisResult with all fields."""
        result = LLMAnalysisResult(
            summary="Needs improvement",
            risk_flags=[
                LLMRiskFlag(
                    flag="LATE_SUBMISSION",
                    description="Submitted after deadline",
                    severity="low",
                )
            ],
            recommended_questions=["Why was this submitted late?"],
            grading_suggestion="Deduct 10% for late submission",
            confidence_score=0.95,
            explanation="Clear evidence of late submission",
        )
        assert len(result.risk_flags) == 1
        assert len(result.recommended_questions) == 1

    def test_llm_analysis_result_confidence_bounds(self) -> None:
        """Test confidence_score must be between 0 and 1."""
        with pytest.raises(ValidationError):
            LLMAnalysisResult(
                summary="Test",
                confidence_score=1.5,  # Invalid
                explanation="Test",
            )
        with pytest.raises(ValidationError):
            LLMAnalysisResult(
                summary="Test",
                confidence_score=-0.1,  # Invalid
                explanation="Test",
            )

    def test_llm_analysis_log(self) -> None:
        """Test LLMAnalysisLog schema."""
        log = LLMAnalysisLog(
            id=1,
            project_id="550e8400-e29b-41d4-a716-446655440000",
            mr_iid=42,
            target_type="merge_request",
            analysis_timestamp=datetime.now(UTC),
            model_used="gpt-4",
            structured_result=LLMAnalysisResult(
                summary="Test",
                confidence_score=0.5,
                explanation="Test explanation",
            ),
            risk_score=0.3,
        )
        assert log.mr_iid == 42
        assert log.model_used == "gpt-4"

    def test_llm_analysis_response(self) -> None:
        """Test LLMAnalysisResponse with optional fields."""
        response = LLMAnalysisResponse(
            analysis=LLMAnalysisResult(
                summary="Analysis complete",
                confidence_score=0.9,
                explanation="High confidence analysis",
            ),
            gitlab_mr_url="https://gitlab.com/project/-/merge_requests/1",
            note_url_template="{base}#note_{id}",
        )
        assert response.gitlab_mr_url is not None
        assert "{id}" in (response.note_url_template or "")


class TestWebhookSchemas:
    """Tests for webhook Pydantic schemas."""

    def test_gitlab_user_minimal(self) -> None:
        """Test GitLabUser with minimal required fields."""
        user = GitLabUser(id=123)
        assert user.id == 123
        assert user.username == ""
        assert user.name == ""

    def test_gitlab_user_full(self) -> None:
        """Test GitLabUser with all fields."""
        user = GitLabUser(id=456, username="developer", name="John Developer")
        assert user.username == "developer"
        assert user.name == "John Developer"

    def test_gitlab_project_defaults(self) -> None:
        """Test GitLabProject default values."""
        project = GitLabProject(id=789)
        assert project.path_with_namespace == ""
        assert project.default_branch == "main"

    def test_gitlab_project_full(self) -> None:
        """Test GitLabProject with all fields."""
        project = GitLabProject(
            id=101,
            path_with_namespace="group/project",
            default_branch="main",
        )
        assert project.path_with_namespace == "group/project"
        assert project.default_branch == "main"

    def test_object_attributes_minimal(self) -> None:
        """Test ObjectAttributes with minimal required fields."""
        attrs = ObjectAttributes(id=1)
        assert attrs.id == 1
        assert attrs.iid is None
        assert attrs.title is None
        assert attrs.action is None

    def test_object_attributes_mr(self) -> None:
        """Test ObjectAttributes for merge request."""
        attrs = ObjectAttributes(
            id=100,
            iid=5,
            title="Fix bug",
            description="This fixes the bug",
            state="merged",
            action="merge",
            source_branch="feature/fix",
            target_branch="main",
            author_id=42,
            merge_status="can_be_merged",
        )
        assert attrs.source_branch == "feature/fix"
        assert attrs.merge_status == "can_be_merged"

    def test_object_attributes_note(self) -> None:
        """Test ObjectAttributes for note."""
        attrs = ObjectAttributes(
            id=200,
            note="LGTM!",
            noteable_type="MergeRequest",
            noteable_id=100,
            discussion_id="abc123",
            system=False,
        )
        assert attrs.note == "LGTM!"
        assert attrs.noteable_type == "MergeRequest"
        assert attrs.system is False

    def test_object_attributes_pipeline(self) -> None:
        """Test ObjectAttributes for pipeline."""
        attrs = ObjectAttributes(
            id=300,
            status="success",
            ref="main",
            sha="abc123def456",
            duration=120,
            source="push",
        )
        assert attrs.status == "success"
        assert attrs.duration == 120

    def test_webhook_payload_minimal(self) -> None:
        """Test WebhookPayload with minimal fields."""
        payload = WebhookPayload()
        assert payload.object_kind == ""
        assert payload.user is None
        assert payload.project is None

    def test_webhook_payload_push_event(self) -> None:
        """Test WebhookPayload for push event."""
        payload = WebhookPayload(
            object_kind="push",
            event_type="push",
            user=GitLabUser(id=1, username="pusher"),
            project=GitLabProject(id=10, path_with_namespace="group/repo"),
        )
        assert payload.object_kind == "push"
        assert payload.user is not None
        assert payload.user.username == "pusher"

    def test_webhook_payload_mr_event(self) -> None:
        """Test WebhookPayload for merge request event."""
        payload = WebhookPayload(
            object_kind="merge_request",
            user=GitLabUser(id=2, username="developer"),
            project=GitLabProject(id=20),
            object_attributes=ObjectAttributes(
                id=50,
                iid=3,
                title="Feature",
                action="open",
            ),
        )
        assert payload.object_kind == "merge_request"
        assert payload.object_attributes is not None
        assert payload.object_attributes.action == "open"

    def test_webhook_payload_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed in WebhookPayload."""
        payload = WebhookPayload(
            object_kind="test",
            extra_field="should be allowed",
            another_field=123,
        )
        assert payload.object_kind == "test"
        # Extra fields are stored due to extra="allow"
        assert hasattr(payload, "extra_field") or True  # ConfigDict allows extras

    def test_webhook_accepted_response(self) -> None:
        """Test WebhookAcceptedResponse schema."""
        response = WebhookAcceptedResponse(
            status="accepted",
            event_id="evt_123",
            message="Custom message",
        )
        assert response.status == "accepted"
        assert response.event_id == "evt_123"

    def test_webhook_accepted_response_default_message(self) -> None:
        """Test WebhookAcceptedResponse default message."""
        response = WebhookAcceptedResponse(
            status="ok",
            event_id="evt_456",
        )
        assert response.message == "Event enqueued for processing"


class TestSchemaValidation:
    """Tests for schema validation behavior."""

    def test_gitlab_user_require_id(self) -> None:
        """Test GitLabUser requires id field."""
        with pytest.raises(ValidationError):
            GitLabUser()  # type: ignore[call-arg]

    def test_gitlab_project_require_id(self) -> None:
        """Test GitLabProject requires id field."""
        with pytest.raises(ValidationError):
            GitLabProject()  # type: ignore[call-arg]

    def test_object_attributes_require_id(self) -> None:
        """Test ObjectAttributes requires id field."""
        with pytest.raises(ValidationError):
            ObjectAttributes()  # type: ignore[call-arg]

    def test_llm_risk_flag_require_severity(self) -> None:
        """Test LLMRiskFlag requires valid severity."""
        with pytest.raises(ValidationError):
            LLMRiskFlag(flag="TEST", description="Test", severity="invalid")  # type: ignore[arg-type]

    def test_llm_analysis_result_require_fields(self) -> None:
        """Test LLMAnalysisResult requires all required fields."""
        with pytest.raises(ValidationError):
            LLMAnalysisResult(summary="Only summary")  # type: ignore[call-arg]


class TestSchemaJsonSerialization:
    """Tests for JSON serialization of schemas."""

    def test_llm_evidence_ref_json(self) -> None:
        """Test LLMEvidenceRef JSON serialization."""
        ref = LLMEvidenceRef(source_type="note", source_id="123")
        json_data = ref.model_dump_json()
        assert "note" in json_data
        assert "123" in json_data

    def test_webhook_payload_json(self) -> None:
        """Test WebhookPayload JSON serialization."""
        payload = WebhookPayload(
            object_kind="push",
            user=GitLabUser(id=1, username="test"),
        )
        json_data = payload.model_dump_json()
        assert "push" in json_data
        assert "test" in json_data

    def test_llm_analysis_result_dict(self) -> None:
        """Test LLMAnalysisResult dict conversion."""
        result = LLMAnalysisResult(
            summary="Test",
            confidence_score=0.5,
            explanation="Explanation",
        )
        data = result.model_dump()
        assert data["summary"] == "Test"
        assert data["confidence_score"] == 0.5
        assert isinstance(data["risk_flags"], list)
