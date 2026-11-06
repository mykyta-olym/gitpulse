"""drop_redundant_indexes_and_assignments

Revision ID: 005
Revises: 004
Create Date: 2026-06-17 16:16:40.753144
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop leftover assignments table if it exists (for prod cleanup)
    op.execute("DROP TABLE IF EXISTS assignments CASCADE")

    # Drop redundant indexes on metric_snapshots
    op.drop_index(
        op.f("ix_metric_snapshots_student_id"), table_name="metric_snapshots", if_exists=True
    )
    op.drop_index(
        op.f("ix_metric_snapshots_team_id"), table_name="metric_snapshots", if_exists=True
    )


def downgrade() -> None:
    # Recreate the dropped indexes
    op.create_index(
        op.f("ix_metric_snapshots_team_id"), "metric_snapshots", ["team_id"], unique=False
    )
    op.create_index(
        op.f("ix_metric_snapshots_student_id"), "metric_snapshots", ["student_id"], unique=False
    )
