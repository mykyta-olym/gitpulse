"""Unit tests for i18n helpers and locale middleware."""

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from app.api.dashboard.auth import switch_language
from app.i18n import (
    get_template_i18n_context,
    normalize_locale,
    safe_redirect_target,
    translate_text,
)
from app.middleware.locale import LocaleMiddleware


def _request(
    path: str = "/",
    query: str = "",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": query.encode("utf-8"),
        "headers": headers or [(b"host", b"testserver")],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
    }
    return Request(scope)


def test_normalize_locale_variants() -> None:
    assert normalize_locale("sk") == "sk"
    assert normalize_locale("sk-SK") == "sk"
    assert normalize_locale("EN_us") == "en"
    assert normalize_locale("de-DE") is None
    assert normalize_locale("") is None


def test_translate_text_slovak_catalog() -> None:
    assert translate_text("en", "Dashboard") == "Dashboard"
    assert translate_text("sk", "Dashboard") == "Prehľad"
    assert translate_text("sk", "Sign out") == "Odhlásiť sa"


def test_safe_redirect_target_rejects_external_hosts() -> None:
    request = _request(path="/dashboard/")
    assert safe_redirect_target(request, "https://evil.example/phish") == "/dashboard/"
    assert safe_redirect_target(request, "/dashboard/courses") == "/dashboard/courses"
    assert safe_redirect_target(request, "dashboard/courses") == "/dashboard/courses"


def test_template_context_contains_i18n_payload() -> None:
    request = _request(
        path="/dashboard/",
        headers=[
            (b"host", b"testserver"),
            (b"accept-language", b"sk-SK,sk;q=0.9,en;q=0.8"),
        ],
    )
    context = get_template_i18n_context(request)
    assert context["current_locale"] == "sk"
    assert context["i18n_client_config"]["locale"] == "sk"
    assert context["i18n_client_config"]["default_locale"] == "sk"
    assert context["i18n_client_config"]["source_locale"] == "en"
    # The catalogue is NOT in the island any more - it ships as a
    # content-hashed file, so the island carries only which locale to read it
    # as. Inlined it was about ninety per cent of a compressed page and could
    # not be cached, having no URL of its own.
    assert "catalog" not in context["i18n_client_config"]
    assert context["i18n_catalog_url"], "the page has no catalogue to load"
    assert "i18n-catalog-sk" in context["i18n_catalog_url"]
    assert any(opt["code"] == "en" for opt in context["supported_locales"])
    assert any(opt["code"] == "sk" for opt in context["supported_locales"])

    # Shared runtime feature flags must be present in the global template context.
    expected_flags = [
        "feature_support_forms",
        "feature_event_pipeline",
        "feature_multi_tenant",
        "feature_llm_suggestions",
    ]
    for flag in expected_flags:
        assert flag in context, f"Missing global template flag: {flag}"
        assert isinstance(context[flag], bool), f"{flag} should be bool"


def test_locale_middleware_sets_state_and_content_language() -> None:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)

    @app.get("/")
    async def read_root(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(getattr(request.state, "locale", "")))

    client = TestClient(app)
    response = client.get("/", headers={"Accept-Language": "sk-SK,sk;q=0.9,en;q=0.8"})
    assert response.status_code == 200
    assert response.text == "sk"
    assert response.headers["Content-Language"] == "sk"


def test_locale_middleware_persists_query_locale_cookie() -> None:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)

    @app.get("/")
    async def read_root(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(getattr(request.state, "locale", "")))

    client = TestClient(app)
    response = client.get("/?lang=sk")
    assert response.status_code == 200
    assert response.text == "sk"
    assert response.cookies.get("gp_lang") == "sk"


def test_locale_middleware_defaults_to_slovak_without_headers() -> None:
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)

    @app.get("/")
    async def read_root(request: Request) -> PlainTextResponse:
        return PlainTextResponse(str(getattr(request.state, "locale", "")))

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "sk"
    assert response.headers["Content-Language"] == "sk"


@pytest.mark.asyncio
async def test_switch_language_endpoint_sets_cookie_and_redirects() -> None:
    request = _request(
        path="/dashboard/language/sk",
        query="next=%2Fdashboard%2Flogin",
    )
    response = await switch_language(request=request, locale="sk", next_url="/dashboard/login")
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard/login"
    assert "gp_lang=sk" in response.headers.get("set-cookie", "")
