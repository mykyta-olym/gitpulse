"""Tests for event pipeline enhancements: schemas, dedup, DLQ, replay, audit."""

import hashlib
import uuid
from datetime import UTC, datetime

from app.schemas.events import (
    DLQEventSummary,
    DLQListResponse,
    ReplayRequest,
    ReplayResponse,
    ResurrectResponse,
)
from app.schemas.webhooks import WebhookAcceptedResponse


class TestReplaySchemas:
    def test_replay_request_defaults(self) -> None:
        r = ReplayRequest(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2025, 1, 2, tzinfo=UTC),
        )
        assert r.project_id is None
        assert r.event_type is None
        assert r.limit == 1000

    def test_replay_request_with_filters(self) -> None:
        r = ReplayRequest(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2025, 1, 2, tzinfo=UTC),
            project_id=42,
            event_type="push",
            limit=50,
        )
        assert r.project_id == 42
        assert r.event_type == "push"

    def test_replay_response(self) -> None:
        r = ReplayResponse(replayed=3, event_ids=["a", "b", "c"])
        assert r.replayed == 3
        assert len(r.event_ids) == 3

    def test_resurrect_response(self) -> None:
        r = ResurrectResponse(event_id="abc", status="resurrected")
        assert r.status == "resurrected"


class TestDLQSchemas:
    def test_dlq_event_summary(self) -> None:
        s = DLQEventSummary(
            id=str(uuid.uuid4()),
            event_type="push",
            gitlab_project_id=123,
            dead_letter_at=datetime.now(UTC),
            dead_letter_reason="Max retries exceeded",
            retry_count=5,
            processing_error="some error",
        )
        assert s.retry_count == 5

    def test_dlq_event_summary_nullable(self) -> None:
        s = DLQEventSummary(
            id=str(uuid.uuid4()),
            event_type="push",
            gitlab_project_id=123,
            dead_letter_at=None,
            dead_letter_reason=None,
            retry_count=0,
            processing_error=None,
        )
        assert s.dead_letter_at is None

    def test_dlq_list_response(self) -> None:
        r = DLQListResponse(count=0, events=[])
        assert r.count == 0


class TestWebhookAcceptedResponse:
    def test_duplicate_response(self) -> None:
        r = WebhookAcceptedResponse(
            status="duplicate",
            event_id="test-uuid",
            message="Duplicate delivery ID",
        )
        assert r.status == "duplicate"

    def test_accepted_response(self) -> None:
        r = WebhookAcceptedResponse(
            status="accepted",
            event_id=str(uuid.uuid4()),
        )
        assert r.status == "accepted"
        assert r.message == "Event enqueued for processing"


# -- Payload hash computation (pure function, no structlog) --


def _compute_payload_hash(raw_body: bytes) -> str:
    return hashlib.sha256(raw_body).hexdigest()


class TestPayloadHash:
    def test_sha256_length(self) -> None:
        h = _compute_payload_hash(b'{"object_kind":"push"}')
        assert len(h) == 64

    def test_deterministic(self) -> None:
        body = b"test-body"
        assert _compute_payload_hash(body) == _compute_payload_hash(body)

    def test_different_bodies(self) -> None:
        h1 = _compute_payload_hash(b'{"a":1}')
        h2 = _compute_payload_hash(b'{"a":2}')
        assert h1 != h2

    def test_matches_hashlib(self) -> None:
        body = b"hello"
        assert _compute_payload_hash(body) == hashlib.sha256(body).hexdigest()


# -- Config feature flags --


class TestEventPipelineConfig:
    def test_feature_flag_exists(self) -> None:
        from app.config import Settings

        assert "feature_event_pipeline" in Settings.model_fields

    def test_dlq_max_retries_default(self) -> None:
        from app.config import Settings

        assert Settings.model_fields["dlq_max_retries"].default == 5


# -- WebhookEvent model fields --


class TestWebhookEventModel:
    def test_has_payload_hash(self) -> None:
        from app.models.webhook_event import WebhookEvent

        cols = {c.name for c in WebhookEvent.__table__.columns}
        assert "payload_hash" in cols

    def test_has_delivery_id(self) -> None:
        from app.models.webhook_event import WebhookEvent

        cols = {c.name for c in WebhookEvent.__table__.columns}
        assert "gitlab_delivery_id" in cols

    def test_has_dlq_fields(self) -> None:
        from app.models.webhook_event import WebhookEvent

        cols = {c.name for c in WebhookEvent.__table__.columns}
        assert "dead_letter_at" in cols
        assert "dead_letter_reason" in cols

    def test_has_replay_fields(self) -> None:
        from app.models.webhook_event import WebhookEvent

        cols = {c.name for c in WebhookEvent.__table__.columns}
        assert "replay_of_id" in cols
        assert "is_replayed" in cols


# -- AuditLog model --


class TestAuditLogModel:
    def test_has_required_fields(self) -> None:
        from app.models.audit_log import AuditLog

        cols = {c.name for c in AuditLog.__table__.columns}
        assert "action" in cols
        assert "actor" in cols
        assert "entity_type" in cols
        assert "entity_id" in cols
        assert "detail" in cols
        assert "correlation_id" in cols
        assert "timestamp" in cols

    def test_action_max_length(self) -> None:
        from sqlalchemy import String

        from app.models.audit_log import AuditLog

        action_col = AuditLog.__table__.c.action
        assert isinstance(action_col.type, String)
        assert action_col.type.length == 50


# -- Dedup key computation --


class TestDedupKeyComputation:
    """Test deterministic dedup key fallback logic (mirrors webhooks.py)."""

    def test_deterministic_dedup_key(self) -> None:
        event_type = "issue"
        project_id = 42
        obj_id = 100
        action = "open"
        updated = "2025-01-01T00:00:00Z"
        hash_input = f"{event_type}:{project_id}:{obj_id}:{action}:{updated}"
        key = hashlib.sha256(hash_input.encode()).hexdigest()
        assert len(key) == 64

    def test_different_inputs_different_keys(self) -> None:
        k1 = hashlib.sha256(b"issue:1:1:open:t1").hexdigest()
        k2 = hashlib.sha256(b"issue:1:1:close:t1").hexdigest()
        assert k1 != k2

    def test_stable_across_calls(self) -> None:
        inp = b"push:42:0::2025-01-01"
        assert hashlib.sha256(inp).hexdigest() == hashlib.sha256(inp).hexdigest()
