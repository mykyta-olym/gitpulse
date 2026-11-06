"""Pure helpers for GitLab group import: bot detection and path parsing.

No database or orchestration logic lives here - only deterministic functions
over GitLab API dicts, so both the orchestrator and persistence layers can import
them without creating an import cycle.
"""

import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

import structlog

from app.services.gitlab_import.normalize import (
    _normalize_optional,
    _to_int,
)

logger = structlog.get_logger(__name__)


_GITLAB_PATH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(/[A-Za-z0-9][A-Za-z0-9._-]*)*$")


def _validate_gitlab_resource_path(path: str) -> None:
    """Reject malformed GitLab resource paths before any upstream API call."""
    if not _GITLAB_PATH_RE.fullmatch(path):
        raise ValueError(
            "Enter a valid GitLab group or project URL/path "
            "(letters, numbers, dots, underscores, dashes, and slashes only)"
        )
    if any(part in {".", ".."} for part in path.split("/")):
        raise ValueError("Enter a valid GitLab group or project URL/path")


# -- Bot / service-account detection --
# GitLab creates internal accounts with predictable username patterns.
# These should never be imported as students.
_BOT_USERNAME_EXACT: frozenset[str] = frozenset(
    {
        "ghost",
        "alert-bot",
        "support-bot",
        "admin",
        "root",
    }
)
_BOT_USERNAME_PREFIXES: tuple[str, ...] = (
    "project_",  # project_{id}_bot, project_{id}_bot1
    "group_",  # group_{id}_bot
)
_BOT_USERNAME_SUFFIXES: tuple[str, ...] = (
    "_bot",
    "-bot",
    "_bot1",
    "_bot2",
)


def is_bot_user(
    username: str,
    *,
    user_type: str | None = None,
    email: str | None = None,
) -> bool:
    """Return True when *username* looks like a GitLab service account / bot.

    Detection layers (in order of confidence):
    1. GitLab API ``user_type`` field (most reliable when present).
    2. Known exact usernames (``ghost``, ``alert-bot``, ...).
    3. Username prefix/suffix heuristics (``project_*_bot*``, ``*-bot``, etc.).
    4. Email plus-aliases (``foo+gitpulse@...``, ``foo+bot@...``, ...) which are
       the canonical pattern for institutional service accounts that share
       a real user's mailbox.
    """
    if user_type and user_type in {
        "project_bot",
        "group_bot",
        "service_account",
        "alert_bot",
        "placeholder",
        "admin_bot",
    }:
        return True
    low = username.lower().strip()
    if low in _BOT_USERNAME_EXACT:
        return True
    if low.startswith(_BOT_USERNAME_PREFIXES):
        return True
    if low.endswith(_BOT_USERNAME_SUFFIXES):
        return True
    if email:
        e = email.strip().lower()
        # Plus-aliasing in the local part (``user+tag@domain``) is almost
        # never used for an interactive human account; in academic
        # deployments it is the standard way to register a CI / GitPulse /
        # automation account that shares the owner's mailbox.
        if "@" in e:
            local, _, _ = e.partition("@")
            if "+" in local:
                return True
    return False


def _detect_historical_projects(
    project_dicts: list[dict[str, Any]],
    semester_start: Any | None,
) -> list[str]:
    """Return warning strings for projects whose GitLab created_at predates semester_start."""
    if not semester_start or not project_dicts:
        return []

    ref: date
    if isinstance(semester_start, date):
        ref = semester_start
    elif isinstance(semester_start, datetime):
        ref = semester_start.date()
    else:
        return []

    old: list[str] = []
    for p in project_dicts:
        raw_ca = p.get("created_at")
        if not raw_ca:
            continue
        try:
            if isinstance(raw_ca, str):
                ca = datetime.fromisoformat(raw_ca).date()
            elif isinstance(raw_ca, datetime):
                ca = raw_ca.date()
            elif isinstance(raw_ca, date):
                ca = raw_ca
            else:
                continue
        except (ValueError, TypeError):
            continue
        if ca < ref:
            name = p.get("path_with_namespace") or p.get("name") or str(p.get("id", "?"))
            old.append(name)

    if not old:
        return []
    return [
        f"Detected {len(old)} project(s) created before semester start ({ref.isoformat()}): "
        + ", ".join(old[:5])
        + (f" ... and {len(old) - 5} more" if len(old) > 5 else "")
        + ". Weekly analytics will auto-adjust the reference date to include historical data."
    ]


def extract_group_path_from_input(group_url: str, gitlab_base_url: str) -> str:
    """Extract GitLab group/project path from URL or plain path input.

    Accepted:
    - https://git.example.com/groups/org/subgroup
    - https://git.example.com/org/subgroup
    - https://git.example.com/user/project.git
    - groups/org/subgroup
    - org/subgroup
    - user/project.git
    """
    raw = group_url.strip()
    if not raw:
        raise ValueError("Group URL/path is required")

    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        base_host = urlparse(gitlab_base_url).netloc
        if parsed.netloc and base_host and parsed.netloc != base_host:
            logger.warning(
                "group_import_foreign_host",
                expected_host=base_host,
                actual_host=parsed.netloc,
            )
        from urllib.parse import unquote

        path = unquote(parsed.path.strip("/"))
    else:
        path = raw.strip("/")

    path = path.removeprefix("groups/")

    # Defensive: remove possible "/-/<resource>" suffix
    if "/-/" in path:
        path = path.split("/-/", maxsplit=1)[0]

    # Strip .git suffix (common for project clone URLs)
    path = path.removesuffix(".git")

    path = path.strip("/")
    if not path:
        raise ValueError("Could not determine GitLab group/project path from input")
    _validate_gitlab_resource_path(path)

    return path


def match_team_group_path(namespace_path: str, team_group_paths: list[str]) -> str | None:
    """Select the most specific team path matching a project namespace."""
    matches = [
        path
        for path in team_group_paths
        if namespace_path == path or namespace_path.startswith(f"{path}/")
    ]
    if not matches:
        return None
    return max(matches, key=len)


def select_team_group_records(
    group_records: list[dict[str, Any]],
    *,
    root_group_id: int,
    project_namespace_paths: set[str],
) -> list[dict[str, Any]]:
    """Choose groups that should be represented as teams.

    Priority:
    1) groups that directly host projects (namespace appears in project list),
    2) fallback to all non-root groups when no project namespaces match,
    3) fallback to root-only when root is the only discovered group.
    """
    if not group_records:
        return []

    if len(group_records) == 1:
        return list(group_records)

    selected_by_projects: list[dict[str, Any]] = []
    for group in group_records:
        full_path = _normalize_optional(group.get("full_path"))
        if full_path and full_path in project_namespace_paths:
            selected_by_projects.append(group)

    if selected_by_projects:
        return selected_by_projects

    non_root_groups = [g for g in group_records if _to_int(g.get("id")) != root_group_id]
    return non_root_groups or list(group_records)
