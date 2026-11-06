"""SQLAlchemy model for student compliance snapshots."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StudentComplianceSnapshot(Base):
    """Weekly compliance snapshots for trend analysis."""

    __tablename__ = "student_compliance_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Compliance scores
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    commit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mr_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ci_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    issue_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Improvement tracking
    prev_week_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    improvement_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    improvement_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Context
    raw_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "student_id", "course_id", "week_number", name="uq_scs_student_course_week"
        ),
        Index(
            "idx_scs_course_week_cover",
            "course_id",
            "week_number",
            postgresql_include=[
                "student_id",
                "snapshot_date",
                "overall_score",
                "improvement_delta",
            ],
        ),
    )

    # Relationships
    course = relationship("Course", back_populates="compliance_snapshots")
    team = relationship("Team", back_populates="compliance_snapshots")
    student = relationship("Student", back_populates="compliance_snapshots")
