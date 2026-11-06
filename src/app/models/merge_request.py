"""Merge Request model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin
from app.utils.constants import DEFAULT_BRANCH


class MergeRequest(Base, UUIDMixin):
    __tablename__ = "merge_requests"
    __table_args__ = (UniqueConstraint("project_id", "gitlab_iid", name="uq_mr_project_iid"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gitlab_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gitlab_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    gitlab_iid: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="opened", index=True)
    source_branch: Mapped[str | None] = mapped_column(String(200))
    target_branch: Mapped[str] = mapped_column(String(200), default=DEFAULT_BRANCH)
    author_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    merged_by_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    merged_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id")
    )

    # Explicit GitLab assignee / reviewers (the actual "assigned vs reviewer"
    # signal, distinct from who happened to comment). Reviewer + approver ids
    # are stored as GitLab user ids and resolved to roster names at display.
    assignee_gitlab_id: Mapped[int | None] = mapped_column(BigInteger)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id")
    )
    reviewer_gitlab_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)
    approved_by_gitlab_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)

    # Linked issue
    linked_issue_iid: Mapped[int | None] = mapped_column(Integer)
    linked_issue_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("issues.id"), index=True
    )

    # Compliance flags
    branch_naming_ok: Mapped[bool | None] = mapped_column(Boolean)
    template_compliant: Mapped[bool | None] = mapped_column(Boolean)
    has_test_changes: Mapped[bool] = mapped_column(Boolean, default=False)
    has_issue_link: Mapped[bool] = mapped_column(Boolean, default=False)

    # Approvals
    approvals_required: Mapped[int] = mapped_column(Integer, default=0)
    approvals_count: Mapped[int] = mapped_column(Integer, default=0)

    # Diff stats
    files_changed: Mapped[int | None] = mapped_column(Integer)
    lines_added: Mapped[int | None] = mapped_column(Integer)
    lines_removed: Mapped[int | None] = mapped_column(Integer)
    changed_files: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    #: The commits GitLab reports for THIS merge request
    #: (``/merge_requests/:iid/commits``) - which is not the same set as "every
    #: commit on the source branch". A branch forked from a template carries the
    #: template's whole history, and listing that made one MR show 30 commits
    #: (23 of them the teacher's, from years before the assignment) where GitLab
    #: showed 7. It cannot be derived from what else is stored: ``git_commits``
    #: keeps one ref per commit and the default branch is never synced.
    #: NULL means the exact MR list is unknown. The page labels its saved branch
    #: fallback explicitly; the next sync backfills it even if the MR is unchanged.
    commit_shas: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Branch lifecycle
    # True when the source branch was deleted after the MR was merged
    # (either via GitLab's auto-delete setting or manual deletion).
    # Used to show a badge and explain why commits were recovered via the MR API.
    source_branch_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # -- Computed properties (used by dynamic checks) --

    _DOC_NAMES = frozenset(
        {
            "readme.md",
            "readme.txt",
            "readme.rst",
            "readme",
            "contributing.md",
            "changelog.md",
            "license.md",
        }
    )

    @property
    def has_doc_changes(self) -> bool:
        """True when any changed file is a documentation artefact.

        Matches README variants, docs/ or doc/ directories, and
        standalone ``.md`` / ``.rst`` files at the repo root.
        Used by the C02 custom-check ``field_check`` rule.
        """
        if not self.changed_files:
            return False
        for fp in self.changed_files:
            low = fp.lower()
            basename = low.rsplit("/", 1)[-1]
            if basename in self._DOC_NAMES:
                return True
            if low.startswith(("docs/", "doc/")):
                return True
        return False
