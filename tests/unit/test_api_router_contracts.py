"""Tests for shared API response contracts in OpenAPI."""

import warnings

from fastapi.testclient import TestClient


def test_api_routes_include_standard_error_responses(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")

    from app import config
    from app.main import create_app

    config.get_settings.cache_clear()
    app = create_app()
    spec = app.openapi()

    operation = spec["paths"]["/api/v1/teams/{team_id}/sync"]["post"]
    responses = operation["responses"]

    for status_code in ("400", "401", "403", "404", "409", "422", "429", "500", "503"):
        assert status_code in responses

    schema_ref = responses["400"]["content"]["application/json"]["schema"]["$ref"]
    assert schema_ref.endswith("/ErrorResponse")


def test_openapi_generation_has_no_duplicate_operation_ids(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")

    from app import config
    from app.main import create_app

    config.get_settings.cache_clear()
    app = create_app()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        spec = app.openapi()

    duplicate_operation_warnings = [
        item for item in caught if "Duplicate Operation ID" in str(item.message)
    ]
    assert duplicate_operation_warnings == []
    assert spec["paths"]["/dashboard/login"]["get"]["operationId"] == "dashboard_login_page"
    assert "head" not in spec["paths"]["/dashboard/login"]


def test_login_error_query_renders_gitlab_alert_in_oauth_fallback(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("GITLAB_OAUTH_ENABLED", "true")
    monkeypatch.setenv("GITLAB_OAUTH_CLIENT_ID", "")
    monkeypatch.setenv("ALLOWED_HOSTS", '["testserver","localhost","127.0.0.1"]')

    from app import config
    from app.main import create_app

    config.get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/dashboard/login",
        params={
            "error": (
                "Something went wrong while loading the actions dropdown list. "
                "Please refresh the page and try again."
            ),
        },
    )

    assert response.status_code == 200
    assert "gitlab-alert gitlab-alert-danger login-auth-alert" in response.text
    assert "Something went wrong while loading the actions dropdown list" in response.text
    assert "login-error-alert" not in response.text
