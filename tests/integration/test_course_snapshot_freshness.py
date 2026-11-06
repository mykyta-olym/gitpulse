"""Course freshness must read the last index entry, not the snapshot history."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.models import Base
from app.models.course import Course
from app.models.team import Team
from app.models.team_metric_snapshot import TeamMetricSnapshot

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_latest_course_snapshot_does_not_scan_history() -> None:
    engine = create_async_engine(str(get_settings().database_url))
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSession(engine) as db:
            course = Course(
                code=f"idx-{uuid.uuid4().hex[:8]}",
                name="Freshness",
                academic_year="2026/2027",
            )
            db.add(course)
            await db.flush()
            team = Team(course_id=course.id, name="Snapshot history")
            db.add(team)
            await db.flush()
            start = datetime(2026, 1, 1, tzinfo=UTC)
            await db.execute(
                insert(TeamMetricSnapshot),
                [
                    {
                        "course_id": course.id,
                        "team_id": team.id,
                        "computed_at": start + timedelta(hours=i),
                    }
                    for i in range(1000)
                ],
            )
            stmt = select(func.max(TeamMetricSnapshot.computed_at)).where(
                TeamMetricSnapshot.course_id == course.id
            )
            assert await db.scalar(stmt) == start + timedelta(hours=999)
            sql = str(stmt.compile(engine, compile_kwargs={"literal_binds": True}))
            plan = await db.scalar(text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"))

            def nodes(node: dict) -> list[dict]:
                return [node, *(child for p in node.get("Plans", []) for child in nodes(p))]

            steps = nodes(plan[0]["Plan"])
            assert any(n.get("Index Name") == "idx_tms_course_computed" for n in steps)
            assert not any(n["Node Type"] == "Seq Scan" for n in steps)
            assert sum(n.get("Actual Rows", 0) for n in steps if "Scan" in n["Node Type"]) == 1
            assert (
                await db.scalar(
                    select(func.max(TeamMetricSnapshot.computed_at)).where(
                        TeamMetricSnapshot.course_id == uuid.uuid4()
                    )
                )
                is None
            )
            await db.rollback()
    finally:
        await engine.dispose()
