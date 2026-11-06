"""Tracing must reject oversized propagation headers before parsing them."""

import pytest

trace = pytest.importorskip("opentelemetry.trace")
tracecontext = pytest.importorskip("opentelemetry.trace.propagation.tracecontext")


def test_tracestate_keeps_valid_members_and_rejects_oversized_headers() -> None:
    propagator = tracecontext.TraceContextTextMapPropagator()
    parent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
    valid = propagator.extract({"traceparent": parent, "tracestate": "tenant=value"})
    valid_span = trace.get_current_span(valid).get_span_context()
    assert valid_span.trace_state.get("tenant") == "value"

    # Each member is valid on its own. The old parser accepted the combined
    # header; the patched API rejects its total size before any regex work.
    oversized = ",".join(f"vendor{i:02d}=" + "x" * 250 for i in range(32))
    assert len(oversized) > 8192
    rejected = propagator.extract({"traceparent": parent, "tracestate": oversized})
    rejected_span = trace.get_current_span(rejected).get_span_context()
    assert len(rejected_span.trace_state) == 0
    assert rejected_span.trace_id == valid_span.trace_id
