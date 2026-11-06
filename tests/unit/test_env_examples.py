"""`.env*.example` must only document variables that actually exist.

The examples drifted badly: they advertised `FEATURE_RUBRIC_ENGINE`,
`FEATURE_GAMING_DETECTION`, `FEATURE_TIMELINE_DASHBOARD`, `FEATURE_ROSTER_IMPORT`,
`CONFLICT_BOT_*`, `DOCKER_VERIFY_*`, `CI_FAILURE_BOT_*` and `RQ_MAX_RETRIES` -
none of which anything reads. Somebody setting up a deployment tuned knobs that
did nothing. This pins the examples to reality.

A key is legitimate when it is either a ``Settings`` field, an interpolation in
a compose file / Caddyfile, or one of the few read straight from ``os.environ``.
"""

import re
from pathlib import Path

import pytest

from app.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLES = (".env.example", ".env.production.example")

# Read directly via os.environ rather than through the Settings model.
DIRECT_ENV_READS = {
    "ENCRYPTION_SALT",  # app/security/token_encryption.py
}


def _settings_keys() -> set[str]:
    return {name.upper() for name in Settings.model_fields}


def _infra_keys() -> set[str]:
    """Keys consumed by docker-compose / Caddy instead of the app."""
    keys: set[str] = set()
    for path in REPO_ROOT.glob("docker-compose*.yml"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        keys |= {m.upper() for m in re.findall(r"\$\{([A-Z0-9_]+)", text)}
    for path in REPO_ROOT.glob("Caddyfile*"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        keys |= {m.upper() for m in re.findall(r"\{\$([A-Z0-9_]+)", text)}
    return keys


def _declared_keys(example: str) -> list[str]:
    keys = []
    for line in (REPO_ROOT / example).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"([A-Za-z0-9_]+)\s*=", line)
        if match:
            keys.append(match.group(1).upper())
    return keys


@pytest.mark.parametrize("example", ENV_EXAMPLES)
def test_env_example_documents_only_real_variables(example: str) -> None:
    known = _settings_keys() | _infra_keys() | DIRECT_ENV_READS
    ghosts = sorted(set(_declared_keys(example)) - known)
    assert not ghosts, (
        f"{example} documents variables nothing reads: {ghosts}. "
        "Remove them, or wire them up in app/config.py / docker-compose.yml."
    )


@pytest.mark.parametrize("example", ENV_EXAMPLES)
def test_env_example_has_no_duplicate_keys(example: str) -> None:
    keys = _declared_keys(example)
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    assert not dupes, f"{example} declares these keys twice: {dupes}"


@pytest.mark.parametrize("example", ENV_EXAMPLES)
def test_env_example_covers_every_feature_flag(example: str) -> None:
    """A flag that exists but is undocumented is just as bad as a ghost."""
    flags = {name.upper() for name in Settings.model_fields if name.startswith("feature_")}
    missing = sorted(flags - set(_declared_keys(example)))
    assert not missing, f"{example} does not document these feature flags: {missing}"
