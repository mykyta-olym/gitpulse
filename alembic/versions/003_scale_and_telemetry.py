"""Scale optimizations & pilot telemetry.

Revision ID: 003
Revises: 002
Create Date: 2026-02-08

Adds performance indexes, partitioned webhook table, cache/report/rate-limit
tables, and all 7 pilot telemetry tables.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ==========================================================================
    # 1. PERFORMANCE INDEXES
    # ==========================================================================

    # Webhook events
    op.create_index(
        "idx_we_retry_sweep",
        "webhook_events",
        ["retry_count", "received_at"],
        postgresql_where=sa.text("processed = false AND dead_letter_at IS NULL"),
    )
    op.create_index(
        "idx_we_dlq",
        "webhook_events",
        ["dead_letter_at"],
        postgresql_where=sa.text("dead_letter_at IS NOT NULL"),
    )
    op.create_index(
        "idx_we_replay_lineage",
        "webhook_events",
        ["replay_of_id"],
        postgresql_where=sa.text("replay_of_id IS NOT NULL"),
    )
    op.create_index(
        "idx_we_project_type_time",
        "webhook_events",
        ["gitlab_project_id", "event_type", "received_at"],
    )

    # Merge requests
    op.create_index("idx_mr_state_created", "merge_requests", ["state", "created_at"])
    op.create_index("idx_mr_author_project", "merge_requests", ["author_id", "project_id"])

    # Issues
    op.create_index(
        "idx_issues_assignee_state",
        "issues",
        ["assignee_id", "state"],
        postgresql_where=sa.text("assignee_id IS NOT NULL"),
    )

    # Metric snapshots
    op.create_index("idx_ms_team_computed", "metric_snapshots", ["team_id", "computed_at"])
    op.create_index("idx_ms_student_computed", "metric_snapshots", ["student_id", "computed_at"])

    # ==========================================================================
    # 6. PILOT TELEMETRY TABLES
    # ==========================================================================

    # -- Teacher Activity Metrics --
    op.create_table(
        "teacher_activity_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metric_type", sa.String(50), nullable=False),
        sa.Column("metric_value", sa.Integer(), server_default="1"),
        sa.Column("context", JSONB(), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "idx_tam_course_type_week",
        "teacher_activity_metrics",
        ["course_id", "metric_type", "week_number"],
    )
    op.create_index("idx_tam_recorded_at", "teacher_activity_metrics", ["recorded_at"])

    # -- Clicks Avoided Metrics --
    op.create_table(
        "clicks_avoided_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("clicks_saved", sa.Integer(), nullable=False),
        sa.Column("teams_affected", sa.Integer(), server_default="1"),
        sa.Column("context", JSONB(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "idx_cam_course_action_week",
        "clicks_avoided_metrics",
        ["course_id", "action_type", "week_number"],
    )

    # -- Flagged Team Resolutions --
    op.create_table(
        "flagged_team_resolutions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("flag_type", sa.String(50), nullable=False),
        sa.Column("flag_reason", sa.Text(), nullable=True),
        sa.Column("flagged_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_type", sa.String(50), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("time_to_resolution_hours", sa.Float(), nullable=True),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "idx_ftr_course_flag_type", "flagged_team_resolutions", ["course_id", "flag_type"]
    )
    op.create_index("idx_ftr_team_flagged", "flagged_team_resolutions", ["team_id", "flagged_at"])
    op.create_index(
        "idx_ftr_unresolved",
        "flagged_team_resolutions",
        ["course_id", "resolved_at"],
        postgresql_where=sa.text("resolved_at IS NULL"),
    )

    # -- Student Compliance Snapshots --
    op.create_table(
        "student_compliance_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("commit_score", sa.Float(), nullable=True),
        sa.Column("mr_score", sa.Float(), nullable=True),
        sa.Column("review_score", sa.Float(), nullable=True),
        sa.Column("ci_score", sa.Float(), nullable=True),
        sa.Column("issue_score", sa.Float(), nullable=True),
        sa.Column("prev_week_score", sa.Float(), nullable=True),
        sa.Column("improvement_delta", sa.Float(), nullable=True),
        sa.Column("improvement_pct", sa.Float(), nullable=True),
        sa.Column("raw_metrics", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "student_id", "course_id", "week_number", name="uq_scs_student_course_week"
        ),
    )
    op.create_index(
        "idx_scs_course_week", "student_compliance_snapshots", ["course_id", "week_number"]
    )
    op.create_index(
        "idx_scs_student_week", "student_compliance_snapshots", ["student_id", "week_number"]
    )
    op.create_index("idx_scs_team_week", "student_compliance_snapshots", ["team_id", "week_number"])

    # -- Pilot Feedback --
    op.create_table(
        "pilot_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feedback_token", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("feedback_type", sa.String(50), nullable=False),
        sa.Column("context_type", sa.String(50), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("usefulness_rating", sa.Integer(), nullable=True),
        sa.Column("accuracy_rating", sa.Integer(), nullable=True),
        sa.Column("time_saved_rating", sa.Integer(), nullable=True),
        sa.Column("would_recommend", sa.Boolean(), nullable=True),
        sa.Column("free_text", sa.Text(), nullable=True),
        sa.Column("improvement_suggestions", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("week_number", sa.Integer(), nullable=True),
        sa.Column("is_processed", sa.Boolean(), server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_pf_course_type", "pilot_feedback", ["course_id", "feedback_type"])
    op.create_index("idx_pf_submitted", "pilot_feedback", ["submitted_at"])

    # -- Telemetry Aggregates --
    op.create_table(
        "telemetry_aggregates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("aggregate_date", sa.Date(), nullable=False),
        # Teacher metrics
        sa.Column("total_report_views", sa.Integer(), server_default="0"),
        sa.Column("total_dashboard_visits", sa.Integer(), server_default="0"),
        sa.Column("total_bulk_actions", sa.Integer(), server_default="0"),
        sa.Column("estimated_time_saved_minutes", sa.Float(), server_default="0"),
        # Click avoidance
        sa.Column("total_clicks_avoided", sa.Integer(), server_default="0"),
        sa.Column("auto_compliance_checks", sa.Integer(), server_default="0"),
        sa.Column("auto_flags_raised", sa.Integer(), server_default="0"),
        # Resolution metrics
        sa.Column("teams_flagged", sa.Integer(), server_default="0"),
        sa.Column("teams_resolved", sa.Integer(), server_default="0"),
        sa.Column("avg_resolution_hours", sa.Float(), nullable=True),
        # Student compliance
        sa.Column("avg_compliance_score", sa.Float(), nullable=True),
        sa.Column("compliance_improvement_avg", sa.Float(), nullable=True),
        sa.Column("students_improved", sa.Integer(), server_default="0"),
        sa.Column("students_declined", sa.Integer(), server_default="0"),
        # Feedback
        sa.Column("feedback_submissions", sa.Integer(), server_default="0"),
        sa.Column("avg_rating", sa.Float(), nullable=True),
        # Metadata
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("course_id", "week_number", name="uq_ta_course_week"),
    )
    op.create_index("idx_ta_course_date", "telemetry_aggregates", ["course_id", "aggregate_date"])


def downgrade() -> None:
    # Telemetry
    op.drop_table("telemetry_aggregates")
    op.drop_table("pilot_feedback")
    op.drop_table("student_compliance_snapshots")
    op.drop_table("flagged_team_resolutions")
    op.drop_table("clicks_avoided_metrics")
    op.drop_table("teacher_activity_metrics")

    # Performance indexes
    op.drop_index("idx_ms_student_computed", table_name="metric_snapshots")
    op.drop_index("idx_ms_team_computed", table_name="metric_snapshots")
    op.drop_index("idx_issues_assignee_state", table_name="issues")
    op.drop_index("idx_mr_author_project", table_name="merge_requests")
    op.drop_index("idx_mr_state_created", table_name="merge_requests")
    op.drop_index("idx_we_project_type_time", table_name="webhook_events")
    op.drop_index("idx_we_replay_lineage", table_name="webhook_events")
    op.drop_index("idx_we_dlq", table_name="webhook_events")
    op.drop_index("idx_we_retry_sweep", table_name="webhook_events")
