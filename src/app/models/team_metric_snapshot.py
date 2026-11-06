"""TeamMetricSnapshot model - per-team aggregated compliance metrics."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class TeamMetricSnapshot(Base, UUIDMixin):
    __tablename__ = "team_metric_snapshots"
    __table_args__ = (
        UniqueConstraint("team_id", "computed_at", name="uq_team_snap_team_time"),
        Index("idx_tms_course_computed", "course_id", "computed_at"),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    members_green: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    members_yellow: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    members_red: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    members_gray: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_weighted_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_weighted_score: Mapped[float | None] = mapped_column(Float)
    max_weighted_score: Mapped[float | None] = mapped_column(Float)
    overall_traffic_light: Mapped[str] = mapped_column(String(10), nullable=False, default="GRAY")
    review_coverage_pct: Mapped[float | None] = mapped_column(Float)
    review_reciprocity_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    team_pipeline_pass_rate: Mapped[float | None] = mapped_column(Float)
    bottlenecks: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
