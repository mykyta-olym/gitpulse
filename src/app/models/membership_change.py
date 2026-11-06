"""MembershipChange audit log model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.team import Team


class MembershipChange(Base, UUIDMixin):
    """Audit log entry for membership lifecycle events.

    Records when students join, leave, get role changes, or are reactivated.
    Enables teachers to see membership history and detect issues.
    """

    __tablename__ = "membership_changes"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gitlab_username: Mapped[str | None] = mapped_column(String(100), nullable=True)

    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="joined | left | role_changed | reactivated",
    )
    old_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    old_access_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_access_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="sync | import | webhook | manual",
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    team: Mapped["Team"] = relationship("Team", lazy="noload")
    student: Mapped["Student"] = relationship("Student", lazy="selectin")
