"""Tests for dashboard fragment-cache invalidation after sync jobs."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import Mock

import pytest


class _FakeResult:
    def __init__(self, rows: list[tuple[uuid.UUID | None]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[uuid.UUID | None]]:
        return self._rows


class _FakeSession:
    def __init__(self, student_ids: list[uuid.UUID | None]) -> None:
        self.student_ids = student_ids

    async def execute(self, _stmt: Any) -> _FakeResult:
        return _FakeResult([(sid,) for sid in self.student_ids])


@pytest.mark.asyncio
async def test_sync_completion_invalidates_dashboard_fragment_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.workers.sync_cache import _invalidate_dashboard_cache_after_sync

    team_id = uuid.uuid4()
    course_id = uuid.uuid4()
    project_id = uuid.uuid4()
    student_id = uuid.uuid4()
    invalidate = Mock()
    monkeypatch.setattr("app.workers.sync_cache.invalidate_cascade", invalidate)

    await _invalidate_dashboard_cache_after_sync(
        _FakeSession([student_id, None]),
        team_id=team_id,
        course_id=course_id,
        project_id=project_id,
    )

    invalidate.assert_called_once_with(
        project_id=project_id,
        team_id=team_id,
        course_id=course_id,
        student_ids=[student_id],
    )
