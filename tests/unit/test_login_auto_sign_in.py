"""GitLab's auto_sign_in_with_provider, ported: the login page can skip its card
and go straight to GitLab OAuth - unless ?auto_sign_in=false says otherwise.

The behaviour is gated on gitlab_oauth_auto_sign_in, which defaults False, so the
'Sign in with GitLab' card is the untouched default. These tests pin all three
edges: off (card), on (redirect), on + the loop-guard param (card).
"""

import pytest
from fastapi.testclient import TestClient


class _FakeOAuth:
    """Stand-in for GitLabOAuth so the login page has an auth_url without Redis."""

    AUTH_URL = "https://gitlab.example/oauth/authorize?state=fixed"

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def generate_state(self) -> str:
        return "fixed"

    def get_authorization_url(self, _state: str) -> str:
        return self.AUTH_URL


def _client(monkeypatch, *, auto_sign_in: bool) -> TestClient:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ALLOWED_HOSTS", '["testserver","localhost","127.0.0.1"]')
    monkeypatch.setenv("GITLAB_OAUTH_CLIENT_ID", "abc123")
    monkeypatch.setenv("GITLAB_OAUTH_AUTO_SIGN_IN", "true" if auto_sign_in else "false")

    from app import config
    from app.api.dashboard import auth as auth_module

    config.get_settings.cache_clear()

    # Give the login page a working auth_url without a live Redis / GitLab.
    async def _save_ok(*_args, **_kwargs) -> bool:
        return True

    monkeypatch.setattr(auth_module, "save_oauth_state", _save_ok)
    monkeypatch.setattr(auth_module, "GitLabOAuth", _FakeOAuth)

    from app.main import create_app

    return TestClient(create_app())


def test_flag_off_renders_the_card(monkeypatch) -> None:
    client = _client(monkeypatch, auto_sign_in=False)
    resp = client.get("/dashboard/login", follow_redirects=False)
    assert resp.status_code == 200
    assert _FakeOAuth.AUTH_URL in resp.text  # the button points at OAuth


def test_flag_on_redirects_straight_to_oauth(monkeypatch) -> None:
    client = _client(monkeypatch, auto_sign_in=True)
    resp = client.get("/dashboard/login", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["location"] == _FakeOAuth.AUTH_URL


def test_flag_on_but_auto_sign_in_false_keeps_the_card(monkeypatch) -> None:
    """The logout guard: ?auto_sign_in=false must show the card, not redirect."""
    client = _client(monkeypatch, auto_sign_in=True)
    resp = client.get("/dashboard/login?auto_sign_in=false", follow_redirects=False)
    assert resp.status_code == 200
    assert _FakeOAuth.AUTH_URL in resp.text


def test_flag_on_but_logged_out_marker_keeps_the_card(monkeypatch) -> None:
    """A diagnostic marker (logged_out) must show the card so its message reads."""
    client = _client(monkeypatch, auto_sign_in=True)
    resp = client.get("/dashboard/login?logged_out=1", follow_redirects=False)
    assert resp.status_code == 200


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
