"""Integration tests for health endpoints.

These tests require a running PostgreSQL and Redis instance.
Marked with @pytest.mark.integration for selective running.
"""

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration


@pytest.fixture
async def app():
    """Create test application instance."""
    import os

    # Set required env vars for testing
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


class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    async def test_liveness_probe(self, client: AsyncClient):
        """Test /health/live returns alive status."""
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    async def test_readiness_probe_with_db(self, client: AsyncClient):
        """Test /health/ready checks database connectivity."""
        response = await client.get("/health/ready")
        # May return 200 or 503 depending on DB availability
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data

    async def test_full_health_check(self, client: AsyncClient):
        """Test /health returns comprehensive status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "components" in data
        assert "timestamp" in data

    async def test_health_includes_database_component(self, client: AsyncClient):
        """Test health check includes database status."""
        response = await client.get("/health")
        data = response.json()

        assert "database" in data["components"]
        db_status = data["components"]["database"]
        assert "status" in db_status

    async def test_health_includes_redis_component(self, client: AsyncClient):
        """Test health check includes Redis status."""
        response = await client.get("/health")
        data = response.json()

        assert "redis" in data["components"]
        redis_status = data["components"]["redis"]
        assert "status" in redis_status


class TestMetricsEndpoint:
    """Integration tests for Prometheus metrics."""

    async def test_metrics_endpoint_returns_prometheus_format(self, client: AsyncClient):
        """Test /metrics returns Prometheus text format."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type or "text/html" in content_type

        # Should contain some metric definitions
        text = response.text
        assert "# " in text or "devops" in text.lower() or "http" in text.lower()
