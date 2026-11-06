"""Structured JSON logging with structlog + OpenTelemetry trace correlation.

Every log line in production is a JSON object containing:
- ``timestamp``  - ISO-8601 UTC
- ``level``      - DEBUG / INFO / WARNING / ERROR / CRITICAL
- ``logger``     - module name
- ``event``      - log message / event key
- ``correlation_id`` - per-request UUID (from middleware)
- ``trace_id`` / ``span_id`` - OpenTelemetry IDs (when tracing is active)
- ``service``    - always ``gitpulse``

Console mode (development) renders coloured human-readable output instead.
"""

import logging
import sys
from collections.abc import MutableMapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import structlog

from app.config import LogFormat


def _add_otel_trace_context(
    logger: Any,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Inject OpenTelemetry trace_id and span_id into log events."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except ImportError:
        pass
    return event_dict


_REDACT_KEYS = frozenset(
    {
        "password",
        "token",
        "secret",
        "api_key",
        "authorization",
        "private_token",
        "secret_key",
        "password_hash",
        "webhook_secret",
        "gitlab_token",
        "teacher_api_token",
        "dashboard_password_hash",
    }
)

_REDACTED = "***REDACTED***"


def redact_url_credentials(value: object) -> str:
    """Return ``value`` as a URL string with userinfo credentials redacted."""
    raw = str(value)
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw
    if "@" not in parts.netloc:
        return raw

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)
    if userinfo.startswith(":"):
        redacted_userinfo = f":{_REDACTED}"
    elif ":" in userinfo:
        username, _password = userinfo.split(":", 1)
        redacted_userinfo = f"{username}:{_REDACTED}"
    else:
        redacted_userinfo = _REDACTED
    return urlunsplit(parts._replace(netloc=f"{redacted_userinfo}@{hostinfo}"))


def _redact_secrets(
    logger: Any,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Replace values of known secret keys with a placeholder."""
    for key in event_dict:
        if key.lower() in _REDACT_KEYS and isinstance(event_dict[key], str):
            event_dict[key] = _REDACTED
    return event_dict


def _add_service_name(
    logger: Any,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Add static service name to every log event."""
    event_dict["service"] = "gitpulse"
    return event_dict


class _PoolTerminationFilter(logging.Filter):
    """Drop SQLAlchemy pool 'Exception terminating/closing connection' messages.

    These occur when Starlette cancels an asyncio task (e.g. SSE stream
    disconnect) and SQLAlchemy's pool tries to terminate the underlying
    asyncpg connection inside the already-cancelled scope.  They are
    harmless - the connection is simply discarded - but produce noisy
    tracebacks.
    """

    _SUPPRESSED = frozenset({"Exception terminating connection", "Exception close failed"})

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(phrase in msg for phrase in self._SUPPRESSED)


def setup_logging(level: str = "info", fmt: LogFormat = LogFormat.JSON) -> None:
    """Configure structured logging for the application.

    Call once at startup (in the lifespan handler).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        _add_service_name,
        _add_otel_trace_context,
        _redact_secrets,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.format_exc_info,
    ]

    if fmt == LogFormat.JSON:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True, pad_level=False, pad_event_to=0)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Apply pool termination filter to the handler (not just loggers) so it
    # catches messages from all child loggers during propagation - Python
    # logging filters on loggers are NOT checked during propagation.
    handler.addFilter(_PoolTerminationFilter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("opentelemetry").setLevel(logging.WARNING)

    # Suppress noisy "Exception terminating connection" tracebacks from
    # SQLAlchemy's pool when Starlette's cancel-scope interrupts asyncpg
    # connections during SSE stream disconnects.  Real pool errors are
    # still logged at CRITICAL level.
    # Python logging filters are NOT inherited by child loggers, so we
    # must attach the filter to BOTH the parent and the concrete pool
    # implementation logger used by asyncpg.
    _pool_filter = _PoolTerminationFilter()
    logging.getLogger("sqlalchemy.pool").addFilter(_pool_filter)
    logging.getLogger("sqlalchemy.pool.impl").addFilter(_pool_filter)
