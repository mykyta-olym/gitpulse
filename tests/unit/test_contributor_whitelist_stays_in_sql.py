"""The contributor whitelist is asked of the database, not shipped to it.

For a 459-member course the Python-built whitelist went back to Postgres as two
`IN` lists: ~900 bind parameters, 20 129 characters of SQL, and a round-trip to
fetch the names and emails before any of that. As a subquery the same filter is
1 954 characters and one query fewer, and returns the same counts group for
group - verified against production data.

What this is NOT is the fix for the slow course page, whatever the first version
of this file said. That claim came from a 2560ms reading of this query, which
was real but was taken while a deploy rebuilt container images on the same four
cores. Measured on an idle host both forms are the same speed: 15.2ms as a
subquery, 16.2ms as a bind list, 0.8ms of planning either way. The pages were
slow because of the deploy (fixed in redeploy.py), not because of this shape.

So the test is on the shape for its own sake: a statement that grows with the
roster is one the database has to parse and log in full on every request, and
the roster is already in `team_members` where the query can reach it.
"""

from __future__ import annotations

import uuid

from app.api.dashboard._stats import (
    _student_inclusion_conditions,
    _student_whitelist_conditions,
)

_TEAMS = [uuid.uuid4() for _ in range(8)]


def _sql(conditions: list[object]) -> str:
    from sqlalchemy import select

    from app.models.commit import Commit

    stmt = select(Commit.id).where(*conditions)  # type: ignore[arg-type]
    return str(stmt.compile(compile_kwargs={"literal_binds": False}))


def test_the_whole_course_path_asks_the_database() -> None:
    sql = _sql(_student_whitelist_conditions(_TEAMS)).lower()
    assert "team_members" in sql, "the whitelist is not derived from the roster in SQL"
    assert "students" in sql, "the student identifiers are not read in SQL"
    assert "select" in sql.split("in (", 1)[1], "the IN is a value list, not a subquery"


def test_it_does_not_carry_a_parameter_per_member() -> None:
    """~900 binds is what made Postgres re-plan the statement every time."""
    from sqlalchemy import select

    from app.models.commit import Commit

    stmt = select(Commit.id).where(*_student_whitelist_conditions(_TEAMS))  # type: ignore[arg-type]
    params = stmt.compile().params
    assert len(params) <= 20, (
        f"the statement carries {len(params)} parameters - the whitelist is being "
        "shipped to the database again"
    )


def test_the_set_based_form_is_still_there_for_short_lists() -> None:
    """A single group holds a handful of members; sending those is fine, and
    callers that already have the identifiers keep using it."""
    conditions = _student_inclusion_conditions({"ada lovelace"}, {"ada@student.university.edu"})
    sql = _sql(conditions).lower()
    assert "team_members" not in sql
    assert "lower(git_commits.author_name) in" in sql


def test_an_empty_roster_matches_nothing_either_way() -> None:
    """Both forms have to agree on the edge: no known students means no
    contributors, not every commit in the course."""
    empty_sets = _sql(_student_inclusion_conditions(set(), set())).lower()
    assert "is null" in empty_sets, "the set form stopped excluding everything"
    # The SQL form needs no special case - an empty subquery matches no row.
    assert "select" in _sql(_student_whitelist_conditions([])).lower()
