"""Tests for shared dashboard stat-query helpers (``_stats``)."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.dashboard._stats import latest_student_metric_map, latest_team_metric_map


@pytest.mark.asyncio
async def test_latest_team_metric_map_empty_skips_db() -> None:
    db = AsyncMock()

    result = await latest_team_metric_map(db, [])

    assert result == {}
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_latest_team_metric_map_keys_by_team_last_wins() -> None:
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    snap_a = SimpleNamespace(team_id=t1)
    snap_b = SimpleNamespace(team_id=t2)
    snap_a_tie = SimpleNamespace(team_id=t1)  # same team, tie -> last row wins

    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = [snap_a, snap_b, snap_a_tie]
    db.execute.return_value = execute_result

    result = await latest_team_metric_map(db, [t1, t2])

    assert result == {t1: snap_a_tie, t2: snap_b}
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_latest_student_metric_map_empty_skips_db() -> None:
    db = AsyncMock()

    result = await latest_student_metric_map(db, [], uuid.uuid4())

    assert result == {}
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_latest_student_metric_map_keys_by_student_last_wins() -> None:
    team_id = uuid.uuid4()
    s1, s2 = uuid.uuid4(), uuid.uuid4()
    snap_a = SimpleNamespace(student_id=s1)
    snap_b = SimpleNamespace(student_id=s2)
    snap_a_tie = SimpleNamespace(student_id=s1)  # same student, tie -> last row wins

    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = [snap_a, snap_b, snap_a_tie]
    db.execute.return_value = execute_result

    result = await latest_student_metric_map(db, [s1, s2], team_id)

    assert result == {s1: snap_a_tie, s2: snap_b}
    db.execute.assert_awaited_once()
