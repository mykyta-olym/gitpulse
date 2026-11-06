"""LLM Analysis Log model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import GitLabProject


class LLMAnalysisLog(Base):
    __tablename__ = "llm_analysis_logs"
    __table_args__ = (Index("ix_llm_analysis_logs_project_mr", "project_id", "mr_iid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gitlab_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mr_iid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'mr', 'team'

    analysis_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    model_used: Mapped[str] = mapped_column(String(100), nullable=False)

    # Store the JSON result
    structured_result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    raw_prompt_redacted: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["GitLabProject"] = relationship("GitLabProject")
