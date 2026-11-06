"""HTTP caching contract for the project GitLab-intel endpoints.

The intel panels (protected branches / contributors / statistics / …) change
only on a sync, so their responses carry a private Cache-Control + a
content-derived ETag and answer 304 to a matching conditional request. This
keeps the project page from re-pulling the full payload on every refresh.
"""

from starlette.requests import Request

from app.api.projects import _cached_json


def _req(if_none_match: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if if_none_match is not None:
        headers.append((b"if-none-match", if_none_match.encode()))
    return Request({"type": "http", "method": "GET", "headers": headers})


def test_cached_json_sets_private_cache_control_and_etag() -> None:
    resp = _cached_json(_req(), [{"name": "main"}])
    assert resp.status_code == 200
    cache_control = resp.headers["cache-control"]
    assert "private" in cache_control
    assert "max-age=" in cache_control
    assert resp.headers["etag"].startswith('W/"')


def test_cached_json_returns_304_on_matching_etag() -> None:
    first = _cached_json(_req(), [{"name": "main"}])
    etag = first.headers["etag"]
    revalidated = _cached_json(_req(if_none_match=etag), [{"name": "main"}])
    assert revalidated.status_code == 304
    assert revalidated.headers["etag"] == etag
    # 304 must still advertise the cache policy so the browser keeps the entry.
    assert "max-age=" in revalidated.headers["cache-control"]


def test_cached_json_etag_changes_when_payload_changes() -> None:
    unchanged = _cached_json(_req(), {"commit_count": 10})
    changed = _cached_json(_req(), {"commit_count": 11})
    assert unchanged.headers["etag"] != changed.headers["etag"]


def test_cached_json_ignores_stale_etag() -> None:
    # A client holding an old ETag must get fresh 200 data, not a 304.
    resp = _cached_json(_req(if_none_match='W/"deadbeef"'), {"commit_count": 11})
    assert resp.status_code == 200
