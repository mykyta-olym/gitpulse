"""Schemas for dynamic support forms, tickets, and comments."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# -- Ticket enums --------------------------------------------------------------


class TicketStatus(StrEnum):
    """Lifecycle statuses for a support ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(StrEnum):
    """Priority levels for a support ticket."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(StrEnum):
    """Classification categories for a support ticket."""

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    QUESTION = "question"
    GENERAL = "general"


# -- Question definition ------------------------------------------------------


class QuestionConfig(BaseModel):
    """Type-specific configuration for a question."""

    min: int | None = Field(default=None, ge=0, le=1000)
    max: int | None = Field(default=None, ge=1, le=1000)
    default: int | str | bool | None = None
    min_label: str | None = Field(default=None, max_length=200)
    max_label: str | None = Field(default=None, max_length=200)
    yes_label: str | None = Field(default=None, max_length=200)
    no_label: str | None = Field(default=None, max_length=200)
    placeholder: str | None = Field(default=None, max_length=500)
    options: list[str] | None = None
    max_selections: int | None = Field(default=None, ge=1, le=50)
    hint: str | None = Field(default=None, max_length=500)


class QuestionDefinition(BaseModel):
    """A single question inside a support form."""

    id: str = Field(
        ...,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique slug, e.g. 'rating' or 'q1'",
    )
    type: Literal[
        "rating",
        "scale",
        "boolean",
        "text",
        "textarea",
        "select",
        "multiselect",
        "nps",
    ] = Field(..., description="Question type")
    label: str = Field(..., max_length=500)
    required: bool = True
    config: QuestionConfig = Field(default_factory=QuestionConfig)


# -- Form CRUD -----------------------------------------------------------------


class SupportFormResponse(BaseModel):
    """Read representation of a support form."""

    id: uuid.UUID
    course_id: uuid.UUID
    category: str | None = None
    title: str
    description: str | None = None
    questions: list[QuestionDefinition]
    is_active: bool
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# -- Responses viewer ----------------------------------------------------------


class SupportResponseItem(BaseModel):
    """Single support ticket as shown in the ticket list."""

    id: int
    title: str | None = None
    submitted_at: datetime
    support_type: str
    status: str = "open"
    priority: str = "medium"
    category: str = "general"
    assigned_to: str | None = None
    resolved_at: datetime | None = None
    updated_at: datetime | None = None
    week_number: int | None = None
    comment_count: int = 0
    responses: dict[str, Any]


class SupportResponsesPage(BaseModel):
    """Paginated list of support ticket responses."""

    items: list[SupportResponseItem]
    total: int
    form: SupportFormResponse | None = None


# -- JSON import / export ------------------------------------------------------


class SupportStatsResponse(BaseModel):
    """Aggregated per-question statistics for support responses."""

    total_responses: int
    question_stats: dict[str, Any]
    nps_score: float | None = None


# -- Support Links -------------------------------------------------------------


# -- Ticket management ---------------------------------------------------------


class SupportTicketUpdate(BaseModel):
    """Payload for updating a support ticket (status, priority, assignment)."""

    title: str | None = Field(default=None, max_length=500)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: TicketCategory | None = None
    assigned_to: str | None = Field(default=None, max_length=100)

    @field_validator("status", "priority", "category")
    @classmethod
    def required_metadata(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Ticket metadata cannot be null")
        return value


# -- Comments ------------------------------------------------------------------


class SupportCommentCreate(BaseModel):
    """Payload for adding a comment to a support ticket."""

    content: str = Field(..., min_length=1, max_length=10_000)
    is_internal: bool = False


class SupportCommentResponse(BaseModel):
    """Read representation of a support comment."""

    id: uuid.UUID
    ticket_id: int
    author: str
    content: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SupportCommentListResponse(BaseModel):
    """Wraps a list of comments."""

    items: list[SupportCommentResponse]
    total: int


class SupportAttachmentUploadResponse(BaseModel):
    """Payload returned after uploading a support attachment."""

    url: str
    filename: str


class TicketPurgeResponse(BaseModel):
    """How many finished tickets a purge removed, and what it was asked for."""

    deleted: int
    hours: int


class SupportCreate(BaseModel):
    """Schema for support ticket submission.

    Supports dynamic-form submissions (``form_id`` + ``responses``).
    Optional ticket metadata (title, priority, category) for ticket lifecycle.
    """

    course_id: uuid.UUID = Field(description="Course UUID")
    context_type: str | None = Field(default=None, max_length=100)

    # Ticket metadata
    title: str | None = Field(default=None, max_length=500)
    priority: TicketPriority = TicketPriority.MEDIUM

    # Dynamic form fields
    form_id: uuid.UUID = Field(description="UUID of the SupportForm")
    responses: dict[str, Any] = Field(description="Dynamic answers keyed by question id")
