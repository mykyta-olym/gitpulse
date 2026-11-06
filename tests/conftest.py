"""Test configuration helpers."""

import importlib
import os
import socket
import sys
from collections.abc import Callable
from typing import cast
from urllib.parse import urlsplit

import pytest

_TEST_ENV_DEFAULTS = {
    "APP_ENV": "test",
    "DEBUG": "false",
    "DATABASE_URL": "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    "SECRET_KEY": "test-secret-key-minimum-sixteen-chars",
    "TEACHER_API_TOKEN": "test-token-12345678",
}


def _has_valid_bool(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {
        "0",
        "1",
        "false",
        "true",
        "off",
        "on",
        "no",
        "yes",
    }


def _normalise_test_env() -> None:
    """Keep unit tests independent from a developer's shell environment."""
    if os.getenv("APP_ENV") not in {"development", "production", "test"}:
        os.environ["APP_ENV"] = _TEST_ENV_DEFAULTS["APP_ENV"]
    if not _has_valid_bool(os.getenv("DEBUG")):
        os.environ["DEBUG"] = _TEST_ENV_DEFAULTS["DEBUG"]
    for key in ("DATABASE_URL", "SECRET_KEY", "TEACHER_API_TOKEN"):
        value = os.getenv(key, "")
        if not value.strip():
            os.environ[key] = _TEST_ENV_DEFAULTS[key]

    if len(os.environ["SECRET_KEY"]) < 16:
        os.environ["SECRET_KEY"] = _TEST_ENV_DEFAULTS["SECRET_KEY"]
    if len(os.environ["TEACHER_API_TOKEN"]) < 8:
        os.environ["TEACHER_API_TOKEN"] = _TEST_ENV_DEFAULTS["TEACHER_API_TOKEN"]


def _is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _parse_port(value: str) -> int:
    """Parse port number, handling Docker-link URLs like ``tcp://host:port``."""
    if "://" in value:
        return int(value.rsplit(":", 1)[-1].rstrip("/"))
    return int(value)


def _service_address(url_var: str, port_var: str, default_port: int) -> tuple[str, int]:
    """Where a service answers: the host of its URL (CI reaches ``postgres`` and
    ``redis`` by name), else localhost on ``port_var``."""
    parts = urlsplit(os.getenv(url_var, ""))
    if parts.hostname:
        return parts.hostname, parts.port or default_port
    return "localhost", _parse_port(os.getenv(port_var, str(default_port)))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip integration tests when PostgreSQL / Redis are not reachable."""
    db = _service_address("DATABASE_URL", "DB_PORT", 5432)
    redis = _service_address("REDIS_URL", "REDIS_PORT", 6379)
    db_ok = _is_port_open(*db)
    redis_ok = _is_port_open(*redis)

    if db_ok and redis_ok:
        return  # both services reachable - let integration tests run

    reason = "integration tests require "
    missing: list[str] = []
    if not db_ok:
        missing.append(f"PostgreSQL on {db[0]}:{db[1]}")
    if not redis_ok:
        missing.append(f"Redis on {redis[0]}:{redis[1]}")
    reason += " and ".join(missing)

    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


@pytest.fixture(autouse=True)
def _isolate_gitlab_token_health():
    """Reset the shared GitLab token-health flag around every test.

    ``GitLabClient`` poisons/clears this Redis-backed flag on every request and
    the background-job guard reads it. Without a reset, a 401 mocked in one test
    leaks an ``unauthorized`` value that makes a guarded job (enrich / member
    sync / project refresh) spuriously skip in a *later* test - a cross-test
    failure that only surfaces when Redis is live (CI), not on a dev box where
    Redis is down and the writes are suppressed. Clearing the in-process +
    Redis state before and after each test keeps the flag hermetic.
    """
    import app.services.gitlab.token_health as _h

    def _reset() -> None:
        import contextlib

        _h._local.reset()
        with contextlib.suppress(Exception):
            from app.redis_pool import get_redis

            get_redis().delete(_h._REDIS_KEY)

    _reset()
    yield
    _reset()


def _build_dist() -> None:
    """Build dist/ as CI and the image do: tests read the served files, and the
    pages they render name them. Unchanged outputs are not rewritten (~1 s)."""
    from tests.build_outputs import build_bundle

    build_bundle().build(verbose=False)


def pytest_configure() -> None:
    """Build dist/; ensure mutmut config is available when running mutation stats."""
    _normalise_test_env()
    _build_dist()

    if not os.environ.get("MUTANT_UNDER_TEST"):
        return
    if sys.platform.startswith("win"):
        return
    main_mod = sys.modules.get("__main__")
    main_file = getattr(main_mod, "__file__", "")
    if main_file and main_file.replace("\\", "/").endswith("mutmut/__main__.py"):
        sys.modules.setdefault("mutmut.__main__", main_mod)
    try:
        mutmut_main = importlib.import_module("mutmut.__main__")
        ensure_config_loaded = cast(
            Callable[[], object],
            mutmut_main.ensure_config_loaded,
        )
    except Exception:
        return
    try:
        ensure_config_loaded()
    except Exception:
        return
