"""API endpoint for parsing GitLab URLs and auto-detecting resource types."""

import re
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import quote as url_quote
from urllib.parse import urlparse

import structlog
from fastapi import APIRouter

from app.api.errors import raise_bad_request
from app.config import get_settings
from app.dependencies import ApiAuth
from app.schemas.gitlab_parse import GitLabParsedResource, GitLabURLParseRequest
from app.services.gitlab.client import GitLabClient

logger = structlog.get_logger(__name__)
router = APIRouter()


# URL patterns for different GitLab resources
GITLAB_PATTERNS = [
    # Issues: /group/project/-/issues/123
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/issues/(?P<iid>\d+)", "issue"),
    # Merge Requests: /group/project/-/merge_requests/123
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/merge_requests/(?P<iid>\d+)", "merge_request"),
    # Pipelines: /group/project/-/pipelines/123
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/pipelines/(?P<pipeline_id>\d+)", "pipeline"),
    # Jobs: /group/project/-/jobs/123
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/jobs/(?P<job_id>\d+)", "job"),
    # Commits: /group/project/-/commit/abc123
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/commit/(?P<sha>[a-f0-9]+)", "commit"),
    # Branches: /group/project/-/tree/branch-name
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/tree/(?P<ref>.+)", "branch"),
    # Tags: /group/project/-/tags/v1.0.0
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/tags/(?P<tag>.+)", "tag"),
    # Files: /group/project/-/blob/main/path/to/file
    (r"^(?P<namespace>.+?)/(?P<project>[^/]+)/-/blob/(?P<ref>[^/]+)/(?P<file_path>.+)", "file"),
    # Project root: /group/project or /group/subgroup/project
    (r"^(?P<namespace>.+?)/(?P<project>[^/-][^/]*)$", "project"),
    # Groups: /groups/group-path
    (r"^groups/(?P<group_path>.+)", "group"),
    # Users: /username or /@username
    (r"^@?(?P<username>[a-zA-Z0-9_.-]+)$", "user"),
]


def parse_gitlab_path(path: str) -> tuple[str, dict[str, str]] | None:
    """Parse GitLab URL path to extract resource type and parameters."""
    # Clean path
    path = path.strip("/")

    for pattern, resource_type in GITLAB_PATTERNS:
        match = re.match(pattern, path)
        if match:
            return resource_type, match.groupdict()

    return None


def _project_path(params: dict[str, str]) -> str:
    return f"{params.get('namespace', '')}/{params.get('project', '')}"


async def _project_data(client: GitLabClient, full_path: str) -> dict[str, Any] | None:
    return await client._get_dict(f"/projects/{url_quote(full_path, safe='')}")


async def _enrich_project(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    namespace = params.get("namespace", "")
    project = params.get("project", "")
    full_path = f"{namespace}/{project}" if namespace else project
    project_data = await _project_data(client, full_path)
    if project_data:
        response.gitlab_id = project_data.get("id")
        response.path = project_data.get("path_with_namespace")
        response.name = project_data.get("name")
        response.namespace = project_data.get("namespace", {}).get("full_path")
        response.extra = {
            "description": project_data.get("description"),
            "default_branch": project_data.get("default_branch"),
            "visibility": project_data.get("visibility"),
            "avatar_url": project_data.get("avatar_url"),
        }


async def _enrich_group(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    group_path = params.get("group_path", "")
    group_data = await client._get_dict(f"/groups/{url_quote(group_path, safe='')}")
    if group_data:
        response.gitlab_id = group_data.get("id")
        response.path = group_data.get("full_path")
        response.name = group_data.get("name")
        response.extra = {
            "description": group_data.get("description"),
            "visibility": group_data.get("visibility"),
            "avatar_url": group_data.get("avatar_url"),
        }


async def _enrich_user(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    username = params.get("username", "")
    users = await client._get_list("/users", params={"username": username})
    if users and len(users) > 0:
        user_data = users[0]
        response.gitlab_id = user_data.get("id")
        response.path = user_data.get("username")
        response.name = user_data.get("name")
        response.extra = {
            "username": user_data.get("username"),
            "avatar_url": user_data.get("avatar_url"),
            "state": user_data.get("state"),
        }


async def _enrich_issue_or_mr(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    full_path = _project_path(params)
    iid = int(params.get("iid", 0))
    project_data = await _project_data(client, full_path)
    if not project_data:
        return
    project_id = project_data["id"]
    response.namespace = full_path
    response.iid = iid
    if response.resource_type == "issue":
        issue_data = await client.get_issue(project_id, iid)
        if issue_data:
            response.gitlab_id = issue_data.get("id")
            response.name = issue_data.get("title")
            response.extra = {
                "state": issue_data.get("state"),
                "author": issue_data.get("author", {}).get("name"),
                "labels": issue_data.get("labels", []),
                "project_id": project_id,
            }
        return
    mr_data = await client.get_merge_request(project_id, iid)
    if mr_data:
        response.gitlab_id = mr_data.get("id")
        response.name = mr_data.get("title")
        response.ref = mr_data.get("source_branch")
        response.extra = {
            "state": mr_data.get("state"),
            "author": mr_data.get("author", {}).get("name"),
            "source_branch": mr_data.get("source_branch"),
            "target_branch": mr_data.get("target_branch"),
            "project_id": project_id,
        }


async def _enrich_commit(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    sha = params.get("sha", "")
    full_path = _project_path(params)
    project_data = await _project_data(client, full_path)
    if not project_data:
        return
    project_id = project_data["id"]
    commit_data = await client._get_dict(f"/projects/{project_id}/repository/commits/{sha}")
    if commit_data:
        response.gitlab_id = None
        response.path = sha
        response.name = commit_data.get("title")
        response.namespace = full_path
        response.extra = {
            "sha": commit_data.get("id"),
            "short_id": commit_data.get("short_id"),
            "author_name": commit_data.get("author_name"),
            "authored_date": commit_data.get("authored_date"),
            "message": commit_data.get("message"),
            "project_id": project_id,
        }


async def _enrich_branch(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    # Nothing to look up: the URL names it.
    full_path = _project_path(params)
    ref = params.get("ref", "")
    response.namespace = full_path
    response.ref = ref
    response.name = ref
    response.path = full_path


async def _enrich_pipeline(
    client: GitLabClient, params: dict[str, str], response: GitLabParsedResource
) -> None:
    pipeline_id = int(params.get("pipeline_id", 0))
    full_path = _project_path(params)
    project_data = await _project_data(client, full_path)
    if not project_data:
        return
    project_id = project_data["id"]
    pipeline_data = await client.get_pipeline(project_id, pipeline_id)
    if pipeline_data:
        response.gitlab_id = pipeline_data.get("id")
        response.ref = pipeline_data.get("ref")
        response.namespace = full_path
        response.extra = {
            "status": pipeline_data.get("status"),
            "sha": pipeline_data.get("sha"),
            "created_at": pipeline_data.get("created_at"),
            "project_id": project_id,
        }


_Enricher = Callable[[GitLabClient, dict[str, str], GitLabParsedResource], Awaitable[None]]
# Jobs, tags and files are recognised but not looked up.
_ENRICH: dict[str, _Enricher] = {
    "project": _enrich_project,
    "group": _enrich_group,
    "user": _enrich_user,
    "issue": _enrich_issue_or_mr,
    "merge_request": _enrich_issue_or_mr,
    "commit": _enrich_commit,
    "branch": _enrich_branch,
    "pipeline": _enrich_pipeline,
}


def _fill_from_url(params: dict[str, str], response: GitLabParsedResource) -> None:
    """What the URL alone says, when GitLab could not be asked."""
    resource_type = response.resource_type
    if resource_type == "project":
        response.path = _project_path(params)
        response.name = params.get("project")
        response.namespace = params.get("namespace")
    elif resource_type == "group":
        response.path = params.get("group_path")
        response.name = params.get("group_path", "").split("/")[-1]
    elif resource_type == "user":
        response.path = params.get("username")
        response.name = params.get("username")
    elif resource_type in ("issue", "merge_request"):
        response.namespace = _project_path(params)
        response.iid = int(params.get("iid", 0))
    elif resource_type == "commit":
        response.namespace = _project_path(params)
        response.path = params.get("sha")
    elif resource_type == "branch":
        response.namespace = _project_path(params)
        response.ref = params.get("ref")


@router.post("/parse-url", response_model=GitLabParsedResource)
async def parse_gitlab_url(
    request: GitLabURLParseRequest,
    _auth: ApiAuth,
) -> GitLabParsedResource:
    """
    Parse a GitLab URL and extract resource information.

    Supports:
    - Projects: https://gitlab.com/group/project
    - Groups: https://gitlab.com/groups/group-name
    - Issues: https://gitlab.com/group/project/-/issues/123
    - Merge Requests: https://gitlab.com/group/project/-/merge_requests/456
    - Pipelines: https://gitlab.com/group/project/-/pipelines/789
    - Commits: https://gitlab.com/group/project/-/commit/abc123
    - Users: https://gitlab.com/username or https://gitlab.com/@username
    - Branches: https://gitlab.com/group/project/-/tree/main
    - Files: https://gitlab.com/group/project/-/blob/main/README.md
    """
    url = request.url.strip()
    settings = get_settings()
    # A plain path or username is relative to the configured GitLab.
    if not url.startswith(("http://", "https://")):
        url = f"{settings.gitlab_url}/{url}"

    path = urlparse(url).path.strip("/")
    if not path:
        raise_bad_request("Invalid GitLab URL: no path found")
    result = parse_gitlab_path(path)
    if not result:
        raise_bad_request(f"Could not parse GitLab URL: {url}")
    resource_type, params = result

    response = GitLabParsedResource(resource_type=resource_type, web_url=url)
    try:
        async with GitLabClient(
            base_url=str(settings.gitlab_url),
            private_token=settings.gitlab_api_token,
            timeout=settings.gitlab_api_timeout_seconds,
        ) as client:
            enrich = _ENRICH.get(resource_type)
            if enrich:
                await enrich(client, params, response)
    except Exception as e:
        logger.warning("gitlab_api_lookup_failed", error=str(e), url=url)
        # Return basic parsed info without API enrichment
        _fill_from_url(params, response)

    return response
