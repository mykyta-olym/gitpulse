"""Unit tests for the Redis-backed session store (#6)."""

from __future__ import annotations

import json
import time
from typing import Any

import pytest
from fastapi import Response
from itsdangerous import URLSafeSerializer
from redis.exceptions import ConnectionError as RedisConnectionError

from app.security import session_auth, session_store
from app.security.session_store import (
    RedisSessionStore,
    SessionStoreUnavailable,
    get_session_store,
    init_session_store,
)

# -- In-memory fake Redis ----------------------------------------------


class _FakeRedis:
    """Minimal subset of redis-py used by RedisSessionStore.

    Stores raw bytes, honours TTL via per-key wall-clock expiry, and
    supports the SET/GET/DEL/EXPIRE/TTL surface."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}
        self._expiry: dict[str, float] = {}

    def _expired(self, key: str) -> bool:
        exp = self._expiry.get(key)
        if exp is None:
            return False
        if time.monotonic() > exp:
            self._data.pop(key, None)
            self._expiry.pop(key, None)
            return True
        return False

    def get(self, name: str) -> bytes | None:
        if self._expired(name):
            return None
        return self._data.get(name)

    def set(self, name: str, value: bytes | str, ex: int | None = None) -> bool:
        if isinstance(value, str):
            value = value.encode("utf-8")
        self._data[name] = value
        if ex is not None:
            self._expiry[name] = time.monotonic() + ex
        else:
            self._expiry.pop(name, None)
        return True

    def delete(self, *names: str) -> int:
        n = 0
        for k in names:
            if k in self._data:
                del self._data[k]
                n += 1
            self._expiry.pop(k, None)
        return n

    def expire(self, name: str, time_seconds: int) -> bool:
        if name in self._data:
            self._expiry[name] = time.monotonic() + time_seconds
            return True
        return False

    def ttl(self, name: str) -> int:
        if name not in self._data:
            return -2
        exp = self._expiry.get(name)
        if exp is None:
            return -1
        return max(0, int(exp - time.monotonic()))


class _BrokenRedis(_FakeRedis):
    def get(self, name: str) -> bytes | None:
        raise RedisConnectionError("simulated outage")

    def set(self, name: str, value: Any, ex: int | None = None) -> bool:
        raise RedisConnectionError("simulated outage")


# -- Fixtures ----------------------------------------------------------


@pytest.fixture
def fake_redis() -> _FakeRedis:
    return _FakeRedis()


@pytest.fixture
def store(fake_redis: _FakeRedis) -> RedisSessionStore:
    return RedisSessionStore(
        fake_redis,
        secret_key="test-secret-key-32-chars-long-xx",
        idle_refresh_seconds=10,
    )


@pytest.fixture(autouse=True)
def _reset_store() -> Any:
    session_store._store = None
    yield
    session_store._store = None


# -- Direct store API --------------------------------------------------


def test_create_returns_signed_token(store: RedisSessionStore) -> None:
    token = store.create({"user": "alice", "role": "teacher"}, max_age=60)
    # signed -> contains a dot separator from itsdangerous
    assert "." in token
    assert len(token) < 200  # tiny compared to a stateless cookie


def test_round_trip_data(store: RedisSessionStore) -> None:
    payload = {"user": "alice", "role": "teacher", "user_id": "42"}
    token = store.create(payload, max_age=60)
    loaded = store.load(token, max_age=60)
    assert loaded is not None
    assert loaded["user"] == "alice"
    assert loaded["user_id"] == "42"


def test_tampered_signature_returns_none(store: RedisSessionStore) -> None:
    token = store.create({"user": "alice"}, max_age=60)
    # Flip a char in the *middle* of the signature. NOTE: tampering the
    # very last base64 char can flip only padding bits - a 27-char b64
    # SHA1 signature has 2 unused bits at the end, so e.g. "QA" and "QB"
    # decode to identical bytes. Mutating an interior char guarantees a
    # changed HMAC.
    payload, _, sig = token.rpartition(".")
    assert sig, "expected itsdangerous to emit payload.signature"
    mid = len(sig) // 2
    tampered_char = "A" if sig[mid] != "A" else "B"
    tampered = f"{payload}.{sig[:mid]}{tampered_char}{sig[mid + 1 :]}"
    assert tampered != token, "test bug: tampering produced identical token"
    assert store.load(tampered, max_age=60) is None


def test_revoke_deletes_session(store: RedisSessionStore, fake_redis: _FakeRedis) -> None:
    token = store.create({"user": "alice", "user_id": "42"}, max_age=60)
    assert store.revoke(token) is True
    assert store.load(token, max_age=60) is None
    # Idempotent
    assert store.revoke(token) is False


def test_load_missing_key_returns_none(store: RedisSessionStore, fake_redis: _FakeRedis) -> None:
    token = store.create({"user": "alice"}, max_age=60)
    fake_redis.delete(
        "session:"
        + URLSafeSerializer(
            "test-secret-key-32-chars-long-xx", salt="gitpulse-session-id-v1"
        ).loads(token)
    )
    assert store.load(token, max_age=60) is None


def test_load_corrupt_payload_returns_none(
    store: RedisSessionStore, fake_redis: _FakeRedis
) -> None:
    token = store.create({"user": "alice"}, max_age=60)
    sid = URLSafeSerializer(
        "test-secret-key-32-chars-long-xx", salt="gitpulse-session-id-v1"
    ).loads(token)
    fake_redis.set(f"session:{sid}", b"not json at all{")
    assert store.load(token, max_age=60) is None


def test_load_non_dict_payload_returns_none(
    store: RedisSessionStore, fake_redis: _FakeRedis
) -> None:
    token = store.create({"user": "alice"}, max_age=60)
    sid = URLSafeSerializer(
        "test-secret-key-32-chars-long-xx", salt="gitpulse-session-id-v1"
    ).loads(token)
    fake_redis.set(f"session:{sid}", json.dumps([1, 2, 3]).encode())
    assert store.load(token, max_age=60) is None


def test_load_returns_none_on_redis_outage() -> None:
    s = RedisSessionStore(
        _BrokenRedis(),
        secret_key="test-secret-key-32-chars-long-xx",
    )
    # The signature is verified locally first, so we need a *valid* token.
    valid = URLSafeSerializer(
        "test-secret-key-32-chars-long-xx",
        salt="gitpulse-session-id-v1",
    ).dumps("anything")
    assert s.load(valid, max_age=60) is None


def test_create_raises_on_redis_outage() -> None:
    s = RedisSessionStore(
        _BrokenRedis(),
        secret_key="test-secret-key-32-chars-long-xx",
    )
    with pytest.raises(SessionStoreUnavailable):
        s.create({"user": "alice"}, max_age=60)


def test_ttl_refresh_only_after_idle_window(
    store: RedisSessionStore, fake_redis: _FakeRedis
) -> None:
    token = store.create({"user": "alice"}, max_age=60)
    sid = URLSafeSerializer(
        "test-secret-key-32-chars-long-xx", salt="gitpulse-session-id-v1"
    ).loads(token)
    key = f"session:{sid}"

    # First load right after create - TTL still ~60s, well above
    # max_age - idle_refresh (50s), so no refresh.
    ttl_before = fake_redis.ttl(key)
    store.load(token, max_age=60)
    ttl_after = fake_redis.ttl(key)
    assert ttl_after <= ttl_before  # not bumped

    # Simulate elapsed time by shrinking the expiry directly.
    fake_redis._expiry[key] = time.monotonic() + 30  # 30s remaining
    store.load(token, max_age=60)
    assert fake_redis.ttl(key) > 50  # bumped back up


# -- Module-level singleton --------------------------------------------


def test_singleton_init_and_reset(fake_redis: _FakeRedis) -> None:
    assert get_session_store() is None
    s = init_session_store(fake_redis, "x" * 32)
    assert get_session_store() is s
    session_store._store = None
    assert get_session_store() is None


# -- Integration with session_auth.create_session_cookie ---------------


def test_create_session_cookie_uses_store_when_initialised(
    fake_redis: _FakeRedis,
) -> None:
    init_session_store(fake_redis, "x" * 32)
    response = Response()
    session_auth.create_session_cookie(
        response,
        secret_key="x" * 32,
        user="alice",
        role="teacher",
        user_id="42",
        max_age=60,
    )
    cookies = response.headers.getlist("set-cookie")
    assert len(cookies) == 1
    cookie_value = cookies[0].split("=", 1)[1].split(";", 1)[0]
    # Cookie should be the small signed sid (much less than the full
    # itsdangerous payload which would be ~400+ chars for our payload).
    assert len(cookie_value) < 250
    # Server-side record exists
    assert any(k.startswith("session:") for k in fake_redis._data)


def test_create_session_cookie_falls_back_when_store_broken() -> None:
    init_session_store(_BrokenRedis(), "x" * 32)
    response = Response()
    # Must not raise - falls back to stateless signed cookie path.
    session_auth.create_session_cookie(
        response,
        secret_key="x" * 32,
        user="alice",
        max_age=60,
    )
    assert response.headers.getlist("set-cookie")


def test_create_session_cookie_can_fail_closed_when_store_broken() -> None:
    init_session_store(_BrokenRedis(), "x" * 32)
    response = Response()
    with pytest.raises(SessionStoreUnavailable):
        session_auth.create_session_cookie(
            response,
            secret_key="x" * 32,
            user="alice",
            max_age=60,
            allow_stateless_fallback=False,
        )


def test_create_session_cookie_can_fail_closed_when_store_missing() -> None:
    response = Response()
    with pytest.raises(SessionStoreUnavailable):
        session_auth.create_session_cookie(
            response,
            secret_key="x" * 32,
            user="alice",
            max_age=60,
            allow_stateless_fallback=False,
        )


def test_create_session_cookie_uses_legacy_path_when_no_store() -> None:
    # No init_session_store called -> legacy stateless path.
    response = Response()
    session_auth.create_session_cookie(
        response,
        secret_key="x" * 32,
        user="alice",
        max_age=60,
    )
    cookies = response.headers.getlist("set-cookie")
    assert cookies
    cookie_value = cookies[0].split("=", 1)[1].split(";", 1)[0]
    # Stateless payload is much larger than a signed sid.
    assert len(cookie_value) > 200


# -- Integration with session_auth.get_current_session -----------------


class _FakeRequest:
    def __init__(self, cookies: dict[str, str], ua: str = "") -> None:
        self.cookies = cookies
        self.headers = {"User-Agent": ua} if ua else {}


def test_get_current_session_reads_from_store(fake_redis: _FakeRedis) -> None:
    init_session_store(fake_redis, "x" * 32)
    response = Response()
    session_auth.create_session_cookie(
        response,
        secret_key="x" * 32,
        user="alice",
        role="teacher",
        user_id="42",
        max_age=60,
    )
    cookie_value = response.headers.getlist("set-cookie")[0].split("=", 1)[1].split(";", 1)[0]
    request = _FakeRequest({"gitpulse_session": cookie_value})
    data = session_auth.get_current_session(
        request,  # type: ignore[arg-type]
        secret_key="x" * 32,
        max_age=60,
    )
    assert data is not None
    assert data["user"] == "alice"
    assert data["role"] == "teacher"


def test_get_current_session_falls_back_to_legacy_cookie(
    fake_redis: _FakeRedis,
) -> None:
    """A legacy stateless cookie still validates even when the store is on.

    Migration safety: existing browsers carrying long cookies must keep
    working through the rollout.
    """
    init_session_store(fake_redis, "x" * 32)
    # Build the legacy stateless cookie WITHOUT touching the store.
    session_store._store = None
    response = Response()
    session_auth.create_session_cookie(
        response,
        secret_key="x" * 32,
        user="alice",
        max_age=60,
    )
    legacy_value = response.headers.getlist("set-cookie")[0].split("=", 1)[1].split(";", 1)[0]
    # Now turn the store back on and try to validate the legacy cookie.
    init_session_store(fake_redis, "x" * 32)
    request = _FakeRequest({"gitpulse_session": legacy_value})
    data = session_auth.get_current_session(
        request,  # type: ignore[arg-type]
        secret_key="x" * 32,
        max_age=60,
    )
    assert data is not None
    assert data["user"] == "alice"


def test_clear_session_cookie_revokes_server_side(fake_redis: _FakeRedis) -> None:
    init_session_store(fake_redis, "x" * 32)
    response = Response()
    session_auth.create_session_cookie(
        response,
        secret_key="x" * 32,
        user="alice",
        user_id="42",
        max_age=60,
    )
    cookie_value = response.headers.getlist("set-cookie")[0].split("=", 1)[1].split(";", 1)[0]

    # Confirm session exists in Redis.
    assert any(k.startswith("session:") for k in fake_redis._data)

    request = _FakeRequest({"gitpulse_session": cookie_value})
    response2 = Response()
    session_auth.clear_session_cookie(
        response2,
        app_base_url="http://localhost:8000",
        request=request,  # type: ignore[arg-type]
    )
    # Server-side record gone.
    assert not any(k.startswith("session:") for k in fake_redis._data)
