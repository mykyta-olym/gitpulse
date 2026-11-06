"""Common response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ValidationIssue(BaseModel):
    field: str
    message: str
    error_type: str | None = None


class ErrorResponse(BaseModel):
    error: str = Field(description="Stable machine-readable error code")
    detail: str = Field(description="Human-readable error description")
    status_code: int = Field(ge=400, le=599)
    path: str
    correlation_id: str | None = None
    timestamp: datetime
    fields: dict[str, str] | None = None
    issues: list[ValidationIssue] | None = None
    error_id: str | None = None


class StatusResponse(BaseModel):
    status: str


class StatusIdResponse(StatusResponse):
    id: int | str | None = None


class ORMBase(BaseModel):
    """Base for ORM-mapped schemas."""

    model_config = ConfigDict(from_attributes=True)
