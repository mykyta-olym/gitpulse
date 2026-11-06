"""GitLab OAuth2 authentication for the teacher dashboard.

This module implements the OAuth2 Authorization Code flow for GitLab authentication.
Teacher role is determined via GitLab group membership or a configurable allowlist.

Token lifecycle:
    1. User authorizes -> we receive authorization code
    2. Code exchange -> access_token + refresh_token + expires_in
    3. Tokens stored encrypted in User model (gitlab_access_token, gitlab_refresh_token)
    4. On session validation, if token is near expiry -> auto-refresh via refresh_token
    5. If refresh fails -> redirect to login
"""

import secrets
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx
import structlog

from app.security.gitlab_oauth_types import (
    GitLabGroup,
    GitLabOAuthError,
    GitLabUser,
    OAuthTokenResponse,
)

if TYPE_CHECKING:
    from app.config import Settings

# Re-export for backward compatibility
__all__ = [
    "GitLabGroup",
    "GitLabOAuth",
    "GitLabOAuthError",
    "GitLabUser",
    "OAuthTokenResponse",
]

logger = structlog.get_logger(__name__)


class GitLabOAuth:
    """GitLab OAuth2 client for authentication and group membership checks."""

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.gitlab_url = settings.gitlab_url.rstrip("/")
        self.client_id = settings.gitlab_oauth_client_id
        self.client_secret = settings.gitlab_oauth_client_secret
        self.redirect_uri = f"{settings.app_base_url.rstrip('/')}/dashboard/oauth/callback"

    @staticmethod
    def generate_state() -> str:
        """Generate a secure random state for CSRF protection in OAuth flow."""
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, state: str) -> str:
        """Build the GitLab OAuth authorization URL.

        Args:
            state: CSRF protection state token

        Returns:
            Full GitLab authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "read_user read_api",
            "state": state,
        }
        return f"{self.gitlab_url}/oauth/authorize?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> OAuthTokenResponse:
        """Exchange authorization code for access + refresh tokens.

        Args:
            code: Authorization code from GitLab callback

        Returns:
            OAuthTokenResponse with access_token, refresh_token, and expires_in

        Raises:
            GitLabOAuthError: If token exchange fails
        """
        token_url = f"{self.gitlab_url}/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient(timeout=self.settings.gitlab_api_timeout_seconds) as client:
            try:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()
                access_token: str = token_data.get("access_token", "")
                if not access_token:
                    raise GitLabOAuthError("No access token in response")
                return OAuthTokenResponse(
                    access_token=access_token,
                    refresh_token=token_data.get("refresh_token", ""),
                    token_type=token_data.get("token_type", "bearer"),
                    expires_in=token_data.get("expires_in", 7200),
                    created_at=token_data.get("created_at", 0),
                    scope=token_data.get("scope", ""),
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    "gitlab_oauth_token_exchange_failed",
                    status_code=e.response.status_code,
                    response_text=e.response.text,
                )
                raise GitLabOAuthError(f"Token exchange failed: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error("gitlab_oauth_request_failed", error=str(e))
                raise GitLabOAuthError(f"Request failed: {e}") from e
            except GitLabOAuthError:
                raise
            except (KeyError, TypeError, ValueError) as e:
                logger.error("gitlab_oauth_token_parse_failed", error=str(e))
                raise GitLabOAuthError(f"Failed to parse token response: {e}") from e

    async def refresh_access_token(self, refresh_token: str) -> OAuthTokenResponse:
        """Use refresh_token to obtain a new access_token.

        Args:
            refresh_token: Valid refresh token from previous token exchange

        Returns:
            OAuthTokenResponse with new access_token and possibly new refresh_token

        Raises:
            GitLabOAuthError: If refresh fails (user must re-login)
        """
        token_url = f"{self.gitlab_url}/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient(timeout=self.settings.gitlab_api_timeout_seconds) as client:
            try:
                response = await client.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()
                access_token: str = token_data.get("access_token", "")
                if not access_token:
                    raise GitLabOAuthError("No access token in refresh response")
                logger.info(
                    "gitlab_oauth_token_refreshed",
                    expires_in=token_data.get("expires_in"),
                )
                return OAuthTokenResponse(
                    access_token=access_token,
                    refresh_token=token_data.get("refresh_token", refresh_token),
                    token_type=token_data.get("token_type", "bearer"),
                    expires_in=token_data.get("expires_in", 7200),
                    created_at=token_data.get("created_at", 0),
                    scope=token_data.get("scope", ""),
                )
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "gitlab_oauth_token_refresh_failed",
                    status_code=e.response.status_code,
                )
                raise GitLabOAuthError(f"Token refresh failed: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error("gitlab_oauth_refresh_request_failed", error=str(e))
                raise GitLabOAuthError(f"Refresh request failed: {e}") from e

    async def get_user_info(self, access_token: str) -> GitLabUser:
        """Fetch current user information from GitLab API.

        Args:
            access_token: Valid OAuth access token

        Returns:
            GitLabUser with user details

        Raises:
            GitLabOAuthError: If API call fails
        """
        api_url = f"{self.gitlab_url}/api/v4/user"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient(timeout=self.settings.gitlab_api_timeout_seconds) as client:
            try:
                response = await client.get(api_url, headers=headers)
                response.raise_for_status()
                data = response.json()
                # Parse email: try email, then public_email (GitLab may hide primary email)
                email = data.get("email", "") or data.get("public_email", "") or ""
                logger.info(
                    "gitlab_user_info_response",
                    username=data.get("username"),
                    name=data.get("name"),
                    email_field=data.get("email"),
                    public_email_field=data.get("public_email"),
                    resolved_email=email or "(empty)",
                )
                return GitLabUser(
                    id=data["id"],
                    username=data["username"],
                    email=email,
                    name=data.get("name", data["username"]),
                    avatar_url=data.get("avatar_url"),
                )
            except httpx.HTTPStatusError as e:
                logger.error(
                    "gitlab_oauth_user_info_failed",
                    status_code=e.response.status_code,
                )
                raise GitLabOAuthError(f"Failed to get user info: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error("gitlab_oauth_request_failed", error=str(e))
                raise GitLabOAuthError(f"Request failed: {e}") from e
            except (KeyError, TypeError, ValueError) as e:
                logger.error("gitlab_oauth_user_info_parse_failed", error=str(e))
                raise GitLabOAuthError(f"Failed to parse user info: {e}") from e

    async def get_user_groups(self, access_token: str) -> list[GitLabGroup]:
        """Fetch groups the user is a member of.

        Args:
            access_token: Valid OAuth access token

        Returns:
            List of GitLabGroup objects

        Raises:
            GitLabOAuthError: If API call fails
        """
        api_url = f"{self.gitlab_url}/api/v4/groups"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"min_access_level": 10, "per_page": 100}  # Guest level or higher

        groups: list[GitLabGroup] = []
        max_pages = 20
        page_count = 0
        async with httpx.AsyncClient(timeout=self.settings.gitlab_api_timeout_seconds) as client:
            try:
                # Handle pagination
                while api_url and page_count < max_pages:
                    page_count += 1
                    response = await client.get(api_url, headers=headers, params=params)
                    response.raise_for_status()
                    data = response.json()

                    for g in data:
                        groups.append(
                            GitLabGroup(
                                id=g["id"],
                                name=g["name"],
                                path=g["path"],
                                full_path=g["full_path"],
                            )
                        )

                    # Check for next page
                    next_page = response.headers.get("x-next-page")
                    if next_page and next_page.strip():
                        params["page"] = next_page
                    else:
                        break

                return groups
            except httpx.HTTPStatusError as e:
                # If 403 Forbidden, user doesn't have API access - return empty groups
                # This happens when OAuth app only has read_user scope
                if e.response.status_code == 403:
                    logger.warning(
                        "gitlab_oauth_groups_forbidden",
                        status_code=e.response.status_code,
                        message="User doesn't have API access, returning empty groups",
                    )
                    return []
                logger.error(
                    "gitlab_oauth_groups_failed",
                    status_code=e.response.status_code,
                )
                raise GitLabOAuthError(f"Failed to get groups: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error("gitlab_oauth_request_failed", error=str(e))
                raise GitLabOAuthError(f"Request failed: {e}") from e
            except (KeyError, TypeError, ValueError) as e:
                logger.error("gitlab_oauth_groups_parse_failed", error=str(e))
                raise GitLabOAuthError(f"Failed to parse groups: {e}") from e

    def determine_role(self, user: GitLabUser, groups: list[GitLabGroup]) -> str:
        """Determine user role based on group membership and allowlist.

        Role precedence:
        1. Username in admin allowlist -> "admin"
        2. Username in teacher allowlist -> "teacher"
        3. Member of any teacher group -> "teacher"
        4. Otherwise -> "student" (can only view own team data)

        Args:
            user: GitLab user info
            groups: List of user's group memberships

        Returns:
            Role string: "admin", "teacher", or "student"
        """
        # Check admin allowlist
        admin_usernames = self.settings.gitlab_admin_usernames
        if user.username in admin_usernames:
            logger.info(
                "gitlab_oauth_role_admin_allowlist",
                username=user.username,
            )
            return "admin"

        # Check teacher allowlist
        teacher_usernames = self.settings.gitlab_teacher_usernames
        if user.username in teacher_usernames:
            logger.info(
                "gitlab_oauth_role_teacher_allowlist",
                username=user.username,
            )
            return "teacher"

        # Check teacher group membership
        teacher_group_ids = set(self.settings.gitlab_teacher_group_ids)
        teacher_group_paths = set(self.settings.gitlab_teacher_group_paths)

        for group in groups:
            if group.id in teacher_group_ids or group.full_path in teacher_group_paths:
                logger.info(
                    "gitlab_oauth_role_teacher_group",
                    username=user.username,
                    group_path=group.full_path,
                    group_id=group.id,
                )
                return "teacher"

        # Default: student (can only view own team data)
        logger.info(
            "gitlab_oauth_role_student",
            username=user.username,
        )
        return "student"
