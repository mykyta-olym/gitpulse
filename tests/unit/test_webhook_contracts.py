"""Contract tests for GitLab webhook payloads.

These tests validate that our webhook handling code correctly processes
GitLab webhook payloads according to the official GitLab webhook schema.

Contract testing ensures:
1. Our code handles valid GitLab payloads correctly
2. Required fields are properly extracted
3. Backward compatibility when GitLab adds new fields
4. Schema validation catches malformed payloads early
"""

import json
import uuid
from pathlib import Path
from typing import Any, cast

import pytest
from jsonschema import Draft7Validator, ValidationError, validate

from app.api.webhooks import _inactive_project_webhook_response
from app.schemas.webhooks import (
    GitLabUser,
    ObjectAttributes,
    WebhookPayload,
)

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SCHEMAS_DIR = FIXTURES_DIR / "schemas"
PAYLOADS_DIR = FIXTURES_DIR / "payloads"


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON file."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_schema(event_type: str) -> dict[str, Any]:
    """Load JSON schema for event type."""
    return load_json(SCHEMAS_DIR / f"{event_type}.json")


def load_payload(event_type: str) -> dict[str, Any]:
    """Load sample payload for event type."""
    return load_json(PAYLOADS_DIR / f"{event_type}.json")


def test_inactive_project_webhook_response_is_ignored_not_enqueued() -> None:
    project_id = uuid.uuid4()

    response = _inactive_project_webhook_response(project_id)

    assert response.status == "ignored"
    assert response.event_id == str(project_id)
    assert "webhook ignored" in response.message


class TestWebhookSchemaValidity:
    """Test that our JSON schemas are valid Draft-7 schemas."""

    @pytest.mark.contract
    @pytest.mark.parametrize(
        "schema_file",
        list(SCHEMAS_DIR.glob("*.json")),
        ids=lambda p: p.stem,
    )
    def test_schema_is_valid_draft7(self, schema_file: Path) -> None:
        """Verify each schema is a valid JSON Schema Draft-7."""
        schema = load_json(schema_file)
        # This will raise if schema is invalid
        Draft7Validator.check_schema(schema)


class TestSamplePayloadsMatchSchemas:
    """Test that our sample payloads match their respective schemas."""

    @pytest.mark.contract
    def test_push_event_matches_schema(self) -> None:
        """Push event payload matches schema."""
        schema = load_schema("push_event")
        payload = load_payload("push_event")
        validate(instance=payload, schema=schema)

    @pytest.mark.contract
    def test_merge_request_event_matches_schema(self) -> None:
        """Merge request event payload matches schema."""
        schema = load_schema("merge_request_event")
        payload = load_payload("merge_request_event")
        validate(instance=payload, schema=schema)

    @pytest.mark.contract
    def test_note_event_matches_schema(self) -> None:
        """Note event payload matches schema."""
        schema = load_schema("note_event")
        payload = load_payload("note_event_mr")
        validate(instance=payload, schema=schema)

    @pytest.mark.contract
    def test_pipeline_event_matches_schema(self) -> None:
        """Pipeline event payload matches schema."""
        schema = load_schema("pipeline_event")
        payload = load_payload("pipeline_event")
        validate(instance=payload, schema=schema)

    @pytest.mark.contract
    def test_issue_event_matches_schema(self) -> None:
        """Issue event payload matches schema."""
        schema = load_schema("issue_event")
        payload = load_payload("issue_event")
        validate(instance=payload, schema=schema)


class TestPydanticModelsParseSamplePayloads:
    """Test that our Pydantic models can parse sample payloads."""

    @pytest.mark.contract
    def test_parse_push_event(self) -> None:
        """Pydantic parses push event."""
        payload = load_payload("push_event")
        model = WebhookPayload.model_validate(payload)

        assert model.object_kind == "push"
        assert model.project is not None
        assert model.project.id == 123
        assert model.project.path_with_namespace == "zsi-2025/team-alpha-project"
        # Push events have user fields at top level, not in a user object
        # The model captures these as extra fields due to Config.extra = "allow"

    @pytest.mark.contract
    def test_parse_merge_request_event(self) -> None:
        """Pydantic parses merge request event."""
        payload = load_payload("merge_request_event")
        model = WebhookPayload.model_validate(payload)

        assert model.object_kind == "merge_request"
        assert model.event_type == "merge_request"
        assert model.project is not None
        assert model.project.id == 123
        assert model.object_attributes is not None
        assert model.object_attributes.id == 789
        assert model.object_attributes.iid == 5
        assert model.object_attributes.title == "Add user authentication module"
        assert model.object_attributes.state == "opened"
        assert model.object_attributes.action == "open"
        assert model.object_attributes.source_branch == "feature/user-auth"
        assert model.object_attributes.target_branch == "main"

    @pytest.mark.contract
    def test_parse_note_event(self) -> None:
        """Pydantic parses note event."""
        payload = load_payload("note_event_mr")
        model = WebhookPayload.model_validate(payload)

        assert model.object_kind == "note"
        assert model.event_type == "note"
        assert model.project is not None
        assert model.object_attributes is not None
        assert model.object_attributes.id == 1234
        assert model.object_attributes.note is not None
        assert "Great implementation" in model.object_attributes.note
        assert model.object_attributes.noteable_type == "MergeRequest"
        assert model.object_attributes.noteable_id == 789

    @pytest.mark.contract
    def test_parse_pipeline_event(self) -> None:
        """Pydantic parses pipeline event."""
        payload = load_payload("pipeline_event")
        model = WebhookPayload.model_validate(payload)

        assert model.object_kind == "pipeline"
        assert model.project is not None
        assert model.project.id == 123
        assert model.object_attributes is not None
        assert model.object_attributes.id == 456
        assert model.object_attributes.status == "success"
        assert model.object_attributes.ref == "feature/user-auth"

    @pytest.mark.contract
    def test_parse_issue_event(self) -> None:
        """Pydantic parses issue event."""
        payload = load_payload("issue_event")
        model = WebhookPayload.model_validate(payload)

        assert model.object_kind == "issue"
        assert model.event_type == "issue"
        assert model.project is not None
        assert model.project.id == 123
        assert model.object_attributes is not None
        assert model.object_attributes.id == 567
        assert model.object_attributes.iid == 15
        assert model.object_attributes.title == "Implement user authentication"
        assert model.object_attributes.state == "opened"


class TestSchemaEvolution:
    """Test backward compatibility with schema evolution."""

    @pytest.mark.contract
    def test_extra_fields_allowed(self) -> None:
        """Pydantic allows extra fields (forward compatibility)."""
        payload = load_payload("merge_request_event")
        # Add unknown field that GitLab might add in future
        payload["new_future_field"] = {"some": "data"}
        payload["object_attributes"]["another_new_field"] = "value"

        # Should not raise
        model = WebhookPayload.model_validate(payload)
        assert model.object_kind == "merge_request"

    @pytest.mark.contract
    def test_minimal_push_event(self) -> None:
        """Minimal push event with only required fields."""
        minimal = {
            "object_kind": "push",
            "event_name": "push",
            "before": "0" * 40,
            "after": "a" * 40,
            "ref": "refs/heads/main",
            "checkout_sha": "a" * 40,
            "user_id": 1,
            "user_name": "test",
            "user_email": "test@example.com",
            "user_avatar": "https://example.com/avatar.png",
            "project_id": 1,
            "project": {
                "id": 1,
                "name": "test",
                "web_url": "https://example.com",
                "git_ssh_url": "git@example.com:test.git",
                "git_http_url": "https://example.com/test.git",
                "namespace": "test",
                "path_with_namespace": "test/test",
                "default_branch": "main",
            },
            "commits": [],
            "total_commits_count": 0,
        }

        schema = load_schema("push_event")
        validate(instance=minimal, schema=schema)

        model = WebhookPayload.model_validate(minimal)
        assert model.object_kind == "push"

    @pytest.mark.contract
    def test_minimal_merge_request_event(self) -> None:
        """Minimal MR event with only required fields."""
        minimal = {
            "object_kind": "merge_request",
            "event_type": "merge_request",
            "user": {"id": 1, "name": "test", "username": "test"},
            "project": {
                "id": 1,
                "name": "test",
                "path_with_namespace": "test/test",
            },
            "object_attributes": {
                "id": 1,
                "iid": 1,
                "title": "Test MR",
                "state": "opened",
                "source_branch": "feature",
                "target_branch": "main",
                "source_project_id": 1,
                "target_project_id": 1,
                "author_id": 1,
                "created_at": "2025-01-30 00:00:00 UTC",
                "updated_at": "2025-01-30 00:00:00 UTC",
            },
        }

        schema = load_schema("merge_request_event")
        validate(instance=minimal, schema=schema)

        model = WebhookPayload.model_validate(minimal)
        assert model.object_kind == "merge_request"


class TestSchemaValidationErrors:
    """Test that schema validation correctly rejects invalid payloads."""

    @pytest.mark.contract
    def test_missing_object_kind_rejected(self) -> None:
        """Payload missing object_kind is rejected."""
        schema = load_schema("push_event")
        invalid = {"event_name": "push"}

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid, schema=schema)

        assert "object_kind" in str(exc_info.value)

    @pytest.mark.contract
    def test_invalid_object_kind_rejected(self) -> None:
        """Payload with wrong object_kind is rejected."""
        schema = load_schema("push_event")
        payload = load_payload("push_event")
        payload["object_kind"] = "merge_request"  # Wrong type

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=payload, schema=schema)

        assert "push" in str(exc_info.value) or "const" in str(exc_info.value)

    @pytest.mark.contract
    def test_invalid_sha_format_rejected(self) -> None:
        """Payload with invalid SHA format is rejected."""
        schema = load_schema("push_event")
        payload = load_payload("push_event")
        payload["after"] = "invalid-sha"  # Not 40 hex chars

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=payload, schema=schema)

        # Should mention pattern validation
        assert "pattern" in str(exc_info.value).lower() or "after" in str(exc_info.value)

    @pytest.mark.contract
    def test_missing_project_id_rejected(self) -> None:
        """Payload missing project.id is rejected."""
        schema = load_schema("merge_request_event")
        payload = load_payload("merge_request_event")
        del payload["project"]["id"]

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=payload, schema=schema)

        assert "id" in str(exc_info.value)


class TestWebhookPayloadExtraction:
    """Test extraction of key fields from webhook payloads."""

    @pytest.mark.contract
    def test_extract_project_gitlab_id(self) -> None:
        """Extract project GitLab ID for routing."""
        for event_type in [
            "push_event",
            "merge_request_event",
            "note_event_mr",
            "pipeline_event",
            "issue_event",
        ]:
            payload = load_payload(event_type)
            project_id = payload.get("project", {}).get("id")
            assert project_id == 123, f"Failed for {event_type}"

    @pytest.mark.contract
    def test_extract_user_info(self) -> None:
        """Extract user info for attribution."""
        mr_payload = load_payload("merge_request_event")
        user = GitLabUser.model_validate(mr_payload["user"])

        assert user.id == 42
        assert user.username == "jnovak"
        assert user.name == "Jan Novak"

    @pytest.mark.contract
    def test_extract_object_attributes(self) -> None:
        """Extract object_attributes for processing."""
        mr_payload = load_payload("merge_request_event")
        attrs = ObjectAttributes.model_validate(mr_payload["object_attributes"])

        assert attrs.id == 789
        assert attrs.iid == 5
        assert attrs.action == "open"
        assert attrs.source_branch == "feature/user-auth"

    @pytest.mark.contract
    def test_extract_commits_from_push(self) -> None:
        """Extract commit list from push event."""
        push_payload = load_payload("push_event")
        commits = push_payload.get("commits", [])

        assert len(commits) == 1
        commit = commits[0]
        assert commit["id"] == "a5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4"
        assert "Add user authentication module" in commit["message"]
        assert len(commit["added"]) == 3
        assert len(commit["modified"]) == 2
