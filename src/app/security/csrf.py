"""CSRF token generation and validation using HMAC-SHA256.

Tokens bind to the user identity from the session and expire after max_age seconds.
Format: {user}:{timestamp}:{hmac_hex}

For pre-login forms (no session), pass a nonce as session_data={"user": nonce}.
"""

import hashlib
import hmac
import time


def generate_csrf_token(session_data: dict[str, str], secret_key: str) -> str:
    """Generate an HMAC-signed CSRF token bound to the session user."""
    user = session_data.get("user", "anonymous")
    ts = str(int(time.time()))
    signature = _sign(user, ts, secret_key)
    return f"{user}:{ts}:{signature}"


def validate_csrf_token(
    token: str,
    session_data: dict[str, str],
    secret_key: str,
    max_age: int = 3600,
) -> bool:
    """Validate a CSRF token. Returns False on any failure."""
    if not token:
        return False

    parts = token.split(":", 2)
    if len(parts) != 3:
        return False

    user_from_token, ts_str, signature = parts

    # Check user matches session
    expected_user = session_data.get("user", "anonymous")
    if not hmac.compare_digest(user_from_token, expected_user):
        return False

    # Check timestamp
    try:
        ts = int(ts_str)
    except ValueError:
        return False

    if time.time() - ts > max_age:
        return False

    # Verify HMAC signature (constant-time)
    expected_sig = _sign(user_from_token, ts_str, secret_key)
    return hmac.compare_digest(signature, expected_sig)


def _sign(user: str, timestamp: str, secret_key: str) -> str:
    """Compute HMAC-SHA256 signature."""
    msg = f"{user}:{timestamp}".encode()
    return hmac.new(secret_key.encode(), msg, hashlib.sha256).hexdigest()
