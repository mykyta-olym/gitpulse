"""WebhookConfiguration - multi-scope webhook secrets per course.

Each row defines *one* webhook secret with a scope that determines
which incoming GitLab payloads it is allowed to authenticate.  See
``alembic/versions/041_webhook_configurations.py`` for the schema and
``app.services.webhook_configs`` for the service layer.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.user import User


class WebhookScope(enum.StrEnum):
    """Allowed webhook scope types.

    Stored as plain text in the database so adding a new scope is a
    pure code change without schema migration.
    """

    GROUP = "group"
    SUBGROUP = "subgroup"
    PROJECTS = "projects"
    COURSE = "course"


class WebhookConfiguration(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "webhook_configurations"
    __table_args__ = (
        CheckConstraint(
            "scope_type IN ('group', 'subgroup', 'projects', 'course')",
            name="ck_webhook_configurations_scope_type",
        ),
        CheckConstraint(
            "("
            "  (scope_type = 'projects' AND array_length(gitlab_project_ids, 1) >= 1)"
            "  OR (scope_type IN ('group','subgroup') AND gitlab_group_path IS NOT NULL)"
            "  OR (scope_type = 'course')"
            ")",
            name="ck_webhook_configurations_scope_payload",
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # -- Scope --
    scope_type: Mapped[str] = mapped_column(String(16), nullable=False)
    gitlab_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    gitlab_group_path: Mapped[str | None] = mapped_column(
        String(300), nullable=True, default=None, index=True
    )
    gitlab_project_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=list
    )

    # -- Secret material --
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    secret_lookup: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    secret_hash_previous: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default=None
    )
    secret_lookup_previous: Mapped[str | None] = mapped_column(
        String(64), nullable=True, default=None, index=True
    )
    previous_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # -- Audit / observability --
    rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # -- Relationships --
    course: Mapped[Course] = relationship("Course", lazy="selectin")
    creator: Mapped[User | None] = relationship("User", lazy="selectin")

    # -- Scope evaluation helpers --
    def matches_payload(
        self,
        *,
        project_id: int | None,
        path_with_namespace: str | None,
    ) -> bool:
        """Return True if this configuration is allowed to authenticate
        a GitLab payload with the given project id and path.

        Path comparison is case-sensitive (GitLab paths are
        case-sensitive) and boundary-aware: ``teaching/zsi-2026`` does
        **not** match ``teaching/zsi-2026-private`` - only
        ``teaching/zsi-2026`` itself or ``teaching/zsi-2026/<anything>``.

        ``course`` scope returns True unconditionally - caller must
        verify the project actually belongs to this configuration's
        course (the receiver does that via the project->team->course
        chain).
        """
        scope = self.scope_type
        if scope == WebhookScope.COURSE.value:
            return True
        if scope == WebhookScope.PROJECTS.value:
            if project_id is None:
                return False
            return project_id in (self.gitlab_project_ids or [])
        if scope in (WebhookScope.GROUP.value, WebhookScope.SUBGROUP.value):
            if not self.gitlab_group_path or not path_with_namespace:
                return False
            base = self.gitlab_group_path.strip("/").lower()
            target = path_with_namespace.strip("/").lower()
            return target == base or target.startswith(base + "/")
        return False

    def scope_summary(self) -> str:
        """Human-readable scope summary for logging / API responses."""
        scope = self.scope_type
        if scope == WebhookScope.COURSE.value:
            return "course (all projects)"
        if scope == WebhookScope.PROJECTS.value:
            ids = self.gitlab_project_ids or []
            if len(ids) <= 3:
                return f"projects: {', '.join(str(i) for i in ids)}"
            return f"projects: {len(ids)} ids"
        if scope == WebhookScope.GROUP.value:
            return f"group: {self.gitlab_group_path}"
        if scope == WebhookScope.SUBGROUP.value:
            return f"subgroup: {self.gitlab_group_path}"
        return scope
