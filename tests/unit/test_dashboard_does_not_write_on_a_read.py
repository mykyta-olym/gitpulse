"""Rendering the dashboard must not write to the database for nothing.

The stale-job self-heal belongs on a read path - a crashed worker cannot reap
its own jobs, so something a reader touches has to. What it must not do is
issue the UPDATE unconditionally: every dashboard load then took row locks on
`background_jobs` and wrote WAL for a set that is almost always empty, and
simultaneous loads contended on the same rows.

These pin both halves: nothing to heal means no write at all, and something to
heal is still healed.
"""

from __future__ import annotations

import uuid

import pytest

from app.api.dashboard.home.sync_info import _load_course_sync_info


class _RecordingDb:
    """Answers each statement plausibly and records what it was asked."""

    def __init__(self, *, has_stale: bool) -> None:
        self.has_stale = has_stale
        self.statements: list[str] = []

    async def execute(self, statement: object, *_a: object, **_kw: object) -> object:
        text = " ".join(str(statement).split())
        self.statements.append(text)
        has_stale = self.has_stale
        is_stale_probe = text.startswith("SELECT background_jobs.id")

        class _Result:
            def first(self) -> object | None:
                return (uuid.uuid4(),) if (is_stale_probe and has_stale) else None

            def all(self) -> list[object]:
                return []

            def scalar(self) -> int:
                return 0

        return _Result()

    async def flush(self) -> None:
        return None

    @property
    def writes(self) -> list[str]:
        return [s for s in self.statements if s.upper().startswith("UPDATE")]


@pytest.mark.asyncio
async def test_a_clean_render_writes_nothing() -> None:
    db = _RecordingDb(has_stale=False)
    await _load_course_sync_info([uuid.uuid4()], db)  # type: ignore[arg-type]
    assert not db.writes, f"the dashboard wrote with nothing to heal: {db.writes}"


@pytest.mark.asyncio
async def test_a_stale_job_is_still_healed() -> None:
    db = _RecordingDb(has_stale=True)
    await _load_course_sync_info([uuid.uuid4()], db)  # type: ignore[arg-type]
    assert len(db.writes) == 1, f"the self-heal stopped running: {db.statements}"
    assert "background_jobs" in db.writes[0].lower()


@pytest.mark.asyncio
async def test_no_courses_means_no_statements_at_all() -> None:
    db = _RecordingDb(has_stale=True)
    assert await _load_course_sync_info([], db) == {}  # type: ignore[arg-type]
    assert not db.statements
