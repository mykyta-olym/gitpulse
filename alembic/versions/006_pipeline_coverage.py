"""pipeline_coverage

Add a nullable test-coverage column to pipelines so the student MR cards can
surface GitLab's reported coverage % (e.g. 37.00).

Revision ID: 006
Revises: 005
Create Date: 2026-06-24 10:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pipelines", sa.Column("coverage", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("pipelines", "coverage")
