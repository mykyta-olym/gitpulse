"""The shared token-health flag must not expire while the condition persists.

The flag exists so one dead token makes every entrypoint and worker refuse
doomed work instead of each independently hammering GitLab. It is stored in
Redis with a TTL, but it used to be written only when the status *changed* - so
a condition that persists (a revoked token) never rewrote it, the key expired,
and every process went back to probing GitLab on its own. That is exactly the
storm the module exists to prevent.
"""

from __future__ import annotations

import pytest

from app.services.gitlab import token_health as th


class _FakeRedis:
    def __init__(self) -> None:
        self.writes: list[tuple[str, str, int | None]] = []

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.writes.append((key, value, ex))

    def get(self, key: str) -> None:
        return None


@pytest.fixture
def redis(monkeypatch: pytest.MonkeyPatch) -> _FakeRedis:
    fake = _FakeRedis()
    monkeypatch.setattr(th, "_pool_get_redis", lambda: fake)
    # A clean module state per test - these are process-wide globals.
    th._local.reset()
    return fake


def test_a_status_change_is_written(redis: _FakeRedis) -> None:
    th.mark_unauthorized()

    assert len(redis.writes) == 1
    assert redis.writes[0][1].startswith("unauthorized")
    assert redis.writes[0][2] == th._STATUS_TTL_S


def test_an_unchanged_status_does_not_write_on_every_call(redis: _FakeRedis) -> None:
    """The hot path stays cheap: mark_ok runs on every successful GitLab call."""
    th.mark_ok()
    for _ in range(50):
        th.mark_ok()

    assert len(redis.writes) == 1, "repeated identical marks must not hit Redis each time"


def test_the_key_is_refreshed_before_it_can_expire(
    redis: _FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The regression: a persistent condition must keep the flag alive.

    Without the refresh the key's TTL lapses and the cross-process flag is gone
    even though the token is still revoked.
    """
    clock = {"t": 1000.0}
    monkeypatch.setattr(th, "_now", lambda: clock["t"])

    th.mark_unauthorized()
    assert len(redis.writes) == 1

    # Still inside the first half of the TTL - no need to write again.
    clock["t"] += th._STATUS_TTL_S / 2 - 1
    th.mark_unauthorized()
    assert len(redis.writes) == 1, "refreshed too eagerly"

    # Past half the TTL: refresh so the key cannot lapse.
    clock["t"] += 2
    th.mark_unauthorized()
    assert len(redis.writes) == 2, "the flag must be refreshed before it expires"
    assert redis.writes[1][1].startswith("unauthorized")
    assert redis.writes[1][2] == th._STATUS_TTL_S


def test_refresh_keeps_working_indefinitely(
    redis: _FakeRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = {"t": 0.0}
    monkeypatch.setattr(th, "_now", lambda: clock["t"])

    th.mark_unauthorized()
    for _ in range(10):
        clock["t"] += th._STATUS_TTL_S
        th.mark_unauthorized()

    # One initial write plus one per elapsed TTL window.
    assert len(redis.writes) == 11
