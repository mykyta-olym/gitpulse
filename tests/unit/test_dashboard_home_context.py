"""Regression coverage for dashboard home context helpers."""

from uuid import uuid4

import pytest

from app.api.dashboard.home.context import _build_sidebar_badges, _build_student_context


class _NoExecuteDb:
    async def execute(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("this path must not query the database")


@pytest.mark.asyncio
async def test_student_context_skips_db_without_active_courses() -> None:
    out = await _build_student_context([], _NoExecuteDb(), {"gitlab_username": "student"})
    assert out["team_ids"] == []
    assert out["compliance_pct"] == 0
    assert out["traffic_light"] == "green"


@pytest.mark.asyncio
async def test_student_context_skips_db_without_username() -> None:
    out = await _build_student_context([uuid4()], _NoExecuteDb(), {})  # type: ignore[arg-type]
    assert out["team_ids"] == []
    assert out["open_mrs"] == 0
    assert out["failed_pipelines"] == 0


@pytest.mark.asyncio
async def test_sidebar_badges_skip_db_for_students() -> None:
    assert await _build_sidebar_badges("student", [], _NoExecuteDb()) == {}  # type: ignore[arg-type]


class _CountingDb:
    """Records every statement, and answers whatever shape is asked of it.

    The admin context asks for five job counts and one webhook count. What
    this pins is the number of ROUND-TRIPS: the five counts used to be five
    separate SELECT count(*) statements against the same table, issued on
    every dashboard render, and the page made fifty queries in total.
    """

    def __init__(self) -> None:
        self.statements: list[str] = []

    async def execute(self, statement: object, *_a: object, **_kw: object) -> object:
        text = " ".join(str(statement).split())
        self.statements.append(text)
        columns = text.count("count(") if text.startswith("SELECT") else 1

        class _Result:
            def one(self) -> tuple[int, ...]:
                return tuple(range(columns))

            def scalar(self) -> int:
                return 0

        return _Result()

    @property
    def job_count_statements(self) -> list[str]:
        return [s for s in self.statements if "background_jobs" in s]


@pytest.mark.asyncio
async def test_admin_context_counts_jobs_in_one_round_trip() -> None:
    from app.api.dashboard.home.context import _build_admin_context

    db = _CountingDb()
    ctx = await _build_admin_context(db)  # type: ignore[arg-type]

    assert len(db.job_count_statements) == 1, (
        f"the five job counts are separate queries again: {db.job_count_statements}"
    )
    # All five still asked for, in that one statement.
    assert db.job_count_statements[0].count("count(") == 5
    for key in ("jobs_queued", "jobs_running", "jobs_failed_24h", "jobs_completed_24h"):
        assert key in ctx


@pytest.mark.asyncio
async def test_admin_context_uses_one_cutoff_for_both_windows() -> None:
    """The failed and completed windows must be the same 24 hours.

    They were computed separately, one per query, so the two windows could
    differ by however long the first query took.
    """
    from app.api.dashboard.home.context import _build_admin_context

    db = _CountingDb()
    await _build_admin_context(db)  # type: ignore[arg-type]

    statement = db.job_count_statements[0]
    assert statement.count("completed_at >=") == 2, statement
