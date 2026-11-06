"""Run unit tests with a shell-independent test environment."""

from __future__ import annotations

import os
import subprocess
import sys

_DEFAULTS = {
    "APP_ENV": "test",
    "DEBUG": "false",
    "DATABASE_URL": "postgresql+asyncpg://gitpulse:testpassword@localhost:5432/gitpulse_test",
    "SECRET_KEY": "test-secret-key-minimum-sixteen-chars",
    "TEACHER_API_TOKEN": "test-token-12345678",
}


def _normalise_env() -> dict[str, str]:
    env = os.environ.copy()
    for key, value in _DEFAULTS.items():
        if not env.get(key, "").strip():
            env[key] = value
    if env.get("APP_ENV") not in {"development", "production", "test"}:
        env["APP_ENV"] = _DEFAULTS["APP_ENV"]
    if env.get("DEBUG", "").strip().lower() not in {"true", "false", "1", "0", "yes", "no"}:
        env["DEBUG"] = _DEFAULTS["DEBUG"]
    if len(env.get("SECRET_KEY", "")) < 16:
        env["SECRET_KEY"] = _DEFAULTS["SECRET_KEY"]
    if len(env.get("TEACHER_API_TOKEN", "")) < 8:
        env["TEACHER_API_TOKEN"] = _DEFAULTS["TEACHER_API_TOKEN"]
    return env


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/unit/",
        "-x",
        "-q",
        "--no-header",
        "--tb=short",
    ]
    return subprocess.call(cmd, env=_normalise_env())


if __name__ == "__main__":
    raise SystemExit(main())
