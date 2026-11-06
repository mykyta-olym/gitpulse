"""SQLAlchemy model for dynamic support forms."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class SupportForm(Base, UUIDMixin, TimestampMixin):
    """Dynamic support form definition.

    ``questions`` is a JSONB array of question objects::

        [
            {
                "id": "rating",
                "type": "rating",          # rating | scale | boolean | text | textarea | select
                "label": "Overall rating",
                "required": true,
                "config": { "max": 5, "default": 4 }
            },
            ...
        ]
    """

    __tablename__ = "feedback_forms"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    course: Mapped[Any] = relationship("Course", back_populates="support_forms")
    responses: Mapped[list[Any]] = relationship(
        "SupportTicket", back_populates="form", lazy="noload"
    )
