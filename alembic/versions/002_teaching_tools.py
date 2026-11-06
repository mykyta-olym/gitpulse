"""Teaching tools - rubrics, gaming, conflict simulator, Docker, CI failures, LLM.

Revision ID: 002
Revises: 001
Create Date: 2026-02-08

Tables created:
  rubrics, rubric_suggestions, conflict_challenges,
  docker_build_reports, ci_failure_scenarios, llm_analysis_logs

Also adds the active_rubric_id FK on course_settings -> rubrics.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    # ==========================================================================
    # CONFLICT CHALLENGES
    # ==========================================================================
    op.create_table(
        "conflict_challenges",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("issue_gitlab_iid", sa.Integer(), nullable=False),
        sa.Column("student_branch", sa.String(300), nullable=False),
        sa.Column("bot_branch", sa.String(300), nullable=False),
        sa.Column("target_file", sa.String(500), nullable=False),
        sa.Column("bot_mr_gitlab_iid", sa.Integer(), nullable=True),
        sa.Column("student_mr_gitlab_iid", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "resolution_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bot_comment_gitlab_id", sa.BigInteger(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "issue_gitlab_iid", name="uq_conflict_project_issue"),
    )
    op.create_index("ix_conflict_challenges_project", "conflict_challenges", ["project_id"])
    op.create_index("ix_conflict_challenges_status", "conflict_challenges", ["status"])

    # ==========================================================================
    # DOCKER BUILD REPORTS
    # ==========================================================================
    op.create_table(
        "docker_build_reports",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=False),
        sa.Column("dockerfile_path", sa.String(500), nullable=False, server_default="Dockerfile"),
        # Static analysis
        sa.Column("lint_passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("lint_violations", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("lint_score", sa.Float(), nullable=False, server_default="0.0"),
        # Build results
        sa.Column("build_attempted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("build_success", sa.Boolean(), nullable=True),
        sa.Column("build_duration_seconds", sa.Float(), nullable=True),
        sa.Column("build_error", sa.Text(), nullable=True),
        # Runtime checks
        sa.Column("healthcheck_defined", sa.Boolean(), nullable=True),
        sa.Column("healthcheck_passed", sa.Boolean(), nullable=True),
        sa.Column("port_exposed", sa.Boolean(), nullable=True),
        sa.Column("runs_as_non_root", sa.Boolean(), nullable=True),
        sa.Column("image_size_mb", sa.Float(), nullable=True),
        # Metadata
        sa.Column("multi_stage", sa.Boolean(), nullable=True),
        sa.Column("base_image", sa.String(300), nullable=True),
        sa.Column("base_image_pinned", sa.Boolean(), nullable=True),
        # Report
        sa.Column("report_summary", sa.Text(), nullable=True),
        sa.Column("report_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("gitlab_issue_iid", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "project_id",
            "commit_sha",
            "dockerfile_path",
            name="uq_docker_report_project_commit_path",
        ),
    )
    op.create_index("ix_docker_reports_project", "docker_build_reports", ["project_id"])
    op.create_index("ix_docker_reports_team", "docker_build_reports", ["team_id"])

    # ==========================================================================
    # CI FAILURE SCENARIOS
    # ==========================================================================
    op.create_table(
        "ci_failure_scenarios",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("scenario_type", sa.String(50), nullable=False),
        sa.Column("target_branch", sa.String(300), nullable=False),
        sa.Column("injected_file_path", sa.String(500), nullable=True),
        sa.Column("bot_commit_sha", sa.String(40), nullable=True),
        sa.Column("issue_gitlab_iid", sa.Integer(), nullable=True),
        sa.Column("comment_gitlab_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("teaching_note", sa.Text(), nullable=True),
        sa.Column("expected_symptoms", sa.Text(), nullable=True),
        sa.Column("fix_instructions", sa.Text(), nullable=True),
        sa.Column("rolled_back", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rollback_commit_sha", sa.String(40), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("injected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ci_failure_scenarios_project", "ci_failure_scenarios", ["project_id"])
    op.create_index("ix_ci_failure_scenarios_team", "ci_failure_scenarios", ["team_id"])
    op.create_index("ix_ci_failure_scenarios_status", "ci_failure_scenarios", ["status"])

    # ==========================================================================
    # LLM ANALYSIS LOGS
    # ==========================================================================
    op.create_table(
        "llm_analysis_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("mr_iid", sa.Integer(), nullable=True),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column(
            "analysis_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("model_used", sa.String(100), nullable=False),
        sa.Column("structured_result", JSONB(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("raw_prompt_redacted", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_llm_analysis_logs_project_id", "llm_analysis_logs", ["project_id"])


def downgrade() -> None:
    op.drop_table("llm_analysis_logs")
    op.drop_table("ci_failure_scenarios")
    op.drop_table("docker_build_reports")
    op.drop_table("conflict_challenges")
