"""Webhook token verification - constant-time comparison against bcrypt hash.

In addition to the bcrypt hash (used for per-project authentication where
we already know which row to verify against) we also store an
HMAC-SHA256 lookup digest keyed by the application SECRET_KEY.  The
digest is deterministic for a given (secret, SECRET_KEY) pair, so it can
be used as a direct ``WHERE`` clause when authenticating *orphan*
webhooks (no project row yet) - turning the previous O(N) bcrypt sweep
across every configured course secret into a single indexed lookup.
"""

import hashlib
import hmac
import os
import secrets

import bcrypt


def generate_webhook_secret() -> str:
    """Generate a secure webhook secret token."""
    return f"whsec_{secrets.token_hex(24)}"


def hash_webhook_secret(secret: str) -> str:
    """Hash a webhook secret for storage."""
    return bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def compute_webhook_lookup_key(secret: str, app_secret_key: str | None = None) -> str:
    """Return a deterministic HMAC-SHA256 digest of ``secret``.

    Keyed by the application SECRET_KEY so the same webhook secret
    yields different lookup keys across installations (and is
    invalidated on SECRET_KEY rotation).  Returned value is hex-encoded
    (64 chars) for safe storage in a TEXT/CHAR column with a B-tree
    index.

    The resulting key is **not** a password hash - its sole purpose is
    to enable a constant-cost ``WHERE webhook_secret_lookup = :h`` query.
    Authentication still verifies the bcrypt hash on the matched row to
    keep the actual secret protected at rest.
    """
    if app_secret_key is None:
        # From the SETTINGS, not straight from the process environment.
        #
        # `os.environ.get("SECRET_KEY", "")` looks equivalent and is not: this
        # app reads its configuration through pydantic-settings, which loads
        # `.env` into the Settings object WITHOUT exporting anything to the
        # environment. So a deployment that keeps SECRET_KEY in `.env` - the
        # documented way to run it - computed every lookup digest with an EMPTY
        # key, while any process that happened to have the variable exported
        # (a container with an `environment:` block, a script that called
        # load_dotenv) computed it with the real one. The two then disagreed,
        # and a webhook whose secret was written by one was rejected by the
        # other with a bare 401.
        #
        # Reproduced locally: a configuration created by a script (env exported)
        # was refused by the uvicorn server (env not exported) for every
        # delivery. It also broke the guarantee in this module's own docstring -
        # with an empty key the digest is identical across installations.
        from app.config import get_settings

        app_secret_key = get_settings().secret_key or os.environ.get("SECRET_KEY", "")
    return hmac.new(
        app_secret_key.encode("utf-8"),
        secret.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_webhook_token(token: str, stored_hash: str) -> bool:
    """Verify a webhook token against its stored bcrypt hash.

    Uses bcrypt.checkpw which is constant-time.
    """
    try:
        return bcrypt.checkpw(token.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
