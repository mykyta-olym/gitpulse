"""The JS and CSS the browser receives are build outputs, not files in the tree.

They used to be committed beside their sources - `core.bundle.js`, the page
bundles, a `.min` twin of every standalone file - and `static_url()` swapped
in the `.min` twin when it found one. Now `scripts/build_bundle.py` writes them
into dist/ under content-hashed names, as Vite does, and `dist/manifest.json`
maps the name a template asks for to the file. Everything else under static/
(vendored builds, images, fonts) is still served from the tree with `?v=`.
"""

from __future__ import annotations

import json
import re

import pytest

from app import assets
from tests.build_outputs import DIST, REPO, build_bundle, served

_STATIC_URL_REF = re.compile(r"""static_url\(\s*['"]([^'"]+)['"]""")


@pytest.fixture
def manifest() -> dict[str, dict[str, str]]:
    return dict(json.loads((DIST / "manifest.json").read_text(encoding="utf-8")))


def test_a_build_output_is_served_from_dist_under_its_hashed_name(
    manifest: dict[str, dict[str, str]],
) -> None:
    for logical in ("js/core.bundle.js", "styles.bundle.css", "js/pages/dashboard.js"):
        url = assets.static_url(logical)
        assert url == f"/static/dist/{manifest[logical]['file']}"
        assert "?v=" not in url, "the name is the version - no query"
        assert served(logical).is_file()


def test_a_source_file_keeps_its_content_hash_query() -> None:
    url = assets.static_url("vendor/htmx-1.9.12.min.js")
    assert re.fullmatch(r"/static/vendor/htmx-1\.9\.12\.min\.js\?v=[0-9a-f]{8}", url), url


def test_the_name_carries_the_content_hash(manifest: dict[str, dict[str, str]]) -> None:
    import hashlib

    for logical, entry in manifest.items():
        digest = hashlib.sha256((DIST / entry["file"]).read_bytes()).hexdigest()[:8]
        head, _, ext = logical.rpartition(".")
        assert entry["file"] == f"{head}.{digest}.{ext}", logical


def test_every_asset_a_template_names_exists(manifest: dict[str, dict[str, str]]) -> None:
    """The same promise `build_bundle.py --check` makes in CI, for every literal
    `static_url('...')` in a template or view."""
    refs: set[str] = set()
    for path in (REPO / "src" / "app").rglob("*"):
        if path.suffix in {".html", ".py"} and "static" not in path.parts:
            refs.update(_STATIC_URL_REF.findall(path.read_text(encoding="utf-8")))
    assert len(refs) > 30, "the scan found almost nothing - the pattern is stale"
    missing = sorted(r for r in refs if not assets.is_served(r))
    assert not missing, f"named but neither built nor in the source tree: {missing}"


def test_dist_lives_outside_the_mounted_templates() -> None:
    """Production mounts src/app/templates from the host; a dist/ inside it
    would be hidden by the mount and every built file would 404."""
    templates = REPO / "src" / "app" / "templates"
    assert templates not in assets.DIST_DIR.parents
    compose = (REPO / "docker-compose.yml").read_text(encoding="utf-8")
    assert "./src/app/templates:/app/src/app/templates" in compose
    dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY --from=assets /build/dist/ ./dist/" in dockerfile


def test_outputs_left_in_the_tree_do_not_reach_the_build() -> None:
    """Exclude stale generated files from build inputs, including files left by a pull."""
    builder = build_bundle()
    clean = builder.entries()
    static = assets.STATIC_DIR
    stale = [
        static / "styles.bundle.css",
        static / "js" / "core.bundle.js",
        static / "js" / "pages" / "dashboard.js",
        static / "js" / "pages" / "dashboard.min.js",
        static / "css" / "login.min.css",
    ]
    assert not any(p.exists() for p in stale), "a build output is already in the tree"
    try:
        for p in stale:
            p.write_text("/* STALE */", encoding="utf-8")
        assert builder.entries() == clean
    finally:
        for p in stale:
            p.unlink(missing_ok=True)
