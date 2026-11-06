"""Maintenance clears caches without unlocking live jobs or losing sessions."""

from fnmatch import fnmatch
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.api.dashboard.admin import system


@pytest.mark.asyncio
async def test_cache_cleanup_preserves_operational_state(monkeypatch):
    keys = {
        "gp:page:v3:student",
        "gitlab:response",
        "cache:data",
        "rq:job:1",
        "joblock:sync",
        "rl:user",
        "session:1",
        "circuit:gitlab",
    }

    def scan(cursor, *, match, count):
        return 0, [key for key in keys if fnmatch(key, match)]

    redis = SimpleNamespace(scan=scan, delete=lambda *items: keys.difference_update(items))
    monkeypatch.setattr(system, "_pool_get_redis", lambda: redis)
    settings = Mock()
    monkeypatch.setattr(system, "get_settings", settings)
    response = await system.admin_clear_cache(None, None, None)
    assert response.status_code == 200
    assert keys == {"rq:job:1", "joblock:sync", "rl:user", "session:1", "circuit:gitlab"}
    settings.cache_clear.assert_called_once()


@pytest.mark.asyncio
async def test_cache_cleanup_reports_redis_failure(monkeypatch):
    def unavailable():
        raise ConnectionError("Redis unavailable")

    monkeypatch.setattr(system, "_pool_get_redis", unavailable)
    with pytest.raises(HTTPException) as error:
        await system.admin_clear_cache(None, None, None)
    assert error.value.status_code == 503
