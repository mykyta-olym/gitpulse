"""classroom_assistant

The classroom assistant: a course's bot account (``course_assistants``) and
what it follows for each student (``assistant_tasks``).

GitPulse watches with a read-only token, and that stays so - the analytics
never write. The assistant is the one part that acts in GitLab (it comments,
plants a merge conflict, opens issues, approves and merges), so it runs under
its own bot account with its own token, kept encrypted per course here.

Both tables are new, so the migration only creates them; the downgrade drops
them.

Revision ID: 023
Revises: 022
Create Date: 2026-10-19 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "023"
down_revision: str | None = "022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "course_assistants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bot_token", sa.String(500), nullable=True),
        sa.Column("bot_user_id", sa.BigInteger(), nullable=True),
        sa.Column("bot_username", sa.String(100), nullable=True),
        sa.Column("bot_name", sa.String(200), nullable=True),
        sa.Column("bot_avatar_url", sa.String(500), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_by", sa.String(100), nullable=True),
        sa.Column(
            "push_review_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("min_commit_title_length", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("conflict_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "conflict_file_path", sa.String(300), nullable=False, server_default="README.md"
        ),
        sa.Column("mr_review_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("mr_bot_merges", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "exercise_file_template",
            sa.String(300),
            nullable=False,
            server_default="ulohy/{username}.txt",
        ),
        sa.Column("last_exercise_run", postgresql.JSONB(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("course_id", name="uq_course_assistants_course"),
    )
    op.create_table(
        "assistant_tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("gitlab_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool", sa.String(20), nullable=False),
        sa.Column("key", sa.String(300), nullable=False),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("student_username", sa.String(100), nullable=True),
        sa.Column("branch", sa.String(255), nullable=True),
        sa.Column("issue_iid", sa.Integer(), nullable=True),
        sa.Column("mr_iid", sa.Integer(), nullable=True),
        sa.Column("commit_sha", sa.String(64), nullable=True),
        sa.Column("file_path", sa.String(300), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("history", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint(
            "project_id", "tool", "key", name="uq_assistant_tasks_project_tool_key"
        ),
    )
    op.create_index(
        "ix_assistant_tasks_course_updated", "assistant_tasks", ["course_id", "updated_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_assistant_tasks_course_updated", table_name="assistant_tasks")
    op.drop_table("assistant_tasks")
    op.drop_table("course_assistants")
