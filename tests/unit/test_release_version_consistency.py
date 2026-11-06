"""Keep all hand-maintained release versions consistent.

The package version, service-worker cache and latest changelog entries must
advance together. Dashboard entry validation lives in test_changelog_entries.py."""

import re
import tomllib
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_PYPROJECT = _ROOT / "pyproject.toml"
_ROOT_CHANGELOG = _ROOT / "CHANGELOG.md"
_DOCS_CHANGELOGS = (
    # The docs moved from MkDocs to Astro Starlight; the changelog pages now
    # live in the content collection, Slovak at the root and English under en/.
    _ROOT / "docs-site" / "content" / "changelog.md",
    _ROOT / "docs-site" / "content-en" / "changelog.md",
)
_SW_JS = _ROOT / "src" / "app" / "templates" / "static" / "sw.js"
_ALERTMANAGER_YML = _ROOT / "monitoring" / "alertmanager.yml"


def _pyproject_version() -> str:
    return tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def _first_h2(path: Path) -> str:
    """Return the first ``## `` heading (the newest changelog entry)."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            return line
    raise AssertionError(f"no '## ' changelog heading found in {path.name}")


def test_root_changelog_top_entry_matches_pyproject_version() -> None:
    version = _pyproject_version()
    heading = _first_h2(_ROOT_CHANGELOG)
    assert version in heading, (
        f"root CHANGELOG.md newest entry {heading!r} does not mention pyproject "
        f"version {version!r} - bump them together (release-version-bump-checklist)"
    )


def test_docs_changelogs_top_entry_matches_pyproject_version() -> None:
    version = _pyproject_version()
    for path in _DOCS_CHANGELOGS:
        heading = _first_h2(path)
        assert version in heading, (
            f"{path.name} newest entry {heading!r} does not mention pyproject "
            f"version {version!r} - bump them together (release-version-bump-checklist)"
        )


def test_service_worker_cache_version_is_wellformed() -> None:
    match = re.search(r"CACHE_VERSION\s*=\s*'(gitpulse-v\d+)'", _SW_JS.read_text(encoding="utf-8"))
    assert match, "sw.js CACHE_VERSION missing/malformed (expected gitpulse-vNNN)"


def test_alertmanager_config_has_no_unsupported_shell_placeholders() -> None:
    src = _ALERTMANAGER_YML.read_text(encoding="utf-8")
    assert "${" not in src, "Alertmanager does not expand shell-style ${VAR:-default} syntax"
