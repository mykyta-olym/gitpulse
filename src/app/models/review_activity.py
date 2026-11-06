"""ReviewActivity model - aggregate per reviewer per MR."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class ReviewActivity(Base, UUIDMixin):
    __tablename__ = "review_activities"
    __table_args__ = (
        UniqueConstraint("merge_request_id", "reviewer_id", name="uq_review_activity_mr_reviewer"),
    )

    merge_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merge_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    note_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_words: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_chars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_note_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_note_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_meaningful: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recomputed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
