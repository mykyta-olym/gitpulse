"""Course model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.course_settings import CourseSettings
    from app.models.team import Team


class Course(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("code", "academic_year", "semester", name="uq_courses_code_year_semester"),
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    semester: Mapped[str] = mapped_column(String(10), nullable=False, default="winter")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Lifecycle (multi-tenant)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cloned_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL")
    )

    # Relationships
    teams: Mapped[list["Team"]] = relationship(
        "Team", back_populates="course", lazy="raise", cascade="all, delete-orphan"
    )
    settings: Mapped["CourseSettings | None"] = relationship(
        "CourseSettings",
        back_populates="course",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    compliance_snapshots: Mapped[list[Any]] = relationship(
        "StudentComplianceSnapshot", back_populates="course", lazy="noload"
    )
    support_tickets: Mapped[list[Any]] = relationship(
        "SupportTicket", back_populates="course", lazy="noload"
    )
    support_forms: Mapped[list[Any]] = relationship(
        "SupportForm", back_populates="course", lazy="noload"
    )
