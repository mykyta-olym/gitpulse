"""Student schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMBase


class StudentCreate(BaseModel):
    gitlab_user_id: int | None = None
    gitlab_username: str | None = Field(None, max_length=100)
    full_name: str | None = Field(None, max_length=200)
    name: str | None = Field(None, max_length=200)  # alias for full_name from UI
    email: str | None = Field(None, max_length=200)
    team_id: UUID | None = None  # for UI convenience

    @model_validator(mode="after")
    def _require_identifier(self) -> "StudentCreate":
        if not self.gitlab_username and not self.email and not self.gitlab_user_id:
            msg = "At least gitlab_username, email, or gitlab_user_id is required"
            raise ValueError(msg)
        return self


class StudentRead(ORMBase):
    id: UUID
    gitlab_user_id: int | None = None
    gitlab_username: str
    full_name: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime | None = None
