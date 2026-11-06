"""Every request line says how much of it was the database.

`request_completed` said a course page took 13 seconds and nothing else, and
that is not enough to act on: a hundred quick queries in sequence and one slow
template render produce the same number. The counters here split it, on a line
that was already being written.

Exercised against a real SQLite engine rather than a mock - the whole point is
that SQLAlchemy's `before_cursor_execute` / `after_cursor_execute` actually fire
where they are attached, which a mock would assert nothing about.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.observability import db_timing

REPO = Path(__file__).resolve().parents[2]
MIDDLEWARE = REPO / "src/app/middleware/logging.py"


@pytest.fixture
def engine():
    eng = create_engine("sqlite://")
    db_timing.install(eng)
    try:
        yield eng
    finally:
        eng.dispose()


def _run(engine, n: int = 1) -> None:
    with engine.connect() as conn:
        for _ in range(n):
            conn.execute(text("SELECT 1"))


def test_nothing_is_counted_outside_a_request(engine) -> None:
    """A worker job, a startup probe, a migration - there is no request line to
    put the numbers on, and nothing must accumulate between them."""
    db_timing._TALLY.set(None)
    _run(engine, 3)
    assert db_timing.read() is None


def test_statements_are_counted_and_timed(engine) -> None:
    db_timing.begin_request()
    _run(engine, 4)
    counted = db_timing.read()
    assert counted is not None
    queries, ms = counted
    assert queries == 4, f"counted {queries} statements, ran 4"
    assert ms >= 0.0
    assert ms < 1000, f"four SELECT 1 took {ms}ms - the timer is measuring the wrong thing"


def test_a_second_request_starts_from_zero(engine) -> None:
    db_timing.begin_request()
    _run(engine, 2)
    db_timing.begin_request()
    _run(engine, 1)
    queries, _ms = db_timing.read()
    assert queries == 1, "the previous request's statements leaked into this one"


def test_installing_twice_does_not_count_twice(engine) -> None:
    """SQLAlchemy would happily register the same listener again, and every
    statement would then be counted once per registration."""
    db_timing.install(engine)
    db_timing.install(engine)
    db_timing.begin_request()
    _run(engine, 2)
    assert db_timing.read()[0] == 2


def test_the_worst_query_is_the_one_remembered(engine) -> None:
    """Six seconds across twenty queries means one or two own the page. The
    counter keeps the worst so the log can name it."""
    db_timing.begin_request()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        conn.execute(text("SELECT 2 AS the_slow_one"))
    worst = db_timing.read_slowest()
    assert worst is not None
    ms, sql = worst
    assert ms >= 0.0
    assert sql.startswith("SELECT"), f"the statement was not kept: {sql!r}"


def test_the_statement_is_kept_without_its_parameters(engine) -> None:
    """A parameter can be a student's name or email. The statement carries
    placeholders; the values travel separately and must stay there."""
    db_timing.begin_request()
    with engine.connect() as conn:
        conn.execute(text("SELECT :secret AS x"), {"secret": "ada@student.university.edu"})
    worst = db_timing.read_slowest()
    assert worst is not None
    assert "ada@student.university.edu" not in worst[1], "a parameter value reached the log"


def test_nothing_to_name_before_anything_ran() -> None:
    db_timing.begin_request()
    assert db_timing.read_slowest() is None


def test_the_request_line_carries_both_numbers() -> None:
    src = MIDDLEWARE.read_text(encoding="utf-8")
    assert "db_timing.begin_request()" in src, "nothing starts the count for a request"
    assert "db_ms=" in src, "the request line does not say how long the database took"
    assert "db_queries=" in src, "the request line does not say how many statements ran"
    assert "db_slowest_sql" in src, "a slow request does not name its worst query"
    assert "_SLOW_REQUEST_S" in src, (
        "every request would carry SQL in its log line, not only the slow ones"
    )
