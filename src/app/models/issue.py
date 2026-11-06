"""Issue model."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Issue(Base, UUIDMixin):
    __tablename__ = "issues"
    __table_args__ = (UniqueConstraint("project_id", "gitlab_iid", name="uq_issues_project_iid"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gitlab_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gitlab_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    gitlab_iid: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(String)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="opened")
    author_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    assignee_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    # All assignees (GitLab allows multiple)
    all_assignee_gitlab_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)
    # Who closed the issue
    closed_by_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    closed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    labels: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
