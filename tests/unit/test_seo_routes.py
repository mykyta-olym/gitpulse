"""SEO route contract tests."""

import re

from fastapi.testclient import TestClient


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_BASE_URL", "https://gitpulse.kpi.fei.tuke.sk")
    monkeypatch.setenv("ALLOWED_HOSTS", '["testserver","localhost","127.0.0.1"]')

    from app import config
    from app.main import create_app

    config.get_settings.cache_clear()
    return TestClient(create_app())


def test_robots_txt_lists_app_and_docs_sitemaps(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert "Disallow: /api/" in response.text
    assert "Disallow: /dashboard/" in response.text
    assert "Disallow: /oauth/" in response.text
    assert "Disallow: /health/" in response.text
    assert "Allow: /dashboard/login" in response.text
    assert "Sitemap: https://gitpulse.kpi.fei.tuke.sk/sitemap.xml" in response.text
    assert "Sitemap: https://gitpulse.kpi.fei.tuke.sk/docs/sitemap.xml" in response.text
    assert response.headers["cache-control"] == "public, max-age=3600"


def test_root_sitemap_only_lists_application_owned_urls(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert "<loc>https://gitpulse.kpi.fei.tuke.sk/dashboard/login</loc>" in response.text
    assert 'hreflang="sk"' in response.text
    assert 'hreflang="en"' in response.text
    assert 'hreflang="x-default"' in response.text
    assert re.search(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>", response.text)
    assert "/docs/" not in response.text
    assert "/api/" not in response.text
    assert response.headers["cache-control"] == "public, max-age=3600"


def test_llms_txt_route(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.get("/llms.txt")

    assert response.status_code == 200
    assert "# GitPulse" in response.text
    assert "User Login: https://gitpulse.kpi.fei.tuke.sk/dashboard/login" in response.text
    assert "Excluded Private Routes" in response.text
    assert "- `/dashboard/*`" in response.text
    assert response.headers["cache-control"] == "public, max-age=3600"


def test_x_robots_tag_middleware(monkeypatch) -> None:
    client = _client(monkeypatch)

    # Public endpoint (no login required, indexable) should not have X-Robots-Tag header
    resp_login = client.get("/dashboard/login")
    assert "x-robots-tag" not in resp_login.headers

    # Private/auth endpoints (like dashboard index or APIs) should have X-Robots-Tag header
    # Note: /dashboard/ redirects to /dashboard/login, but the redirect response
    # itself should have the header
    resp_dashboard = client.get("/dashboard/", follow_redirects=False)
    assert resp_dashboard.headers.get("x-robots-tag") == "noindex, nofollow, noarchive"

    # API endpoints should have the header
    resp_api = client.get("/api/v1/health", follow_redirects=False)
    assert resp_api.headers.get("x-robots-tag") == "noindex, nofollow, noarchive"

    # Health endpoints should have the header
    resp_health = client.get("/health/live", follow_redirects=False)
    assert resp_health.headers.get("x-robots-tag") == "noindex, nofollow, noarchive"
