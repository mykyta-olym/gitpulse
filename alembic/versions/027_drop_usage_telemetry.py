"""Drop the pilot usage telemetry.

Report views, dashboard visits and other staff activity, clicks avoided,
flagged-team resolutions and their weekly aggregates were recorded for the
pilot evaluation and are no longer collected or read. The students' weekly
compliance snapshots and the support tickets are not part of it and stay.

Revision ID: 027
Revises: 026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "027"
down_revision: str | None = "026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "telemetry_aggregates",
    "teacher_activity_metrics",
    "clicks_avoided_metrics",
    "flagged_team_resolutions",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


def downgrade() -> None:
    """The tables come back empty: what was recorded in them is gone."""

    def course_fk() -> sa.ForeignKey:
        return sa.ForeignKey("courses.id", ondelete="CASCADE")

    op.create_table(
        "teacher_activity_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", UUID(as_uuid=True), course_fk(), nullable=False),
        sa.Column(
            "teacher_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metric_type", sa.String(50), nullable=False),
        sa.Column("metric_value", sa.Integer(), nullable=True),
        sa.Column("context", JSONB(), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("week_number", sa.Integer(), nullable=True),
    )
    op.create_table(
        "clicks_avoided_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", UUID(as_uuid=True), course_fk(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("clicks_saved", sa.Integer(), nullable=False),
        sa.Column("teams_affected", sa.Integer(), nullable=True),
        sa.Column("context", JSONB(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("week_number", sa.Integer(), nullable=True),
    )
    op.create_table(
        "flagged_team_resolutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", UUID(as_uuid=True), course_fk(), nullable=False),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("flag_type", sa.String(50), nullable=False),
        sa.Column("flag_reason", sa.Text(), nullable=True),
        sa.Column("flagged_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_type", sa.String(50), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("time_to_resolution_hours", sa.Float(), nullable=True),
        sa.Column("week_number", sa.Integer(), nullable=True),
    )
    op.create_table(
        "telemetry_aggregates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", UUID(as_uuid=True), course_fk(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("aggregate_date", sa.Date(), nullable=False),
        sa.Column("total_report_views", sa.Integer(), nullable=True),
        sa.Column("total_dashboard_visits", sa.Integer(), nullable=True),
        sa.Column("total_bulk_actions", sa.Integer(), nullable=True),
        sa.Column("estimated_time_saved_minutes", sa.Float(), nullable=True),
        sa.Column("total_clicks_avoided", sa.Integer(), nullable=True),
        sa.Column("auto_compliance_checks", sa.Integer(), nullable=True),
        sa.Column("auto_flags_raised", sa.Integer(), nullable=True),
        sa.Column("teams_flagged", sa.Integer(), nullable=True),
        sa.Column("teams_resolved", sa.Integer(), nullable=True),
        sa.Column("avg_resolution_hours", sa.Float(), nullable=True),
        sa.Column("avg_compliance_score", sa.Float(), nullable=True),
        sa.Column("compliance_improvement_avg", sa.Float(), nullable=True),
        sa.Column("students_improved", sa.Integer(), nullable=True),
        sa.Column("students_declined", sa.Integer(), nullable=True),
        sa.Column("feedback_submissions", sa.Integer(), nullable=True),
        sa.Column("avg_rating", sa.Float(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("course_id", "week_number", name="uq_ta_course_week"),
    )
