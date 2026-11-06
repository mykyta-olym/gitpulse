"""SQLAlchemy declarative base with common mixins."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class UUIDMixin:
    """Adds UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    """Adds created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class NoteMixin:
    """Columns shared by IssueNote and MRNote (GitLab comment records).

    Both note tables carried an identical block of author / body / counts /
    timestamp columns; only the parent FK (issue_id vs merge_request_id),
    __tablename__ and __table_args__ differ, and MRNote adds review-specific
    columns (discussion/position/resolution). Those stay on the subclasses.

    Column definitions are byte-identical to the originals, so this is
    schema-neutral (verified with ``alembic check``) - it does NOT require a
    migration. The per-table index name for ``author_id`` is derived from the
    table name, so it stays ``ix_<table>_author_id``.
    """

    gitlab_note_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    author_username: Mapped[str | None] = mapped_column(String(120))
    body: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
