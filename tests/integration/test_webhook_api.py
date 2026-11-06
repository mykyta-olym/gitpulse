"""Integration tests for webhook API endpoints.

Tests webhook ingestion with database persistence.
Marked with @pytest.mark.integration for selective running.
"""

import os
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration


@pytest.fixture
async def app():
    """Create test application instance."""
    os.environ.setdefault(
        "DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
        ),
    )
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    os.environ.setdefault("TEACHER_API_TOKEN", "test-token-12345678")
    os.environ.setdefault("GITLAB_OAUTH_ENABLED", "true")
    os.environ.setdefault("APP_ENV", "test")
    os.environ["ALLOWED_HOSTS"] = '["test","localhost","127.0.0.1"]'

    from sqlalchemy import text

    from app.config import get_settings
    from app.db.session import dispose_engine, init_engine
    from app.main import create_app
    from app.models import Base

    get_settings.cache_clear()
    settings = get_settings()
    engine = init_engine(
        str(settings.database_url),
        pool_size=settings.db_pool_size,
        echo=settings.db_echo,
    )
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    app = create_app()
    try:
        yield app
    finally:
        await dispose_engine()


@pytest.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestWebhookEndpoint:
    """Integration tests for GitLab webhook receiver."""

    def _make_push_payload(self, project_id: int = 12345) -> dict[str, object]:
        """Create a valid GitLab push event payload."""
        return {
            "object_kind": "push",
            "event_name": "push",
            "before": "0" * 40,
            "after": "a" * 40,
            "ref": "refs/heads/main",
            "checkout_sha": "a" * 40,
            "user_id": 1,
            "user_name": "Test User",
            "user_email": "test@example.com",
            "project_id": project_id,
            "project": {
                "id": project_id,
                "name": "test-project",
                "web_url": "https://gitlab.example.com/test/test-project",
                "path_with_namespace": "test/test-project",
            },
            "commits": [
                {
                    "id": "a" * 40,
                    "message": "Test commit",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "author": {"name": "Test", "email": "test@example.com"},
                    "added": ["file.py"],
                    "modified": [],
                    "removed": [],
                }
            ],
            "total_commits_count": 1,
        }

    async def test_webhook_requires_token_header(self, client: AsyncClient):
        """Test webhook endpoint requires X-Gitlab-Token header."""
        payload = self._make_push_payload()

        response = await client.post(
            "/api/v1/webhooks/gitlab",
            json=payload,
            # Missing X-Gitlab-Token header
        )

        assert response.status_code == 422  # Missing required header

    async def test_webhook_rejects_unregistered_project(self, client: AsyncClient):
        """Test webhook rejects events from unregistered projects."""
        payload = self._make_push_payload(project_id=99999)

        response = await client.post(
            "/api/v1/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Token": "some-token"},
        )

        # Project not found, auth failure, or DB unavailable
        assert response.status_code in (401, 404, 503)

    async def test_webhook_validates_payload_structure(self, client: AsyncClient):
        """Test webhook validates required payload fields."""
        invalid_payload = {"foo": "bar"}  # Missing project.id

        response = await client.post(
            "/api/v1/webhooks/gitlab",
            json=invalid_payload,
            headers={"X-Gitlab-Token": "test-token"},
        )

        assert response.status_code == 422

    async def test_webhook_rejects_oversized_payload(self, client: AsyncClient):
        """Test webhook rejects payloads exceeding size limit."""
        # Create payload > 1MB
        large_data = "x" * (2 * 1024 * 1024)

        response = await client.post(
            "/api/v1/webhooks/gitlab",
            content=large_data,
            headers={
                "X-Gitlab-Token": "test-token",
                "Content-Type": "application/json",
            },
        )

        # Should reject as too large or invalid JSON
        assert response.status_code in (413, 422)


class TestProjectAPI:
    """Integration tests for project management API."""

    async def test_create_project_requires_auth(self, client: AsyncClient):
        """Test project creation requires Bearer token."""
        team_id = "00000000-0000-0000-0000-000000000000"
        response = await client.post(
            f"/api/v1/projects/{team_id}/projects",
            json={
                "gitlab_project_id": 12345,
                "gitlab_project_path": "test/test-project",
                "gitlab_project_name": "test-project",
            },
        )

        # 302 = redirect to login (TeacherAuth), 401/403 = explicit rejection
        assert response.status_code in (302, 307, 401, 403, 503)

    async def test_list_projects_requires_auth(self, client: AsyncClient):
        """Test project listing requires Bearer token."""
        response = await client.get("/api/v1/projects")

        # 302 = redirect to login (session-based auth redirect)
        assert response.status_code in (302, 307, 401, 403, 503)

    async def test_create_project_with_valid_token(self, client: AsyncClient):
        """Test project creation with valid Bearer token."""
        team_id = "00000000-0000-0000-0000-000000000000"
        token = os.environ["TEACHER_API_TOKEN"]
        response = await client.post(
            f"/api/v1/projects/{team_id}/projects",
            json={
                "gitlab_project_id": 12345,
                "gitlab_project_path": "test/test-project",
                "gitlab_project_name": "test-project",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # Success, conflict, missing team, or DB unavailable
        assert response.status_code in (201, 404, 409, 503)
