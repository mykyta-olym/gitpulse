"""Middleware for structured request logging and HTTP metrics.

Uses raw ASGI middleware instead of ``BaseHTTPMiddleware`` to avoid
cancel-scope issues with SSE / streaming responses.  ``BaseHTTPMiddleware``
wraps every response body in a background task with a cancel scope; when
the middleware task finishes, the cancel scope fires ``CancelledError`` in
any still-running DB connection cleanup, leaking asyncpg connections back
to the pool.
"""

import time

import structlog
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.observability import db_timing
from app.observability.metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS

logger = structlog.get_logger(__name__)

#: A request over this gets its worst query named. Everything faster is not a
#: mystery worth a line of SQL in the log.
_SLOW_REQUEST_S = 1.0


def _metric_path(scope: Scope, root_path: str) -> str:
    """The route a request matched, as the label of its metrics.

    The template (``/dashboard/courses/{course_id}``), so a label never holds
    an id or a file name: each release's hashed bundle and each path a scanner
    tries would otherwise be a series of its own, without end. A mounted app
    (the static files) is its mount point; anything that matched nothing is one
    label.
    """
    route = scope.get("route")
    if route is not None and isinstance(getattr(route, "path", None), str):
        return str(route.path)
    mounted = str(scope.get("root_path", ""))
    if mounted != root_path:
        return mounted[len(root_path) :] or "/"
    return "<unmatched>"


class RequestLoggingMiddleware:
    """Log request/response and track HTTP metrics (pure ASGI)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        db_timing.begin_request()
        request = Request(scope)
        method = request.method
        path = request.url.path
        root_path = str(scope.get("root_path", ""))
        status_code = 500  # default until we see a response
        streaming = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code, streaming
            if message["type"] == "http.response.start":
                status_code = message["status"]
                streaming = any(
                    k.lower() == b"content-type" and v.startswith(b"text/event-stream")
                    for k, v in message.get("headers", ())
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start

            metric_path = _metric_path(scope, root_path)
            HTTP_REQUESTS.labels(method=method, path=metric_path, status=str(status_code)).inc()
            # An event stream lasts as long as its tab stays open; its hours are
            # not a response time and would make the stream's p95 the alert.
            if not streaming:
                HTTP_REQUEST_DURATION.labels(method=method, path=metric_path).observe(duration)

            # Structured log (skip health/metrics to reduce noise)
            if not path.startswith(("/health", "/metrics")):
                # How much of that duration was the database. A page that is
                # slow because it runs a hundred quick queries and one that is
                # slow because it renders a big template look identical without
                # these two numbers - which is exactly where the 13s course page
                # left the investigation.
                db = db_timing.read()
                extra: dict[str, object] = {}
                # The worst single query, but only on a request slow enough to
                # be worth explaining. Twenty queries and six seconds means one
                # or two of them own the page; naming it is the difference
                # between "the database" and something that can be fixed.
                if duration >= _SLOW_REQUEST_S:
                    worst = db_timing.read_slowest()
                    if worst is not None:
                        extra["db_slowest_ms"] = worst[0]
                        extra["db_slowest_sql"] = worst[1]
                logger.info(
                    "request_completed",
                    method=method,
                    path=path,
                    status=status_code,
                    duration_ms=round(duration * 1000, 1),
                    db_ms=db[1] if db else None,
                    db_queries=db[0] if db else None,
                    **extra,
                )
