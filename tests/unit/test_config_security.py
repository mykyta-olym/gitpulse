"""Security-focused settings validation tests."""

import pytest
from pydantic import ValidationError

from app.config import AppEnv, Settings


def _production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": AppEnv.PRODUCTION,
        "database_url": "postgresql+asyncpg://gitpulse:secret@postgres:5432/gitpulse",
        "redis_url": "redis://:redis-secret@redis:6379/0",
        "secret_key": "k" * 32,
        "teacher_api_token": "t" * 24,
        "app_base_url": "https://gitpulse.example.edu",
        "allowed_hosts": ["gitpulse.example.edu"],
        "feature_redis_sessions": True,
    }
    values.update(overrides)
    return Settings(**values)


def test_production_accepts_hardened_public_https_settings() -> None:
    settings = _production_settings()
    assert settings.is_production


def test_production_rejects_http_app_base_url() -> None:
    with pytest.raises(ValidationError, match="APP_BASE_URL must use https"):
        _production_settings(app_base_url="http://gitpulse.example.edu")


def test_production_rejects_localhost_app_base_url() -> None:
    with pytest.raises(ValidationError, match="localhost"):
        _production_settings(app_base_url="https://localhost")


def test_production_requires_allowed_host_for_public_base_url() -> None:
    with pytest.raises(ValidationError, match="ALLOWED_HOSTS must include"):
        _production_settings(allowed_hosts=["other.example.edu"])


def test_production_rejects_short_secret_key() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY is shorter"):
        _production_settings(secret_key="k" * 16)


def test_production_requires_redis_backed_sessions() -> None:
    with pytest.raises(ValidationError, match="FEATURE_REDIS_SESSIONS"):
        _production_settings(feature_redis_sessions=False)
