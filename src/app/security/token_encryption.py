"""Fernet-based symmetric encryption for GitLab OAuth tokens.

Derives a 32-byte Fernet key from the application SECRET_KEY via HKDF
(HMAC-based Key Derivation). This avoids requiring a separate encryption
key while ensuring the derived key is cryptographically suitable for Fernet.

Usage:
    from app.security.token_encryption import encrypt_token, decrypt_token

    cipher = encrypt_token("ghp_abc123...", secret_key)
    plain  = decrypt_token(cipher, secret_key)
"""

import base64
import hashlib
import hmac
import os
from threading import Lock
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from cryptography.fernet import Fernet

logger = structlog.get_logger(__name__)

# Marker prefix so we know if a stored value is already encrypted
_ENCRYPTED_PREFIX = "enc:v1:"

# Module-level Fernet cache.  We deliberately do NOT use ``functools.lru_cache``
# keyed on ``secret_key`` because that would retain the plaintext secret in
# the cache key forever (and surface it via ``cache_info()`` introspection).
# Instead we cache by a constant-time HMAC fingerprint of the secret so a
# rotated SECRET_KEY transparently invalidates the cache.
_fernet_lock = Lock()
_fernet_cache: tuple[bytes, "Fernet"] | None = None


def _hkdf_salt() -> bytes:
    """Return the HKDF salt used for token-key derivation.

    Operators can supply an installation-unique salt via the
    ``ENCRYPTION_SALT`` environment variable (hex-encoded preferred, raw
    UTF-8 accepted as a fallback).  When it is set the value is used
    verbatim, which gives each installation a distinct derived key even
    if SECRET_KEY values were ever shared across environments.

    For backward compatibility the historical fixed salt is used when
    ``ENCRYPTION_SALT`` is not set - changing the default would silently
    invalidate every previously encrypted token in the database.  New
    installations should set ``ENCRYPTION_SALT`` (e.g. via
    ``openssl rand -hex 32``) before any tokens are stored.
    """
    env_salt = os.environ.get("ENCRYPTION_SALT", "").strip()
    if env_salt:
        try:
            return bytes.fromhex(env_salt)
        except ValueError:
            return env_salt.encode("utf-8")
    return b"dta-token-encryption-v1"


def _derive_fernet_key(secret_key: str) -> bytes:
    """Derive a Fernet-compatible key from the app secret using HKDF."""
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=_hkdf_salt(),
        info=b"gitlab-oauth-tokens",
    )
    raw = hkdf.derive(secret_key.encode("utf-8"))
    return base64.urlsafe_b64encode(raw)


def _secret_fingerprint(secret_key: str) -> bytes:
    """Constant-time-comparable fingerprint of the secret for cache keying."""
    return hmac.new(b"dta-token-encryption-fp", secret_key.encode("utf-8"), hashlib.sha256).digest()


def _get_fernet(secret_key: str) -> "Fernet":
    """Return a cached Fernet instance for ``secret_key``.

    Cache key is an HMAC fingerprint, so the plaintext secret never sits in
    a long-lived cache structure beyond the live ``Fernet`` object itself.
    """
    global _fernet_cache
    from cryptography.fernet import Fernet

    fp = _secret_fingerprint(secret_key)
    cached = _fernet_cache
    if cached is not None and hmac.compare_digest(cached[0], fp):
        return cached[1]
    with _fernet_lock:
        cached = _fernet_cache
        if cached is not None and hmac.compare_digest(cached[0], fp):
            return cached[1]
        instance = Fernet(_derive_fernet_key(secret_key))
        _fernet_cache = (fp, instance)
        return instance


def encrypt_token(plaintext: str | None, secret_key: str) -> str | None:
    """Encrypt a token string. Returns None for None input.

    Already-encrypted values (prefixed with ``enc:v1:``) are returned as-is.
    """
    if not plaintext:
        return plaintext
    if plaintext.startswith(_ENCRYPTED_PREFIX):
        return plaintext  # idempotent
    f = _get_fernet(secret_key)
    cipher_bytes: bytes = f.encrypt(plaintext.encode("utf-8"))
    return _ENCRYPTED_PREFIX + cipher_bytes.decode("ascii")


def decrypt_token(ciphertext: str | None, secret_key: str, *, strict: bool = False) -> str | None:
    """Decrypt a token string. Returns None for None input.

    Non-encrypted values (legacy plaintext):
      - If ``strict=True`` (recommended after running encrypt_legacy_tokens.py):
        returns None and logs an error - plaintext tokens are rejected.
      - If ``strict=False`` (default, backward-compatible):
        returns the plaintext value as-is with a warning.

    In production (APP_ENV=production), strict mode is auto-enabled.
    """
    if not ciphertext:
        return ciphertext
    if not ciphertext.startswith(_ENCRYPTED_PREFIX):
        # Legacy plaintext token detected
        import os

        is_production = os.environ.get("APP_ENV", "").lower() == "production"
        if strict or is_production:
            logger.error(
                "token_plaintext_rejected",
                token_preview=ciphertext[:8] + "...",
                msg="Plaintext token rejected. Run encrypt_legacy_tokens to migrate.",
            )
            return None
        logger.warning("token_not_encrypted_legacy", token_preview=ciphertext[:8] + "...")
        return ciphertext  # legacy plaintext - return as-is (dev only)
    raw = ciphertext[len(_ENCRYPTED_PREFIX) :]
    try:
        f = _get_fernet(secret_key)
        decrypted: str = f.decrypt(raw.encode("ascii")).decode("utf-8")
        return decrypted
    except Exception:
        logger.error("token_decryption_failed", exc_info=True)
        return None


def is_encrypted(value: str | None) -> bool:
    """Check if a value is already Fernet-encrypted."""
    return bool(value and value.startswith(_ENCRYPTED_PREFIX))
