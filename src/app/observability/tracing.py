"""OpenTelemetry tracing setup.

Instruments:
- FastAPI (incoming HTTP requests)
- SQLAlchemy (database queries)
- httpx (outgoing GitLab API calls)
- Redis (queue operations)

Traces are exported to an OTLP-compatible collector (Jaeger, Tempo, etc.)
via the OTEL_EXPORTER_OTLP_ENDPOINT env var.  When no endpoint is set,
tracing is disabled (NoOp exporter) - zero overhead in dev.

Webhook trace correlation
-------------------------
The ``X-Correlation-ID`` header is propagated as a span attribute
``app.correlation_id``.  The worker also sets this attribute when
processing an event, allowing the full webhook -> enqueue -> process
chain to be correlated across services.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "gitpulse", otlp_endpoint: str | None = None) -> None:
    """Initialize OpenTelemetry tracing if the SDK is installed.

    Safe to call even if opentelemetry packages are not present -
    silently becomes a no-op.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        # SDK not installed - silently skip.
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Export to OTLP if endpoint is configured
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP trace exporter configured: %s", otlp_endpoint)
        except ImportError:
            logger.warning(
                "opentelemetry OTLP exporter not installed - traces will not be exported"
            )
    else:
        # Dev mode: no OTLP endpoint - tracing stays local, no export.
        pass

    trace.set_tracer_provider(provider)

    # Auto-instrument libraries
    _instrument_fastapi()
    _instrument_sqlalchemy()
    _instrument_httpx()
    _instrument_redis()


def _instrument_fastapi() -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_sqlalchemy() -> None:
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_httpx() -> None:
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_redis() -> None:
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except ImportError:
        pass


def get_tracer(name: str = "gitpulse") -> Any | None:
    """Return an OpenTelemetry tracer, or a no-op context manager factory if unavailable."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return None


def set_correlation_attribute(correlation_id: str) -> None:
    """Set the correlation ID as an attribute on the current span."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("app.correlation_id", correlation_id)
    except ImportError:
        pass
