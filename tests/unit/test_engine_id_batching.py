"""The compliance engine must not exceed the wire protocol's parameter cap.

An IN clause sends one bind parameter per id and PostgreSQL refuses a statement
carrying more than 32767 of them. Loading per-merge-request rows for a team that
had accumulated more merge requests than that failed the whole recompute with
asyncpg's "the number of query arguments cannot exceed 32767" instead of simply
taking longer, so the ids are queried in batches.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.compliance.engine import _MAX_QUERY_IDS, _load_by_mr

# The hard limit the batching exists to stay under.
PG_MAX_BIND_PARAMS = 32767


class _FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def scalars(self) -> _FakeResult:
        return self

    def all(self) -> list[Any]:
        return self._rows


class _RecordingSession:
    """Captures the id-list length of every statement it is asked to run."""

    def __init__(self) -> None:
        self.batch_sizes: list[int] = []

    async def execute(self, stmt: Any) -> _FakeResult:
        # SQLAlchemy keeps an IN list as ONE "expanding" bind parameter until
        # execution, so counting keys would always report 1. The value behind
        # that key is the id list, and its length is what becomes one bind
        # parameter each on the wire.
        ids = 0
        for value in stmt.compile().params.values():
            ids += len(value) if isinstance(value, (list, tuple)) else 1
        self.batch_sizes.append(ids)
        return _FakeResult([f"row-{len(self.batch_sizes)}"])


@pytest.fixture
def model() -> type[Any]:
    from app.models.mr_note import MRNote

    return MRNote


@pytest.mark.asyncio
async def test_a_single_batch_is_left_as_one_query(model: type[Any]) -> None:
    session = _RecordingSession()
    ids = [uuid.uuid4() for _ in range(5)]

    await _load_by_mr(session, model, ids)  # type: ignore[arg-type]

    assert len(session.batch_sizes) == 1
    assert session.batch_sizes[0] == 5


@pytest.mark.asyncio
async def test_more_ids_than_the_cap_are_split_into_safe_batches(
    model: type[Any],
) -> None:
    session = _RecordingSession()
    # Comfortably past the cap - this is the case that used to raise.
    ids = [uuid.uuid4() for _ in range(PG_MAX_BIND_PARAMS + 1000)]

    await _load_by_mr(session, model, ids)  # type: ignore[arg-type]

    assert len(session.batch_sizes) > 1, "must not send one oversized statement"
    assert max(session.batch_sizes) <= _MAX_QUERY_IDS
    assert max(session.batch_sizes) < PG_MAX_BIND_PARAMS
    # Nothing may be dropped on the way.
    assert sum(session.batch_sizes) == len(ids)


@pytest.mark.asyncio
async def test_every_batch_result_is_returned(model: type[Any]) -> None:
    session = _RecordingSession()
    ids = [uuid.uuid4() for _ in range(_MAX_QUERY_IDS * 2 + 1)]

    rows = await _load_by_mr(session, model, ids)  # type: ignore[arg-type]

    assert len(rows) == 3, "one row per batch, concatenated"


@pytest.mark.asyncio
async def test_an_empty_id_list_runs_no_query(model: type[Any]) -> None:
    session = _RecordingSession()

    rows = await _load_by_mr(session, model, [])  # type: ignore[arg-type]

    assert rows == []
    assert session.batch_sizes == []
