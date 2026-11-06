"""Event pipeline schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ReplayRequest(BaseModel):
    """Which events to replay.

    Either an explicit ``event_ids`` selection - what the events table sends
    when rows are ticked - or a time range. The selection wins when both are
    present: it names exactly the rows the user looked at, while a range can
    only approximate them.
    """

    start: datetime | None = None
    end: datetime | None = None
    project_id: int | None = None
    event_type: str | None = None
    event_ids: list[UUID] | None = Field(default=None, max_length=1000)
    limit: int = Field(default=1000, ge=1, le=10_000)

    @model_validator(mode="after")
    def _needs_a_selection_or_a_range(self) -> "ReplayRequest":
        if not self.event_ids and (self.start is None or self.end is None):
            raise ValueError("Provide event_ids, or both start and end")
        return self


class ReplayResponse(BaseModel):
    replayed: int
    event_ids: list[str]


class RecentEventSummary(BaseModel):
    """One event in the live feed, successful or not."""

    id: str
    event_type: str
    gitlab_project_id: int
    received_at: datetime | None
    processed: bool
    processed_at: datetime | None
    retry_count: int
    # Set only for failures, so the feed can show why without a second call.
    dead_letter_at: datetime | None
    processing_error: str | None
    # Who and where, resolved server-side. A raw GitLab project id tells a
    # teacher nothing about which course or student the event belongs to.
    project_path: str | None = None
    course_code: str | None = None
    course_name: str | None = None
    course_academic_year: str | None = None
    course_semester: str | None = None
    team_name: str | None = None
    actor: str | None = None
    summary: str | None = None


class RecentEventsResponse(BaseModel):
    count: int
    events: list[RecentEventSummary]


class DLQEventSummary(BaseModel):
    id: str
    event_type: str
    gitlab_project_id: int
    dead_letter_at: datetime | None
    dead_letter_reason: str | None
    retry_count: int
    processing_error: str | None


class DLQListResponse(BaseModel):
    count: int
    events: list[DLQEventSummary]


class ResurrectResponse(BaseModel):
    event_id: str
    status: str


class PurgeResponse(BaseModel):
    """How many rows a purge removed, and what it was asked to remove."""

    deleted: int
    scope: str
    hours: int
