"""drop_sandbox_features

Permanently removes the three unused sandbox features:
  * git conflict simulator      (conflict_challenges + course_settings.conflict_config)
  * Docker build verification   (docker_build_reports + course_settings.docker_lint_config)
  * CI-failure scenario generator (ci_failure_scenarios + course_settings.ci_failure_config)

All three were feature-flagged OFF by default and never enabled in production, so
their tables carry no data (verified against prod: 0 rows in each) and their
course_settings JSONB config columns are unused. The objects were created in
migration 002 and extended in 004.

Drops (idempotent via IF EXISTS, so it is safe regardless of whether a given
environment ever created these objects):
  * tables ci_failure_scenarios, docker_build_reports, conflict_challenges
  * course_settings columns conflict_config, docker_lint_config, ci_failure_config

One-way removal: downgrade is intentionally unsupported (restore migrations
002/004 if the historical schema is ever required).

Revision ID: 009
Revises: 008
Create Date: 2026-07-07 09:40:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Unused config columns on course_settings (added in 004).
    op.execute("ALTER TABLE course_settings DROP COLUMN IF EXISTS conflict_config")
    op.execute("ALTER TABLE course_settings DROP COLUMN IF EXISTS docker_lint_config")
    op.execute("ALTER TABLE course_settings DROP COLUMN IF EXISTS ci_failure_config")
    # Feature tables (their indexes drop with the table via CASCADE).
    op.execute("DROP TABLE IF EXISTS ci_failure_scenarios CASCADE")
    op.execute("DROP TABLE IF EXISTS docker_build_reports CASCADE")
    op.execute("DROP TABLE IF EXISTS conflict_challenges CASCADE")


def downgrade() -> None:
    raise NotImplementedError(
        "Migration 009 permanently removes the sandbox features (conflict "
        "simulator / Docker verification / CI-failure generator). Downgrade is not "
        "supported; restore migrations 002/004 if the historical schema is needed."
    )
