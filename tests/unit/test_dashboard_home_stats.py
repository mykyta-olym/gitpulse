"""Tests for dashboard home stat-card helpers."""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_student_stat_cards_skip_db_when_no_active_courses() -> None:
    from app.api.dashboard.home.stats import _build_stat_cards

    db = AsyncMock()

    cards = await _build_stat_cards("student", [], [], db, {"user": "alice"})

    db.execute.assert_not_awaited()
    assert {card["id"]: card["value"] for card in cards} == {
        "statActiveCourses": 0,
        "statMyTeams": 0,
        "statCompliance": "0%",
        "statOpenMrs": 0,
    }
