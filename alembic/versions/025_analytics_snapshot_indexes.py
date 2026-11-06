"""Read course analytics from small indexes rather than snapshot history pages.

Revision ID: 025
Revises: 024
"""

from collections.abc import Sequence

from alembic import op

revision: str = "025"
down_revision: str | None = "024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_ms_course_student_computed",
        "metric_snapshots",
        ["course_id", "student_id", "computed_at"],
    )
    op.create_index(
        "idx_scs_course_week_cover",
        "student_compliance_snapshots",
        ["course_id", "week_number"],
        postgresql_include=["student_id", "snapshot_date", "overall_score", "improvement_delta"],
    )


def downgrade() -> None:
    op.drop_index("idx_scs_course_week_cover", table_name="student_compliance_snapshots")
    op.drop_index("idx_ms_course_student_computed", table_name="metric_snapshots")
