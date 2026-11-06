"""Unit tests for GitLab OAuth authentication."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.security.gitlab_oauth import (
    GitLabGroup,
    GitLabOAuth,
    GitLabOAuthError,
    GitLabUser,
    OAuthTokenResponse,
)


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for GitLab OAuth."""
    settings = MagicMock()
    settings.gitlab_url = "https://gitlab.example.com"
    settings.gitlab_oauth_client_id = "test-client-id"
    settings.gitlab_oauth_client_secret = "test-client-secret"
    settings.app_base_url = "https://myapp.example.com"
    settings.gitlab_teacher_group_ids = [100, 200]
    settings.gitlab_teacher_group_paths = ["kpi/teachers", "faculty/staff"]
    settings.gitlab_teacher_usernames = ["john.teacher"]
    settings.gitlab_admin_usernames = ["admin.user"]
    return settings


class TestGitLabOAuthInit:
    """Tests for GitLabOAuth initialization."""

    def test_init_strips_trailing_slash_from_gitlab_url(self, mock_settings: MagicMock) -> None:
        mock_settings.gitlab_url = "https://gitlab.example.com/"
        oauth = GitLabOAuth(mock_settings)
        assert oauth.gitlab_url == "https://gitlab.example.com"

    def test_init_sets_redirect_uri(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        assert oauth.redirect_uri == "https://myapp.example.com/dashboard/oauth/callback"

    def test_init_strips_trailing_slash_from_app_url(self, mock_settings: MagicMock) -> None:
        mock_settings.app_base_url = "https://myapp.example.com/"
        oauth = GitLabOAuth(mock_settings)
        assert oauth.redirect_uri == "https://myapp.example.com/dashboard/oauth/callback"


class TestGenerateState:
    """Tests for OAuth state generation."""

    def test_generates_non_empty_state(self) -> None:
        state = GitLabOAuth.generate_state()
        assert state
        assert len(state) > 20

    def test_generates_unique_states(self) -> None:
        states = {GitLabOAuth.generate_state() for _ in range(100)}
        assert len(states) == 100  # All unique


class TestGetAuthorizationUrl:
    """Tests for authorization URL generation."""

    def test_includes_required_parameters(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        url = oauth.get_authorization_url("test-state")

        assert "client_id=test-client-id" in url
        assert "response_type=code" in url
        assert "state=test-state" in url
        assert "scope=read_user" in url

    def test_uses_correct_gitlab_url(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        url = oauth.get_authorization_url("test-state")
        assert url.startswith("https://gitlab.example.com/oauth/authorize?")

    def test_includes_redirect_uri(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        url = oauth.get_authorization_url("test-state")
        assert "redirect_uri=" in url
        assert "dashboard%2Foauth%2Fcallback" in url or "dashboard/oauth/callback" in url


class TestExchangeCodeForToken:
    """Tests for OAuth code exchange."""

    @pytest.mark.asyncio
    async def test_successful_token_exchange(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test-token-123",
            "refresh_token": "refresh-token-456",
            "token_type": "bearer",
            "expires_in": 7200,
            "created_at": 1700000000,
            "scope": "read_user read_api",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            token_response = await oauth.exchange_code_for_token("auth-code")

        assert isinstance(token_response, OAuthTokenResponse)
        assert token_response.access_token == "test-token-123"
        assert token_response.refresh_token == "refresh-token-456"
        assert token_response.token_type == "bearer"
        assert token_response.expires_in == 7200
        assert token_response.created_at == 1700000000
        assert token_response.scope == "read_user read_api"

    @pytest.mark.asyncio
    async def test_raises_error_on_http_failure(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(GitLabOAuthError) as exc_info:
                await oauth.exchange_code_for_token("bad-code")

        assert "400" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_error_on_missing_token(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {}  # No access_token
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(GitLabOAuthError) as exc_info:
                await oauth.exchange_code_for_token("code")

        assert "No access token" in str(exc_info.value)


class TestRefreshAccessToken:
    """Tests for OAuth token refresh."""

    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
            "expires_in": 7200,
            "created_at": 1700003600,
            "scope": "read_user read_api",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            token_response = await oauth.refresh_access_token("old-refresh-token")

        assert isinstance(token_response, OAuthTokenResponse)
        assert token_response.access_token == "new-access-token"
        assert token_response.refresh_token == "new-refresh-token"
        assert token_response.expires_in == 7200

    @pytest.mark.asyncio
    async def test_refresh_preserves_old_refresh_token(self, mock_settings: MagicMock) -> None:
        """If provider doesn't rotate refresh tokens, the old one should be preserved."""
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            # No refresh_token in response - some providers don't rotate
            "token_type": "bearer",
            "expires_in": 7200,
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            token_response = await oauth.refresh_access_token("original-refresh-token")

        # Should fall back to the provided refresh_token
        assert token_response.refresh_token == "original-refresh-token"

    @pytest.mark.asyncio
    async def test_raises_error_on_http_failure(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(GitLabOAuthError) as exc_info:
                await oauth.refresh_access_token("invalid-refresh-token")

        assert "401" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_error_on_missing_access_token(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {}  # No access_token
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(GitLabOAuthError) as exc_info:
                await oauth.refresh_access_token("refresh-token")

        assert "No access token" in str(exc_info.value)


class TestGetUserInfo:
    """Tests for user info retrieval."""

    @pytest.mark.asyncio
    async def test_successful_user_info(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 42,
            "username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": "https://gitlab.example.com/avatar.png",
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            user = await oauth.get_user_info("token")

        assert user.id == 42
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.avatar_url == "https://gitlab.example.com/avatar.png"

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 42,
            "username": "testuser",
            # email, name, avatar_url missing
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            user = await oauth.get_user_info("token")

        assert user.id == 42
        assert user.username == "testuser"
        assert user.email == ""
        assert user.name == "testuser"  # Falls back to username
        assert user.avatar_url is None


class TestGetUserGroups:
    """Tests for user groups retrieval."""

    @pytest.mark.asyncio
    async def test_successful_groups_fetch(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "name": "Group 1", "path": "group1", "full_path": "org/group1"},
            {"id": 2, "name": "Group 2", "path": "group2", "full_path": "org/group2"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {}

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            groups = await oauth.get_user_groups("token")

        assert len(groups) == 2
        assert groups[0].id == 1
        assert groups[0].full_path == "org/group1"
        assert groups[1].id == 2
        assert groups[1].full_path == "org/group2"

    @pytest.mark.asyncio
    async def test_handles_empty_groups(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)

        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {}

        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            groups = await oauth.get_user_groups("token")

        assert groups == []


class TestDetermineRole:
    """Tests for role determination based on groups and allowlists."""

    def test_admin_allowlist_takes_precedence(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=1, username="admin.user", email="", name="Admin")
        groups: list[GitLabGroup] = []

        role = oauth.determine_role(user, groups)
        assert role == "admin"

    def test_teacher_allowlist(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=2, username="john.teacher", email="", name="John")
        groups: list[GitLabGroup] = []

        role = oauth.determine_role(user, groups)
        assert role == "teacher"

    def test_teacher_group_id_match(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=3, username="regular.user", email="", name="Regular")
        groups = [GitLabGroup(id=100, name="Teachers", path="teachers", full_path="kpi/teachers")]

        role = oauth.determine_role(user, groups)
        assert role == "teacher"

    def test_teacher_group_path_match(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=4, username="another.user", email="", name="Another")
        groups = [GitLabGroup(id=999, name="Staff", path="staff", full_path="faculty/staff")]

        role = oauth.determine_role(user, groups)
        assert role == "teacher"

    def test_student_role_default(self, mock_settings: MagicMock) -> None:
        """Default role for non-teacher/admin users is 'student' (limited access)."""
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=5, username="student.user", email="", name="Student")
        groups = [GitLabGroup(id=500, name="Students", path="students", full_path="students")]

        role = oauth.determine_role(user, groups)
        assert role == "student"

    def test_no_groups_no_allowlist_is_student(self, mock_settings: MagicMock) -> None:
        """Users not in any teacher/admin list default to 'student' role."""
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=6, username="unknown.user", email="", name="Unknown")
        groups: list[GitLabGroup] = []

        role = oauth.determine_role(user, groups)
        assert role == "student"

    def test_admin_takes_precedence_over_teacher_group(self, mock_settings: MagicMock) -> None:
        oauth = GitLabOAuth(mock_settings)
        user = GitLabUser(id=1, username="admin.user", email="", name="Admin")
        # User is in teacher group but also in admin allowlist
        groups = [GitLabGroup(id=100, name="Teachers", path="teachers", full_path="kpi/teachers")]

        role = oauth.determine_role(user, groups)
        assert role == "admin"


class TestGitLabUserDataclass:
    """Tests for GitLabUser dataclass."""

    def test_create_with_all_fields(self) -> None:
        user = GitLabUser(
            id=1,
            username="test",
            email="test@example.com",
            name="Test User",
            avatar_url="https://example.com/avatar.png",
        )
        assert user.id == 1
        assert user.username == "test"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.png"

    def test_create_with_optional_fields_none(self) -> None:
        user = GitLabUser(id=1, username="test", email="", name="Test")
        assert user.avatar_url is None


class TestGitLabGroupDataclass:
    """Tests for GitLabGroup dataclass."""

    def test_create_group(self) -> None:
        group = GitLabGroup(
            id=1,
            name="Test Group",
            path="test-group",
            full_path="org/test-group",
        )
        assert group.id == 1
        assert group.name == "Test Group"
        assert group.path == "test-group"
        assert group.full_path == "org/test-group"
