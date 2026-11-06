"""MR Note (comment) model."""

import uuid

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, NoteMixin, UUIDMixin


class MRNote(Base, UUIDMixin, NoteMixin):
    __tablename__ = "mr_notes"
    __table_args__ = (
        UniqueConstraint("merge_request_id", "gitlab_note_id", name="uq_mr_note_mr_gitlab"),
        {"comment": "Comments on merge requests for review analysis."},
    )

    merge_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merge_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Author / body / counts / timestamp columns come from NoteMixin.
    # MR-specific review columns:
    is_resolvable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_resolved: Mapped[bool | None] = mapped_column(Boolean)
    discussion_id: Mapped[str | None] = mapped_column(String(100), index=True)
    noteable_type: Mapped[str] = mapped_column(String(50), default="MergeRequest")
    note_type: Mapped[str | None] = mapped_column(String(50))
    position_path: Mapped[str | None] = mapped_column(String(500))
    position_new_line: Mapped[int | None] = mapped_column(Integer)
    position_old_line: Mapped[int | None] = mapped_column(Integer)
    contains_commit_ref: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    commit_refs: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
