"""User schemas for RBAC.

OAuth-only mode: Users are created automatically via GitLab OAuth.
These schemas are for reading and updating user data.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase


class UserRead(ORMBase):
    """User data returned from API."""

    id: UUID
    username: str
    full_name: str | None
    email: str | None
    role: str
    role_locked: bool = False
    is_active: bool
    is_bot: bool = False
    gitlab_username: str | None
    gitlab_user_id: int | None = None
    created_at: datetime


class UserUpdate(BaseModel):
    """Fields that can be updated by admin.

    Name / email / avatar are synced from GitLab on every login and
    cannot be changed manually.
    """

    role: str | None = Field(default=None, pattern=r"^(admin|teacher|student)$")
    is_active: bool | None = None
    role_locked: bool | None = None
    is_bot: bool | None = None
