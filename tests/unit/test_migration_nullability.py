"""A migration's nullability must match its model, and must be applicable to a
table that already has rows.

This exists because migration 012 shipped with the condition inverted:

    nullable=server_default is not None   # wrong

which made ``preferred_language`` - the one column with no server default -
NOT NULL. Unit tests never run migrations against a real database, so it passed
every gate and failed only in production, on the ALTER:

    NotNullViolationError: column "preferred_language" of relation "users"
    contains null values

The rule it encodes is simple and has nothing to do with SQLAlchemy: adding a
NOT NULL column to a populated table only works if the column carries a default
for the existing rows to take.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

from app.models.user import User

VERSIONS = Path(__file__).resolve().parents[2] / "alembic/versions"


def _load(filename: str) -> Any:
    spec = importlib.util.spec_from_file_location(filename, VERSIONS / filename)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PREFS = _load("012_user_preferences.py")
DIFFS = _load("013_diff_colors.py")
NOTIFY = _load("014_notification_prefs.py")
WORKSPACE = _load("015_workspace_prefs.py")
QUEUE = _load("016_ticket_queue_pref.py")


def _columns_the_migration_would_add(module: Any) -> dict[str, Any]:
    """Run upgrade() with op.add_column captured, and return the real Column
    objects it builds.

    Reading ``_COLUMNS`` and re-deriving the rule would NOT catch the bug this
    file exists for: the data was right and the expression using it was
    inverted. Only executing upgrade() sees what actually reaches the database.
    """
    captured: dict[str, Any] = {}

    class _Op:
        @staticmethod
        def add_column(table: str, column: Any) -> None:
            captured[column.name] = column

    original = module.op
    module.op = _Op()
    try:
        module.upgrade()
    finally:
        module.op = original
    return captured


PREFS_ADDED = _columns_the_migration_would_add(PREFS)
DIFFS_ADDED = _columns_the_migration_would_add(DIFFS)
NOTIFY_ADDED = _columns_the_migration_would_add(NOTIFY)
WORKSPACE_ADDED = _columns_the_migration_would_add(WORKSPACE)
QUEUE_ADDED = _columns_the_migration_would_add(QUEUE)


@pytest.mark.parametrize("name", [c[0] for c in PREFS._COLUMNS])
def test_not_null_column_always_carries_a_default(name: str) -> None:
    """The whole rule, stated once: NOT NULL needs a default on a populated
    table. A column with no default MUST be nullable."""
    column = PREFS_ADDED[name]
    if not column.nullable:
        assert column.server_default is not None, (
            f"{name} is NOT NULL with no server default - the ALTER fails on "
            "any table that already has rows"
        )


@pytest.mark.parametrize("name", [c[0] for c in PREFS._COLUMNS])
def test_migration_nullability_matches_the_model(name: str) -> None:
    """A column the migration makes NOT NULL while the model calls it optional
    (or the reverse) is a schema the ORM cannot round-trip."""
    assert PREFS_ADDED[name].nullable == User.__table__.columns[name].nullable, (
        f"{name}: migration nullable={PREFS_ADDED[name].nullable} but the model "
        f"says nullable={User.__table__.columns[name].nullable}"
    )


@pytest.mark.parametrize("name", DIFFS._COLUMNS)
def test_diff_colour_columns_are_nullable_in_both_places(name: str) -> None:
    """NULL is the meaningful value here - "no override" - so neither the
    migration nor the model may forbid it."""
    assert User.__table__.columns[name].nullable is True
    assert DIFFS_ADDED[name].nullable is True


def test_every_preference_column_in_the_model_is_covered_by_a_migration() -> None:
    """A column added to the model without a migration exists in dev (created
    from metadata) and is missing in production, which is the same outage in a
    different disguise."""
    # DISCOVERED, not listed: this set used to name each migration module by
    # hand, so the check went stale the moment a new one landed and reported the
    # new column as un-migrated when its migration was sitting right there.
    migrated: set[str] = set()
    for path in sorted(VERSIONS.glob("*.py")):
        module = _load(path.name)
        for entry in getattr(module, "_COLUMNS", ()):
            migrated.add(entry[0] if isinstance(entry, tuple) else entry)
    from app.api.dashboard.preferences import PREFERENCE_FIELDS

    declared = {f.name for f in PREFERENCE_FIELDS}
    # theme_preference predates these migrations and has its own.
    missing = declared - migrated - {"theme_preference"}
    assert not missing, f"preference columns with no migration: {sorted(missing)}"


@pytest.mark.parametrize("name", NOTIFY._COLUMNS)
def test_notification_flags_are_not_null_with_a_default(name: str) -> None:
    """NOT NULL is only safe here because each carries a server default for the
    existing rows to take - the rule migration 012 got wrong."""
    column = NOTIFY_ADDED[name]
    assert column.nullable is False
    assert column.server_default is not None
    assert User.__table__.columns[name].nullable is False


@pytest.mark.parametrize("name", [c[0] for c in WORKSPACE._COLUMNS])
def test_workspace_columns_are_not_null_with_a_default(name: str) -> None:
    """GitPulse's own two. NOT NULL is safe only because each carries a default
    for the existing rows to take - the rule migration 012 got wrong."""
    column = WORKSPACE_ADDED[name]
    assert column.nullable is False
    assert column.server_default is not None
    assert User.__table__.columns[name].nullable is False


@pytest.mark.parametrize("name", QUEUE._COLUMNS)
def test_ticket_queue_flag_is_not_null_with_a_default(name: str) -> None:
    column = QUEUE_ADDED[name]
    assert column.nullable is False
    assert column.server_default is not None
