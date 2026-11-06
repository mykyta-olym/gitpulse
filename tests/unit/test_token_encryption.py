"""Unit tests for token_encryption - Fernet-based encrypt/decrypt.

Tests encrypt_token, decrypt_token, is_encrypted, and key derivation.
"""

from app.security.token_encryption import (
    _ENCRYPTED_PREFIX,
    decrypt_token,
    encrypt_token,
    is_encrypted,
)

SECRET = "test-secret-key-for-unit-tests-only"


class TestEncryptToken:
    def test_encrypt_returns_prefixed(self) -> None:
        result = encrypt_token("my-token-123", SECRET)
        assert result is not None
        assert result.startswith(_ENCRYPTED_PREFIX)

    def test_encrypt_none_returns_none(self) -> None:
        assert encrypt_token(None, SECRET) is None

    def test_encrypt_empty_returns_empty(self) -> None:
        assert encrypt_token("", SECRET) == ""

    def test_encrypt_idempotent(self) -> None:
        encrypted = encrypt_token("my-token", SECRET)
        assert encrypted is not None
        # Encrypting again should return same value (already encrypted)
        result = encrypt_token(encrypted, SECRET)
        assert result == encrypted

    def test_encrypt_different_tokens_differ(self) -> None:
        e1 = encrypt_token("token-a", SECRET)
        e2 = encrypt_token("token-b", SECRET)
        assert e1 != e2


class TestDecryptToken:
    def test_decrypt_returns_original(self) -> None:
        original = "ghp_test_token_12345"
        encrypted = encrypt_token(original, SECRET)
        decrypted = decrypt_token(encrypted, SECRET)
        assert decrypted == original

    def test_decrypt_none_returns_none(self) -> None:
        assert decrypt_token(None, SECRET) is None

    def test_decrypt_empty_returns_empty(self) -> None:
        assert decrypt_token("", SECRET) == ""

    def test_decrypt_legacy_plaintext(self) -> None:
        """Non-encrypted values returned as-is (legacy support)."""
        result = decrypt_token("plain-token-not-encrypted", SECRET)
        assert result == "plain-token-not-encrypted"

    def test_decrypt_invalid_cipher_returns_none(self) -> None:
        """Corrupted encrypted value returns None."""
        corrupted = _ENCRYPTED_PREFIX + "not-valid-base64-fernet-data"
        result = decrypt_token(corrupted, SECRET)
        assert result is None

    def test_decrypt_wrong_key_returns_none(self) -> None:
        """A different key must not reuse the cached Fernet instance."""
        encrypted = encrypt_token("secret-data", SECRET)
        assert decrypt_token(encrypted, "wrong-key-entirely-different") is None
        assert decrypt_token(encrypted, SECRET) == "secret-data"


class TestIsEncrypted:
    def test_encrypted_value(self) -> None:
        encrypted = encrypt_token("my-token", SECRET)
        assert encrypted is not None
        assert is_encrypted(encrypted) is True

    def test_plain_value(self) -> None:
        assert is_encrypted("plain-text") is False

    def test_none_value(self) -> None:
        assert is_encrypted(None) is False

    def test_empty_value(self) -> None:
        assert is_encrypted("") is False


class TestRoundTrip:
    def test_roundtrip_short_token(self) -> None:
        token = "abc"
        assert decrypt_token(encrypt_token(token, SECRET), SECRET) == token

    def test_roundtrip_long_token(self) -> None:
        token = "token_prefix_" + "x" * 200
        assert decrypt_token(encrypt_token(token, SECRET), SECRET) == token

    def test_roundtrip_unicode(self) -> None:
        token = "tökën-wíth-üñícödé"
        assert decrypt_token(encrypt_token(token, SECRET), SECRET) == token
