"""Issue Note (comment) model."""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, NoteMixin, UUIDMixin


class IssueNote(Base, UUIDMixin, NoteMixin):
    __tablename__ = "issue_notes"
    __table_args__ = (
        UniqueConstraint("issue_id", "gitlab_note_id", name="uq_issue_note_issue_gitlab"),
    )

    issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Author / body / counts / timestamp columns come from NoteMixin.
