"""SQLAlchemy model for support ticket submissions."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SupportTicket(Base):
    """Support ticket - stores form-driven submissions with ticket lifecycle.

    Each ticket tracks status, priority, category, and optional assignment.
    Dynamic-form rows set ``form_id`` and store answers in ``responses`` JSONB.
    """

    __tablename__ = "pilot_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feedback_token: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), unique=True, nullable=False
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)
    context_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Ticket metadata
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    category: Mapped[str] = mapped_column(String(50), nullable=False, server_default="general")
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    submitted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Dynamic form link
    form_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("feedback_forms.id", ondelete="SET NULL"), nullable=True
    )
    responses: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Form-driven rating columns (populated from JSONB for indexed queries)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usefulness_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_saved_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    would_recommend: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Free text (anonymized)
    free_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_suggestions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    week_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_processed: Mapped[bool | None] = mapped_column(Boolean, default=False)

    # Relationships
    course = relationship("Course", back_populates="support_tickets")
    form = relationship("SupportForm", back_populates="responses")
    comments = relationship(
        "SupportComment", back_populates="ticket", order_by="SupportComment.created_at"
    )
