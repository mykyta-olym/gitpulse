"""Static asset URLs - build outputs from ``dist/``, everything else as it is.

``scripts/build_bundle.py`` writes the JS and CSS the browser receives into
``dist/`` under content-hashed names (``js/core.bundle.3f2a91c4.js``) and maps
each logical name a template asks for to its file in ``dist/manifest.json`` -
Vite's model. The name is the version, so those files are cached for good.

Everything else under ``static/`` - vendored builds, images, fonts, the
manifest the browser installs - is served from the source tree with a
``?v=<content hash>`` query.
"""

from __future__ import annotations

import hashlib
import json
import logging
import pathlib

from app.config import get_settings

STATIC_DIR = pathlib.Path(__file__).parent / "templates" / "static"
# Beside src/, not inside templates/: production mounts templates/ from the
# host, which would hide a dist/ built into the image.
DIST_DIR = pathlib.Path(__file__).resolve().parents[2] / "dist"
DIST_URL = "/static/dist"
_MANIFEST = DIST_DIR / "manifest.json"

logger = logging.getLogger(__name__)

_manifest: dict[str, str] | None = None
_manifest_mtime = 0.0
_source_hashes: dict[str, str] = {}


def manifest() -> dict[str, str]:
    """Logical name -> file in ``dist/``.

    Read once in production; in development again whenever a rebuild has
    replaced it. Missing, it is empty and every page names unbuilt files - so
    say how to build it.
    """
    global _manifest, _manifest_mtime
    development = get_settings().is_development
    if _manifest is not None and not development:
        return _manifest
    try:
        mtime = _MANIFEST.stat().st_mtime
    except OSError:
        if _manifest is None:
            logger.warning("dist/manifest.json is missing - run: python scripts/build_bundle.py")
            _manifest = {}
        return _manifest
    if _manifest is None or mtime != _manifest_mtime:
        raw = json.loads(_MANIFEST.read_text(encoding="utf-8"))
        _manifest = {logical: entry["file"] for logical, entry in raw.items()}
        _manifest_mtime = mtime
    return _manifest


def _source_hash(rel_path: str) -> str:
    """First 8 hex chars of a source file's SHA-256 (``0`` when it is missing)."""
    development = get_settings().is_development
    cached = None if development else _source_hashes.get(rel_path)
    if cached is not None:
        return cached
    full = STATIC_DIR / rel_path
    digest = hashlib.sha256(full.read_bytes()).hexdigest()[:8] if full.is_file() else "0"
    if not development:
        _source_hashes[rel_path] = digest
    return digest


def static_url(rel_path: str) -> str:
    """The URL of a static file: its build output when it has one, otherwise
    ``/static/<path>?v=<content hash>``."""
    built = manifest().get(rel_path)
    if built:
        return f"{DIST_URL}/{built}"
    return f"/static/{rel_path}?v={_source_hash(rel_path)}"


def absolute_static_url(rel_path: str) -> str:
    """Return an absolute, cache-busted static URL for metadata tags."""
    path = static_url(rel_path)
    base = (get_settings().app_base_url or "").rstrip("/")
    return f"{base}{path}" if base else path


def is_served(rel_path: str) -> bool:
    """Whether ``static_url(rel_path)`` names a file that exists."""
    return rel_path in manifest() or (STATIC_DIR / rel_path).is_file()
