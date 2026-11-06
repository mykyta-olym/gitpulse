"""Performance middleware - GZip compression + static asset cache headers.

Provides two middlewares:
- ``GZipMiddleware``: Compresses responses > 500 bytes with gzip
- Static asset ``Cache-Control`` via ``StaticCacheMiddleware``
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl

from starlette.types import ASGIApp, Message, Receive, Scope, Send

# One year in seconds (immutable since we use query-string versioning)
_ONE_YEAR = 31_536_000
_UNVERSIONED_STATIC_MAX_AGE = 300
_STATIC_VERSION_RE = re.compile(r"^[a-fA-F0-9]{8,64}$")

#: Font files are immutable by NAME - a new face ships under a new filename -
#: which is why `fonts.css` and the `<link rel=preload>` in base.html both
#: reference them unversioned: a preload only matches a request by exact URL.
#: That put them in the unversioned bucket, so GitLabSans.woff2 - 325 KB - was
#: served with a five-minute lifetime and downloaded again all day. It is
#: declared `font-display: optional`, which uses the face ONLY when it is
#: already available, so a font that is never in cache is never applied: the
#: reader saw the fallback, and Chrome reported the preload as "preloaded but
#: not used within a few seconds from the window's load event" on every visit.
#: The build outputs in dist/ carry their content hash in the name too.
_IMMUTABLE_STATIC_PREFIXES = ("/static/fonts/", "/static/dist/")


class StaticCacheMiddleware:
    """Add ``Cache-Control`` headers to /static/ assets.

    In **production** the URLs ``static_url()`` gives are versioned - a
    content-hashed name under ``/static/dist/``, or a ``?v=...`` query on a
    source file - so those responses can be cached aggressively (1 year,
    immutable). Direct unversioned ``/static/...``
    requests use a short TTL instead so manifests, icons, and hand-typed
    URLs do not stay stale for a year after a deploy.

    In **development** the header is ``no-cache`` so the browser always
    revalidates with the server, avoiding stale-bundle surprises after
    JS/CSS rebuilds.
    """

    def __init__(self, app: ASGIApp, *, dev_mode: bool = False) -> None:
        self.app = app
        self._dev_mode = dev_mode

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        is_static = path.startswith("/static/")
        query_string = scope.get("query_string", b"")
        is_versioned = _has_version_param(query_string)
        is_immutable_by_name = path.startswith(_IMMUTABLE_STATIC_PREFIXES)
        is_font = path.startswith("/static/fonts/")

        if not is_static:
            await self.app(scope, receive, send)
            return

        async def inject_cache(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                if self._dev_mode and not is_font:
                    # Dev: always revalidate - no stale bundles
                    headers = _set_header(headers, b"cache-control", b"no-cache")
                elif self._dev_mode:
                    # ...but not the fonts: a face never changes under its
                    # name, and one revalidated on every page load arrived
                    # after `font-display: optional` had given up on it now
                    # and then - that page stayed in Segoe UI, the next one
                    # in GitLab Sans, and the text "jumped" between them.
                    immutable = f"public, max-age={_ONE_YEAR}, immutable"
                    headers = _set_header(headers, b"cache-control", immutable.encode())
                else:
                    if is_versioned or is_immutable_by_name:
                        # Production: immutable cache for content-hash versioned
                        # assets, and for the ones whose FILENAME is the version.
                        cache_control = f"public, max-age={_ONE_YEAR}, immutable"
                    else:
                        cache_control = f"public, max-age={_UNVERSIONED_STATIC_MAX_AGE}"
                    headers = _set_header(headers, b"cache-control", cache_control.encode())
                # Vary on encoding so CDN/proxies cache gzip/br separately
                headers = _merge_vary(headers, b"Accept-Encoding")

                message = {**message, "headers": headers}

            await send(message)

        await self.app(scope, receive, inject_cache)


def _has_version_param(query_string: bytes | str) -> bool:
    """Return True when the static request carries a content-hash ``v`` parameter."""
    query = query_string.decode("latin-1") if isinstance(query_string, bytes) else query_string
    return any(
        key == "v" and _STATIC_VERSION_RE.fullmatch(value) is not None
        for key, value in parse_qsl(query, keep_blank_values=True)
    )


def _set_header(
    headers: list[tuple[bytes, bytes]],
    name: bytes,
    value: bytes,
) -> list[tuple[bytes, bytes]]:
    """Return headers with a single canonical ``name`` value."""
    lowered = name.lower()
    without_existing = [(key, val) for key, val in headers if key.lower() != lowered]
    without_existing.append((lowered, value))
    return without_existing


def _merge_vary(
    headers: list[tuple[bytes, bytes]],
    token: bytes,
) -> list[tuple[bytes, bytes]]:
    """Merge ``token`` into Vary without duplicating existing values."""
    existing: list[str] = []
    out: list[tuple[bytes, bytes]] = []
    for key, value in headers:
        if key.lower() != b"vary":
            out.append((key, value))
            continue
        existing.extend(part.strip() for part in value.decode("latin-1").split(",") if part.strip())

    token_text = token.decode("latin-1")
    if not any(part.lower() == token_text.lower() for part in existing):
        existing.append(token_text)
    out.append((b"vary", ", ".join(existing).encode("latin-1")))
    return out
