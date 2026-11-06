"""Data types for GitLab OAuth integration."""

from dataclasses import dataclass


@dataclass
class GitLabUser:
    """GitLab user information from OAuth."""

    id: int
    username: str
    email: str
    name: str
    avatar_url: str | None = None


@dataclass
class GitLabGroup:
    """GitLab group membership info."""

    id: int
    name: str
    path: str
    full_path: str


@dataclass
class OAuthTokenResponse:
    """Structured OAuth token response from GitLab."""

    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"  # noqa: S105
    expires_in: int = 7200  # GitLab default: 2 hours
    created_at: int = 0
    scope: str = ""


class GitLabOAuthError(Exception):
    """Raised when OAuth flow encounters an error."""
