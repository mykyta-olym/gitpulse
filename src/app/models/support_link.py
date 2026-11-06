"""SQLAlchemy model for persisted support links."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class SupportLink(Base, UUIDMixin, TimestampMixin):
    """Persisted support link - teachers can generate and manage multiple links."""

    __tablename__ = "feedback_links"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    form_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feedback_forms.id", ondelete="SET NULL"),
        nullable=True,
    )
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False, default="teacher")
    feedback_url: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    course = relationship("Course")
    form = relationship("SupportForm")
