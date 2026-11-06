"""Redis-backed session store (#6 - server-side sessions).

The cookie still carries an opaque, signed identifier so that:

* tampered IDs are rejected before any Redis round-trip (constant time);
* the server can revoke a session instantly by deleting the Redis key;
* an admin can force-logout a user by scanning ``session:*`` keys.

Layout
------
- ``session:<sid>``       -> JSON blob (utf-8) with the same fields the
  legacy stateless cookie carried (``user``, ``role``, ``email`` ...).
- ``session:user:<uid>``  -> Redis SET of every active ``sid`` for the
  given user, used for "log everywhere" revocation.

Both keys share the same TTL (sliding window).  The user-index set is
kept slightly longer (TTL + 60 s) so that a session whose primary key
just expired is still cleaned up on the next revoke call.

Failure mode
------------
If Redis is unreachable the store fails *closed*: ``load`` returns
``None`` (caller treats as "not authenticated") and ``save`` raises
``SessionStoreUnavailable`` so the caller can fall back to the legacy
stateless cookie path during a partial outage.
"""

from __future__ import annotations

import builtins
import contextlib
import json
import secrets
import time
from typing import Any, Protocol, cast

import structlog
from itsdangerous import BadSignature, URLSafeSerializer
from redis.exceptions import RedisError

logger = structlog.get_logger(__name__)

_SID_BYTES = 24  # 32 chars base64url - 192 bits entropy
_SIGNER_SALT = "gitpulse-session-id-v1"


class SessionStoreUnavailableError(RuntimeError):
    """Raised when the underlying Redis store cannot be reached."""


# Backward-compatible alias (kept until callers migrate).
SessionStoreUnavailable = SessionStoreUnavailableError


class _RedisLike(Protocol):
    """The narrow subset of redis-py we use; lets tests inject a fake."""

    def get(self, name: str) -> bytes | None: ...
    def set(
        self,
        name: str,
        value: bytes | str,
        ex: int | None = ...,
    ) -> bool | None: ...
    def delete(self, *names: str) -> int: ...
    def expire(self, name: str, time: int) -> bool: ...
    def sadd(self, name: str, *values: str) -> int: ...
    def smembers(self, name: str) -> builtins.set[bytes]: ...
    def ttl(self, name: str) -> int: ...


class RedisSessionStore:
    """Server-side session store backed by Redis.

    Parameters
    ----------
    client:
        Redis client - anything implementing the small ``_RedisLike``
        protocol.  Production wires the shared ``redis_pool.get_redis()``.
    secret_key:
        Used to HMAC-sign the opaque session id placed in the cookie.
        Must equal ``Settings.secret_key`` so that signed ids stay valid
        across process restarts (state lives in Redis, not the boot
        nonce).
    key_prefix:
        Redis key namespace (default ``session:``).
    idle_refresh_seconds:
        TTL is bumped only when the remaining lifetime is *less* than
        ``max_age - idle_refresh_seconds``.  Prevents hammering Redis on
        every request.  Set to 0 to refresh on every load.
    """

    def __init__(
        self,
        client: _RedisLike,
        secret_key: str,
        *,
        key_prefix: str = "session:",
        idle_refresh_seconds: int = 300,
        absolute_max_age_seconds: int = 24 * 3600,
    ) -> None:
        self._client = client
        self._signer = URLSafeSerializer(secret_key, salt=_SIGNER_SALT)
        self._prefix = key_prefix
        self._idle_refresh = max(0, idle_refresh_seconds)
        self._absolute_max_age = max(0, absolute_max_age_seconds)

    # -- Public API ----------------------------------------------------
    def create(self, data: dict[str, Any], max_age: int) -> str:
        """Store ``data`` and return a *signed* opaque identifier.

        The returned token is what callers should put in the cookie
        value - it is HMAC-signed so a tampered cookie is rejected
        before any Redis round-trip.
        """
        sid = secrets.token_urlsafe(_SID_BYTES)
        # AUTH-06: stamp creation time so ``load`` can enforce an absolute
        # session-lifetime ceiling regardless of how often the sliding
        # TTL is refreshed.
        if "created_at" not in data:
            data = {**data, "created_at": int(time.time())}
        try:
            self._client.set(self._key(sid), self._encode(data), ex=max_age)
        except RedisError as exc:
            logger.error("session_store_create_failed", error=str(exc))
            raise SessionStoreUnavailableError("redis unavailable") from exc

        logger.info(
            "session_store_created",
            user=data.get("user"),
            role=data.get("role"),
            ttl=max_age,
        )
        return self._signer.dumps(sid)

    def load(self, signed_sid: str, max_age: int) -> dict[str, Any] | None:
        """Return session data for ``signed_sid`` or ``None``.

        Always returns ``None`` (never raises) so callers can treat any
        problem - bad signature, missing key, Redis outage - as
        "not authenticated".
        """
        sid = self._unwrap(signed_sid)
        if sid is None:
            return None
        try:
            raw = self._client.get(self._key(sid))
            if raw is None:
                return None
            data = self._decode(raw)
            # AUTH-06: hard ceiling on session age regardless of sliding TTL
            if self._absolute_max_age > 0:
                created_at = data.get("created_at")
                if (
                    isinstance(created_at, int | float)
                    and int(time.time()) - int(created_at) >= self._absolute_max_age
                ):
                    # Session has exceeded its absolute lifetime - force re-auth.
                    with contextlib.suppress(RedisError):
                        self._client.delete(self._key(sid))
                    logger.info(
                        "session_absolute_lifetime_exceeded",
                        user=data.get("user"),
                        age_seconds=int(time.time()) - int(created_at),
                    )
                    return None
            self._maybe_refresh_ttl(sid, max_age)
            return data
        except RedisError as exc:
            logger.warning("session_store_load_failed", error=str(exc))
            return None
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("session_store_decode_failed", error=str(exc))
            return None

    def revoke(self, signed_sid: str) -> bool:
        """Delete a single session.  Idempotent.  Returns True if a key
        was actually removed."""
        sid = self._unwrap(signed_sid)
        if sid is None:
            return False
        try:
            removed = bool(self._client.delete(self._key(sid)))
            if removed:
                logger.info("session_store_revoked", sid_prefix=sid[:8])
            return removed
        except RedisError as exc:
            logger.warning("session_store_revoke_failed", error=str(exc))
            return False

    # -- Helpers -------------------------------------------------------
    def _key(self, sid: str) -> str:
        return f"{self._prefix}{sid}"

    def _unwrap(self, signed_sid: str) -> str | None:
        if not signed_sid:
            return None
        try:
            return cast(str, self._signer.loads(signed_sid))
        except BadSignature:
            logger.warning("session_store_bad_signature")
            return None

    def _encode(self, data: dict[str, Any]) -> bytes:
        # ``separators`` strips redundant whitespace; ``default=str``
        # safely coerces datetimes already serialised upstream.
        return json.dumps(data, separators=(",", ":"), default=str).encode("utf-8")

    def _decode(self, raw: bytes) -> dict[str, Any]:
        decoded = json.loads(raw.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("session payload is not a JSON object")
        return cast(dict[str, Any], decoded)

    def _maybe_refresh_ttl(self, sid: str, max_age: int) -> None:
        """Bump the TTL only when more than ``idle_refresh_seconds`` of
        the lifetime has been consumed - avoids 1 round-trip per request.
        """
        if self._idle_refresh == 0:
            with contextlib.suppress(RedisError):
                self._client.expire(self._key(sid), max_age)
            return
        try:
            remaining = self._client.ttl(self._key(sid))
        except RedisError:
            return
        if remaining < 0:
            return  # no TTL set or key vanished mid-flight
        if max_age - remaining >= self._idle_refresh:
            with contextlib.suppress(RedisError):
                self._client.expire(self._key(sid), max_age)


# -- Module-level singleton accessor ----------------------------------
_store: RedisSessionStore | None = None


def init_session_store(
    client: _RedisLike,
    secret_key: str,
    *,
    key_prefix: str = "session:",
    idle_refresh_seconds: int = 300,
    absolute_max_age_seconds: int = 24 * 3600,
) -> RedisSessionStore:
    """Initialise the process-global Redis session store.

    Called once from the FastAPI lifespan after ``init_redis_pool``.
    """
    global _store
    _store = RedisSessionStore(
        client,
        secret_key,
        key_prefix=key_prefix,
        idle_refresh_seconds=idle_refresh_seconds,
        absolute_max_age_seconds=absolute_max_age_seconds,
    )
    logger.info(
        "session_store_initialised",
        key_prefix=key_prefix,
        idle_refresh_seconds=idle_refresh_seconds,
        absolute_max_age_seconds=absolute_max_age_seconds,
    )
    return _store


def get_session_store() -> RedisSessionStore | None:
    """Return the configured store, or ``None`` if the feature flag is
    off / lifespan never initialised it."""
    return _store
