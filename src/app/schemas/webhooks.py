"""GitLab webhook payload schemas - permissive parsing."""

from typing import Any

from pydantic import BaseModel, ConfigDict

from app.utils.constants import DEFAULT_BRANCH


class GitLabUser(BaseModel):
    id: int
    username: str = ""
    name: str = ""


class GitLabProject(BaseModel):
    id: int
    path_with_namespace: str = ""
    default_branch: str = DEFAULT_BRANCH


class ObjectAttributes(BaseModel):
    """Common fields across issue/MR/note object_attributes."""

    id: int
    iid: int | None = None
    title: str | None = None
    description: str | None = None
    state: str | None = None
    action: str | None = None
    source_branch: str | None = None
    target_branch: str | None = None
    author_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    # Note-specific
    note: str | None = None
    noteable_type: str | None = None
    noteable_id: int | None = None
    discussion_id: str | None = None
    system: bool | None = None
    # MR-specific
    merge_status: str | None = None
    # Pipeline-specific
    status: str | None = None
    ref: str | None = None
    sha: str | None = None
    duration: int | None = None
    # A pipeline's source is a word ("push", "merge_request_event"); a merge
    # request's is its source project - GitLab sends both under this key.
    source: str | dict[str, Any] | None = None


class WebhookPayload(BaseModel):
    """Top-level GitLab webhook payload. Extra fields are allowed/ignored."""

    object_kind: str = ""
    event_type: str | None = None
    user: GitLabUser | None = None
    project: GitLabProject | None = None
    object_attributes: ObjectAttributes | None = None

    model_config = ConfigDict(extra="allow")


class WebhookAcceptedResponse(BaseModel):
    status: str
    event_id: str
    message: str = "Event enqueued for processing"
