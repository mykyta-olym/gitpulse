"""Index the latest course snapshot without reading its history.

Revision ID: 026
Revises: 025
"""

from collections.abc import Sequence

from alembic import op

revision: str = "026"
down_revision: str | None = "025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "idx_tms_course_computed", "team_metric_snapshots", ["course_id", "computed_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_tms_course_computed", table_name="team_metric_snapshots")
