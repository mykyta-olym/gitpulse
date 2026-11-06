"""Tests for the arena email lookup fallback (JSON API with identities)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def arena_settings():
    s = MagicMock()
    s.arena_email_api_enabled = True
    s.arena_email_api_url = "https://arena.kpi.fei.tuke.sk/emails"
    s.arena_email_api_timeout_seconds = 5
    s.arena_email_api_token = ""
    return s


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear module-level cache between tests."""
    from app.services.arena_email import _cache

    _cache.clear()
    yield
    _cache.clear()


def _json_response(data, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = data
    return resp


def _mock_client(resp):
    client_instance = AsyncMock()
    client_instance.get = AsyncMock(return_value=resp)
    client_instance.__aenter__ = AsyncMock(return_value=client_instance)
    client_instance.__aexit__ = AsyncMock(return_value=False)
    return client_instance


@pytest.mark.asyncio
async def test_lookup_returns_email(arena_settings):
    from app.services.arena_email import lookup_email

    resp = _json_response({"tk511zn": "student@university.edu"})

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        ci = _mock_client(resp)
        mock_client.return_value = ci

        result = await lookup_email("tk511zn", arena_settings)
        assert result == "student@university.edu"
        ci.get.assert_called_once_with("https://arena.kpi.fei.tuke.sk/emails/tk511zn", headers={})


@pytest.mark.asyncio
async def test_lookup_full_result_with_identities(arena_settings):
    from app.services.arena_email import lookup

    resp = _json_response(
        {
            "mykyta.olym": "mykyta.olym.work@gmail.com",
            "identities": [
                {"provider": "openid_connect", "extern_uid": "mo562nu"},
                {"provider": "cas3", "extern_uid": "mo562nu"},
            ],
        }
    )

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        mock_client.return_value = _mock_client(resp)

        result = await lookup("mykyta.olym", arena_settings)
        assert result.email == "mykyta.olym.work@gmail.com"
        assert len(result.identities) == 2
        assert result.identities[0]["provider"] == "openid_connect"
        assert result.ldap_uid == "mo562nu"


@pytest.mark.asyncio
async def test_lookup_no_identities(arena_settings):
    from app.services.arena_email import lookup

    resp = _json_response({"someuser": "someuser@university.edu"})

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        mock_client.return_value = _mock_client(resp)

        result = await lookup("someuser", arena_settings)
        assert result.email == "someuser@university.edu"
        assert result.identities == []
        assert result.ldap_uid is None


@pytest.mark.asyncio
async def test_lookup_caches_result(arena_settings):
    from app.services.arena_email import lookup_email

    resp = _json_response({"abc123": "cached@university.edu"})

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        ci = _mock_client(resp)
        mock_client.return_value = ci

        r1 = await lookup_email("abc123", arena_settings)
        r2 = await lookup_email("abc123", arena_settings)
        assert r1 == r2 == "cached@university.edu"
        assert ci.get.call_count == 1


@pytest.mark.asyncio
async def test_lookup_disabled(arena_settings):
    from app.services.arena_email import lookup_email

    arena_settings.arena_email_api_enabled = False
    result = await lookup_email("anyone", arena_settings)
    assert result is None


@pytest.mark.asyncio
async def test_lookup_empty_username(arena_settings):
    from app.services.arena_email import lookup_email

    assert await lookup_email("", arena_settings) is None
    assert await lookup_email("   ", arena_settings) is None


@pytest.mark.asyncio
async def test_lookup_not_found(arena_settings):
    from app.services.arena_email import lookup_email

    resp = _json_response({"error": "Not found"}, status=404)

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        mock_client.return_value = _mock_client(resp)

        result = await lookup_email("nonexistent", arena_settings)
        assert result is None


@pytest.mark.asyncio
async def test_lookup_invalid_email(arena_settings):
    from app.services.arena_email import lookup_email

    resp = _json_response({"baduser": "not-an-email"})

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        mock_client.return_value = _mock_client(resp)

        result = await lookup_email("baduser", arena_settings)
        assert result is None


@pytest.mark.asyncio
async def test_lookup_network_error(arena_settings):
    from app.services.arena_email import lookup_email

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        ci = AsyncMock()
        ci.get = AsyncMock(side_effect=ConnectionError("timeout"))
        ci.__aenter__ = AsyncMock(return_value=ci)
        ci.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = ci

        result = await lookup_email("timeout_user", arena_settings)
        assert result is None


@pytest.mark.asyncio
async def test_lookup_strips_whitespace(arena_settings):
    from app.services.arena_email import lookup_email

    resp = _json_response({"username": "user@university.edu"})

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        ci = _mock_client(resp)
        mock_client.return_value = ci

        result = await lookup_email("  UserName  ", arena_settings)
        assert result == "user@university.edu"
        ci.get.assert_called_once_with("https://arena.kpi.fei.tuke.sk/emails/username", headers={})


@pytest.mark.asyncio
async def test_lookup_empty_identities_list(arena_settings):
    from app.services.arena_email import lookup

    resp = _json_response(
        {
            "user1": "user1@university.edu",
            "identities": [],
        }
    )

    with patch("app.services.arena_email.httpx.AsyncClient") as mock_client:
        mock_client.return_value = _mock_client(resp)

        result = await lookup("user1", arena_settings)
        assert result.email == "user1@university.edu"
        assert result.identities == []
        assert result.ldap_uid is None
