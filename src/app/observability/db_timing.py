"""How much of a request was spent waiting on the database.

`request_completed` says a course page took 13 seconds. It does not say whether
those seconds were queries, Python, or rendering 96 projects into a template,
and on a page that cannot be reproduced outside production - the slow course is
8 groups, 96 projects and 459 members - that difference is the whole
investigation. Measured facts so far: the database itself answers `SELECT 1` in
1.3ms and its largest table holds 14 305 rows, so "the database is slow" is not
the explanation on its own. It could still be a hundred fast queries in
sequence, which looks nothing like a slow query and everything like a slow page.

So each request carries a counter: how many statements it ran and how long they
took in total. Two numbers on a line that is already being written.

Deliberately not a tracer. There is OpenTelemetry in `tracing.py` for following
one request through its spans; this is the always-on summary that makes a slow
request in a log file say which half to look in, without turning tracing on for
everyone.

Cost: one `perf_counter()` pair per statement, into a ContextVar the request
already owns. Nothing is stored between requests, and nothing is logged here -
the middleware reads the totals when it writes its own line.
"""

from __future__ import annotations

import time
from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

#: [statements, seconds, slowest seconds, slowest statement] for the request
#: being served on this task. `None` outside a request - a worker job, a startup
#: probe - where nothing reads it.
_TALLY: ContextVar[list[Any] | None] = ContextVar("gp_db_tally", default=None)

#: How much of a statement to keep. Enough to recognise which query it is; the
#: parameters are NOT part of it - SQLAlchemy passes them separately and they
#: can carry student names and emails, which have no business in a log line.
_SQL_KEPT = 240

#: Set on the connection while a statement is in flight. Per-connection rather
#: than per-task: the two events fire on the same connection, and a task can
#: hold more than one.
_STARTED_AT = "_gp_stmt_started_at"


def begin_request() -> None:
    """Start counting for the request about to be served."""
    _TALLY.set([0, 0.0, 0.0, ""])


def read() -> tuple[int, float] | None:
    """(statements, milliseconds) for this request, or None if nothing counted."""
    tally = _TALLY.get()
    if tally is None:
        return None
    return int(tally[0]), round(tally[1] * 1000, 1)


def read_slowest() -> tuple[float, str] | None:
    """(milliseconds, statement) for the single worst query, or None.

    Twenty queries and 5.9 seconds says the time is in one or two of them, not
    spread across all twenty - so the useful thing to log is which one. Only the
    statement, never its parameters.
    """
    tally = _TALLY.get()
    if tally is None or not tally[3]:
        return None
    return round(float(tally[2]) * 1000, 1), str(tally[3])


def install(engine: Engine) -> None:
    """Attach the counters to a *sync* engine (``async_engine.sync_engine``).

    Safe to call more than once: SQLAlchemy would happily register the same
    listener twice and count every statement twice with it.
    """
    if getattr(engine, "_gp_db_timing_installed", False):
        return

    @event.listens_for(engine, "before_cursor_execute")
    def _before(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        conn.info[_STARTED_AT] = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def _after(
        conn: Any,
        cursor: Any,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        started = conn.info.pop(_STARTED_AT, None)
        if started is None:
            return
        tally = _TALLY.get()
        if tally is None:
            return
        elapsed = time.perf_counter() - started
        tally[0] += 1
        tally[1] += elapsed
        if elapsed > tally[2]:
            tally[2] = elapsed
            tally[3] = " ".join(str(statement).split())[:_SQL_KEPT]

    engine._gp_db_timing_installed = True  # type: ignore[attr-defined]
