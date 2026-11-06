"""Pydantic schemas for multi-scope webhook configurations API.

Mirrors :class:`app.models.webhook_configuration.WebhookConfiguration`
with strict validation: scope payload coherence, name length, project
id positivity & uniqueness, etc.  Mutating ``scope_type`` after
creation is not supported (see service layer rationale).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ScopeType = Literal["group", "subgroup", "projects", "course"]


def _normalize_path(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip("/")
    return cleaned.lower() or None


class _ScopeFieldsMixin(BaseModel):
    gitlab_group_id: int | None = Field(default=None, ge=1)
    gitlab_group_path: str | None = Field(default=None, max_length=300)
    gitlab_project_ids: list[Annotated[int, Field(ge=1)]] = Field(default_factory=list)

    @field_validator("gitlab_group_path")
    @classmethod
    def _normalize_group_path(cls, v: str | None) -> str | None:
        return _normalize_path(v)

    @field_validator("gitlab_project_ids")
    @classmethod
    def _dedupe_ids(cls, v: list[int]) -> list[int]:
        if not v:
            return []
        if len(set(v)) != len(v):
            raise ValueError("gitlab_project_ids must be unique")
        return sorted(v)


class WebhookConfigCreate(_ScopeFieldsMixin):
    """Request body for creating a new webhook configuration."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    scope_type: ScopeType

    @model_validator(mode="after")
    def _scope_payload_consistent(self) -> WebhookConfigCreate:
        if self.scope_type == "projects" and not self.gitlab_project_ids:
            raise ValueError("scope_type='projects' requires at least one gitlab_project_id")
        if self.scope_type in ("group", "subgroup") and not self.gitlab_group_path:
            raise ValueError(f"scope_type='{self.scope_type}' requires gitlab_group_path")
        return self


class WebhookConfigUpdate(BaseModel):
    """Patch body - every field optional, scope_type immutable."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    gitlab_group_id: int | None = Field(default=None, ge=1)
    gitlab_group_path: str | None = Field(default=None, max_length=300)
    gitlab_project_ids: list[Annotated[int, Field(ge=1)]] | None = None
    is_active: bool | None = None

    @field_validator("gitlab_group_path")
    @classmethod
    def _normalize_group_path(cls, v: str | None) -> str | None:
        return _normalize_path(v)

    @field_validator("gitlab_project_ids")
    @classmethod
    def _dedupe_ids(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        if len(set(v)) != len(v):
            raise ValueError("gitlab_project_ids must be unique")
        return sorted(v)


class WebhookConfigRead(BaseModel):
    """Response model - never includes secret material."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    name: str
    description: str | None
    scope_type: ScopeType
    scope_summary: str
    gitlab_group_id: int | None
    gitlab_group_path: str | None
    gitlab_project_ids: list[int]
    is_active: bool
    created_at: datetime
    rotated_at: datetime | None
    last_used_at: datetime | None
    previous_expires_at: datetime | None
    has_previous_secret: bool
    has_secret: bool


class WebhookConfigRevealResponse(BaseModel):
    """Response body for create / rotate - reveals plaintext exactly once."""

    config: WebhookConfigRead
    webhook_secret: str
    first_time: bool
    rotated_at: datetime | None
    previous_expires_at: datetime | None
    grace_seconds: int | None
    webhook_url: str
    setup_instructions: dict[str, Any]


class WebhookConfigListResponse(BaseModel):
    """List view for the management UI."""

    course_id: uuid.UUID
    webhook_url: str
    configurations: list[WebhookConfigRead]


class WebhookConfigRevokeResponse(BaseModel):
    """Response body for DELETE - confirms revocation."""

    status: str
    deleted: bool
    config_id: uuid.UUID
