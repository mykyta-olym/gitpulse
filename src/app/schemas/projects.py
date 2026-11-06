"""GitLab project schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class ProjectRegister(BaseModel):
    gitlab_project_id: int
    gitlab_project_path: str = Field(max_length=300)
    gitlab_project_name: str | None = Field(default=None, max_length=200)


class ProjectRead(ORMBase):
    id: UUID
    team_id: UUID
    gitlab_project_id: int
    gitlab_project_path: str
    gitlab_project_name: str | None
    default_branch: str = "main"
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime


class ProjectRegistered(ProjectRead):
    """Returned once on creation - includes the plaintext webhook secret."""

    webhook_secret: str
    webhook_url: str
    setup_instructions: str
