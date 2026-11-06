"""Deployment build fingerprint.

Extracted into a dedicated module to break the circular dependency
between ``app.main`` and modules used during request handling
(``app.dependencies``, ``app.api.dashboard.auth``,
``app.middleware.security``) that need the build hash to
validate session cookies and emit ``X-Build`` response headers.

The hash changes on every deploy so the client can detect stale
pages and so that sessions can embed it for version validation.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import time

_SRC_DIR = pathlib.Path(__file__).parent


_SOURCE_SUFFIXES = frozenset({".py", ".html", ".js", ".css", ".json"})


def _newest_source_mtime() -> float:
    """The latest mtime under the app package - what "the code changed" means in dev."""
    newest = 0.0
    for root, dirs, files in os.walk(_SRC_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if pathlib.Path(name).suffix in _SOURCE_SUFFIXES:
                try:
                    newest = max(newest, os.stat(os.path.join(root, name)).st_mtime)
                except OSError:
                    continue
    return newest or time.time()


def _compute_build_hash() -> str:
    """Deterministic hash of the application source + bundle.

    Uses ``GIT_SHA`` env var when available (set by CI/CD),
    otherwise hashes the build manifest + Python package metadata
    for a unique per-deploy fingerprint.

    In DEVELOPMENT the fingerprint is the newest modification time of any
    source file (Python, template, script, stylesheet, catalogue): the static
    hash below only covers the build manifest + main.py, so template / page-bundle
    edits were invisible to the client's version detection in dev. A file edit
    therefore announces a new version and open tabs show the update toast +
    auto-reload - the intended dev flow. It used to be per-process-START, which
    made every restart (a crash, a second session, a plain re-run with nothing
    changed) reload every open tab the moment it was looked at again: tabs
    "replaying themselves" on alt-tab. A restart with no change now keeps the
    fingerprint, and only a change moves it.
    (Safe for sessions: dev runs PERSISTENT_SESSIONS=true, and the build-hash
    session rejection only applies when persistent sessions are off.)
    """
    git_sha = os.environ.get("GIT_SHA", "").strip()
    if git_sha:
        return git_sha[:12]

    try:  # lazy import - config never imports build_info, so no cycle
        from app.config import get_settings

        if get_settings().is_development:
            return f"dev-{int(_newest_source_mtime()):x}"
    except Exception:  # noqa: S110 - never let dev sugar break startup
        pass

    h = hashlib.sha256()
    # Hash the build manifest (its file names change on every front-end change)
    from app.assets import DIST_DIR

    manifest = DIST_DIR / "manifest.json"
    if manifest.is_file():
        h.update(manifest.read_bytes())
    # Hash the Python app entry (changes on every back-end deploy)
    main_py = _SRC_DIR / "main.py"
    if main_py.is_file():
        h.update(main_py.read_bytes())
    return h.hexdigest()[:12]


BUILD_HASH: str = _compute_build_hash()
"""12-char hex fingerprint of the current deployment."""
