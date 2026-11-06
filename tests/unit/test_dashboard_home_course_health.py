"""Regression coverage for dashboard home course-health helpers."""

import pytest

from app.api.dashboard.home.course_health import _build_course_health


class _NoExecuteDb:
    async def execute(self, *_args: object, **_kwargs: object) -> object:
        raise AssertionError("empty active course input must not query the database")


@pytest.mark.asyncio
async def test_build_course_health_skips_db_without_active_courses() -> None:
    assert await _build_course_health([], _NoExecuteDb()) == {}  # type: ignore[arg-type]
