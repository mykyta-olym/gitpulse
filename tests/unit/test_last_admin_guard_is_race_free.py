"""The last-admin guard reads under a lock, not as a bare count.

`PATCH /users/{id}` refuses to demote the last active admin. The check was a
plain aggregate: read the count, compare, then write. Two admins demoting each
other in the same moment would both read two, both pass, and leave the
installation with no admin at all - and no way back in without database
access. It is the one time-of-check/time-of-use race in the app whose
consequence is a lockout rather than a stale number.

`SELECT ... FOR UPDATE` over the admin rows makes the second request wait for
the first to commit and then see one. It has to select the rows rather than
count them, because Postgres refuses `FOR UPDATE` alongside an aggregate; the
set is every active human admin, which is small by definition.

The course-owner equivalent needs no lock: it counts owners in the SUBMITTED
payload, and that endpoint already carries an optimistic lock, so a concurrent
change bumps `updated_at` and the second save is refused outright.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
USERS = REPO / "src/app/api/users.py"
TEACHERS = REPO / "src/app/api/dashboard/admin/course_teachers.py"


def _guard() -> str:
    src = USERS.read_text(encoding="utf-8")
    start = src.index("# Prevent demoting the last admin")
    return src[start : src.index("allowed_fields", start)]


def test_the_admin_count_is_taken_under_a_row_lock() -> None:
    body = _guard()
    assert ".with_for_update()" in body, (
        "the last-admin check reads without a lock again - two concurrent "
        "demotions can leave the installation with no admin"
    )


def test_it_counts_rows_rather_than_using_an_aggregate() -> None:
    """Postgres rejects `FOR UPDATE` alongside an aggregate, so a `func.count`
    here would mean the lock had been dropped."""
    body = _guard()
    assert "func.count" not in body
    assert "sa_func" not in USERS.read_text(encoding="utf-8"), (
        "the aggregate helper is imported but unused"
    )


def test_the_owner_guard_still_leans_on_its_optimistic_lock() -> None:
    src = TEACHERS.read_text(encoding="utf-8")
    assert "expected_updated_at" in src, (
        "the teachers endpoint lost its optimistic lock, so its owner count - "
        "taken from the submitted payload - no longer has anything protecting it"
    )
    assert re.search(r"owner_count\s*=\s*sum\(", src), "the owner guard is gone"
