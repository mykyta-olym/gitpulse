#!/usr/bin/env python3
"""Detect build outputs in the source tree.

The served JS and CSS are built into dist/ (scripts/build_bundle.py), which is
never committed. A minified, bundled or precompressed file anywhere else is a
stale output from before that, or an accident - only vendored builds ship
minified in the tree.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_PREFIXES = ("src/app/templates/static/vendor/",)
STATIC_SUFFIXES = (".min.js", ".min.css", ".bundle.js", ".bundle.css", ".js.gz", ".css.gz")


_SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    ".tox",
    "dist",
    "build",
    "site",
    "htmlcov",
    ".ruff_cache",
}


def _all_files() -> list[str]:
    """Walk the repository tree, skipping generated/tool directories."""
    paths: list[str] = []
    for p in ROOT.rglob("*"):
        if p.is_file() and not any(part in _SKIP_DIRS for part in p.parts):
            paths.append(p.relative_to(ROOT).as_posix())
    return paths


def _looks_generated_static(path: str) -> bool:
    name = Path(path).name
    if name in {"-w"}:
        return True
    if path.endswith(STATIC_SUFFIXES):
        return not path.startswith(ALLOWED_PREFIXES)
    return False


def main() -> int:
    offenders = [path for path in _all_files() if _looks_generated_static(path)]
    if not offenders:
        print("[OK] No stray generated static artifacts found.")
        return 0

    print("[FAIL] Build outputs in the source tree (builds go to dist/):")
    for path in offenders:
        print(f"  - {path}")
    print("Delete them; a vendored library goes under src/app/templates/static/vendor/.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
