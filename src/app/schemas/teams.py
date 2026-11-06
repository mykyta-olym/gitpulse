"""Team schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMBase


class TeamCreate(BaseModel):
    name: str = Field(..., max_length=100)
    course_id: UUID | None = None
    gitlab_group_id: int | None = None
    gitlab_group_path: str | None = Field(None, max_length=300)

    @field_validator("name")
    @classmethod
    def _name_must_be_meaningful(cls, v: str) -> str:
        """Reject blank / single-character garbage (e.g. a stray "ф") and trim
        surrounding whitespace so a group always has a real, usable name."""
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Group name must be at least 2 non-space characters.")
        return stripped


class TeamUpdate(BaseModel):
    is_active: bool | None = None
    expected_updated_at: datetime | None = Field(
        default=None,
        description="Optimistic lock: expected updated_at timestamp. Returns 409 if stale.",
    )


class TeamRead(ORMBase):
    id: UUID
    course_id: UUID
    name: str
    gitlab_group_id: int | None
    gitlab_group_path: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
