"""Merge Request diff file model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class MergeRequestDiff(Base, UUIDMixin):
    __tablename__ = "merge_request_diffs"
    __table_args__ = (
        UniqueConstraint("merge_request_id", "file_path", name="uq_merge_request_diff_file"),
    )

    merge_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merge_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(300), nullable=False)
    old_path: Mapped[str | None] = mapped_column(String(300))
    diff: Mapped[str | None] = mapped_column(Text)
    new_file: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    renamed_file: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_file: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
