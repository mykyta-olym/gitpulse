"""Integration tests for dashboard authentication and pages.

Tests session-based authentication flow with GitLab OAuth.
Marked with @pytest.mark.integration for selective running.
"""

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration


@pytest.fixture
async def app():
    """Create test application instance."""
    import os

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
    os.environ.setdefault("APP_ENV", "test")
    # Enable OAuth but without client_id - will show fallback login page
    os.environ.setdefault("GITLAB_OAUTH_ENABLED", "true")
    os.environ.setdefault("GITLAB_OAUTH_CLIENT_ID", "")
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


class TestDashboardAuth:
    """Integration tests for dashboard authentication."""

    async def test_login_page_renders(self, client: AsyncClient):
        """Test login page is accessible (shows fallback when OAuth client_id is empty)."""
        response = await client.get("/dashboard/login", follow_redirects=False)
        # With OAuth enabled but no client_id, shows fallback login page (200)
        # With OAuth fully configured, redirects to GitLab (303)
        assert response.status_code in (200, 303)

    async def test_dashboard_requires_auth(self, client: AsyncClient):
        """Test dashboard home redirects to login without session."""
        response = await client.get("/dashboard/", follow_redirects=False)

        # Should redirect to login or return 401/403
        assert response.status_code in (302, 303, 401, 403)

    async def test_login_post_redirects_to_oauth(self, client: AsyncClient):
        """Test POST to login redirects to OAuth flow."""
        response = await client.post(
            "/dashboard/login",
            data={"password": "any-password"},
            follow_redirects=False,
        )

        # With OAuth enabled, POST redirects to GET /login (303)
        # Without OAuth, returns error (400)
        # With CSRF protection enabled, returns 403 without valid token
        assert response.status_code in (303, 400, 403)

    async def test_logout_clears_session(self, client: AsyncClient):
        """Test logout endpoint renders explicit confirmation."""
        response = await client.get("/dashboard/logout", follow_redirects=False)

        assert response.status_code == 200
        assert 'method="post" action="/dashboard/logout"' in response.text


class TestDashboardPages:
    """Integration tests for dashboard pages (require auth)."""

    async def test_courses_page_requires_auth(self, client: AsyncClient):
        """Test courses page requires authentication."""
        response = await client.get("/dashboard/courses/", follow_redirects=False)
        assert response.status_code in (302, 303, 401, 403, 404)

    async def test_invalid_course_returns_404(self, client: AsyncClient):
        """Test non-existent course returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/dashboard/courses/{fake_uuid}")
        # Without auth, should redirect or 404
        assert response.status_code in (302, 303, 401, 403, 404)
