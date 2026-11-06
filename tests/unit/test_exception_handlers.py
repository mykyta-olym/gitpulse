"""Tests for centralized exception handler registration."""

from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from starlette.templating import Jinja2Templates

from app.api.exception_handlers import register_exception_handlers
from app.dependencies import FeatureDisabledError


def _write_template(directory: Path, template_name: str, content: str) -> None:
    template_path = directory / template_name
    template_path.parent.mkdir(parents=True, exist_ok=True)
    template_path.write_text(content, encoding="utf-8")


def _build_templates(directory: Path) -> Jinja2Templates:
    # One template for every error page; the stub shows what it is given.
    _write_template(
        directory,
        "errors/error.html",
        "page {{ status_code }}: {{ title }} | {{ message }} | offer={{ offer }}"
        "{% if error_id %} id={{ error_id }}{% endif %}"
        "{% if feature_name %} feature={{ feature_name }} {{ feature_flag }}{% endif %}",
    )
    return Jinja2Templates(directory=str(directory))


@pytest.fixture
def app(tmp_path: Path) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app, _build_templates(tmp_path))

    @app.get("/api/forbidden")
    async def api_forbidden() -> None:
        raise HTTPException(status_code=403, detail="forbidden")

    @app.get("/dashboard/forbidden")
    async def dashboard_forbidden() -> None:
        raise HTTPException(status_code=403, detail="forbidden")

    @app.get("/api/crash")
    async def api_crash() -> None:
        raise RuntimeError("boom")

    @app.get("/dashboard/crash")
    async def dashboard_crash() -> None:
        raise RuntimeError("boom")

    @app.get("/api/feature")
    async def api_feature() -> None:
        raise FeatureDisabledError(
            feature_name="Example Integration",
            feature_flag="FEATURE_EXAMPLE_INTEGRATION",
            expected_availability="Soon",
        )

    @app.get("/api/custom-http")
    async def api_custom_http() -> None:
        raise HTTPException(status_code=409, detail="Already exists")

    @app.get("/api/validation/{item_id}")
    async def api_validation(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @app.get("/dashboard/feature")
    async def dashboard_feature() -> None:
        raise FeatureDisabledError(
            feature_name="Example Integration",
            feature_flag="FEATURE_EXAMPLE_INTEGRATION",
            expected_availability="Soon",
        )

    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_api_404_returns_json(client: AsyncClient) -> None:
    response = await client.get("/api/missing")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "not_found"
    assert body["detail"] == "Not Found"
    assert body["status_code"] == 404
    assert body["path"] == "/api/missing"
    assert body["timestamp"]


async def test_dashboard_404_returns_html(client: AsyncClient) -> None:
    response = await client.get("/dashboard/missing")
    assert response.status_code == 404
    assert "page 404: Page not found" in response.text
    assert "offer=find" in response.text


async def test_api_403_returns_access_denied_json(client: AsyncClient) -> None:
    response = await client.get("/api/forbidden")
    assert response.status_code == 403
    body = response.json()
    assert body["error"] == "access_denied"
    assert body["detail"] == "Access Denied"
    assert body["status_code"] == 403
    assert body["path"] == "/api/forbidden"


async def test_dashboard_500_returns_html_with_error_id(client: AsyncClient) -> None:
    response = await client.get("/dashboard/crash")
    assert response.status_code == 500
    assert "page 500: Internal server error" in response.text
    assert "offer=retry id=" in response.text


async def test_api_500_returns_json_with_error_id(client: AsyncClient) -> None:
    response = await client.get("/api/crash")
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "internal_server_error"
    assert data["detail"] == "Internal Server Error"
    assert data["status_code"] == 500
    assert data["path"] == "/api/crash"
    assert len(data["error_id"]) == 8


async def test_feature_disabled_api_returns_json_payload(client: AsyncClient) -> None:
    response = await client.get("/api/feature")
    assert response.status_code == 503
    body = response.json()
    assert body["error"] == "feature_disabled"
    assert body["status_code"] == 503
    assert body["fields"]["feature_flag"] == "FEATURE_EXAMPLE_INTEGRATION"
    assert body["fields"]["feature_name"] == "Example Integration"
    assert "disabled" in body["detail"]


async def test_generic_http_exception_uses_standard_payload(client: AsyncClient) -> None:
    response = await client.get("/api/custom-http")
    assert response.status_code == 409
    body = response.json()
    assert body["error"] == "conflict"
    assert body["detail"] == "Already exists"
    assert body["status_code"] == 409


async def test_request_validation_error_uses_standard_payload(client: AsyncClient) -> None:
    response = await client.get("/api/validation/not-int")
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["detail"] == "Validation failed"
    assert body["status_code"] == 422
    assert body["issues"]


async def test_feature_disabled_dashboard_returns_html(client: AsyncClient) -> None:
    response = await client.get("/dashboard/feature")
    assert response.status_code == 503
    assert "feature=Example Integration FEATURE_EXAMPLE_INTEGRATION" in response.text
    # The app is up: the way back, not an outage's Retry.
    assert "offer=back" in response.text
