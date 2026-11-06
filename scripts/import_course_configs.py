#!/usr/bin/env python3
"""Import course configurations from fixture files on first deployment.

This script reads JSON config files from docs/fixtures/ and imports them
into the database using the same logic as the dashboard import endpoint.
It is idempotent - if a course with the same (code, year, semester) already
exists, it is updated in-place rather than duplicated.

Usage:
    python -m scripts.import_course_configs                   # import all
    python -m scripts.import_course_configs --files zsi       # import ZSI only
    python -m scripts.import_course_configs --files devops    # import DevOps only
    python -m scripts.import_course_configs --dry-run         # preview only

Can also be invoked inside Docker:
    docker compose exec api python -m scripts.import_course_configs
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_MAX_CONFIG_SIZE = 2 * 1024 * 1024  # 2 MB

# Ensure src/ is importable when running from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Also make project root available for scripts module
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

FIXTURES_DIR = _PROJECT_ROOT / "docs" / "fixtures"

# Map of short names to fixture files
CONFIG_FILES: dict[str, str] = {
    "zsi": "zsi-course-config.json",
    "devops": "devops-course-config.json",
}


def _discover_configs(names: list[str] | None) -> list[Path]:
    """Return paths to fixture files to import."""
    if names:
        paths = []
        for name in names:
            key = name.lower().strip()
            if key in CONFIG_FILES:
                p = FIXTURES_DIR / CONFIG_FILES[key]
            else:
                # Try as literal filename
                p = FIXTURES_DIR / key
                if not p.suffix:
                    p = p.with_suffix(".json")
            if not p.exists():
                print(f"  [WARN] Config file not found: {p}")
                continue
            paths.append(p)
        return paths

    # Default: import all full-config files
    return sorted(p for p in FIXTURES_DIR.glob("*-course-config.json") if p.is_file())


async def _import_config(config_path: Path, *, dry_run: bool = False) -> bool:
    """Import a single config file into the database.

    Returns True on success, False on error.
    """
    from sqlalchemy import select

    from app.config import get_settings
    from app.db.session import get_async_session, init_engine
    from app.models.course import Course
    from app.models.course_settings import CourseSettings

    print(f"\n  Importing: {config_path.name}")

    # Load and validate JSON (sync I/O is fine for this one-shot script)
    try:
        with open(config_path, encoding="utf-8") as f:
            raw = f.read(_MAX_CONFIG_SIZE + 1)
        if len(raw) > _MAX_CONFIG_SIZE:
            print(f"  [ERROR] {config_path.name}: config file exceeds 2 MB limit")
            return False
        config = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [ERROR] Failed to read {config_path.name}: {exc}")
        return False

    if not isinstance(config, dict):
        print(f"  [ERROR] {config_path.name}: root must be a JSON object")
        return False

    # Extract course identity
    course_meta = config.get("course") or config.get("source_course") or {}
    code = str(course_meta.get("code", "")).strip()[:20]
    name = str(course_meta.get("name", code)).strip()[:200]
    academic_year = str(course_meta.get("academic_year", "")).strip()[:10]
    semester = str(course_meta.get("semester", "winter")).strip().lower()

    if not code or not academic_year:
        print(f"  [ERROR] {config_path.name}: course.code and course.academic_year are required")
        return False

    print(f"  Course: {code} ({name}) - {academic_year} {semester}")

    if dry_run:
        section_names = [
            k
            for k in (
                "course",
                "settings",
                "builtin_checks",
                "custom_checks",
                "weekly_deadlines",
                "gaming_detection",
                "rubric",
            )
            if k in config
        ]
        print(f"  Sections: {', '.join(section_names)}")
        print("  [DRY-RUN] No changes applied")
        return True

    # Initialize DB engine if needed
    settings = get_settings()
    init_engine(str(settings.database_url), pool_size=2)

    async for db in get_async_session():
        # -- Find or create course --
        stmt = select(Course).where(
            Course.code == code,
            Course.academic_year == academic_year,
            Course.semester == semester,
        )
        result = await db.execute(stmt)
        course_obj = result.scalar_one_or_none()
        created = False

        if course_obj is None:
            course_obj = Course(
                code=code,
                name=name,
                description=str(course_meta.get("description", ""))[:2000],
                academic_year=academic_year,
                semester=semester,
                is_active=course_meta.get("is_active", True),
            )
            db.add(course_obj)
            await db.flush()

            cs = CourseSettings(course_id=course_obj.id)
            cs.course = course_obj
            db.add(cs)
            await db.flush()
            created = True
            print(f"  [NEW] Created course {code} (id={course_obj.id})")
        elif not course_obj.settings:
            cs = CourseSettings(course_id=course_obj.id)
            cs.course = course_obj
            db.add(cs)
            await db.flush()
        else:
            cs = course_obj.settings
            print(f"  [EXISTS] Updating course {code} (id={course_obj.id})")

        # -- Import all sections using the same config-application helpers as the dashboard --
        from app.api.dashboard.courses.settings_config import (
            _apply_builtin_checks_from_config,
            _apply_course_metadata,
            _apply_custom_checks_from_config,
            _apply_settings_from_config,
            _apply_weekly_deadlines,
        )

        errors: list[str] = []
        applied: list[str] = []

        if isinstance(config.get("course"), dict):
            _apply_course_metadata(course_obj, course_obj.id, db, config["course"], errors)
            applied.append("course_metadata")

        settings_data = config.get("settings")
        if isinstance(settings_data, dict):
            _apply_settings_from_config(cs, settings_data, errors)
            applied.append("settings")

        builtin_list = config.get("builtin_checks")
        if isinstance(builtin_list, list):
            _apply_builtin_checks_from_config(cs, builtin_list, errors)
            applied.append("builtin_checks")

        custom_list = config.get("custom_checks")
        if isinstance(custom_list, list):
            await _apply_custom_checks_from_config(db, course_obj.id, custom_list, errors)
            applied.append("custom_checks")

        weekly = config.get("weekly_deadlines")
        if isinstance(weekly, list):
            _apply_weekly_deadlines(cs, weekly, errors)
            applied.append("weekly_deadlines")

        await db.flush()

        # Report
        action = "Created" if created else "Updated"
        print(f"  [{action.upper()}] Applied sections: {', '.join(applied)}")
        if errors:
            for err in errors:
                print(f"  [WARN] {err}")

        # Write audit log
        try:
            from app.services.audit import write_audit

            await write_audit(
                db,
                action="course.create" if created else "course.update",
                actor="auto-import",
                entity_type="course",
                entity_id=course_obj.id,
                detail={
                    "summary": f"Auto-import from {config_path.name}",
                    "sections": applied,
                    "warnings": len(errors),
                },
            )
        except Exception:
            logger.debug("audit_log_write_failed_during_import", exc_info=True)

    return True


async def _main(args: argparse.Namespace) -> int:
    """Main async entry point."""
    configs = _discover_configs(args.files)

    if not configs:
        print("  [WARN] No config files found to import")
        return 0

    print(f"\n  Found {len(configs)} config file(s) to import:")
    for p in configs:
        print(f"    - {p.name}")

    success = 0
    fail = 0
    for config_path in configs:
        try:
            ok = await _import_config(config_path, dry_run=args.dry_run)
            if ok:
                success += 1
            else:
                fail += 1
        except Exception as exc:
            print(f"  [ERROR] {config_path.name}: {type(exc).__name__}: {exc}")
            fail += 1

    # Cleanup
    if not args.dry_run:
        from app.db.session import dispose_engine

        await dispose_engine()

    print(f"\n  Done: {success} imported, {fail} failed")
    return 1 if fail else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import course configurations from fixture files",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        metavar="NAME",
        help="Config names to import (e.g. 'zsi', 'devops'). Default: all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be imported without applying changes",
    )
    args = parser.parse_args()

    # Load .env if running outside Docker
    env_file = _PROJECT_ROOT / ".env"
    if env_file.exists() and not os.environ.get("DATABASE_URL"):
        print("  Loading .env file...")
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value

    exit_code = asyncio.run(_main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
