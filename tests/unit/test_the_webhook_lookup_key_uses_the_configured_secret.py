"""The webhook lookup digest is keyed by the SECRET_KEY the app is running with.

`compute_webhook_lookup_key` fell back to `os.environ.get("SECRET_KEY", "")`.
That is not where this application's configuration lives: pydantic-settings
reads `.env` into the Settings object and exports nothing to the environment. So
a deployment that keeps SECRET_KEY in `.env` - the documented way to run it -
computed every digest with an EMPTY key, while any process that happened to have
the variable exported (a container with an `environment:` block, a script that
called `load_dotenv`) computed it with the real one.

The two then disagreed, and the disagreement is silent: a webhook configuration
whose secret was written by one process is not found by the other, and the
delivery is refused with a bare 401.

Reproduced end to end before the fix: a configuration created by a script was
rejected by the uvicorn server for every delivery - issue, push, merge request
and pipeline hooks all 401 - and accepted by all four afterwards.

It also broke this module's own guarantee: with an empty key the digest is
identical across installations, which is exactly what keying it was for.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest

from app.config import get_settings
from app.security.webhook_auth import compute_webhook_lookup_key

TOKEN = "whsec_0123456789abcdef0123456789abcdef0123456789abcdef"


def _expected(key: str) -> str:
    return hmac.new(key.encode("utf-8"), TOKEN.encode("utf-8"), hashlib.sha256).hexdigest()


def test_it_keys_on_the_settings_secret_when_the_environment_has_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The case that broke webhooks: SECRET_KEY in `.env`, not in os.environ."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    settings_key = get_settings().secret_key
    assert settings_key, "the test settings carry no secret key to check against"
    assert compute_webhook_lookup_key(TOKEN) == _expected(settings_key)


def test_an_explicit_key_still_wins() -> None:
    """Callers that pass a key - rotation tooling, tests - are unaffected."""
    assert compute_webhook_lookup_key(TOKEN, "some-other-key") == _expected("some-other-key")


def test_the_digest_is_never_the_unkeyed_one(monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty key produces a digest that is the same on every installation,
    which is the thing this function exists to avoid."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    assert compute_webhook_lookup_key(TOKEN) != _expected("")


def test_it_is_stable_across_processes_with_and_without_the_export(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One process has the variable exported, the other does not - they have to
    agree, or a secret written by one cannot be found by the other."""
    settings_key = get_settings().secret_key
    monkeypatch.delenv("SECRET_KEY", raising=False)
    without_export = compute_webhook_lookup_key(TOKEN)
    monkeypatch.setenv("SECRET_KEY", settings_key)
    with_export = compute_webhook_lookup_key(TOKEN)
    assert without_export == with_export
