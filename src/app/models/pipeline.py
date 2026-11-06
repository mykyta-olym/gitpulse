"""Pipeline model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Pipeline(Base, UUIDMixin):
    __tablename__ = "pipelines"
    __table_args__ = (
        UniqueConstraint("project_id", "gitlab_pipeline_id", name="uq_pipeline_project_glid"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gitlab_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gitlab_pipeline_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    merge_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merge_requests.id"), index=True
    )
    ref: Mapped[str | None] = mapped_column(String(200))
    sha: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="created", index=True)
    source: Mapped[str | None] = mapped_column(String(50))
    has_test_job: Mapped[bool] = mapped_column(Boolean, default=False)
    test_job_status: Mapped[str | None] = mapped_column(String(30))
    # Test coverage % reported by the pipeline (GitLab `coverage`), e.g. 37.0.
    coverage: Mapped[float | None] = mapped_column(Float)
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    queued_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
