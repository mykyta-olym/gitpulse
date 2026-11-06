"""Middleware for injecting a correlation ID into requests and responses.

Uses raw ASGI middleware instead of ``BaseHTTPMiddleware`` to avoid
cancel-scope leaks with SSE / streaming responses.
"""

import uuid
from contextlib import suppress

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CorrelationIdMiddleware:
    """Inject a correlation ID into every request and response (pure ASGI).

    Also sets the correlation ID as an OpenTelemetry span attribute
    for cross-service trace correlation on webhook deliveries.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Propagate to OTel span
        with suppress(Exception):
            from app.observability.tracing import set_correlation_attribute

            set_correlation_attribute(correlation_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                raw_headers.append((b"x-correlation-id", correlation_id.encode()))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_wrapper)
