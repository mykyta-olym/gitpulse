"""Shared API contracts: error responses and OpenAPI defaults."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from app.schemas.common import ErrorResponse

API_ERROR_RESPONSES: Mapping[int, dict[str, Any]] = MappingProxyType(
    {
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
        409: {"model": ErrorResponse, "description": "Conflict"},
        422: {"model": ErrorResponse, "description": "Validation failed"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"},
    }
)
