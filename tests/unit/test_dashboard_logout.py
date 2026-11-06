"""Dashboard logout security contracts."""

from fastapi.testclient import TestClient


def test_logout_requires_explicit_post_and_preserves_local_preferences(monkeypatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    )
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-minimum-sixteen-chars")
    monkeypatch.setenv("TEACHER_API_TOKEN", "test-token-12345678")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ALLOWED_HOSTS", '["testserver","localhost","127.0.0.1"]')

    from app import config
    from app.main import create_app

    config.get_settings.cache_clear()
    client = TestClient(create_app())

    confirmation = client.get("/dashboard/logout", follow_redirects=False)

    assert confirmation.status_code == 200
    assert 'method="post" action="/dashboard/logout"' in confirmation.text
    # Default locale is Slovak, so the confirmation prompt renders translated
    # ("Do you want to log out?" -> "Chcete sa odhlásiť?"). Asserting the
    # translated string also guards the catalog entry against regressing.
    assert "Chcete sa odhlásiť?" in confirmation.text

    token_marker = 'name="csrf_token" value="'
    token_start = confirmation.text.index(token_marker) + len(token_marker)
    token_end = confirmation.text.index('"', token_start)
    response = client.post(
        "/dashboard/logout",
        data={"csrf_token": confirmation.text[token_start:token_end]},
        follow_redirects=False,
    )

    assert response.status_code == 303
    # auto_sign_in=false is GitLab's re-login-loop guard: with auto_sign_in on it
    # keeps a just-signed-out user on the card instead of bouncing them into OAuth.
    assert response.headers["location"] == "/dashboard/login?logged_out=1&auto_sign_in=false"
    assert response.headers["clear-site-data"] == '"cache"'
