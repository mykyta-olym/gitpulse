"""Background job schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobEnqueued(BaseModel):
    job_id: UUID
    job_type: str
    status: str = "enqueued"
    message: str = ""


class JobPollingStatus(BaseModel):
    job_id: UUID
    status: str
    job_type: str
    result_summary: str | None = None
    error_message: str | None = None
    enqueued_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobCancelRequest(BaseModel):
    reason: str = "Cancelled by user"
    job_types: list[str] | None = None


class JobCancelResponse(BaseModel):
    job_id: UUID | None = None
    status: str
    cancelled: int
    message: str
