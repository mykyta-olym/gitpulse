"""What scripts/build_bundle.py produces, for the tests that read it.

dist/ holds what the browser receives - minified, under content-hashed names,
indexed by dist/manifest.json. tests/conftest.py builds it at session start.
The page bundles and the translation catalogue read better before
minification, which is how the checks on them were written.
"""

from __future__ import annotations

import importlib.util
import json
from functools import cache
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]
DIST = REPO / "dist"


@cache
def build_bundle() -> ModuleType:
    """``scripts/build_bundle.py`` as a module."""
    path = REPO / "scripts" / "build_bundle.py"
    spec = importlib.util.spec_from_file_location("build_bundle", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def served(logical: str) -> Path:
    """The dist/ file ``static_url(logical)`` points at, e.g. ``js/core.bundle.js``."""
    manifest = json.loads((DIST / "manifest.json").read_text(encoding="utf-8"))
    return DIST / manifest[logical]["file"]


def page_bundle(rel: str) -> str:
    """A page bundle (``pages/dashboard.js``, ``tours.js``) before minification."""
    module = build_bundle()
    return str(module._build_page_bundle(module.PAGE_BUNDLES[rel]))


def catalog(locale: str) -> str:
    """The client translation catalogue of ``locale`` before minification."""
    return str(build_bundle()._catalog_js(locale))
