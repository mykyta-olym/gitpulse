"""Core schema - all tables for the GitPulse platform.

Revision ID: 001
Revises: -
Create Date: 2026-02-08

Consolidated migration containing all core application tables in their
final form. This replaces the original 25 incremental migrations with
a single clean baseline.

Tables created:
  courses, course_settings, users, students, teams, team_members,
  gitlab_projects, webhook_events, issues, issue_notes,
  merge_requests, merge_request_diffs, mr_notes, mr_approvals,
  review_activities, pipelines, git_commits, metric_snapshots,
  team_metric_snapshots, audit_log, background_jobs, roster_imports
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # ==========================================================================
    # COURSES
    # ==========================================================================
    op.create_table(
        "courses",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("academic_year", sa.String(10), nullable=False),
        sa.Column("semester", sa.String(10), nullable=False, server_default="winter"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cloned_from_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "code", "academic_year", "semester", name="uq_courses_code_year_semester"
        ),
    )
    op.create_foreign_key(
        "fk_courses_cloned_from",
        "courses",
        "courses",
        ["cloned_from_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ==========================================================================
    # USERS (RBAC)
    # ==========================================================================
    op.create_table(
        "users",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("gitlab_username", sa.String(100), nullable=True),
        sa.Column("gitlab_user_id", sa.BigInteger(), nullable=True),
        sa.Column("gitlab_access_token", sa.String(500), nullable=True),
        sa.Column("gitlab_refresh_token", sa.String(500), nullable=True),
        sa.Column("gitlab_token_expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gitlab_username", name="uq_users_gitlab_username"),
        sa.UniqueConstraint("gitlab_user_id", name="uq_users_gitlab_user_id"),
    )

    # ==========================================================================
    # COURSE SETTINGS
    # ==========================================================================
    op.create_table(
        "course_settings",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        # Branch & template
        sa.Column(
            "branch_pattern", sa.String(200), nullable=False, server_default=r"^issue-(\d+)(-.+)?$"
        ),
        sa.Column(
            "mr_template_required_sections", ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        # Review thresholds
        sa.Column("min_reviews_per_mr", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("min_review_word_count", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("min_distinct_mrs_reviewed", sa.Integer(), nullable=False, server_default="2"),
        # Deadlines
        sa.Column("mr_creation_deadline", sa.DateTime(timezone=True)),
        sa.Column("merge_deadline", sa.DateTime(timezone=True)),
        # Scoring weights (12 rules)
        sa.Column("weight_issue_ownership", sa.Float(), nullable=False, server_default="0.08"),
        sa.Column("weight_branch_naming", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("weight_mr_issue_link", sa.Float(), nullable=False, server_default="0.08"),
        sa.Column("weight_mr_template", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("weight_test_changes", sa.Float(), nullable=False, server_default="0.10"),
        sa.Column("weight_review_count", sa.Float(), nullable=False, server_default="0.12"),
        sa.Column("weight_review_duty", sa.Float(), nullable=False, server_default="0.12"),
        sa.Column("weight_response_complete", sa.Float(), nullable=False, server_default="0.10"),
        sa.Column("weight_approvals", sa.Float(), nullable=False, server_default="0.08"),
        sa.Column("weight_merge_by_author", sa.Float(), nullable=False, server_default="0.07"),
        sa.Column("weight_closure", sa.Float(), nullable=False, server_default="0.05"),
        sa.Column("weight_pipeline_health", sa.Float(), nullable=False, server_default="0.05"),
        # Traffic-light thresholds
        sa.Column("green_threshold", sa.Float(), nullable=False, server_default="0.80"),
        sa.Column("yellow_threshold", sa.Float(), nullable=False, server_default="0.50"),
        sa.Column("test_file_patterns", ARRAY(sa.String()), nullable=False, server_default="{}"),
        # Multi-tenant & config
        sa.Column(
            "enabled_checks",
            ARRAY(sa.String()),
            nullable=False,
            server_default="{R01,R02,R03,R04,R05,R06,R07,R08,R09,R10,R11,R12}",
        ),
        sa.Column("weekly_deadlines", JSONB(), nullable=False, server_default="[]"),
        sa.Column("semester_start_date", sa.Date(), nullable=True),
        # GitLab integration
        sa.Column("gitlab_group_path", sa.String(300), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("course_id", name="uq_course_settings_course"),
    )

    # ==========================================================================
    # STUDENTS
    # ==========================================================================
    op.create_table(
        "students",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("gitlab_user_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("gitlab_username", sa.String(100), nullable=False),
        sa.Column("full_name", sa.String(200)),
        sa.Column("email", sa.String(200)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_students_username", "students", ["gitlab_username"])

    # ==========================================================================
    # TEAMS
    # ==========================================================================
    op.create_table(
        "teams",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("gitlab_group_id", sa.BigInteger()),
        sa.Column("gitlab_group_path", sa.String(300)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("course_id", "name", name="uq_teams_course_name"),
    )
    op.create_index("idx_teams_course_id", "teams", ["course_id"])

    # ==========================================================================
    # TEAM MEMBERS
    # ==========================================================================
    op.create_table(
        "team_members",
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("gitlab_access_level", sa.Integer(), nullable=True),
        sa.Column("gitlab_access_role", sa.String(32), nullable=True),
        sa.PrimaryKeyConstraint("team_id", "student_id"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_team_members_student", "team_members", ["student_id"])

    # ==========================================================================
    # GITLAB PROJECTS
    # ==========================================================================
    op.create_table(
        "gitlab_projects",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gitlab_project_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("gitlab_project_path", sa.String(300), nullable=False),
        sa.Column("gitlab_project_name", sa.String(200)),
        sa.Column("default_branch", sa.String(100), server_default="master"),
        sa.Column("webhook_secret_hash", sa.String(128)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_gitlab_projects_team", "gitlab_projects", ["team_id"])

    # ==========================================================================
    # WEBHOOK EVENTS (with full pipeline: dedup, DLQ, replay)
    # ==========================================================================
    op.create_table(
        "webhook_events",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("gitlab_event_uuid", sa.String(100), nullable=False, unique=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("gitlab_object_kind", sa.String(50)),
        sa.Column("gitlab_project_id", sa.BigInteger(), nullable=False),
        sa.Column("gitlab_object_id", sa.BigInteger()),
        sa.Column("action", sa.String(50)),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("processing_error", sa.Text()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correlation_id", UUID(as_uuid=True)),
        # Triple idempotency
        sa.Column("payload_hash", sa.String(64), nullable=True),
        sa.Column("gitlab_delivery_id", sa.String(100), nullable=True),
        # Dead-letter queue
        sa.Column("dead_letter_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dead_letter_reason", sa.Text(), nullable=True),
        # Replay lineage
        sa.Column("replay_of_id", UUID(as_uuid=True), nullable=True),
        sa.Column("is_replayed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_foreign_key(
        "fk_we_replay_of",
        "webhook_events",
        "webhook_events",
        ["replay_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_we_project_received", "webhook_events", ["gitlab_project_id", "received_at"]
    )
    op.create_index("idx_we_event_type", "webhook_events", ["event_type", "received_at"])
    op.create_index("ix_we_payload_hash", "webhook_events", ["payload_hash"])
    op.create_index("ix_we_delivery_id", "webhook_events", ["gitlab_delivery_id"])
    op.create_index(
        "ix_we_dead_letter",
        "webhook_events",
        ["dead_letter_at"],
        postgresql_where="dead_letter_at IS NOT NULL",
    )
    op.create_index(
        "ix_we_sweep",
        "webhook_events",
        ["received_at"],
        postgresql_where="processed = false AND dead_letter_at IS NULL",
    )

    # ==========================================================================
    # ISSUES
    # ==========================================================================
    op.create_table(
        "issues",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gitlab_id", sa.BigInteger(), nullable=False),
        sa.Column("gitlab_iid", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.String()),
        sa.Column("state", sa.String(20), nullable=False, server_default="opened"),
        sa.Column("author_gitlab_id", sa.BigInteger()),
        sa.Column("author_id", UUID(as_uuid=True)),
        sa.Column("assignee_gitlab_id", sa.BigInteger()),
        sa.Column("assignee_id", UUID(as_uuid=True)),
        sa.Column("all_assignee_gitlab_ids", ARRAY(sa.BigInteger()), server_default="{}"),
        sa.Column("closed_by_gitlab_id", sa.BigInteger(), nullable=True),
        sa.Column("closed_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("labels", ARRAY(sa.String()), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["assignee_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["closed_by_id"], ["students.id"]),
        sa.UniqueConstraint("project_id", "gitlab_iid", name="uq_issues_project_iid"),
    )
    op.create_index("idx_issues_project", "issues", ["project_id"])
    op.create_index("idx_issues_closed_by_id", "issues", ["closed_by_id"])

    # ==========================================================================
    # ISSUE NOTES
    # ==========================================================================
    op.create_table(
        "issue_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("issue_id", sa.UUID(), nullable=False),
        sa.Column("gitlab_note_id", sa.BigInteger(), nullable=False),
        sa.Column("author_gitlab_id", sa.BigInteger(), nullable=True),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("author_username", sa.String(120), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["students.id"]),
        sa.UniqueConstraint("gitlab_note_id", name="uq_issue_note_gitlab_id"),
    )
    op.create_index("ix_issue_notes_issue_id", "issue_notes", ["issue_id"])
    op.create_index("ix_issue_notes_author_id", "issue_notes", ["author_id"])

    # ==========================================================================
    # MERGE REQUESTS
    # ==========================================================================
    op.create_table(
        "merge_requests",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gitlab_id", sa.BigInteger(), nullable=False),
        sa.Column("gitlab_iid", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("state", sa.String(20), nullable=False, server_default="opened"),
        sa.Column("source_branch", sa.String(200)),
        sa.Column("target_branch", sa.String(200), server_default="master"),
        sa.Column("author_gitlab_id", sa.BigInteger()),
        sa.Column("author_id", UUID(as_uuid=True)),
        sa.Column("merged_by_gitlab_id", sa.BigInteger()),
        sa.Column("merged_by_id", UUID(as_uuid=True)),
        sa.Column("linked_issue_iid", sa.Integer()),
        sa.Column("linked_issue_id", UUID(as_uuid=True)),
        sa.Column("branch_naming_ok", sa.Boolean()),
        sa.Column("template_compliant", sa.Boolean()),
        sa.Column("has_test_changes", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("has_issue_link", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("approvals_required", sa.Integer(), server_default="0"),
        sa.Column("approvals_count", sa.Integer(), server_default="0"),
        sa.Column("files_changed", sa.Integer()),
        sa.Column("lines_added", sa.Integer()),
        sa.Column("lines_removed", sa.Integer()),
        sa.Column("changed_files", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("merged_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["merged_by_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["linked_issue_id"], ["issues.id"]),
        sa.UniqueConstraint("project_id", "gitlab_iid", name="uq_mr_project_iid"),
    )
    op.create_index("idx_mr_project", "merge_requests", ["project_id"])
    op.create_index("idx_mr_state", "merge_requests", ["state"])

    # ==========================================================================
    # MERGE REQUEST DIFFS
    # ==========================================================================
    op.create_table(
        "merge_request_diffs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("merge_request_id", sa.UUID(), nullable=False),
        sa.Column("file_path", sa.String(300), nullable=False),
        sa.Column("old_path", sa.String(300), nullable=True),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("new_file", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("renamed_file", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_file", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "synced_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merge_request_id"], ["merge_requests.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("merge_request_id", "file_path", name="uq_merge_request_diff_file"),
    )
    op.create_index(
        "ix_merge_request_diffs_merge_request_id", "merge_request_diffs", ["merge_request_id"]
    )

    # ==========================================================================
    # MR NOTES
    # ==========================================================================
    op.create_table(
        "mr_notes",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("merge_request_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gitlab_note_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("author_gitlab_id", sa.BigInteger()),
        sa.Column("author_id", UUID(as_uuid=True)),
        sa.Column("author_username", sa.String(120), nullable=True),
        sa.Column("body", sa.Text()),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_resolvable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_resolved", sa.Boolean()),
        sa.Column("discussion_id", sa.String(100)),
        sa.Column("noteable_type", sa.String(50), server_default="MergeRequest"),
        sa.Column(
            "contains_commit_ref", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("commit_refs", ARRAY(sa.String()), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merge_request_id"], ["merge_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["students.id"]),
    )
    op.create_index("idx_notes_mr", "mr_notes", ["merge_request_id"])
    op.create_index("idx_notes_discussion", "mr_notes", ["discussion_id"])

    # ==========================================================================
    # MR APPROVALS
    # ==========================================================================
    op.create_table(
        "mr_approvals",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("merge_request_id", UUID(as_uuid=True), nullable=False),
        sa.Column("approver_gitlab_id", sa.BigInteger(), nullable=False),
        sa.Column("approver_id", UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merge_request_id"], ["merge_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approver_id"], ["students.id"]),
        sa.UniqueConstraint(
            "merge_request_id", "approver_gitlab_id", name="uq_mr_approval_mr_approver"
        ),
    )

    # ==========================================================================
    # REVIEW ACTIVITIES
    # ==========================================================================
    op.create_table(
        "review_activities",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("merge_request_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("note_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_words", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_chars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_note_at", sa.DateTime(timezone=True)),
        sa.Column("last_note_at", sa.DateTime(timezone=True)),
        sa.Column("is_meaningful", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recomputed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["merge_request_id"], ["merge_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["students.id"]),
        sa.UniqueConstraint(
            "merge_request_id", "reviewer_id", name="uq_review_activity_mr_reviewer"
        ),
    )
    op.create_index("idx_ra_mr", "review_activities", ["merge_request_id"])
    op.create_index("idx_ra_reviewer", "review_activities", ["reviewer_id"])

    # ==========================================================================
    # PIPELINES
    # ==========================================================================
    op.create_table(
        "pipelines",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("gitlab_pipeline_id", sa.BigInteger(), nullable=False),
        sa.Column("merge_request_id", UUID(as_uuid=True)),
        sa.Column("ref", sa.String(200)),
        sa.Column("sha", sa.String(40)),
        sa.Column("status", sa.String(30), nullable=False, server_default="created"),
        sa.Column("source", sa.String(50)),
        sa.Column("has_test_job", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("test_job_status", sa.String(30)),
        sa.Column("total_jobs", sa.Integer(), server_default="0"),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("queued_duration_seconds", sa.Integer()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["merge_request_id"], ["merge_requests.id"]),
        sa.UniqueConstraint("project_id", "gitlab_pipeline_id", name="uq_pipeline_project_glid"),
    )
    op.create_index("idx_pipelines_project", "pipelines", ["project_id"])
    op.create_index("idx_pipelines_mr", "pipelines", ["merge_request_id"])

    # ==========================================================================
    # GIT COMMITS
    # ==========================================================================
    op.create_table(
        "git_commits",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("project_id", UUID(as_uuid=True), nullable=False),
        sa.Column("sha", sa.String(40), nullable=False),
        sa.Column("short_sha", sa.String(8), nullable=False),
        sa.Column("author_name", sa.String(200), nullable=True),
        sa.Column("author_email", sa.String(200), nullable=True),
        sa.Column("author_gitlab_id", sa.BigInteger(), nullable=True),
        sa.Column("author_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("files_changed", sa.Integer(), server_default="0"),
        sa.Column("additions", sa.Integer(), server_default="0"),
        sa.Column("deletions", sa.Integer(), server_default="0"),
        sa.Column("parent_shas", ARRAY(sa.String()), server_default="{}"),
        sa.Column("ref", sa.String(200), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["gitlab_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["students.id"]),
        sa.UniqueConstraint("project_id", "sha", name="uq_commit_project_sha"),
    )
    op.create_index("idx_commits_project_id", "git_commits", ["project_id"])
    op.create_index("idx_commits_sha", "git_commits", ["sha"])
    op.create_index("idx_commits_author_email", "git_commits", ["author_email"])
    op.create_index("idx_commits_author_gitlab_id", "git_commits", ["author_gitlab_id"])
    op.create_index("idx_commits_author_id", "git_commits", ["author_id"])
    op.create_index("idx_commits_committed_at", "git_commits", ["committed_at"])
    op.create_index("idx_commits_project_author", "git_commits", ["project_id", "author_id"])

    # ==========================================================================
    # METRIC SNAPSHOTS (final column names - no renames needed)
    # ==========================================================================
    op.create_table(
        "metric_snapshots",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # R01: Issue ownership
        sa.Column("issues_assigned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "r01_issue_assigned", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R02: Branch naming
        sa.Column("branches_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("branches_correctly_named", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "r02_branch_naming", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R03: Test changes
        sa.Column("mrs_with_test_changes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "r03_test_changes", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R04: MR-Issue link
        sa.Column("mrs_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mrs_with_issue_link", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "r04_mr_issue_link", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R05: MR template
        sa.Column("mrs_template_compliant", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("own_mr_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("r05_mr_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # R06: Reviews received
        sa.Column("distinct_mrs_reviewed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meaningful_reviews_given", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "r06_reviews_received", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R07: Review duty
        sa.Column("total_review_threads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_threads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("response_rate", sa.Float()),
        sa.Column("r07_review_duty", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # R08: Response quality
        sa.Column("responses_with_commit_ref", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "r08_response_quality", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R09: Approvals
        sa.Column("own_mr_approvals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("r09_approvals", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        # R10: Merged by author
        sa.Column("own_mr_merged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "own_mr_merged_by_self", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "r10_merged_by_author", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R11: Closure state
        sa.Column("own_mr_closed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "linked_issue_closed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "r11_closure_state", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # R12: Pipeline health
        sa.Column("pipeline_total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pipeline_success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "pipeline_has_test_job", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "r12_pipeline_health", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # Aggregates
        sa.Column("checks_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checks_total", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("weighted_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("traffic_light", sa.String(10), nullable=False, server_default="GRAY"),
        sa.Column("checks_detail", JSONB(), nullable=False, server_default="{}"),
        sa.Column("bottlenecks", ARRAY(sa.String()), server_default="{}"),
        # Communication indicators
        sa.Column("median_first_response_hours", sa.Float(), nullable=True),
        sa.Column("median_review_rounds", sa.Float(), nullable=True),
        sa.Column("discussion_resolution_pct", sa.Float(), nullable=True),
        sa.Column("review_word_depth", sa.Float(), nullable=True),
        sa.Column("author_response_word_depth", sa.Float(), nullable=True),
        sa.Column("median_time_to_merge_hours", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.UniqueConstraint(
            "team_id", "student_id", "computed_at", name="uq_metric_snap_team_student_time"
        ),
    )
    op.create_index("idx_ms_team", "metric_snapshots", ["team_id"])
    op.create_index("idx_ms_student", "metric_snapshots", ["student_id"])

    # ==========================================================================
    # TEAM METRIC SNAPSHOTS
    # ==========================================================================
    op.create_table(
        "team_metric_snapshots",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("team_id", UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("members_green", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("members_yellow", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("members_red", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("members_gray", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_weighted_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("min_weighted_score", sa.Float()),
        sa.Column("max_weighted_score", sa.Float()),
        sa.Column("overall_traffic_light", sa.String(10), nullable=False, server_default="GRAY"),
        sa.Column("review_coverage_pct", sa.Float()),
        sa.Column("review_reciprocity_flag", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("team_pipeline_pass_rate", sa.Float()),
        sa.Column("bottlenecks", ARRAY(sa.String()), server_default="{}"),
        sa.Column("detail_json", JSONB(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.UniqueConstraint("team_id", "computed_at", name="uq_team_snap_team_time"),
    )

    # ==========================================================================
    # AUDIT LOG
    # ==========================================================================
    op.create_table(
        "audit_log",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False, server_default="system"),
        sa.Column("actor_ip", postgresql.INET()),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", UUID(as_uuid=True)),
        sa.Column("detail", JSONB(), nullable=False, server_default="{}"),
        sa.Column("correlation_id", UUID(as_uuid=True)),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("idx_audit_action", "audit_log", ["action"])

    # ==========================================================================
    # BACKGROUND JOBS
    # ==========================================================================
    op.create_table(
        "background_jobs",
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("rq_job_id", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False, server_default="enqueued"),
        sa.Column("team_id", UUID(as_uuid=True)),
        sa.Column("course_id", UUID(as_uuid=True)),
        sa.Column("result_summary", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "enqueued_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
    )
    op.create_index("idx_jobs_status", "background_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("background_jobs")
    op.drop_table("audit_log")
    op.drop_table("team_metric_snapshots")
    op.drop_table("metric_snapshots")
    op.drop_table("git_commits")
    op.drop_table("pipelines")
    op.drop_table("review_activities")
    op.drop_table("mr_approvals")
    op.drop_table("mr_notes")
    op.drop_table("merge_request_diffs")
    op.drop_table("merge_requests")
    op.drop_table("issue_notes")
    op.drop_table("issues")
    op.drop_table("webhook_events")
    op.drop_table("gitlab_projects")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_table("students")
    op.drop_table("course_settings")
    op.drop_table("users")
    op.drop_table("courses")
