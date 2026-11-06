"""Application-wide exception handlers and registration helper."""

import asyncio
import logging
import re
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, TypeAlias

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.dependencies import FeatureDisabledError
from app.middleware.error_pages import error_context
from app.schemas.common import ErrorResponse, ValidationIssue

logger = logging.getLogger(__name__)

_API_PREFIX = "/api/"
_DB_MIGRATION_HINT = "Run: docker compose --profile migrate run --rm migrate"
_REQUEST_LOCATIONS = {"body", "query", "path", "header", "cookie"}
_STATUS_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "access_denied",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "internal_server_error",
    502: "bad_gateway",
    503: "service_unavailable",
    504: "gateway_timeout",
}


def _role_contact_suggestion(request: Request) -> str:
    """Return a role-aware 'contact ...' suggestion for error pages.

    Best-effort: if the session cookie is missing or unparseable the
    returned text is generic.
    """
    try:
        from app.config import get_settings
        from app.security.session_auth import get_current_session

        settings = get_settings()
        session_data = get_current_session(
            request,
            secret_key=settings.secret_key,
            app_base_url=str(settings.app_base_url),
            enforce_ua=False,
        )
        if session_data:
            role = session_data.get("role", "")
            if role == "admin":
                return "Check service logs and database status"
            if role == "teacher":
                return "Contact the system administrator if the issue persists"
            return "Contact your instructor if the issue persists"
    except Exception:  # noqa: S110 -- error-page hint is purely cosmetic; falls back to generic message.
        pass
    return "Contact the administrator if the issue persists"


TemplateAwareHandler: TypeAlias = Callable[[Request, Any, Jinja2Templates], Awaitable[Response]]


def _is_htmx_request(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


def _is_api_request(request: Request) -> bool:
    if request.url.path.startswith(_API_PREFIX):
        return True
    accept = request.headers.get("accept", "")
    return "application/json" in accept and "text/html" not in accept


def _template_response(
    request: Request,
    templates: Jinja2Templates,
    *,
    template_name: str,
    status_code: int,
    context: dict[str, Any],
) -> Response:
    merged_context = {"request": request}
    merged_context.update(context)
    return templates.TemplateResponse(
        request,
        template_name,
        merged_context,
        status_code=status_code,
    )


def _error_page(
    request: Request, templates: Jinja2Templates, status_code: int, **page: Any
) -> Response:
    """The error page (errors/error.html) for a browser; see app.middleware.error_pages."""
    return _template_response(
        request,
        templates,
        template_name="errors/error.html",
        status_code=status_code,
        context=error_context(status_code, **page),
    )


def _status_error_code(status_code: int) -> str:
    return _STATUS_ERROR_CODES.get(status_code, "request_failed")


def _status_default_detail(status_code: int) -> str:
    default_by_status = {
        400: "Bad request",
        401: "Authentication required",
        403: "Access denied",
        404: "Not found",
        409: "Conflict",
        422: "Validation failed",
        429: "Rate limit exceeded",
        500: "Internal server error",
        502: "Bad gateway",
        503: "Service unavailable",
        504: "Gateway timeout",
    }
    return default_by_status.get(status_code, "Request failed")


def _correlation_id(request: Request) -> str | None:
    correlation = getattr(request.state, "correlation_id", None)
    return str(correlation) if correlation is not None else None


def _build_error_payload(
    request: Request,
    *,
    status_code: int,
    detail: str,
    error: str | None = None,
    fields: dict[str, str] | None = None,
    issues: list[ValidationIssue] | None = None,
    error_id: str | None = None,
) -> dict[str, Any]:
    payload = ErrorResponse(
        error=error or _status_error_code(status_code),
        detail=detail,
        status_code=status_code,
        path=request.url.path,
        correlation_id=_correlation_id(request),
        timestamp=datetime.now(UTC),
        fields=fields,
        issues=issues,
        error_id=error_id,
    )
    return payload.model_dump(mode="json", exclude_none=True)


def _api_error_response(
    request: Request,
    *,
    status_code: int,
    detail: str,
    error: str | None = None,
    headers: dict[str, str] | None = None,
    fields: dict[str, str] | None = None,
    issues: list[ValidationIssue] | None = None,
    error_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=_build_error_payload(
            request,
            status_code=status_code,
            detail=detail,
            error=error,
            fields=fields,
            issues=issues,
            error_id=error_id,
        ),
        headers=headers,
    )


def _extract_http_exception_payload(
    status_code: int,
    detail_value: Any,
) -> tuple[str, str, dict[str, str] | None, str | None]:
    error_code = _status_error_code(status_code)
    fields: dict[str, str] | None = None
    error_id: str | None = None

    if isinstance(detail_value, dict):
        raw_error = detail_value.get("error")
        if raw_error is not None:
            error_code = str(raw_error)

        detail = detail_value.get("detail")
        if detail is None:
            detail = detail_value.get("message")
        detail_text = str(detail) if detail is not None else _status_default_detail(status_code)

        raw_fields = detail_value.get("fields")
        if isinstance(raw_fields, dict):
            fields = {str(key): str(value) for key, value in raw_fields.items()}

        for key in ("feature_name", "feature_flag", "expected_availability", "hint", "error_type"):
            value = detail_value.get(key)
            if value is None:
                continue
            if fields is None:
                fields = {}
            fields[key] = str(value)

        raw_error_id = detail_value.get("error_id")
        if raw_error_id is not None:
            error_id = str(raw_error_id)

        return error_code, detail_text, fields, error_id

    if isinstance(detail_value, str):
        return error_code, detail_value, fields, error_id

    return error_code, _status_default_detail(status_code), fields, error_id


def _format_validation_field(location: tuple[Any, ...]) -> str:
    filtered = [str(part) for part in location if str(part) not in _REQUEST_LOCATIONS]
    if filtered:
        return ".".join(filtered)
    if location:
        return str(location[-1])
    return "request"


def _db_unavailable_response(request: Request, templates: Jinja2Templates) -> Response:
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=503,
            detail="Database unavailable",
            error="service_unavailable",
        )
    return _error_page(
        request,
        templates,
        503,
        message="Database unavailable. Please try again shortly.",
        suggestions=["Try again in a few minutes", _role_contact_suggestion(request)],
    )


def _integrity_error_detail(error_msg: str) -> str:
    detail = "Database constraint violation"
    if "UniqueViolation" in error_msg or "duplicate key" in error_msg:
        match = re.search(r'constraint "([^"]+)"', error_msg)
        constraint = match.group(1) if match else None
        if constraint == "uq_courses_code_year_semester":
            return "A course with this code, academic year, and semester already exists"
        if constraint == "users_username_key":
            return "A user with this username already exists"
        if constraint == "uq_users_gitlab_username":
            return "A user with this GitLab username already exists"
        if constraint == "teams_name_key" or "teams" in str(constraint):
            return "A group with this name already exists in this course"
        if constraint == "students_email_key" or "students" in str(constraint):
            return "A student with this email already exists"
        if "gitlab_projects" in str(constraint):
            return "This GitLab project is already linked to another group"
        key_match = re.search(r"Key \(([^)]+)\)=\(([^)]+)\)", error_msg)
        if key_match:
            fields = key_match.group(1)
            return f"Duplicate value for: {fields}"
        return "A record with these values already exists"
    if "ForeignKeyViolation" in error_msg or "foreign key" in error_msg:
        return "Referenced record does not exist or cannot be deleted due to related records"
    if "NotNullViolation" in error_msg or "not-null" in error_msg:
        match = re.search(r'column "([^"]+)"', error_msg)
        column = match.group(1) if match else "field"
        return f"Required field '{column}' cannot be empty"
    if "CheckViolation" in error_msg:
        return "Value does not meet validation requirements"
    return detail


def _programming_error_detail(error_msg: str) -> str:
    if "UndefinedTable" in error_msg or "does not exist" in error_msg:
        if "relation" in error_msg:
            return "Database migrations need to be applied. Please run migrations."
        return "Database table or column not found. Migrations may be required."
    if "UndefinedColumn" in error_msg or "column" in error_msg:
        return "Database column not found. Please run pending migrations."
    return "Database schema error"


def _with_templates(
    handler: TemplateAwareHandler,
    templates: Jinja2Templates,
) -> Callable[[Request, Any], Awaitable[Response]]:
    async def wrapped(request: Request, exc: Any) -> Response:
        return await handler(request, exc, templates)

    return wrapped


async def handle_unauthorized(
    request: Request,
    exc: StarletteHTTPException,
    templates: Jinja2Templates,
) -> Response:
    if _is_htmx_request(request):
        return Response(
            status_code=401,
            headers={"HX-Redirect": "/dashboard/login"},
        )
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=401,
            detail="Authentication required",
            error="unauthorized",
        )
    return _error_page(request, templates, 401)


async def handle_not_found(
    request: Request,
    exc: StarletteHTTPException,
    templates: Jinja2Templates,
) -> Response:
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=404,
            detail="Not Found",
            error="not_found",
        )
    return _error_page(request, templates, 404)


async def handle_forbidden(
    request: Request,
    exc: StarletteHTTPException,
    templates: Jinja2Templates,
) -> Response:
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=403,
            detail="Access Denied",
            error="access_denied",
        )
    return _error_page(request, templates, 403)


async def handle_internal_error(
    request: Request,
    exc: Exception,
    templates: Jinja2Templates,
) -> Response:
    error_id = str(uuid.uuid4())[:8].upper()
    logger.exception("Internal Server Error [ID: %s]", error_id, exc_info=exc)
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=500,
            detail="Internal Server Error",
            error="internal_server_error",
            error_id=error_id,
        )
    return _error_page(request, templates, 500, error_id=error_id)


def _log_db_unavailable(request: Request, exc: BaseException, kind: str) -> None:
    """Record WHY the database was unreachable.

    Both handlers used to accept the exception and drop it, so a 503 left no
    trace of its cause: connection refused, pool timeout, exhausted server
    connections and bad credentials all produced the same blank page. That is
    unactionable in production, and it is what made an intermittent 503 in the
    browser test suite take several sessions to even characterise.
    """
    # `exc_info=exc` explicitly: these run as exception HANDLERS, not inside an
    # `except` block, so `logger.exception()` alone would attach "NoneType:
    # None" and drop the very message that identifies the fault.
    logger.error(
        "db_unavailable kind=%s method=%s path=%s error_type=%s error=%s",
        kind,
        request.method,
        request.url.path,
        type(exc).__name__,
        exc,
        exc_info=exc,
    )


async def handle_db_connection_refused(
    request: Request,
    exc: ConnectionRefusedError,
    templates: Jinja2Templates,
) -> Response:
    _log_db_unavailable(request, exc, "connection_refused")
    return _db_unavailable_response(request, templates)


async def handle_db_operational_error(
    request: Request,
    exc: OperationalError,
    templates: Jinja2Templates,
) -> Response:
    _log_db_unavailable(request, exc, "operational_error")
    return _db_unavailable_response(request, templates)


async def handle_timeout_error(
    request: Request,
    exc: BaseException,
    templates: Jinja2Templates,
) -> Response:
    """Render a 504 Gateway Timeout for any uncaught timeout/cancellation.

    Catches asyncio.TimeoutError, builtin TimeoutError, httpx.TimeoutException
    and asyncio.CancelledError that escapes a route - typically a slow
    upstream (GitLab API, Redis) hanging past the configured timeout.
    """
    logger.warning(
        "Upstream timeout: %s on %s %s",
        type(exc).__name__,
        request.method,
        request.url.path,
    )
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=504,
            detail="Upstream service timed out. Please retry.",
            error="gateway_timeout",
        )
    return _error_page(request, templates, 504)


async def handle_upstream_network_error(
    request: Request,
    exc: httpx.RequestError,
    templates: Jinja2Templates,
) -> Response:
    """Render a 502 Bad Gateway for unreachable/failing upstream services."""
    if isinstance(exc, httpx.TimeoutException):
        return await handle_timeout_error(request, exc, templates)
    logger.warning(
        "Upstream network error: %s on %s %s",
        type(exc).__name__,
        request.method,
        request.url.path,
    )
    detail = "Unable to reach an upstream service (GitLab). Please retry shortly."
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=502,
            detail=detail,
            error="bad_gateway",
        )
    return _error_page(
        request,
        templates,
        502,
        message=detail,
        suggestions=[
            "Try again in a moment",
            "Check the GitLab status page",
            _role_contact_suggestion(request),
        ],
    )


async def handle_redis_error(
    request: Request,
    exc: RedisError,
    templates: Jinja2Templates,
) -> Response:
    """Render 503 when Redis (cache/queue/SSE bus) is unreachable."""
    logger.warning("Redis error: %s", exc)
    detail = "Cache/queue service unavailable. Please retry shortly."
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=503,
            detail=detail,
            error="service_unavailable",
        )
    return _error_page(
        request,
        templates,
        503,
        message=detail,
        suggestions=["Try again in a few minutes", _role_contact_suggestion(request)],
    )


async def handle_integrity_error(
    request: Request,
    exc: IntegrityError,
    templates: Jinja2Templates,
) -> Response:
    error_msg = str(exc.orig) if exc.orig else str(exc)
    detail = _integrity_error_detail(error_msg)
    logger.warning("IntegrityError: %s", error_msg)
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=409,
            detail=detail,
            error="conflict",
        )
    return _error_page(
        request,
        templates,
        409,
        message=detail,
        suggestions=[
            "Check if a similar record already exists",
            "Try using different values",
            "Go back and modify your input",
        ],
    )


async def handle_programming_error(
    request: Request,
    exc: ProgrammingError,
    templates: Jinja2Templates,
) -> Response:
    error_msg = str(exc.orig) if exc.orig else str(exc)
    logger.error("Database schema error: %s", error_msg)
    detail = _programming_error_detail(error_msg)
    if _is_api_request(request):
        return _api_error_response(
            request,
            status_code=503,
            detail=detail,
            error="schema_error",
            fields={"hint": _DB_MIGRATION_HINT},
        )
    return _error_page(
        request,
        templates,
        503,
        title="Database Schema Error",
        message=detail,
        suggestions=[
            "Database migrations need to be applied",
            _DB_MIGRATION_HINT,
            _role_contact_suggestion(request),
        ],
    )


async def handle_feature_disabled(
    request: Request,
    exc: FeatureDisabledError,
    templates: Jinja2Templates,
) -> Response:
    if _is_api_request(request):
        error_code, detail, fields, error_id = _extract_http_exception_payload(
            exc.status_code, exc.detail
        )
        return _api_error_response(
            request,
            status_code=503,
            detail=detail,
            error=error_code,
            fields=fields,
            error_id=error_id,
        )
    # Not an outage: the app is up and the rest of it works, so the page
    # offers the way back rather than Retry, and names no status.
    return _error_page(
        request,
        templates,
        503,
        title="Feature Disabled",
        numbered=False,
        offer="back",
        feature_name=exc.feature_name,
        feature_flag=exc.feature_flag,
        expected_availability=exc.expected_availability,
    )


async def handle_http_exception(
    request: Request,
    exc: StarletteHTTPException,
    templates: Jinja2Templates,
) -> Response:
    # Redirect responses (3xx) must be passed through regardless of client type
    if 300 <= exc.status_code < 400:
        headers = dict(exc.headers) if exc.headers else {}
        location = headers.get("Location", "")
        # For HTMX requests, convert login redirects to HX-Redirect so
        # htmx does a full-page navigation instead of swapping login HTML.
        if _is_htmx_request(request) and "/login" in location:
            return Response(
                status_code=401,
                headers={"HX-Redirect": location},
            )
        # For API/JSON requests, convert login redirects to 401 JSON so
        # fetch() doesn't follow cross-origin OAuth redirects (CORS error).
        if _is_api_request(request) and "/login" in location:
            return _api_error_response(
                request,
                status_code=401,
                detail="Session expired",
            )
        return Response(status_code=exc.status_code, headers=headers)

    if not _is_api_request(request):
        # Render styled error page for browser requests instead of plain text
        status = exc.status_code
        detail = exc.detail if isinstance(exc.detail, str) else _status_default_detail(status)
        extra_headers = dict(exc.headers) if exc.headers else None

        # Dedicated 429 page with countdown timer
        if status == 429:
            retry_after = int(extra_headers.get("Retry-After", 60)) if extra_headers else 60
            response = _error_page(request, templates, 429, retry_after=retry_after)
            if extra_headers:
                response.headers.update(extra_headers)
            return response

        # The heading names the status and the detail goes under it - it
        # used to be both, the same sentence twice.
        response = _error_page(request, templates, status, message=detail)
        if extra_headers:
            response.headers.update(extra_headers)
        return response
    error_code, detail, fields, error_id = _extract_http_exception_payload(
        exc.status_code,
        exc.detail,
    )
    api_headers = dict(exc.headers) if exc.headers else None
    return _api_error_response(
        request,
        status_code=exc.status_code,
        detail=detail,
        error=error_code,
        headers=api_headers,
        fields=fields,
        error_id=error_id,
    )


async def handle_request_validation_error(
    request: Request,
    exc: RequestValidationError,
    templates: Jinja2Templates,
) -> Response:
    if not _is_api_request(request):
        field_messages = []
        for error in exc.errors():
            location = error.get("loc", ())
            if not isinstance(location, tuple):
                location = tuple(location) if isinstance(location, list) else ()
            field = _format_validation_field(location)
            message = str(error.get("msg", "Invalid value"))
            field_messages.append(f"{field}: {message}")
        return _error_page(
            request,
            templates,
            422,
            message="The submitted data is invalid.",
            suggestions=field_messages[:5],
        )

    issues: list[ValidationIssue] = []
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = error.get("loc", ())
        if not isinstance(location, tuple):
            location = tuple(location) if isinstance(location, list) else ()
        field = _format_validation_field(location)
        message = str(error.get("msg", "Invalid value"))
        raw_error_type = error.get("type")
        error_type = str(raw_error_type) if raw_error_type is not None else None
        issues.append(ValidationIssue(field=field, message=message, error_type=error_type))
        fields[field] = message

    return _api_error_response(
        request,
        status_code=422,
        detail="Validation failed",
        error="validation_error",
        fields=fields or None,
        issues=issues,
    )


def register_exception_handlers(app: FastAPI, templates: Jinja2Templates) -> None:
    """Register all application exception handlers."""
    app.add_exception_handler(401, _with_templates(handle_unauthorized, templates))
    app.add_exception_handler(404, _with_templates(handle_not_found, templates))
    app.add_exception_handler(403, _with_templates(handle_forbidden, templates))
    app.add_exception_handler(500, _with_templates(handle_internal_error, templates))
    app.add_exception_handler(
        ConnectionRefusedError,
        _with_templates(handle_db_connection_refused, templates),
    )
    app.add_exception_handler(
        OperationalError,
        _with_templates(handle_db_operational_error, templates),
    )
    app.add_exception_handler(
        IntegrityError,
        _with_templates(handle_integrity_error, templates),
    )
    app.add_exception_handler(
        ProgrammingError,
        _with_templates(handle_programming_error, templates),
    )
    app.add_exception_handler(
        FeatureDisabledError,
        _with_templates(handle_feature_disabled, templates),
    )
    # Upstream timeouts / network failures - render 504/502 instead of generic 500
    app.add_exception_handler(
        asyncio.TimeoutError,
        _with_templates(handle_timeout_error, templates),
    )
    app.add_exception_handler(
        TimeoutError,
        _with_templates(handle_timeout_error, templates),
    )
    app.add_exception_handler(
        httpx.RequestError,
        _with_templates(handle_upstream_network_error, templates),
    )
    app.add_exception_handler(
        RedisError,
        _with_templates(handle_redis_error, templates),
    )
    app.add_exception_handler(
        StarletteHTTPException,
        _with_templates(handle_http_exception, templates),
    )
    app.add_exception_handler(
        RequestValidationError,
        _with_templates(handle_request_validation_error, templates),
    )
    # Generic catch-all - any uncaught Exception (ValueError, KeyError,
    # RuntimeError, etc.) thrown from a route or middleware ends here.
    # Without this, Starlette's ServerErrorMiddleware would render a raw
    # plaintext "Internal Server Error" (or debug traceback in dev).
    # The 500 HTTPException handler registered above only fires for
    # explicit HTTPException(500, ...) raises, not for bare exceptions.
    app.add_exception_handler(
        Exception,
        _with_templates(handle_internal_error, templates),
    )
