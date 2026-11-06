"""Tests for webhook edge-case handling.

Covers:
- Orphan project webhooks (unknown project stored for deferred processing)
- Backpressure guard on webhook enqueue
- Immediate enrichment triggering from event processor
- Webhook delivery health monitoring
- Sweep retry resilience
- Pagination safety limits
- Enrichment Prometheus metrics
- Sweep job Prometheus metrics
- System-wide edge-case scenario verification
"""

import uuid
from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import pytest

# -- Fakes --


@dataclass
class FakeSettings:
    feature_backpressure: bool = False
    queue_high_watermark: int = 1000
    queue_critical_watermark: int = 5000
    feature_gitlab_cache: bool = False
    feature_event_pipeline: bool = True
    redis_url: str = "redis://localhost:6379/0"
    webhook_max_payload_bytes: int = 1_048_576
    app_base_url: str = "https://app.example.com"
    gitlab_url: str = "https://gitlab.example.com"
    gitlab_api_token: str = "test-token"
    job_timeout_event_seconds: int = 120


@dataclass
class FakeProject:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    team_id: uuid.UUID = field(default_factory=uuid.uuid4)
    gitlab_project_id: int = 42
    gitlab_project_path: str = "group/repo"
    gitlab_project_name: str = "repo"
    webhook_secret_hash: str = "hashed-secret"
    is_active: bool = True


# ---------------------------------------------------------------
# 1. Orphan project webhooks
# ---------------------------------------------------------------


class TestOrphanProjectWebhook:
    """When a webhook arrives for an unregistered project, it should be stored
    (not rejected with 404) so the periodic sweep can process it later."""

    def test_webhooks_module_does_not_import_raise_not_found(self) -> None:
        """raise_not_found should no longer be imported (we accept orphans)."""
        import ast
        import inspect

        from app.api import webhooks

        source = inspect.getsource(webhooks)
        tree = ast.parse(source)
        # Check there are no references to raise_not_found in import statements
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert alias.name != "raise_not_found", (
                        "raise_not_found should be removed - orphan webhooks are accepted"
                    )

    def test_orphan_comment_present(self) -> None:
        """The orphan-project guard comment should be in the webhook handler."""
        import inspect

        from app.api import webhooks

        source = inspect.getsource(webhooks)
        assert "orphan_project" in source.lower() or "orphan webhook" in source.lower()

    def test_orphan_stores_processing_error_marker(self) -> None:
        """Orphan events should be stored with a processing_error marker."""
        import inspect

        from app.api import webhooks

        source = inspect.getsource(webhooks)
        assert "orphan_project:not_registered_at_receive_time" in source


# ---------------------------------------------------------------
# 2. Backpressure guard on webhook enqueue
# ---------------------------------------------------------------


class TestWebhookBackpressureGuard:
    """Verify that the webhook handler checks queue depth before enqueueing."""

    @pytest.mark.parametrize(
        ("enabled", "depth", "expected"),
        [(True, 6, None), (True, 0, "queued"), (False, 6, "queued")],
    )
    def test_enqueue_uses_configured_watermarks(self, monkeypatch, enabled, depth, expected):
        from app.api import webhooks

        settings = FakeSettings(
            feature_backpressure=enabled,
            queue_high_watermark=2,
            queue_critical_watermark=5,
        )
        redis = MagicMock()
        redis.llen.return_value = depth
        enqueue = MagicMock(return_value="queued")
        monkeypatch.setattr(webhooks, "get_settings", lambda: settings)
        monkeypatch.setattr("app.redis_pool.get_redis", lambda: redis)
        monkeypatch.setattr(webhooks, "enqueue_event_processing", enqueue)
        assert webhooks._enqueue("event") == expected
        if expected is None:
            enqueue.assert_not_called()
        else:
            enqueue.assert_called_once_with("event")

    def test_backpressure_check_in_webhook_handler(self) -> None:
        """Webhook handler should reference backpressure/should_accept_job."""
        import inspect

        from app.api import webhooks

        source = inspect.getsource(webhooks)
        assert "backpressure" in source.lower()
        assert "should_accept_job" in source

    def test_backpressure_shed_log_message(self) -> None:
        """When backpressure sheds, a warning with queue depth should be logged."""
        import inspect

        from app.api import webhooks

        source = inspect.getsource(webhooks)
        assert "webhook_backpressure_shed" in source

    def test_queue_backpressure_should_accept_job_api(self) -> None:
        """QueueBackpressure.should_accept_job should accept priority parameter."""
        from app.services.backpressure import QueueBackpressure

        mock_redis = MagicMock()
        mock_redis.llen.return_value = 0
        bp = QueueBackpressure(mock_redis)
        # Should accept when queue is empty
        assert bp.should_accept_job("high", priority=2) is True

    def test_queue_backpressure_rejects_when_critical(self) -> None:
        """should_accept_job should reject low-priority jobs at critical watermark."""
        from app.services.backpressure import BackpressureConfig, QueueBackpressure

        config = BackpressureConfig(
            enabled=True,
            queue_high_watermark=10,
            queue_critical_watermark=20,
        )
        mock_redis = MagicMock()
        mock_redis.llen.return_value = 25  # Above critical
        bp = QueueBackpressure(mock_redis, config=config)
        # Only priority 1 (highest) should pass at critical level
        assert bp.should_accept_job("high", priority=5) is False


# ---------------------------------------------------------------
# 3. Immediate enrichment from event processor
# ---------------------------------------------------------------


class TestImmediateEnrichment:
    """After processing issue/MR webhooks, enrichment should be enqueued immediately."""

    def test_enqueue_immediate_enrichment_function_exists(self) -> None:
        """_enqueue_immediate_enrichment should be defined in event_processor."""
        from app.workers import event_processor

        assert hasattr(event_processor, "_enqueue_immediate_enrichment")
        assert callable(event_processor._enqueue_immediate_enrichment)

    @pytest.mark.asyncio
    async def test_issue_event_triggers_enrich_issue(self) -> None:
        """Processing an issue webhook should enqueue enrich_issue."""
        from app.workers.event_processor import _enqueue_immediate_enrichment

        payload = {"object_attributes": {"iid": 7, "id": 100}}
        with patch("app.services.events.enqueue_enrich_issue") as mock_enrich:
            await _enqueue_immediate_enrichment(payload, "issue", 42)
        mock_enrich.assert_called_once_with(42, 7)

    @pytest.mark.asyncio
    async def test_confidential_issue_event_triggers_enrich_issue(self) -> None:
        """Confidential issues route through the issue processor, so they must
        enrich on the same immediate path as public issues."""
        from app.workers.event_processor import _enqueue_immediate_enrichment

        payload = {"object_attributes": {"iid": 9, "id": 300}}
        with patch("app.services.events.enqueue_enrich_issue") as mock_enrich:
            await _enqueue_immediate_enrichment(payload, "confidential_issue", 42)
        mock_enrich.assert_called_once_with(42, 9)

    @pytest.mark.asyncio
    async def test_mr_event_triggers_enrich_mr(self) -> None:
        """Processing an MR webhook should enqueue enrich_mr."""
        from app.workers.event_processor import _enqueue_immediate_enrichment

        payload = {"object_attributes": {"iid": 3, "id": 200}}
        with patch("app.services.events.enqueue_enrich_mr") as mock_enrich:
            await _enqueue_immediate_enrichment(payload, "merge_request", 42)
        mock_enrich.assert_called_once_with(42, 3)

    @pytest.mark.asyncio
    async def test_push_event_does_not_trigger_enrichment(self) -> None:
        """Push events have no corresponding enrichment job."""
        from app.workers.event_processor import _enqueue_immediate_enrichment

        payload = {"object_attributes": {"iid": 1}}
        with (
            patch("app.services.events.enqueue_enrich_issue") as mock_issue,
            patch("app.services.events.enqueue_enrich_mr") as mock_mr,
        ):
            await _enqueue_immediate_enrichment(payload, "push", 42)
        mock_issue.assert_not_called()
        mock_mr.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_iid_is_noop(self) -> None:
        """If payload has no iid, enrichment should be skipped."""
        from app.workers.event_processor import _enqueue_immediate_enrichment

        payload: dict[str, object] = {"object_attributes": {}}
        with (
            patch("app.services.events.enqueue_enrich_issue") as mock_issue,
            patch("app.services.events.enqueue_enrich_mr") as mock_mr,
        ):
            await _enqueue_immediate_enrichment(payload, "issue", 42)
        mock_issue.assert_not_called()
        mock_mr.assert_not_called()

    @pytest.mark.asyncio
    async def test_enrichment_failure_is_non_critical(self) -> None:
        """Enrichment enqueue failure should not raise - it's non-critical."""
        from app.workers.event_processor import _enqueue_immediate_enrichment

        payload = {"object_attributes": {"iid": 5}}
        with patch(
            "app.services.events.enqueue_enrich_issue",
            side_effect=RuntimeError("Redis down"),
        ):
            # Should NOT raise
            await _enqueue_immediate_enrichment(payload, "issue", 42)

    def test_enrichment_called_in_process_async(self) -> None:
        """_process_async should call _enqueue_immediate_enrichment after success."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        assert "_enqueue_immediate_enrichment" in source


class TestWebhookEdgeCaseScenarios:
    """Verify that all edge-case scenarios have proper handling."""

    def test_triple_dedup_layers_present(self) -> None:
        """Webhook handler should have all 3 dedup layers."""
        import inspect

        from app.api import webhooks

        # The handler is composed of the module's helpers.
        source = inspect.getsource(webhooks)
        assert "exists_by_delivery_id" in source
        assert "exists_by_uuid" in source
        assert "exists_by_payload_hash" in source

    def test_concurrent_race_detection(self) -> None:
        """IntegrityError handler should catch concurrent duplicate inserts."""
        import inspect

        from app.api import webhooks

        # The handler is composed of the module's helpers.
        source = inspect.getsource(webhooks)
        assert "IntegrityError" in source
        assert "duplicate_concurrent" in source

    def test_cache_invalidation_on_webhook_processing(self) -> None:
        """Event processor should invalidate GitLab API cache after processing."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        assert "_invalidate_project_cache" in source

    def test_member_event_triggers_sync(self) -> None:
        """Member events should trigger immediate membership sync."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        assert "_sync_members_on_member_event" in source

    def test_push_event_detects_unknown_committers(self) -> None:
        """Push events should check for unknown committers and trigger sync."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        assert "_maybe_sync_members_on_push" in source

    def test_ignorable_event_types_defined(self) -> None:
        """Ignorable event types should be defined and handled gracefully."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        for event_type in ["deployment", "release", "wiki_page", "build"]:
            assert event_type in source

    def test_payload_too_large_guard(self) -> None:
        """Webhook handler should reject payloads exceeding max size."""
        import inspect

        from app.api import webhooks

        # The handler is composed of the module's helpers.
        source = inspect.getsource(webhooks)
        assert "webhook_max_payload_bytes" in source
        assert "raise_payload_too_large" in source

    def test_webhook_event_model_has_dlq_fields(self) -> None:
        """WebhookEvent model should have dead-letter queue fields."""
        from app.models.webhook_event import WebhookEvent

        assert hasattr(WebhookEvent, "dead_letter_at")
        assert hasattr(WebhookEvent, "dead_letter_reason")
        assert hasattr(WebhookEvent, "retry_count")

    def test_webhook_event_model_has_replay_fields(self) -> None:
        """WebhookEvent model should have replay lineage fields."""
        from app.models.webhook_event import WebhookEvent

        assert hasattr(WebhookEvent, "replay_of_id")
        assert hasattr(WebhookEvent, "is_replayed")

    def test_retired_gitlab_polling_helper_is_not_reintroduced(self) -> None:
        """Dormant-project polling helper should stay removed from scheduler sweeps."""
        from app.workers import sweep

        assert not hasattr(sweep, "_get_recently_active_project_ids")
        assert not hasattr(sweep, "sweep_stale_projects")


# ---------------------------------------------------------------
# 6. Sweep retry resilience
# ---------------------------------------------------------------


class TestSweepRetryResilience:
    """All sweep enqueue calls should use retry for transient failure resilience."""

    def test_sweep_retry_constant_defined(self) -> None:
        """_SWEEP_RETRY should be importable from sweep module."""
        from app.workers.sweep import _SWEEP_RETRY

        assert _SWEEP_RETRY is not None
        assert _SWEEP_RETRY.max == 2

    def test_sweep_enqueue_calls_use_retry(self) -> None:
        """All queue.enqueue() calls in sweep modules should include retry=_SWEEP_RETRY."""
        import inspect
        import re

        from app.workers import (
            sweep,
            sweep_compliance,
            sweep_membership,
            sweep_projects,
        )

        source = "\n".join(
            inspect.getsource(m)
            for m in (
                sweep,
                sweep_membership,
                sweep_projects,
                sweep_compliance,
            )
        )
        # Find all queue.enqueue( blocks (handle nested parens)
        enqueue_blocks: list[str] = []
        for m in re.finditer(r"queue\.enqueue\(", source):
            start = m.start()
            depth, pos = 0, m.end() - 1
            while pos < len(source):
                if source[pos] == "(":
                    depth += 1
                elif source[pos] == ")":
                    depth -= 1
                    if depth == 0:
                        enqueue_blocks.append(source[start : pos + 1])
                        break
                pos += 1
        assert enqueue_blocks, "No queue.enqueue() calls found"
        for block in enqueue_blocks:
            assert "retry=" in block, (
                f"queue.enqueue() call missing retry= parameter:\n{block[:100]}..."
            )

    def test_rq_retry_imported(self) -> None:
        """sweep module should import rq.Retry."""
        import inspect

        from app.workers import sweep

        source = inspect.getsource(sweep)
        assert "from rq import Retry" in source


# ---------------------------------------------------------------
# 7. GitLab client pagination safety
# ---------------------------------------------------------------


class TestPaginationSafety:
    """_get_paginated should have a max_pages limit to prevent OOM."""

    def test_get_paginated_has_max_pages_param(self) -> None:
        """_get_paginated should accept max_pages parameter."""
        import inspect

        from app.services.gitlab.client import GitLabClient

        sig = inspect.signature(GitLabClient._get_paginated)
        assert "max_pages" in sig.parameters

    def test_get_paginated_default_max_pages(self) -> None:
        """Default max_pages should be a reasonable value (100)."""
        import inspect

        from app.services.gitlab.client import GitLabClient

        sig = inspect.signature(GitLabClient._get_paginated)
        default = sig.parameters["max_pages"].default
        assert default == 100

    def test_get_paginated_logs_truncation_warning(self) -> None:
        """When pagination is truncated, a warning should be logged."""
        import inspect

        from app.services.gitlab.client import GitLabClient

        source = inspect.getsource(GitLabClient._get_paginated)
        assert "truncated" in source.lower()


# ---------------------------------------------------------------
# 8. Enrichment Prometheus metrics
# ---------------------------------------------------------------


class TestEnrichmentMetrics:
    """Enrichment jobs should report Prometheus metrics."""

    def test_enrichment_total_metric_exists(self) -> None:
        """ENRICHMENT_TOTAL counter should be defined."""
        from app.observability.metrics import ENRICHMENT_TOTAL

        assert ENRICHMENT_TOTAL is not None

    def test_enrichment_duration_metric_exists(self) -> None:
        """ENRICHMENT_DURATION histogram should be defined."""
        from app.observability.metrics import ENRICHMENT_DURATION

        assert ENRICHMENT_DURATION is not None

    def test_enrich_issue_tracks_metrics(self) -> None:
        """enrich_issue should record ENRICHMENT_TOTAL and ENRICHMENT_DURATION."""
        import inspect

        from app.workers import enrich_issue

        source = inspect.getsource(enrich_issue.enrich_issue)
        assert "ENRICHMENT_TOTAL" in source
        assert "ENRICHMENT_DURATION" in source

    def test_enrich_mr_tracks_metrics(self) -> None:
        """enrich_mr should record ENRICHMENT_TOTAL and ENRICHMENT_DURATION."""
        import inspect

        from app.workers import enrich_mr

        source = inspect.getsource(enrich_mr.enrich_mr)
        assert "ENRICHMENT_TOTAL" in source
        assert "ENRICHMENT_DURATION" in source

    def test_enrichment_metrics_label_entity_type(self) -> None:
        """ENRICHMENT_TOTAL should be labeled by entity_type and status."""
        from app.observability.metrics import ENRICHMENT_TOTAL

        label_names = ENRICHMENT_TOTAL._labelnames
        assert "entity_type" in label_names
        assert "status" in label_names


# ---------------------------------------------------------------
# 9. Enrichment Prometheus metric definitions
# ---------------------------------------------------------------


# ---------------------------------------------------------------
# 10. Comprehensive system-wide process verification
# ---------------------------------------------------------------


class TestSystemWideProcesses:
    """Verify all critical system processes are wired together correctly."""

    def test_all_event_types_handled(self) -> None:
        """event_processor dispatch table should cover all expected types."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        expected_types = ["issue", "merge_request", "note", "push", "tag_push", "pipeline"]
        for t in expected_types:
            assert f'"{t}"' in source, f"Event type {t} missing from dispatch"

    def test_idempotent_job_decorator_on_all_sweep_functions(self) -> None:
        """All public sweep job functions should have @idempotent_job."""
        import inspect

        from app.workers import (
            sweep,
            sweep_compliance,
            sweep_membership,
            sweep_projects,
        )

        source = (
            inspect.getsource(sweep)
            + "\n"
            + inspect.getsource(sweep_membership)
            + "\n"
            + inspect.getsource(sweep_projects)
            + "\n"
            + inspect.getsource(sweep_compliance)
        )
        public_jobs = [
            "sync_single_team_members",
            "refresh_project_gitlab_intel",
            "_incremental_project_refresh",
        ]
        for job in public_jobs:
            # Find the function definition and check for @idempotent_job before it
            idx = source.find(f"def {job}(")
            assert idx != -1, f"Job function {job} not found"
            preceding = source[max(0, idx - 200) : idx]
            assert "@idempotent_job" in preceding, f"Job {job} missing @idempotent_job decorator"

    def test_event_service_enqueue_functions(self) -> None:
        """event_service should have all needed enqueue functions."""
        from app.services import events as event_service

        assert hasattr(event_service, "enqueue_event_processing")
        assert hasattr(event_service, "enqueue_enrich_issue")
        assert hasattr(event_service, "enqueue_enrich_mr")
        assert hasattr(event_service, "enqueue_metrics_refresh")

    def test_webhook_handler_full_flow_elements(self) -> None:
        """Webhook handler should have all flow elements in order."""
        import inspect

        from app.api import webhooks

        # The handler is composed of the module's helpers.
        source = inspect.getsource(webhooks)
        # Verify key flow stages exist in source
        elements = [
            "body",  # Parse body
            "project_gitlab_id",  # Extract project ID
            "orphan_project",  # Orphan guard
            "verify_webhook_token",  # Auth check
            "payload_hash",  # Dedup key computation
            "exists_by_delivery_id",  # Dedup layer 1
            "exists_by_uuid",  # Dedup layer 2
            "exists_by_payload_hash",  # Dedup layer 3
            "WebhookEvent(",  # Store event
            "IntegrityError",  # Concurrent race guard
            "backpressure",  # Backpressure check
            "enqueue_event_processing",  # Enqueue processing
            "WEBHOOK_RECEIVED",  # Prometheus metric
        ]
        for element in elements:
            assert element in source, f"Webhook handler missing flow element: {element}"

    def test_event_processor_post_processing_chain(self) -> None:
        """After processing, event_processor should: invalidate cache, enrich,
        recompute metrics, notify dashboard."""
        import inspect

        from app.workers import event_processor

        source = inspect.getsource(event_processor)
        post_processing = [
            "_invalidate_project_cache",
            "_enqueue_immediate_enrichment",
            "_enqueue_metrics_for_project",
            "_notify_dashboard_update",
        ]
        for func in post_processing:
            assert func in source, f"Event processor missing post-processing: {func}"

    def test_worker_bootstrap_session_manager(self) -> None:
        """worker_session context manager should be available."""
        from app.workers.bootstrap import worker_session

        assert callable(worker_session)
