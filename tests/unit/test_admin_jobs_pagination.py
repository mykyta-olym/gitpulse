"""Actual SQL paging and terminal-only cleanup of the operational job list."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import Session

from app.api.dashboard.admin.system import admin_delete_jobs, admin_purge_jobs, build_jobs_payload
from app.models.background_job import BackgroundJob
from app.observability.job_diagnostics import FailureLog
from app.services import job_history


@pytest.fixture
def job_db():
    engine = create_engine("sqlite:///:memory:")
    BackgroundJob.__table__.create(engine)
    with Session(engine, expire_on_commit=False) as db:
        yield SimpleNamespace(
            execute=AsyncMock(side_effect=db.execute),
            scalars=AsyncMock(side_effect=db.scalars),
            commit=AsyncMock(side_effect=db.commit),
        )
    engine.dispose()


@pytest.mark.asyncio
async def test_filtered_total_and_pages_beyond_one_thousand(job_db):
    now = datetime.now(UTC)
    jobs = [
        {
            "id": uuid.uuid4(),
            "job_type": "sync",
            "status": "failed",
            "enqueued_at": now - timedelta(seconds=i),
        }
        for i in range(1105)
    ]
    jobs.append(
        {"id": uuid.uuid4(), "job_type": "run_checks", "status": "completed", "enqueued_at": now}
    )
    await job_db.execute(insert(BackgroundJob), jobs)
    await job_db.commit()
    page = await build_jobs_payload(job_db, "failed", "sync", 50, 1050)
    assert page["total"] == 1105
    assert [row["id"] for row in page["jobs"]] == [str(row["id"]) for row in jobs[1050:1100]]
    assert page["job_types"] == ["run_checks", "sync"]
    empty = await build_jobs_payload(job_db, "completed", "sync", 50, 0)
    assert empty["total"] == 0
    assert empty["jobs"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("purge", [False, True])
async def test_cleanup_preserves_active_jobs(job_db, purge, monkeypatch):
    monkeypatch.setattr(job_history, "_remove_rq_history", lambda *args: (set(), set()))
    rows = [
        {
            "id": uuid.uuid4(),
            "job_type": "sync",
            "status": status,
            "enqueued_at": datetime.now(UTC) - timedelta(days=2),
        }
        for status in ("enqueued", "started", "running", "completed", "failed", "cancelled")
    ]
    await job_db.execute(insert(BackgroundJob), rows)
    await job_db.commit()
    body = (
        {"hours": 87600, "status": "both", "scope": "both"}
        if purge
        else {"ids": [str(row["id"]) for row in rows]}
    )
    request = SimpleNamespace(json=AsyncMock(return_value=body))
    endpoint = admin_purge_jobs if purge else admin_delete_jobs
    result = await endpoint(request, job_db, None, None, None)
    assert b'"deleted":3' in result.body
    assert set((await job_db.execute(select(BackgroundJob.status))).scalars()) == {
        "enqueued",
        "started",
        "running",
    }


@pytest.mark.asyncio
async def test_purge_uses_last_activity_and_counts_each_execution_once(job_db, monkeypatch):
    now = datetime.now(UTC)
    old = now - timedelta(days=3)
    for status, rq_id, completed in (
        ("failed", "shared", old),
        ("failed", "recent", now),
        ("completed", "finished", old),
        ("running", "active", None),
    ):
        await job_db.execute(
            insert(BackgroundJob),
            [
                {
                    "id": uuid.uuid4(),
                    "job_type": "sync",
                    "status": status,
                    "rq_job_id": rq_id,
                    "enqueued_at": old,
                    "completed_at": completed,
                }
            ],
        )
    await job_db.commit()
    from unittest.mock import Mock

    purge = Mock(return_value=({"shared", "rq-only"}, set()))
    monkeypatch.setattr(job_history, "_remove_rq_history", purge)
    response = await admin_purge_jobs(
        SimpleNamespace(json=AsyncMock(return_value={"hours": 24})), job_db, None, None, None
    )
    assert json.loads(response.body)["deleted"] == 3
    assert set((await job_db.execute(select(BackgroundJob.rq_job_id))).scalars()) == {
        "recent",
        "active",
    }
    assert (
        now - timedelta(hours=24)
        <= purge.call_args.args[1]
        <= datetime.now(UTC) - timedelta(hours=24)
    )


@pytest.mark.asyncio
async def test_purge_reports_redis_failure_before_deleting_sql(job_db, monkeypatch):
    from unittest.mock import Mock

    monkeypatch.setattr(job_history, "_remove_rq_history", Mock(side_effect=ConnectionError))
    job_db.execute.reset_mock()
    job_db.commit.reset_mock()
    with pytest.raises(HTTPException, match="Job history cleanup is unavailable") as exc:
        await admin_purge_jobs(
            SimpleNamespace(json=AsyncMock(return_value={})), job_db, None, None, None
        )
    assert exc.value.status_code == 503
    job_db.execute.assert_not_called()
    job_db.commit.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["completed", "cancelled"])
async def test_status_specific_purge_does_not_remove_failed_history(job_db, monkeypatch, status):
    from unittest.mock import Mock

    purge = Mock(return_value=(set(), set()))
    monkeypatch.setattr(job_history, "_remove_rq_history", purge)
    await admin_purge_jobs(
        SimpleNamespace(json=AsyncMock(return_value={"status": status})), job_db, None, None, None
    )
    assert purge.call_args.args[2] is False


@pytest.mark.asyncio
async def test_audit_ids_cannot_be_deleted_through_jobs(job_db):
    request = SimpleNamespace(json=AsyncMock(return_value={"ids": [f"audit:{uuid.uuid4()}"]}))
    with pytest.raises(HTTPException, match="background job UUIDs"):
        await admin_delete_jobs(request, job_db, None, None, None)


@pytest.mark.asyncio
async def test_merged_log_deduplicates_filters_and_pages_without_missing_rows(job_db):
    now = datetime.now(UTC)
    rows = [
        {
            "id": uuid.uuid4(),
            "job_type": "sync",
            "status": "failed",
            "enqueued_at": now - timedelta(seconds=i * 2),
            "rq_job_id": f"rq-{i}",
        }
        for i in range(120)
    ]
    await job_db.execute(insert(BackgroundJob), rows)
    await job_db.commit()
    failures = FailureLog(
        total=1000,
        rows=[
            {
                "id": f"rq-{i}" if i < 10 else f"untracked-{i}",
                "function": "app.workers.sync_job.full_sync",
                "queue": "default",
                "observed_at": now - timedelta(seconds=i * 3 + 1),
                "cause": "Job execution failed",
                "hint": "Check worker logs",
                "reference": f"safe-reference-{i}",
            }
            for i in range(30)
        ],
    )
    whole = await build_jobs_payload(job_db, None, None, 500, 0, failures=failures)
    assert whole["total"] == 140
    assert sum(bool(row.get("read_only")) for row in whole["jobs"]) == 20
    assert len({row["rq_job_id"] for row in whole["jobs"]}) == 140
    assert sum(bool(row.get("diagnostic")) for row in whole["jobs"]) == 30
    pages = [
        await build_jobs_payload(job_db, None, None, 25, offset, failures=failures)
        for offset in range(0, 150, 25)
    ]
    assert [r["id"] for page in pages for r in page["jobs"]] == [r["id"] for r in whole["jobs"]]
    filtered = await build_jobs_payload(job_db, "failed", "full_sync", 50, 0, failures=failures)
    assert filtered["total"] == 20
    assert all(row["read_only"] for row in filtered["jobs"])
    tracked = await build_jobs_payload(job_db, "failed", "sync", 500, 0, failures=failures)
    assert tracked["total"] == 120
    assert not any(row.get("read_only") for row in tracked["jobs"])
    assert whole["failure_history"] == {"available": True, "total": 1000, "limit": 100}
    import json

    json.dumps(whole)  # No datetime objects escape into the API contract.


@pytest.mark.asyncio
async def test_unavailable_registry_keeps_sql_rows_and_cannot_delete_rq_ids(job_db):
    await job_db.execute(
        insert(BackgroundJob), [{"id": uuid.uuid4(), "job_type": "sync", "status": "completed"}]
    )
    await job_db.commit()
    payload = await build_jobs_payload(
        job_db, None, None, 50, 0, failures=FailureLog(available=False)
    )
    assert payload["total"] == 1
    assert not payload["failure_history"]["available"]
    request = SimpleNamespace(json=AsyncMock(return_value={"ids": [f"rq-{uuid.uuid4()}"]}))
    with pytest.raises(HTTPException, match="background job UUIDs"):
        await admin_delete_jobs(request, job_db, None, None, None)
