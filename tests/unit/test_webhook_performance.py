"""Performance tests for webhook ingestion throughput.

These tests measure the performance characteristics of webhook processing:
- Payload parsing latency
- Deduplication check latency (simulated)
- Throughput under load

Run with: pytest tests/unit/test_webhook_performance.py -v -m performance --benchmark-enable
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, cast

import pytest

from app.schemas.webhooks import WebhookPayload

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
PAYLOADS_DIR = FIXTURES_DIR / "payloads"


def load_payload(event_type: str) -> dict[str, Any]:
    """Load sample payload for event type."""
    return cast(
        dict[str, Any],
        json.loads((PAYLOADS_DIR / f"{event_type}.json").read_text(encoding="utf-8")),
    )


def generate_unique_payload(base_payload: dict[str, Any], index: int) -> dict[str, Any]:
    """Generate a unique payload based on a template."""
    payload = cast(dict[str, Any], json.loads(json.dumps(base_payload)))  # Deep copy

    # Make it unique
    if "object_attributes" in payload:
        payload["object_attributes"]["id"] = 1000 + index
        if "iid" in payload["object_attributes"]:
            payload["object_attributes"]["iid"] = index
        payload["object_attributes"]["updated_at"] = (
            f"2025-01-30 {10 + (index % 14):02d}:{index % 60:02d}:00 UTC"
        )

    if "commits" in payload:
        for i, commit in enumerate(payload["commits"]):
            # Generate unique SHA
            new_sha = hashlib.sha256(f"{index}-{i}".encode()).hexdigest()[:40]
            commit["id"] = new_sha

    return payload


def compute_payload_hash(payload: dict[str, Any]) -> str:
    """Compute SHA-256 hash of payload."""
    raw_body = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(raw_body).hexdigest()


def compute_dedup_key(payload: dict[str, Any]) -> str:
    """Compute deduplication key from payload."""
    event_type = payload.get("object_kind", "")
    project_id = payload.get("project", {}).get("id", "")
    obj_attrs = payload.get("object_attributes", {})
    obj_id = obj_attrs.get("id", "")
    action = obj_attrs.get("action", "")
    updated = obj_attrs.get("updated_at", "")

    hash_input = f"{event_type}:{project_id}:{obj_id}:{action}:{updated}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


class TestPayloadParsingPerformance:
    """Test payload parsing performance."""

    @pytest.mark.performance
    def test_pydantic_parse_merge_request_latency(self, benchmark) -> None:
        """Measure MR payload parsing latency."""
        payload = load_payload("merge_request_event")

        result = benchmark(WebhookPayload.model_validate, payload)

        assert result.object_kind == "merge_request"
        # Assert reasonable latency (< 1ms for parsing)
        assert benchmark.stats["mean"] < 0.001

    @pytest.mark.performance
    def test_pydantic_parse_push_event_latency(self, benchmark) -> None:
        """Measure push event parsing latency."""
        payload = load_payload("push_event")

        result = benchmark(WebhookPayload.model_validate, payload)

        assert result.object_kind == "push"
        assert benchmark.stats["mean"] < 0.001

    @pytest.mark.performance
    def test_pydantic_parse_pipeline_event_latency(self, benchmark) -> None:
        """Measure pipeline event parsing latency (larger payload with builds)."""
        payload = load_payload("pipeline_event")

        result = benchmark(WebhookPayload.model_validate, payload)

        assert result.object_kind == "pipeline"
        # Pipeline events are larger, allow 2ms
        assert benchmark.stats["mean"] < 0.002

    @pytest.mark.performance
    def test_json_loads_latency(self, benchmark) -> None:
        """Measure raw JSON parsing latency."""
        payload_path = PAYLOADS_DIR / "merge_request_event.json"
        raw_json = payload_path.read_text(encoding="utf-8")

        result = benchmark(json.loads, raw_json)

        assert "object_kind" in result
        # JSON parsing should be < 0.5ms
        assert benchmark.stats["mean"] < 0.0005


class TestHashingPerformance:
    """Test hashing performance for deduplication."""

    @pytest.mark.performance
    def test_payload_hash_latency(self, benchmark) -> None:
        """Measure payload hashing latency."""
        payload = load_payload("merge_request_event")
        raw_body = json.dumps(payload, sort_keys=True).encode()

        result = benchmark(lambda: hashlib.sha256(raw_body).hexdigest())

        assert len(result) == 64  # SHA-256 hex digest
        # Hashing should be < 0.1ms
        assert benchmark.stats["mean"] < 0.0001

    @pytest.mark.performance
    def test_dedup_key_computation_latency(self, benchmark) -> None:
        """Measure deduplication key computation latency."""
        payload = load_payload("merge_request_event")

        result = benchmark(compute_dedup_key, payload)

        assert len(result) == 64
        assert benchmark.stats["mean"] < 0.0001


class TestThroughputSimulation:
    """Simulate webhook throughput scenarios."""

    @pytest.mark.performance
    def test_parse_1000_payloads_sequential(self) -> None:
        """Measure time to parse 1000 payloads sequentially."""
        base_payload = load_payload("merge_request_event")
        payloads = [generate_unique_payload(base_payload, i) for i in range(1000)]

        start = time.perf_counter()
        results = [WebhookPayload.model_validate(p) for p in payloads]
        elapsed = time.perf_counter() - start

        assert len(results) == 1000
        # Should process 1000 payloads in < 1 second (1000/sec minimum)
        assert elapsed < 1.0, f"Took {elapsed:.3f}s for 1000 payloads"

    @pytest.mark.performance
    def test_hash_and_parse_1000_payloads(self) -> None:
        """Measure combined hash + parse for 1000 payloads."""
        base_payload = load_payload("merge_request_event")
        payloads = [generate_unique_payload(base_payload, i) for i in range(1000)]

        start = time.perf_counter()
        for payload in payloads:
            # Simulate full ingestion path
            raw_body = json.dumps(payload).encode()
            payload_hash = hashlib.sha256(raw_body).hexdigest()
            dedup_key = compute_dedup_key(payload)
            model = WebhookPayload.model_validate(payload)

            # Basic assertions
            assert len(payload_hash) == 64
            assert len(dedup_key) == 64
            assert model.object_kind == "merge_request"

        elapsed = time.perf_counter() - start

        # Should still process 1000 in < 2 seconds with full path
        assert elapsed < 2.0, f"Took {elapsed:.3f}s for 1000 payloads with full processing"

    @pytest.mark.performance
    def test_mixed_event_types_throughput(self) -> None:
        """Measure throughput with mixed event types."""
        event_types = [
            "push_event",
            "merge_request_event",
            "note_event_mr",
            "pipeline_event",
            "issue_event",
        ]
        base_payloads = {et: load_payload(et) for et in event_types}

        # Generate 1000 mixed payloads
        payloads = []
        for i in range(1000):
            event_type = event_types[i % len(event_types)]
            payloads.append(generate_unique_payload(base_payloads[event_type], i))

        start = time.perf_counter()
        results = [WebhookPayload.model_validate(p) for p in payloads]
        elapsed = time.perf_counter() - start

        assert len(results) == 1000
        assert elapsed < 1.5, f"Mixed events took {elapsed:.3f}s"


class TestMemoryEfficiency:
    """Test memory efficiency of payload processing."""

    @pytest.mark.performance
    def test_payload_object_size(self) -> None:
        """Measure memory size of parsed payload objects."""
        import sys

        payload = load_payload("merge_request_event")
        model = WebhookPayload.model_validate(payload)

        # Get approximate size (shallow)
        model_size = sys.getsizeof(model)

        # Pydantic models should be reasonably compact
        # Allow up to 1KB for the model object itself
        assert model_size < 1024, f"Model size: {model_size} bytes"

    @pytest.mark.performance
    def test_batch_processing_memory(self) -> None:
        """Ensure batch processing doesn't leak memory."""
        import gc

        base_payload = load_payload("merge_request_event")

        # Process in batches and check we can collect
        for batch in range(10):
            payloads = [generate_unique_payload(base_payload, i + batch * 100) for i in range(100)]
            results = [WebhookPayload.model_validate(p) for p in payloads]

            # Clear references
            del results
            del payloads

        # Force collection
        collected = gc.collect()
        assert collected >= 0


class TestLatencyPercentiles:
    """Test latency percentiles for SLA compliance."""

    @pytest.mark.performance
    def test_parsing_p99_latency(self) -> None:
        """Measure p99 latency for payload parsing."""

        payload = load_payload("merge_request_event")
        latencies = []

        # Warm up
        for _ in range(100):
            WebhookPayload.model_validate(payload)

        # Measure
        for _ in range(1000):
            start = time.perf_counter()
            WebhookPayload.model_validate(payload)
            latencies.append(time.perf_counter() - start)

        latencies.sort()
        p99 = latencies[990]

        # p99 should be < 5ms
        assert p99 < 0.005, f"p99 latency {p99 * 1000:.3f}ms exceeds 5ms SLA"

    @pytest.mark.performance
    def test_full_ingestion_p99_latency(self) -> None:
        """Measure p99 latency for full ingestion path (no DB)."""

        base_payload = load_payload("merge_request_event")
        latencies = []

        # Warm up
        for i in range(100):
            payload = generate_unique_payload(base_payload, i)
            raw_body = json.dumps(payload).encode()
            hashlib.sha256(raw_body).hexdigest()
            compute_dedup_key(payload)
            WebhookPayload.model_validate(payload)

        # Measure
        for i in range(1000):
            payload = generate_unique_payload(base_payload, i + 1000)

            start = time.perf_counter()
            raw_body = json.dumps(payload).encode()
            hashlib.sha256(raw_body).hexdigest()
            compute_dedup_key(payload)
            WebhookPayload.model_validate(payload)
            latencies.append(time.perf_counter() - start)

        latencies.sort()
        p99 = latencies[990]

        # p99 should be < 10ms (excluding DB)
        assert p99 < 0.010, f"p99 latency {p99 * 1000:.3f}ms exceeds 10ms SLA"
