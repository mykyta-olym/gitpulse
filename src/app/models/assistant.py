"""Classroom assistant - a course's bot account and what it follows.

GitPulse watches with a read-only token. The assistant is the one part that
acts in GitLab - it comments, plants a merge conflict, opens issues, approves
and merges - so it runs as its own bot account with its own token, stored here
per course. Students never see a GitPulse page for it: they meet it in GitLab,
as a colleague on the project.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin

#: The tools, in the order the page lists them.
TOOL_PUSH_REVIEW = "push_review"
TOOL_CONFLICT = "conflict"
TOOL_MR_REVIEW = "mr_review"
TOOLS = (TOOL_PUSH_REVIEW, TOOL_CONFLICT, TOOL_MR_REVIEW)

# What a course starts with, before a teacher changes anything.
DEFAULT_MIN_COMMIT_TITLE_LENGTH = 10
DEFAULT_CONFLICT_FILE = "README.md"
DEFAULT_EXERCISE_FILE_TEMPLATE = "ulohy/{username}.txt"
DEFAULT_COMMENT_LANGUAGE = "sk"


class CourseAssistant(Base, UUIDMixin, TimestampMixin):
    """One course's assistant: the bot it acts as and the tools it runs."""

    __tablename__ = "course_assistants"
    __table_args__ = (UniqueConstraint("course_id", name="uq_course_assistants_course"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    # The bot's token, Fernet-encrypted (app.security.token_encryption). NULL
    # until a teacher connects one; the tools run only while it is set.
    bot_token: Mapped[str | None] = mapped_column(String(500))
    # Who the token is, read from GitLab when it was connected - the assistant
    # ignores the events its own actions cause by this id.
    bot_user_id: Mapped[int | None] = mapped_column(BigInteger)
    bot_username: Mapped[str | None] = mapped_column(String(100))
    bot_name: Mapped[str | None] = mapped_column(String(200))
    bot_avatar_url: Mapped[str | None] = mapped_column(String(500))
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When GitLab last answered the token with 401; the assistant stops until a
    # teacher connects a new one.
    token_rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    connected_by: Mapped[str | None] = mapped_column(String(100))
    # The language the bot writes in GitLab (``app.i18n.SUPPORTED_LOCALES``).
    comment_language: Mapped[str] = mapped_column(
        String(5), nullable=False, default=DEFAULT_COMMENT_LANGUAGE, server_default="sk"
    )

    # Push review: a comment on a pushed commit about how it was pushed.
    push_review_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    min_commit_title_length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_MIN_COMMIT_TITLE_LENGTH,
        server_default=str(DEFAULT_MIN_COMMIT_TITLE_LENGTH),
    )

    # Merge conflict: a colleague's commit on the default branch that edits
    # the lines a student's branch edits in this file.
    conflict_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    conflict_file_path: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default=DEFAULT_CONFLICT_FILE,
        server_default=DEFAULT_CONFLICT_FILE,
    )

    # Issues and merge requests: an issue per student, reviewed, approved and
    # merged when the merge request does what the issue asked.
    mr_review_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # Off: the assistant approves and the student merges - R10 counts a merge
    # by a bot as not the student's. On: it merges the approved request itself.
    mr_bot_merges: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    exercise_file_template: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        default=DEFAULT_EXERCISE_FILE_TEMPLATE,
        server_default=DEFAULT_EXERCISE_FILE_TEMPLATE,
    )
    # What the last "Prepare exercise" run did, per project:
    # {"at": iso, "by": username, "projects": [{"path", "created", "skipped", "error"}]}
    last_exercise_run: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    @property
    def is_connected(self) -> bool:
        return bool(self.bot_token)

    def can_act(self, now: datetime) -> bool:
        """Connected, and with a token GitLab still takes."""
        if not self.bot_token or self.token_rejected_at is not None:
            return False
        return self.token_expires_at is None or self.token_expires_at > now


class AssistantTask(Base, UUIDMixin, TimestampMixin):
    """One thing the assistant follows for one student - a push it reviewed, a
    conflict it planted, an issue it assigned - and where that stands.

    ``key`` makes the row unique per project and tool: the pushed commit for a
    push review, the student for a conflict (one exercise each), the issue for
    a merge-request review.
    """

    __tablename__ = "assistant_tasks"
    __table_args__ = (
        UniqueConstraint("project_id", "tool", "key", name="uq_assistant_tasks_project_tool_key"),
        Index("ix_assistant_tasks_course_updated", "course_id", "updated_at"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gitlab_projects.id", ondelete="CASCADE"), nullable=False
    )
    tool: Mapped[str] = mapped_column(String(20), nullable=False)
    key: Mapped[str] = mapped_column(String(300), nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)

    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL")
    )
    student_username: Mapped[str | None] = mapped_column(String(100))
    branch: Mapped[str | None] = mapped_column(String(255))
    issue_iid: Mapped[int | None] = mapped_column(Integer)
    mr_iid: Mapped[int | None] = mapped_column(Integer)
    # The reviewed commit (push review) or the colleague's commit (conflict).
    commit_sha: Mapped[str | None] = mapped_column(String(64))
    file_path: Mapped[str | None] = mapped_column(String(300))

    # Tool-specific facts the next step needs (the control line, the lines the
    # student wrote, the signature of the last review).
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # What the assistant did, oldest first: [{"at", "action", "note", "url"}].
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
