"""GitLab Project model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.utils.constants import DEFAULT_BRANCH

if TYPE_CHECKING:
    from app.models.team import Team


class GitLabProject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "gitlab_projects"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gitlab_project_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    gitlab_project_path: Mapped[str] = mapped_column(String(300), nullable=False)
    gitlab_project_name: Mapped[str | None] = mapped_column(String(200))
    default_branch: Mapped[str] = mapped_column(String(100), default=DEFAULT_BRANCH)
    webhook_secret_hash: Mapped[str | None] = mapped_column(String(128))
    # HMAC-SHA256(SECRET_KEY, secret) lookup digest - see migration 037.
    webhook_secret_lookup: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Last-synced GitLab "intelligence" snapshot (protected branches, contributors,
    # repository statistics) so the project-detail panels render from STORED sync
    # data when GitLab is unreachable (expired token / maintenance window) instead
    # of failing live. Shape mirrors the route's live fetch:
    #   {"protectedBranches": [...], "contributors": [...],
    #    "statistics": {...}, "synced_at": "<iso8601>"}
    gitlab_intel: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="projects")
