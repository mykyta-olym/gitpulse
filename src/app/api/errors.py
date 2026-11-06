"""Shared error factories for API and dashboard routers."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, NoReturn

from fastapi import HTTPException, status


def raise_http_error(
    status_code: int,
    detail: str,
    *,
    error: str | None = None,
    fields: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> NoReturn:
    """Raise ``HTTPException`` with optional structured metadata."""
    payload: str | dict[str, Any] = detail
    if error is not None or fields is not None:
        payload_dict: dict[str, Any] = {"detail": detail}
        if error is not None:
            payload_dict["error"] = error
        if fields is not None:
            payload_dict["fields"] = {str(k): str(v) for k, v in fields.items()}
        payload = payload_dict

    raise HTTPException(
        status_code=status_code,
        detail=payload,
        headers=dict(headers) if headers is not None else None,
    )


def raise_bad_request(detail: str, *, fields: Mapping[str, Any] | None = None) -> NoReturn:
    raise_http_error(status.HTTP_400_BAD_REQUEST, detail, fields=fields)


def raise_unauthorized(
    detail: str = "Authentication required",
    *,
    fields: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> NoReturn:
    raise_http_error(
        status.HTTP_401_UNAUTHORIZED,
        detail,
        fields=fields,
        headers=headers,
    )


def raise_forbidden(
    detail: str = "Access denied",
    *,
    fields: Mapping[str, Any] | None = None,
) -> NoReturn:
    raise_http_error(status.HTTP_403_FORBIDDEN, detail, fields=fields)


def raise_not_found(
    detail: str = "Resource not found",
    *,
    fields: Mapping[str, Any] | None = None,
) -> NoReturn:
    raise_http_error(status.HTTP_404_NOT_FOUND, detail, fields=fields)


def raise_conflict(detail: str, *, fields: Mapping[str, Any] | None = None) -> NoReturn:
    raise_http_error(status.HTTP_409_CONFLICT, detail, fields=fields)


def raise_unprocessable(detail: str, *, fields: Mapping[str, Any] | None = None) -> NoReturn:
    raise_http_error(status.HTTP_422_UNPROCESSABLE_CONTENT, detail, fields=fields)


def raise_payload_too_large(detail: str) -> NoReturn:
    raise_http_error(status.HTTP_413_CONTENT_TOO_LARGE, detail)


def raise_internal_error(detail: str = "Internal server error") -> NoReturn:
    raise_http_error(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail,
    )


def raise_service_unavailable(detail: str = "Service unavailable") -> NoReturn:
    raise_http_error(status.HTTP_503_SERVICE_UNAVAILABLE, detail)


def check_optimistic_lock(
    entity: Any,
    expected_updated_at: datetime | None,
    *,
    label: str = "Resource",
) -> None:
    """Compare *expected_updated_at* with the entity's current ``updated_at``.

    If the caller supplied ``expected_updated_at`` and it does not match
    (i.e. the record was modified by another user after the page was loaded),
    raise a **409 Conflict** so the client can ask the user to reload.

    When *expected_updated_at* is ``None`` the check is skipped - this keeps
    backward compatibility with older clients that don't send the field.
    """
    if expected_updated_at is None:
        return  # field not supplied - skip check

    current = getattr(entity, "updated_at", None)
    if current is None:
        return  # entity has no updated_at - nothing to compare

    # Normalise both to UTC-aware for safe comparison, truncate to
    # milliseconds to avoid float rounding issues between JSON and DB.

    def _trunc_ms(dt: datetime) -> datetime:
        return dt.replace(microsecond=(dt.microsecond // 1000) * 1000)

    cur = _trunc_ms(current.astimezone(UTC) if current.tzinfo else current.replace(tzinfo=UTC))
    exp = _trunc_ms(
        expected_updated_at.astimezone(UTC)
        if expected_updated_at.tzinfo
        else expected_updated_at.replace(tzinfo=UTC)
    )

    if cur != exp:
        raise_conflict(
            f"{label} was modified by another user. Please reload the page and try again.",
            fields={
                "expected_updated_at": expected_updated_at.isoformat(),
                "actual_updated_at": current.isoformat(),
            },
        )
