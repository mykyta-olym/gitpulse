"""Git Commit model for tracking individual commits."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Commit(Base, UUIDMixin):
    """Stores individual git commits for attribution and metrics."""

    __tablename__ = "git_commits"
    __table_args__ = (UniqueConstraint("project_id", "sha", name="uq_commit_project_sha"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gitlab_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Git commit identifiers
    sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    short_sha: Mapped[str] = mapped_column(String(8), nullable=False)

    # Author info (from git)
    author_name: Mapped[str | None] = mapped_column(String(200))
    author_email: Mapped[str | None] = mapped_column(String(200), index=True)
    author_gitlab_id: Mapped[int | None] = mapped_column(BigInteger, index=True)

    # Link to student (resolved from email/username)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )

    # Commit message
    title: Mapped[str | None] = mapped_column(String(500))
    message: Mapped[str | None] = mapped_column(Text)

    # Stats
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    additions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)

    # Parent commits (for merge detection)
    parent_shas: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Branch ref (if known from push event)
    ref: Mapped[str | None] = mapped_column(String(200))

    # Timestamps
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def is_merge_commit(self) -> bool:
        """Check if this is a merge commit (has multiple parents)."""
        return len(self.parent_shas or []) > 1
