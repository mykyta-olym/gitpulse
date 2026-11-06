"""GitLab URL parsing request/response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class GitLabURLParseRequest(BaseModel):
    """Request model for parsing GitLab URLs."""

    url: str = Field(..., description="GitLab URL to parse")


class GitLabParsedResource(BaseModel):
    """Parsed GitLab resource information."""

    resource_type: str = Field(
        ..., description="Type of resource: project, group, user, issue, mr, commit, etc."
    )
    gitlab_id: int | None = Field(default=None, description="GitLab numeric ID if available")
    path: str | None = Field(default=None, description="Full path with namespace")
    name: str | None = Field(default=None, description="Display name")
    namespace: str | None = Field(default=None, description="Group/namespace path")
    iid: int | None = Field(default=None, description="Issue or MR IID within project")
    ref: str | None = Field(default=None, description="Branch or tag reference")
    web_url: str | None = Field(default=None, description="Web URL")
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Additional resource-specific data"
    )
