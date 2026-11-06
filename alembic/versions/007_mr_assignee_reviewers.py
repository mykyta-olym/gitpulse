"""mr_assignee_reviewers

Add explicit GitLab assignee / reviewers / approvers to merge_requests so the
student profile can show the real "assigned vs reviewer" signal (not just who
commented) plus per-reviewer approval status.

Revision ID: 007
Revises: 006
Create Date: 2026-06-24 11:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("merge_requests", sa.Column("assignee_gitlab_id", sa.BigInteger(), nullable=True))
    op.add_column("merge_requests", sa.Column("assignee_id", sa.UUID(), nullable=True))
    op.add_column(
        "merge_requests",
        sa.Column(
            "reviewer_gitlab_ids",
            sa.ARRAY(sa.BigInteger()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.add_column(
        "merge_requests",
        sa.Column(
            "approved_by_gitlab_ids",
            sa.ARRAY(sa.BigInteger()),
            server_default="{}",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "fk_merge_requests_assignee_id_students",
        "merge_requests",
        "students",
        ["assignee_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_merge_requests_assignee_id_students", "merge_requests", type_="foreignkey"
    )
    op.drop_column("merge_requests", "approved_by_gitlab_ids")
    op.drop_column("merge_requests", "reviewer_gitlab_ids")
    op.drop_column("merge_requests", "assignee_id")
    op.drop_column("merge_requests", "assignee_gitlab_id")
