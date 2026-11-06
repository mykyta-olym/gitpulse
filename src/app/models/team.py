"""Team model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.project import GitLabProject
    from app.models.team_member import TeamMember


class Team(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("course_id", "name", name="uq_teams_course_name"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gitlab_group_id: Mapped[int | None] = mapped_column(BigInteger)
    gitlab_group_path: Mapped[str | None] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    members_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="teams")
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team", lazy="raise", cascade="all, delete-orphan"
    )
    projects: Mapped[list["GitLabProject"]] = relationship(
        "GitLabProject", back_populates="team", lazy="raise", cascade="all, delete-orphan"
    )

    @property
    def active_members(self) -> list["TeamMember"]:
        """Return only active (non-removed) team members."""
        return [m for m in self.members if m.is_active]

    compliance_snapshots: Mapped[list[Any]] = relationship(
        "StudentComplianceSnapshot", back_populates="team", lazy="noload"
    )
