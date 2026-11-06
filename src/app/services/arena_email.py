"""Arena KPI email lookup - fallback for GitLab-private emails.

The arena endpoint ``/emails/{username}`` returns JSON::

    {
        "username": "user@student.university.edu",
        "identities": [
            {"provider": "openid_connect", "extern_uid": "xy123ab"},
            {"provider": "cas3", "extern_uid": "xy123ab"}
        ]
    }

Not every user has identity info - ``identities`` may be empty or absent.
The ``extern_uid`` is the university LDAP UID (e.g. ``mo562nu``).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ArenaLookupResult:
    """Parsed result from the arena email endpoint."""

    email: str | None = None
    identities: list[dict[str, str]] = field(default_factory=list)
    ldap_uid: str | None = None


# Module-level cache to avoid repeated lookups within the same process.
_cache: dict[str, tuple[ArenaLookupResult, float]] = {}  # username -> (result, timestamp)
_fail_cache: dict[str, float] = {}  # username -> timestamp of last failure
_FAIL_TTL = 120  # retry failed lookups after 2 minutes
_CACHE_TTL = 3600  # expire successful lookups after 1 hour
_MAX_CACHE_SIZE = 5000  # evict oldest entries when cache exceeds this size
_EMPTY = ArenaLookupResult()


def _parse_response(username: str, data: Any) -> ArenaLookupResult:
    """Parse arena API JSON into a structured result."""
    if not isinstance(data, dict):
        return _EMPTY

    # Email is stored as {username: email}
    email = None
    raw_email = data.get(username)
    if isinstance(raw_email, str):
        raw_email = raw_email.strip()
        if "@" in raw_email and 5 <= len(raw_email) <= 254:
            email = raw_email

    # Identities
    identities: list[dict[str, str]] = []
    ldap_uid: str | None = None
    raw_ids = data.get("identities")
    if isinstance(raw_ids, list):
        for entry in raw_ids:
            if isinstance(entry, dict):
                provider = str(entry.get("provider", "")).strip()
                extern_uid = str(entry.get("extern_uid", "")).strip()
                if provider and extern_uid:
                    identities.append({"provider": provider, "extern_uid": extern_uid})
                    # Use the first extern_uid as LDAP UID
                    if not ldap_uid and extern_uid:
                        ldap_uid = extern_uid

    if not email and not identities:
        return _EMPTY

    return ArenaLookupResult(email=email, identities=identities, ldap_uid=ldap_uid)


async def lookup(
    username: str,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> ArenaLookupResult:
    """Fetch email + identity for *username* via arena API.

    Returns an ``ArenaLookupResult`` (always non-None).
    The result is cached for up to 1 hour per username.

    Pass *client* to reuse an existing ``httpx.AsyncClient`` (avoids
    per-request TLS overhead during bulk enrichment).
    """
    if not settings.arena_email_api_enabled:
        return _EMPTY
    if not username or not username.strip():
        return _EMPTY
    username = username.strip().lower()
    cached = _cache.get(username)
    if cached is not None:
        result, ts = cached
        if (time.monotonic() - ts) < _CACHE_TTL:
            return result
        del _cache[username]
    # Skip recently-failed lookups (retry after TTL)
    fail_ts = _fail_cache.get(username)
    if fail_ts is not None and (time.monotonic() - fail_ts) < _FAIL_TTL:
        return _EMPTY

    base_url = (settings.arena_email_api_url or "").rstrip("/")
    if not base_url:
        return _EMPTY

    url = f"{base_url}/{username}"
    headers: dict[str, str] = {}
    token = settings.arena_email_api_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        if client is not None:
            resp = await client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(
                timeout=settings.arena_email_api_timeout_seconds,
                follow_redirects=True,
            ) as _client:
                resp = await _client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning("arena_lookup status=%d user=%s", resp.status_code, username)
            _fail_cache[username] = time.monotonic()
            return _EMPTY
        data = resp.json()
        result = _parse_response(username, data)
        _cache[username] = (result, time.monotonic())
        # Evict oldest entries when cache grows too large
        if len(_cache) > _MAX_CACHE_SIZE:
            oldest = sorted(_cache, key=lambda k: _cache[k][1])[: len(_cache) - _MAX_CACHE_SIZE]
            for k in oldest:
                del _cache[k]
        if len(_fail_cache) > _MAX_CACHE_SIZE:
            oldest_f = sorted(_fail_cache, key=lambda k: _fail_cache[k])[
                : len(_fail_cache) - _MAX_CACHE_SIZE
            ]
            for k in oldest_f:
                del _fail_cache[k]
        if result.email:
            logger.debug(
                "arena_lookup user=%s email=%s ldap=%s",
                username,
                result.email,
                result.ldap_uid,
            )
        return result
    except Exception:
        logger.warning("arena_lookup_failed user=%s", username, exc_info=True)
        _fail_cache[username] = time.monotonic()
        return _EMPTY


async def lookup_email(
    username: str,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> str | None:
    """Convenience wrapper - returns just the email string or None."""
    result = await lookup(username, settings, client=client)
    return result.email
