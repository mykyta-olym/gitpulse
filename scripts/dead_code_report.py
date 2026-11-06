"""Conservative dead-code candidate report.

This is intentionally non-blocking. It reports files that look unreferenced by
static text search while whitelisting framework entry points that are commonly
loaded dynamically (FastAPI routes, SQLAlchemy models, schemas, Alembic, Jinja).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "dead-code-report.txt"

WHITELIST_PARTS = (
    "src/app/api/",
    "src/app/models/",
    "src/app/schemas/",
    "src/app/templates/",
    "alembic/",
)
WHITELIST_NAMES = {"__init__.py", "main.py", "config.py", "dependencies.py"}


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


def _git_files() -> list[str]:
    """Return all repo files as posix paths relative to ROOT."""
    paths: list[str] = []
    for p in ROOT.rglob("*"):
        if p.is_file() and not any(part in _SKIP_DIRS for part in p.parts):
            paths.append(p.relative_to(ROOT).as_posix())
    return paths


def _is_whitelisted(path: str) -> bool:
    return path.rsplit("/", maxsplit=1)[-1] in WHITELIST_NAMES or any(
        part in path for part in WHITELIST_PARTS
    )


def _has_reference(path: str, files: list[str]) -> bool:
    module = path.removesuffix(".py").replace("/", ".")
    if module.startswith("src."):
        module = module.removeprefix("src.")
    stem = path.rsplit("/", maxsplit=1)[-1].removesuffix(".py")
    needles = {module, f"import {stem}", f"from {module}"}
    for candidate in files:
        if candidate == path or not candidate.endswith(
            (".py", ".jinja", ".html", ".md", ".toml", ".yml")
        ):
            continue
        try:
            text = (ROOT / candidate).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(needle in text for needle in needles):
            return True
    return False


def main() -> int:
    files = _git_files()
    python_files = [
        path
        for path in files
        if path.startswith("src/app/")
        and path.endswith(".py")
        and not _is_whitelisted(path)
        and "/__pycache__/" not in path
    ]
    candidates = [path for path in python_files if not _has_reference(path, files)]

    lines = [
        "Dead-code candidate report",
        "==========================",
        "",
        "Policy: informational only. Do not delete a candidate until runtime, template,",
        "public compatibility exports, migrations, and bundle/static checks are reviewed.",
        "",
    ]
    if candidates:
        lines.append("Candidates:")
        lines.extend(f"- {path}" for path in candidates)
    else:
        lines.append("No unreferenced candidates found by conservative static search.")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
