"""Bearer token verification for API endpoints."""

import hmac


def verify_bearer_token(provided_token: str, expected_token: str) -> bool:
    """Constant-time comparison of bearer tokens."""
    return hmac.compare_digest(provided_token.encode("utf-8"), expected_token.encode("utf-8"))
