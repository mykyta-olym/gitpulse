"""project_gitlab_intel

Add a JSONB ``gitlab_intel`` snapshot to gitlab_projects so the project-detail
"GitLab Intelligence" panels (protected branches, contributors, repository
statistics) render from STORED sync data when GitLab is unreachable (expired
token / maintenance window) instead of failing live with "GitLab is
unreachable". Unlike the compliance MetricSnapshot tables this is current-state
only (overwritten each sync), so a single nullable column - not a time-series
table - is the right shape.

Revision ID: 008
Revises: 007
Create Date: 2026-07-02 18:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "gitlab_projects",
        sa.Column("gitlab_intel", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gitlab_projects", "gitlab_intel")
