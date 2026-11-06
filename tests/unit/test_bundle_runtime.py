"""Every page's JavaScript must actually execute, not merely parse.

`node --check` proves a file is syntactically valid. It cannot catch a bundle
that throws the instant a browser evaluates it - a typo'd global, a call on an
undefined export, a bad destructure at module top level. That failure takes the
whole bundle down, so every feature on the page dies at once, and nothing else
in this suite notices.

The runner (scripts/check_bundle_runtime.mjs) is dependency-free: node's
built-in `vm` plus a stub DOM, no package.json and no npm install. The stub is
shallow on purpose, so a pass means "the page's scripts load", not "the UI
works".

It runs what the browser receives: the dist/ build of each file.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.build_outputs import served

_TEMPLATES = Path("src/app/templates")
_RUNNER = Path("scripts/check_bundle_runtime.mjs")
_CORE = served("js/core.bundle.js")

# `static_url('js/pages/course-settings.js')` -> `pages/course-settings.js`
_SCRIPT_SRC = re.compile(r"static_url\(\s*'js/([^']+)'\s*\)")

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


def _pages_with_scripts() -> list[tuple[str, list[Path]]]:
    """Each template paired with the JS files it loads, in template order.

    Read from the templates rather than hard-coded: a page bundle is written
    against globals its siblings installed (course-settings needs
    config-import.js for `GP.ConfigImport`), so running it with core alone
    fails for a reason the browser never sees.
    """
    pages: list[tuple[str, list[Path]]] = []
    for template in sorted(_TEMPLATES.rglob("*.html")):
        text = template.read_text(encoding="utf-8", errors="ignore")
        rels = [rel for rel in _SCRIPT_SRC.findall(text) if rel != "core.bundle.js"]
        if any(rel.startswith("pages/") for rel in rels):
            scripts = [served(f"js/{rel}") for rel in rels]
            pages.append((template.relative_to(_TEMPLATES).as_posix(), scripts))
    return pages


def test_the_page_scan_is_not_vacuous() -> None:
    """A silent empty list would make the parametrised test disappear."""
    pages = _pages_with_scripts()

    assert len(pages) >= 10, f"only found {len(pages)} pages with page bundles"
    names = {name for name, _ in pages}
    assert "course_settings.html" in names


def _run(scripts: list[Path]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["node", str(_RUNNER), str(_CORE), *(str(p) for p in scripts)],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_core_bundle_executes() -> None:
    result = _run([])

    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.parametrize(
    ("template", "scripts"),
    _pages_with_scripts(),
    ids=[name for name, _ in _pages_with_scripts()],
)
def test_page_scripts_execute(template: str, scripts: list[Path]) -> None:
    result = _run(scripts)

    assert result.returncode == 0, f"{template}: {result.stderr or result.stdout}"
