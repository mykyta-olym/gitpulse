"""Regression: ``POST /support/upload`` must reach the multipart upload endpoint.

The upload route was declared *after* ``POST /support/{token}`` (the JSON
support-submit route), so ``/support/upload`` matched the ``{token}`` param
route with ``token="upload"`` and every attachment upload failed with a 422
"Input should be a valid dictionary or object to extract fields from" (the raw
multipart body fed into a Pydantic model). The fix declares the fixed path
first; these tests lock that ordering in.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.support import router
from app.dependencies import get_current_user, verify_csrf


class _FakeUser:
    username = "tester"
    gitlab_username = "tester"
    id = "00000000-0000-0000-0000-000000000001"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: _FakeUser()
    # The session and its CSRF token are not what this file tests.
    app.dependency_overrides[verify_csrf] = lambda: None
    return TestClient(app)


def test_upload_route_declared_before_token_param_route() -> None:
    post_paths = [
        r.path
        for r in router.routes
        if "POST" in (getattr(r, "methods", set()) or set())
        and r.path in ("/support/upload", "/support/{token}")
    ]
    assert post_paths[:2] == ["/support/upload", "/support/{token}"], (
        f"/support/upload must be registered before /support/{{token}} "
        f"(got {post_paths}) - else multipart uploads 422 against the JSON submit route"
    )


def test_multipart_upload_reaches_upload_endpoint(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "feature_support_forms", True)
    client = _client()
    resp = client.post(
        "/api/v1/support/upload",
        files={"file": ("probe.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["filename"] == "probe.txt"
    assert data["url"].startswith("/static/uploads/")

    # The file must land in the directory /static/uploads/ is served from -
    # the path is computed from the module's __file__, so a module move that
    # changes its depth writes uploads to a directory nothing serves.
    repo_root = Path(__file__).resolve().parents[2]
    saved = repo_root / "src" / "app" / "templates" / "static" / "uploads" / Path(data["url"]).name
    assert saved.exists(), f"upload was not written under templates/static/uploads: {saved}"
    saved.unlink()


def test_support_upload_is_unavailable_when_the_module_is_disabled(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "feature_support_forms", False)
    response = _client().post(
        "/api/v1/support/upload", files={"file": ("probe.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 503
