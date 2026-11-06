"""Tests for backend auth dependencies."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import dependencies


def _settings(**overrides: object) -> SimpleNamespace:
    base = {
        "secret_key": "test-secret-key-minimum-sixteen-chars",
        "session_max_age_seconds": 3600,
        "persistent_sessions": True,
        "teacher_api_token": "good-token",
        "feature_rbac": True,
        "app_base_url": "http://localhost:8000",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _request(path: str, headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (name.lower().encode("ascii"), value.encode("ascii"))
        for name, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "scheme": "http",
        "server": ("test", 80),
        "root_path": "",
    }
    return Request(scope)


async def test_require_api_auth_accepts_valid_bearer_token() -> None:
    request = _request("/api/v1/courses", headers={"Authorization": "Bearer good-token"})
    result = await dependencies.require_api_auth(request, _settings())
    assert result == "api_token"


async def test_require_api_auth_rejects_invalid_bearer_even_with_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("/api/v1/courses", headers={"Authorization": "Bearer bad-token"})
    monkeypatch.setattr(dependencies, "_validate_session", lambda *_args: {"user": "admin"})
    with pytest.raises(HTTPException) as exc:
        await dependencies.require_api_auth(request, _settings())
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid API token"


async def test_require_api_auth_accepts_valid_session_when_no_bearer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("/api/v1/courses")
    monkeypatch.setattr(dependencies, "_validate_session", lambda *_args: {"user": "teacher"})
    result = await dependencies.require_api_auth(request, _settings())
    assert result == "session"


async def test_require_api_auth_rejects_missing_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/api/v1/courses")
    monkeypatch.setattr(dependencies, "_validate_session", lambda *_args: None)
    with pytest.raises(HTTPException) as exc:
        await dependencies.require_api_auth(request, _settings())
    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing or invalid authentication (Bearer token or Session cookie)"


async def test_require_api_teacher_auth_requires_teacher_or_admin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("/api/v1/courses")
    monkeypatch.setattr(
        dependencies,
        "_validate_session",
        lambda *_args: {"user": "student", "role": "student"},
    )
    with pytest.raises(HTTPException) as exc:
        await dependencies.require_api_teacher_auth(request, _settings(feature_rbac=True))
    assert exc.value.status_code == 403
    assert exc.value.detail == "Requires teacher or admin role"


async def test_require_api_teacher_auth_allows_any_session_when_rbac_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("/api/v1/courses")
    monkeypatch.setattr(
        dependencies,
        "_validate_session",
        lambda *_args: {"user": "student", "role": "student"},
    )
    result = await dependencies.require_api_teacher_auth(request, _settings(feature_rbac=False))
    assert result == "session"


async def test_require_api_admin_auth_requires_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/api/v1/users")
    monkeypatch.setattr(
        dependencies,
        "_validate_session",
        lambda *_args: {"user": "teacher", "role": "teacher"},
    )
    with pytest.raises(HTTPException) as exc:
        await dependencies.require_api_admin_auth(request, _settings(feature_rbac=True))
    assert exc.value.status_code == 403
    assert exc.value.detail == "Requires admin role"


async def test_require_dashboard_auth_redirects_to_login(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/dashboard/")
    monkeypatch.setattr(dependencies, "_validate_session", lambda *_args: None)
    with pytest.raises(HTTPException) as exc:
        await dependencies.require_dashboard_auth(request, _settings(), None)
    assert exc.value.status_code == 302
    assert exc.value.headers == {"Location": "/dashboard/login"}


async def test_require_dashboard_auth_fails_closed_when_role_db_check_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("/dashboard/")
    monkeypatch.setattr(
        dependencies,
        "_validate_session",
        lambda *_args: {"user": "teacher", "role": "teacher"},
    )

    async def _broken_enforce(*_a, **_k):
        raise RuntimeError("db down")

    monkeypatch.setattr(dependencies, "_enforce_db_role", _broken_enforce)
    with pytest.raises(HTTPException) as exc:
        await dependencies.require_dashboard_auth(request, _settings(), None)
    assert exc.value.status_code == 503


async def test_require_role_skips_role_check_when_rbac_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("/dashboard/admin")
    monkeypatch.setattr(
        dependencies,
        "_validate_session",
        lambda *_args: {"user": "student", "role": "student"},
    )
    check_admin = dependencies.require_role("admin")

    async def _noop_enforce(*_a, **_k):
        pass

    monkeypatch.setattr(dependencies, "_enforce_db_role", _noop_enforce)
    session_data = await check_admin(request, _settings(feature_rbac=False), None)
    assert session_data["user"] == "student"
