"""CourseSettings model - per-course configuration."""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.course import Course

DEFAULT_BRANCH_PATTERN = r"^(?!(?:master|main|dev|develop|release|trunk)$).+$"


class CourseSettings(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "course_settings"
    __table_args__ = (UniqueConstraint("course_id", name="uq_course_settings_course"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    # Branch naming
    # Default pattern is permissive: accept any branch name that is NOT one of
    # the protected long-lived branches (master/main/dev/develop/release).
    # Per ZSI assignment text the course does not mandate a specific naming
    # convention, only that work happens on a separate (feature) branch.
    # Teachers can tighten this to e.g. ``^issue-\d+`` if their course requires
    # a stricter convention.
    branch_pattern: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default=DEFAULT_BRANCH_PATTERN,
    )

    # MR template
    mr_template_required_sections: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    # Review thresholds
    min_reviews_per_mr: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    # Min words for a review comment aggregate to count as "meaningful".
    # Lowered from 30 to 15: ZSI text gives no quantitative threshold, and
    # 30 words proved too strict for typical line-level review comments.
    min_review_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    min_distinct_mrs_reviewed: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    # Deadlines
    mr_creation_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    merge_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Scoring weights
    # Scoring weights for the 12 compliance checks (must sum to 1.0)
    weight_issue_ownership: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.08
    )  # R01
    weight_branch_naming: Mapped[float] = mapped_column(Float, nullable=False, default=0.06)  # R02
    weight_mr_issue_link: Mapped[float] = mapped_column(Float, nullable=False, default=0.08)  # R04
    weight_mr_template: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)  # R05
    weight_test_changes: Mapped[float] = mapped_column(Float, nullable=False, default=0.10)  # R03
    weight_review_count: Mapped[float] = mapped_column(Float, nullable=False, default=0.12)  # R06
    weight_review_duty: Mapped[float] = mapped_column(Float, nullable=False, default=0.12)  # R07
    weight_response_complete: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.10
    )  # R08
    weight_approvals: Mapped[float] = mapped_column(Float, nullable=False, default=0.09)  # R09
    weight_merge_by_author: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.07
    )  # R10
    weight_closure: Mapped[float] = mapped_column(Float, nullable=False, default=0.06)  # R11
    weight_pipeline_health: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.07
    )  # R12
    weight_commit_quality: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )  # R13 - opt-in, default 0 so existing scores unaffected

    # Traffic light thresholds
    green_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.80)
    yellow_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.50)

    # Test file patterns
    test_file_patterns: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )

    # Multi-tenant: selectively enable/disable checks
    enabled_checks: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=lambda: [
            "R01",
            "R02",
            "R03",
            "R04",
            "R05",
            "R06",
            "R07",
            "R08",
            "R10",
            "R12",
        ],
    )

    # Per-week deadline schedule:
    # [{"week": 1, "label": "Sprint 1", "mr_deadline": "...", "merge_deadline": "...",
    #   "expected_checks": ["R01", ...]}]
    weekly_deadlines: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Timeline dashboard: the Monday of week 1 for computing current academic week
    semester_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Last day of teaching / exams.  After this date + SEMESTER_GRACE_DAYS the
    # auto-archive sweep flips ``courses.is_active`` to False so every periodic
    # automation (sync, metrics, enrichment, LLM...) stops generating
    # GitLab API calls for this course.  NULL means "derive from
    # semester_start_date + default semester length" (see
    # ``app.utils.semester.get_effective_semester_end``).
    semester_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Per-course override: when True, the auto-archive sweep will NOT flip
    # this course's ``is_active`` flag even if the semester has ended.
    # Set automatically when an archived course is manually re-activated so
    # the course doesn't get re-archived on the next sweep run; teachers can
    # toggle it from the course settings page.
    skip_auto_archive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Per-check configurable thresholds and behaviour overrides (JSONB).
    # Keys are check IDs (e.g. "R01"), values are dicts with check-specific
    # options.  Unknown keys are silently ignored by the engine.
    # Example: {"R01": {"min_issues": 1}, "R12": {"require_test_job": false}}
    check_configs: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Per-check configurable thresholds and behavior overrides",
    )

    # GitLab Integration (course-level / group-level webhook)
    gitlab_group_path: Mapped[str | None] = mapped_column(String(300), nullable=True, default=None)
    # Stable numeric GitLab group id - preferred over path which can be
    # renamed.  Used by the management UI to deep-link into GitLab Group
    # Settings -> Webhooks.
    gitlab_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    webhook_secret_hash: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default=None
    )
    # §3b: Previous secret hash for zero-downtime rotation.
    # During rotation, both current and previous hashes are accepted.
    # Set to None after rotation grace period expires.
    webhook_secret_hash_previous: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default=None
    )
    # §7 (audit-batch-4): HMAC-SHA256(SECRET_KEY, secret) lookup digest.
    # Lets the orphan webhook handler authenticate via a single indexed
    # equality lookup instead of bcrypt-iterating every configured course
    # secret.  See ``app.security.webhook_auth.compute_webhook_lookup_key``.
    webhook_secret_lookup: Mapped[str | None] = mapped_column(
        String(64), nullable=True, default=None, index=True
    )
    webhook_secret_lookup_previous: Mapped[str | None] = mapped_column(
        String(64), nullable=True, default=None, index=True
    )
    # -- Group-webhook audit trail (migration 040) --
    # All four are nullable so legacy rows keep working; the management
    # API populates them on every rotate / revoke.
    webhook_secret_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    webhook_secret_rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    # When the *previous* secret stops authenticating during rotation.
    webhook_secret_previous_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    # Last time an incoming webhook authenticated against this secret.
    # Updated best-effort from the receiver - surfaces "configured but
    # never delivered" misconfigurations in the dashboard.
    webhook_secret_last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    webhook_secret_created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # LLM / AI analysis configuration
    llm_course_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="default",
        comment="Course type hint for LLM prompt: default, zsi, devops",
    )
    llm_resource_urls: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="URLs to fetch for dynamic course context [{url, label}]",
    )
    llm_custom_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Custom LLM analysis prompt body; NULL = use default",
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="settings")
