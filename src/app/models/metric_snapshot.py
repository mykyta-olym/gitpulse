"""MetricSnapshot model - per-student compliance metrics."""

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


class MetricSnapshot(Base, UUIDMixin):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "team_id", "student_id", "computed_at", name="uq_metric_snap_team_student_time"
        ),
        Index("idx_ms_team", "team_id"),
        Index("idx_ms_student", "student_id"),
        Index("ix_metric_snapshots_course_id", "course_id"),
        Index("idx_ms_team_computed", "team_id", "computed_at"),
        Index("idx_ms_student_computed", "student_id", "computed_at"),
        Index("idx_ms_course_student_computed", "course_id", "student_id", "computed_at"),
    )

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # -- R01: Issue ownership  |assigned_issues| >= 1 --
    issues_assigned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r01_issue_assigned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R02: Branch naming  ∃ MR: branch_naming_ok (or convention off), |MRs| ≥ 1 --
    branches_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    branches_correctly_named: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r02_branch_naming: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R03: Test changes  ∃ MR: has_test_changes --
    mrs_with_test_changes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r03_test_changes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R04: MR-Issue link  ∃ MR: has_issue_link --
    mrs_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mrs_with_issue_link: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r04_mr_issue_link: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R05: MR template  ∃ MR: template_compliant --
    mrs_template_compliant: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r05_mr_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R06: Reviews received  |distinct reviewers on own MR| ≥ threshold --
    own_mr_review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r06_reviews_received: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R07: Review duty  |distinct MRs meaningfully reviewed| ≥ threshold --
    distinct_mrs_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meaningful_reviews_given: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r07_review_duty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R08: Response quality  all threads answered + commit ref --
    total_review_threads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    answered_threads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_rate: Mapped[float | None] = mapped_column(Float)
    responses_with_commit_ref: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r08_response_quality: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R09: Approvals  |approvals| ≥ threshold --
    own_mr_approvals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r09_approvals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R10: Merge by author --
    own_mr_merged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    own_mr_merged_by_self: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    r10_merged_by_author: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R11: Closure state  MR ∈ {merged,closed} AND issue closed --
    own_mr_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    linked_issue_closed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    r11_closure_state: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R12: Pipeline health  ∃ pipeline: success + test_job --
    pipeline_total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pipeline_success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pipeline_has_test_job: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    r12_pipeline_health: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- R13: Commit quality  web_editor_ratio <= max_web_editor_ratio --
    commits_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commits_web_editor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    r13_commit_quality: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -- Communication indicators (non-scoring, diagnostic) --
    median_first_response_hours: Mapped[float | None] = mapped_column(Float)
    median_review_rounds: Mapped[float | None] = mapped_column(Float)
    discussion_resolution_pct: Mapped[float | None] = mapped_column(Float)
    review_word_depth: Mapped[float | None] = mapped_column(Float)
    author_response_word_depth: Mapped[float | None] = mapped_column(Float)
    median_time_to_merge_hours: Mapped[float | None] = mapped_column(Float)

    # -- Aggregates --
    checks_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Live code always passes the dynamic count (built-in + custom + weekly-
    # expected) via checks_total_override; this constant is only a fallback for
    # a row inserted without it. 13 = current built-in check count (R01-R13).
    checks_total: Mapped[int] = mapped_column(Integer, nullable=False, default=13)
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    traffic_light: Mapped[str] = mapped_column(String(10), nullable=False, default="GRAY")
    checks_detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    bottlenecks: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
