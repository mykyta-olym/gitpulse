#!/usr/bin/env python3
"""Build the JS and CSS the browser receives into dist/, from their sources.

Usage:
    python scripts/build_bundle.py             # build dist/ (minified)
    python scripts/build_bundle.py --check     # build into a scratch dir, check references (CI)
    python scripts/build_bundle.py --watch     # rebuild on changes (dev)
    python scripts/build_bundle.py --no-minify # skip minification (debugging)

dist/ is a build output, like Vite's: never committed, built by the Docker
image and by CI. Each file's name carries its content hash
(``js/core.bundle.3f2a91c4.js``) and ``dist/manifest.json`` maps the logical
name a template asks for - ``static_url('js/core.bundle.js')`` - to it, so the
browser may keep every file for good. The output is deterministic: the same
sources always give the same names.

Minification:
    Uses ``rjsmin`` (JS) and ``rcssmin`` (CSS) - pure-Python, conservative
    whitespace/comment strippers (no AST transforms, no ES5 transpilation).
    Safe with vendored libs that ship modern JS.  The header comment is
    preserved so the bundle stays self-documenting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Pure-Python minifiers (whitespace + comment strippers).  Imported via
# ``importlib`` so static analysers don't flag missing stubs - these are
# build-time-only deps installed via ``pip install -c requirements.lock -e '.[dev,otel]'``.
_rjsmin: Any
_rcssmin: Any
try:
    import importlib

    _rjsmin = importlib.import_module("rjsmin")
    _rcssmin = importlib.import_module("rcssmin")
    _HAS_MINIFIERS = True
except ImportError:  # pragma: no cover - only triggers if dev deps not installed
    _rjsmin = None
    _rcssmin = None
    _HAS_MINIFIERS = False

# Flipped by ``--no-minify`` CLI flag. Module-level so all helpers see the
# same value and ``--check`` rebuilds with the same minification policy.
MINIFY_ENABLED: bool = True

# -- Paths --
ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "src" / "app" / "templates" / "static"

JS_DIR = STATIC_DIR / "js"
CSS_MANIFEST = STATIC_DIR / "styles.css"

DIST_DIR = ROOT / "dist"
MANIFEST_NAME = "manifest.json"

# -- JS module order --
# Order matters: earlier modules expose globals consumed by later ones.
JS_MODULES: list[str] = [
    "i18n.js",
    "cookies.js",
    "cookie-consent.js",
    "icons.js",
    "dropdowns.js",
    # The motion system. A top-level file rather than a core/ part because the
    # auth pages do not load core.bundle.js and still need the same animations -
    # they pull motion.min.js on its own.
    "motion.js",
    # The shared core, one file per component (_parts/core/NN-<component>.js):
    # 0x primitives, 1x modals and navigation, 2x-3x UI components, 4x the
    # SPA shell. Order matters - earlier files expose names later ones use.
    "_parts/core/00-namespace.js",
    "_parts/core/01-job-messages.js",
    "_parts/core/02-icons.js",
    "_parts/core/03-download.js",
    "_parts/core/04-http.js",
    "_parts/core/05-auth-sync.js",
    "_parts/core/06-utilities.js",
    "_parts/core/07-api.js",
    "_parts/core/08-sse.js",
    "_parts/core/09-toasts.js",
    "_parts/core/10-modals.js",
    "_parts/core/11-bottom-sheet.js",
    "_parts/core/12-user-info.js",
    "_parts/core/13-leave-guard.js",
    "_parts/core/14-save-guard.js",
    "_parts/core/15-number-stepper.js",
    "_parts/core/16-reload.js",
    "_parts/core/17-form-select.js",
    "_parts/core/18-alpine.js",
    "_parts/core/19-confirm-dialog.js",
    "_parts/core/20-field-errors.js",
    "_parts/core/21-buttons.js",
    "_parts/core/22-content-states.js",
    "_parts/core/23-utilities.js",
    "_parts/core/24-scoped-processes.js",
    "_parts/core/25-shortcuts.js",
    "_parts/core/26-tooltips.js",
    "_parts/core/27-live-updates.js",
    "_parts/core/28-date-pickers.js",
    "_parts/core/29-dom-helpers.js",
    "_parts/core/30-data-actions.js",
    "_parts/core/31-banners.js",
    "_parts/core/32-page-scroll.js",
    "_parts/core/33-anti-spam.js",
    "_parts/core/35-dropdown-menu.js",
    "_parts/core/36-boot.js",
    "_parts/core/37-json-drop.js",
    "_parts/core/38-swap-reveal.js",
    "_parts/core/39-tabs-and-toggles.js",
    "_parts/core/40-top-progress.js",
    "_parts/core/41-htmx-config.js",
    "_parts/core/42-spa-navigation.js",
    "_parts/core/43-htmx-requests.js",
    "_parts/core/44-session.js",
    "_parts/core/45-touch-scrollbar.js",
    "_parts/core/46-avatar-fallback.js",
    "_parts/core/47-chart-theme.js",
    "_parts/core/48-archived-course.js",
    "components.js",
    # The academic period: its label, the period selector, and the
    # period-and-dates fields every course dialog shares. Before any page
    # bundle, which call GP.periodLabel / GP.periodFields.
    "academic-period.js",
    "course-tabs.js",
    "gitlab-helpers.js",
    "sse-stream.js",
    "sortable-table.js",
    "table-scroll.js",
    "import-stream.js",
    "member-exclusion.js",
    "_parts/global-job-bar/00-state-polling.js",
    "_parts/global-job-bar/10-sse-render.js",
    "_parts/global-job-bar/20-listeners-api.js",
    "process-action-guards.js",
    "sidebar.js",
    "search-palette.js",
    "health-monitor.js",
    "pull-to-refresh.js",
    "localize-time.js",
    "run-checks-modal.js",
    "pwa-install.js",
    # Loads the guided tours (tours.js) once the page is idle.
    "_parts/core/49-tours.js",
]

JS_HEADER = """\
/* ------------------------------------------------------------------
 *  core.bundle.js - AUTO-GENERATED, DO NOT EDIT
 *
 *  Rebuild: python scripts/build_bundle.py
 *  Source modules ({count}):
{listing}
 * ------------------------------------------------------------------ */
"""

# Regex to extract CSS file paths from @import url('...')
_IMPORT_RE = re.compile(r"@import\s+url\(['\"]([^'\"?]+)(?:\?[^'\"]*)?['\"]\)")


# --------------------------------------------------------------------
# JS bundle
# --------------------------------------------------------------------


def _build_js_bundle() -> str:
    """Concatenate JS source modules into a single bundle string."""
    listing_lines = []
    for i, mod in enumerate(JS_MODULES, 1):
        listing_lines.append(f" *    {i:2d}. {mod}")
    header = JS_HEADER.format(count=len(JS_MODULES), listing="\n".join(listing_lines))

    parts: list[str] = []

    # i18n must come first
    i18n_content = (JS_DIR / "i18n.js").read_text(encoding="utf-8")
    parts.append(f"\n/* -- Module: i18n.js -- */\n{i18n_content.rstrip()}")

    # Remaining modules
    for mod in JS_MODULES:
        if mod == "i18n.js":
            continue  # already added
        path = JS_DIR / mod
        if not path.exists():
            print(f"WARNING: {mod} not found, skipping", file=sys.stderr)
            continue
        content = path.read_text(encoding="utf-8")
        if mod == "_parts/core/01-job-messages.js":
            metadata = json.loads(
                (ROOT / "src/app/i18n/job_messages.json").read_text(encoding="utf-8")
            )
            content = content.replace("__GP_JOB_LABELS__", json.dumps(metadata["labels"]))
        if mod == "_parts/global-job-bar/00-state-polling.js":
            content = ";(function() {\n  'use strict';\n" + content
        elif mod == "_parts/global-job-bar/20-listeners-api.js":
            content = content + "\n})();\n"
        parts.append(f"\n/* -- Module: {mod} -- */\n{content.rstrip()}")

    body = "\n".join(parts)

    if MINIFY_ENABLED and _HAS_MINIFIERS:
        # ``keep_bang_comments`` is False - module separators (/* -- Module: ... -- */)
        # are stripped, but the file-level ``JS_HEADER`` is prepended after
        # minification so the bundle stays self-documenting for code review.
        body = _rjsmin.jsmin(body, keep_bang_comments=False)

    return header.rstrip() + "\n" + body.lstrip() + "\n"


# --------------------------------------------------------------------
# CSS bundle
# --------------------------------------------------------------------


def _parse_css_manifest() -> list[str]:
    """Parse styles.css to extract ordered list of CSS file paths."""
    manifest = CSS_MANIFEST.read_text(encoding="utf-8")
    paths: list[str] = []
    for match in _IMPORT_RE.finditer(manifest):
        paths.append(match.group(1))
    return paths


def _build_css_bundle() -> str:
    """Concatenate CSS source files (in manifest order) into a single bundle."""
    css_paths = _parse_css_manifest()
    parts: list[str] = []

    for rel_path in css_paths:
        full_path = STATIC_DIR / rel_path
        if not full_path.exists():
            print(f"WARNING: {rel_path} not found, skipping", file=sys.stderr)
            continue
        content = full_path.read_text(encoding="utf-8").rstrip()
        parts.append(content)

    bundle = "\n".join(parts) + "\n"

    if MINIFY_ENABLED and _HAS_MINIFIERS:
        # ``keep_bang_comments`` preserves any ``/*! ... */`` license headers
        # (e.g. embedded vendor CSS) which is the polite default.
        bundle = _rcssmin.cssmin(bundle, keep_bang_comments=True)

    return bundle


# --------------------------------------------------------------------
# Page bundles (standalone page controllers split into SRP source parts)
# --------------------------------------------------------------------
# A page controller is a single IIFE whose functions share one closure, so
# it cannot be split into independent modules. Instead the *source* is split
# into ordered parts under ``js/_parts/<name>/`` that are concatenated
# *verbatim* back into the served file - byte-identical output, zero runtime
# risk, but each source part stays small and single-responsibility.
PAGE_BUNDLES: dict[str, list[str]] = {
    "pages/admin-courses.js": [
        "_parts/admin-courses/00-core.js",
        "_parts/admin-courses/10-lifecycle.js",
        "_parts/admin-courses/20-events.js",
    ],
    "pages/project-detail.js": [
        "_parts/project-detail/00-core.js",
        "_parts/project-detail/10-analysis.js",
        "_parts/project-detail/20-mr-ci.js",
        "_parts/project-detail/30-live-intel.js",
    ],
    "pages/course-settings.js": [
        "_parts/course-settings/00-core.js",
        "_parts/course-settings/10-sections.js",
        "_parts/course-settings/20-checks-import.js",
        "_parts/course-settings/30-llm-generate.js",
        "_parts/course-settings/40-full-config.js",
        "_parts/course-settings/50-danger-zone.js",
        "_parts/course-settings/60-live-state.js",
        "_parts/course-settings/70-webhooks.js",
        "_parts/course-settings/80-weekly-deadlines.js",
    ],
    "pages/course-detail.js": [
        "_parts/course-detail/00-sync-stream.js",
        "_parts/course-detail/10-teams-crud.js",
        "_parts/course-detail/20-sync-all.js",
        "_parts/course-detail/30-course-data.js",
    ],
    "pages/team-detail.js": [
        "_parts/team-detail/00-core.js",
        "_parts/team-detail/10-sync.js",
        "_parts/team-detail/20-analysis-boot.js",
        "_parts/team-detail/30-live.js",
    ],
    "pages/dashboard.js": [
        "_parts/dashboard/00-core.js",
        "_parts/dashboard/10-course-crud.js",
        "_parts/dashboard/20-live-updates.js",
        "_parts/dashboard/30-sse.js",
    ],
    "pages/course-analytics.js": [
        "_parts/course-analytics/00-charts.js",
        "_parts/course-analytics/10-refresh.js",
        "_parts/course-analytics/20-week-explorer.js",
    ],
    # The guided tours: the engine (its own IIFE, opened in 00 and closed in
    # 10, whose locals the two share) and the tours it registers. Not part of
    # core: _parts/core/49-tours.js fetches it, with Driver.js, when the page
    # is idle. Once per document, like core - not a pages/ bundle, which the
    # SPA re-runs on every navigation into its page.
    "tours.js": [
        "_parts/tours/00-engine.js",
        "_parts/tours/10-render.js",
        "_parts/tours/20-courses.js",
        "_parts/tours/30-entities.js",
        "_parts/tours/40-support.js",
        "_parts/tours/50-preferences.js",
    ],
    "pages/admin-system.js": [
        "_parts/admin-system/00-format-render.js",
        "_parts/admin-system/10-stats.js",
        "_parts/admin-system/20-jobs.js",
        "_parts/admin-system/25-config-filter.js",
        "_parts/admin-system/30-maintenance-boot.js",
    ],
}


def _build_page_bundle(parts: list[str]) -> str:
    """Concatenate page-source parts and wrap in an IIFE."""
    body = "".join((JS_DIR / rel).read_text(encoding="utf-8") for rel in parts)
    return f";(function() {{\n  'use strict';\n{body}\n}})();\n"


# --------------------------------------------------------------------
# Client translation catalogue
#
# The whole catalogue used to be inlined into every page as a JSON island.
# Measured on the served login page: 205KB raw, and ~69KB of the ~76KB that
# page weighed compressed - about ninety per cent of it. It is byte-identical
# for every reader on a locale and never changes between page loads, yet
# inline content has no URL, so the browser had to take it again every time.
#
# Emitted as a file instead, so it gets a content-hashed name and the browser
# keeps it until the translations actually change.
# --------------------------------------------------------------------

_CATALOG_SRC_DIR = ROOT / "src" / "app" / "i18n" / "catalogs"


def _canonical_key(text: str) -> str:
    """Collapse whitespace exactly as ``app.i18n._canonical_text`` does.

    Deliberately duplicated rather than imported: this script runs in CI with
    no application environment. A unit test asserts the generated file equals
    ``get_catalog()`` exactly, so the two cannot drift apart silently.
    """
    return " ".join(text.split())


def _catalog_js(locale: str) -> str:
    raw = json.loads((_CATALOG_SRC_DIR / f"{locale}.json").read_text(encoding="utf-8"))
    catalog = {
        _canonical_key(k): v for k, v in raw.items() if isinstance(k, str) and isinstance(v, str)
    }
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    header = (
        "/* AUTO-GENERATED by scripts/build_bundle.py - DO NOT EDIT."
        + chr(10)
        + f"   Source: src/app/i18n/catalogs/{locale}.json */"
        + chr(10)
    )
    return header + "window.__GP_I18N_CATALOG__=" + payload + ";" + chr(10)


# ``app.i18n.SOURCE_LOCALE``. Phrases are authored in it, so `get_catalog()`
# returns nothing for it and there is no file to ship. Named here rather than
# imported for the same reason as `_canonical_key`, and pinned by the test.
_SOURCE_LOCALE = "en"


def _catalog_locales() -> list[str]:
    """Locales with a catalogue worth shipping."""
    return sorted(
        p.stem
        for p in _CATALOG_SRC_DIR.glob("*.json")
        if p.stem != _SOURCE_LOCALE and json.loads(p.read_text(encoding="utf-8"))
    )


# --------------------------------------------------------------------
# Standalone files
#
# Templates that load files outside the bundle - e.g.
# ``static_url('js/config-import.js')`` or ``static_url('css/login.css')`` -
# get a minified build of that file in dist/, under the same logical name.
# --------------------------------------------------------------------

_STATIC_URL_REF = re.compile(r"""static_url\(\s*['"]([^'"]+\.(?:js|css))['"]""")


def _loaded_on_their_own() -> set[str]:
    """Static paths a template or view names in ``static_url('...')``."""
    refs: set[str] = set()
    for path in (ROOT / "src" / "app").rglob("*"):
        if path.suffix in {".html", ".py"} and "static" not in path.parts:
            refs.update(_STATIC_URL_REF.findall(path.read_text(encoding="utf-8")))
    return refs


def _bundled_only(rel: str, bundled: set[str], loaded: set[str]) -> bool:
    """A bundle source no page loads by itself is never served on its own."""
    return rel in bundled and rel not in loaded


def _iter_standalone_js() -> list[Path]:
    """The JS sources served on their own.

    A module of ``core.bundle.js`` is included only when a template also loads
    it by itself - the login and error pages render without the bundle.
    ``_parts`` holds source fragments concatenated into a served file, and the
    vendor directory ships pre-minified builds, so neither is included.
    """
    bundled, loaded = set(JS_MODULES), {r.removeprefix("js/") for r in _loaded_on_their_own()}
    out: list[Path] = []
    for path in sorted(JS_DIR.rglob("*.js")):
        rel = path.relative_to(JS_DIR).as_posix()
        if "vendor" in path.parts or "_parts" in path.parts:
            continue
        if _bundled_only(rel, bundled, loaded):
            continue
        out.append(path)
    return out


def _iter_standalone_css() -> list[Path]:
    """The CSS sources served on their own.

    The ``styles.css`` manifest and every stylesheet it imports reach the
    browser inside ``styles.bundle.css`` - except the few the auth and error
    pages link directly.
    """
    bundled = {*_parse_css_manifest(), CSS_MANIFEST.name}
    loaded = _loaded_on_their_own()
    out: list[Path] = []
    for path in sorted(STATIC_DIR.rglob("*.css")):
        rel = path.relative_to(STATIC_DIR).as_posix()
        if "vendor" in path.parts or "_parts" in path.parts:
            continue
        if _bundled_only(rel, bundled, loaded):
            continue
        out.append(path)
    return out


def _minify_one_js(src: str) -> str:
    if not (MINIFY_ENABLED and _HAS_MINIFIERS):
        return src
    return str(_rjsmin.jsmin(src, keep_bang_comments=False))


def _minify_one_css(src: str) -> str:
    if not (MINIFY_ENABLED and _HAS_MINIFIERS):
        return src
    return str(_rcssmin.cssmin(src, keep_bang_comments=True))


# --------------------------------------------------------------------
# dist/
#
# Every file the browser receives, under a name that carries its content hash,
# and ``manifest.json`` mapping the logical name a template asks for
# (``static_url('js/core.bundle.js')``) to that file. Built, never committed:
# the Docker image and CI build it from the sources.
# --------------------------------------------------------------------


def entries() -> dict[str, str]:
    """Every served build output: logical static path -> content."""
    out = {
        "js/core.bundle.js": _build_js_bundle(),
        "styles.bundle.css": _build_css_bundle(),
    }
    for rel, parts in PAGE_BUNDLES.items():
        out[f"js/{rel}"] = _minify_one_js(_build_page_bundle(parts))
    for locale in _catalog_locales():
        out[f"js/i18n-catalog-{locale}.js"] = _minify_one_js(_catalog_js(locale))
    for path, minify in (
        *((p, _minify_one_js) for p in _iter_standalone_js()),
        *((p, _minify_one_css) for p in _iter_standalone_css()),
    ):
        logical = path.relative_to(STATIC_DIR).as_posix()
        if logical in out or _is_build_output(path):
            # A build output left in the tree - a deploy keeps the files its
            # pull deleted for the running containers - is not a source: it
            # must never replace, or ship beside, what was just built.
            continue
        out[logical] = minify(path.read_text(encoding="utf-8"))
    return dict(sorted(out.items()))


def _is_build_output(path: Path) -> bool:
    return ".min." in path.name or ".bundle." in path.name


def _hashed_name(logical: str, content: str) -> str:
    """``js/core.bundle.js`` -> ``js/core.bundle.3f2a91c4.js``."""
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
    head, _, ext = logical.rpartition(".")
    return f"{head}.{digest}.{ext}"


def build(out_dir: Path = DIST_DIR, *, verbose: bool = True) -> dict[str, dict[str, str]]:
    """Write every build output and ``manifest.json`` into ``out_dir``.

    The manifest is written last and atomically, then files it no longer names
    are removed - a running dev server never reads a manifest whose files are
    not on disk yet.
    """
    manifest: dict[str, dict[str, str]] = {}
    total = 0
    for logical, content in entries().items():
        name = _hashed_name(logical, content)
        target = out_dir / name
        data = content.encode("utf-8")
        if not target.is_file() or target.read_bytes() != data:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest[logical] = {"file": name}
        total += len(data)
        if verbose:
            print(f"  {logical:<42} -> {name}  ({len(data) // 1024} KB)")

    tmp = out_dir / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(out_dir / MANIFEST_NAME)

    keep = {out_dir / MANIFEST_NAME, *(out_dir / e["file"] for e in manifest.values())}
    for path in sorted(out_dir.rglob("*"), reverse=True):
        if path.is_file() and path not in keep:
            path.unlink()
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    if verbose:
        print(f"  [OK] {len(manifest)} files, {total // 1024} KB -> {out_dir.relative_to(ROOT)}/")
    return manifest


def check() -> bool:
    """Build into a scratch directory and check that every asset a template or
    view names resolves - to a build output or to a source file served as is.
    """
    with tempfile.TemporaryDirectory() as tmp:
        manifest = build(Path(tmp), verbose=False)
    missing = sorted(
        ref
        for ref in _loaded_on_their_own()
        if ref not in manifest and not (STATIC_DIR / ref).is_file()
    )
    for ref in missing:
        print(f"  [FAIL] static_url('{ref}') names neither a build output nor a source file")
    if not missing:
        print(f"  [OK] the build succeeds ({len(manifest)} files) and every reference resolves")
    return not missing


def _source_hash() -> str:
    """Combined hash of every source the build reads."""
    h = hashlib.sha256()
    for path in sorted(
        p
        for p in (
            *STATIC_DIR.rglob("*.js"),
            *STATIC_DIR.rglob("*.css"),
            *_CATALOG_SRC_DIR.glob("*.json"),
            ROOT / "src/app/i18n/job_messages.json",
        )
        if "vendor" not in p.parts
    ):
        h.update(path.as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:16]


def watch() -> None:
    """Rebuild on source changes (simple polling)."""
    print("Watching for JS/CSS changes... (Ctrl+C to stop)")
    last_hash = ""
    while True:
        current_hash = _source_hash()
        if current_hash != last_hash:
            if last_hash:
                print(f"\n[{time.strftime('%H:%M:%S')}] Change detected, rebuilding...")
            build()
            last_hash = current_hash
        time.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the served JS & CSS into dist/")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--check",
        action="store_true",
        help="Build into a scratch dir and verify every reference resolves (CI)",
    )
    group.add_argument("--watch", action="store_true", help="Rebuild on changes (dev)")
    parser.add_argument(
        "--no-minify",
        action="store_true",
        help="Skip minification (debug builds only - CI/prod must stay minified)",
    )
    args = parser.parse_args()

    global MINIFY_ENABLED
    if args.no_minify:
        MINIFY_ENABLED = False
    elif not _HAS_MINIFIERS:
        # Never ship an un-minified build by accident.
        print(
            "ERROR: rjsmin/rcssmin not installed.\n"
            "  Install with: pip install -c requirements.lock -e '.[dev,otel]'  (or --no-minify for a debug build)",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.check:
        sys.exit(0 if check() else 1)
    elif args.watch:
        watch()
    else:
        build()


if __name__ == "__main__":
    main()
