"""SQLAlchemy model for support ticket comments."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class SupportComment(Base, UUIDMixin, TimestampMixin):
    """Threaded comment on a support ticket.

    ``is_internal`` comments are visible only to course staff (teachers/admins).
    """

    __tablename__ = "support_comments"

    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("pilot_feedback.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    ticket = relationship("SupportTicket", back_populates="comments")
