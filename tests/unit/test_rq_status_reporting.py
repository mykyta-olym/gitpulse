"""A lost Redis connection is unknown progress, rather than a successful job."""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from rq.exceptions import NoSuchJobError
from rq.job import JobStatus

from app.api.dashboard.teams import llm
from app.api.helpers import sync
from app.models.background_job import BackgroundJob


@pytest.mark.parametrize("error", [RedisConnectionError, NoSuchJobError])
def test_team_analysis_does_not_report_unobserved_success(monkeypatch, error):
    monkeypatch.setattr(llm, "_get_redis", lambda: Mock())
    monkeypatch.setattr(llm.Job, "fetch", Mock(side_effect=error))
    payload, done = llm._jobs_status(
        SimpleNamespace(session={}), uuid.uuid4(), {"job_ids": ["job"], "total": 1}
    )
    assert payload["completed"] == 0
    assert payload["status"] == ("running" if error is RedisConnectionError else "failed")
    assert done is (error is NoSuchJobError)


def test_team_analysis_preserves_tracking_when_connection_creation_fails(monkeypatch):
    monkeypatch.setattr(llm, "_get_redis", Mock(side_effect=RedisConnectionError))
    payload, done = llm._jobs_status(
        SimpleNamespace(session={}), uuid.uuid4(), {"job_ids": ["job"], "total": 1}
    )
    assert payload["status"] == "running"
    assert payload["completed"] == 0
    assert done is False


@pytest.mark.parametrize("status", [JobStatus.CANCELED, JobStatus.STOPPED])
def test_team_analysis_recognises_rq_cancelled_enums(monkeypatch, status):
    monkeypatch.setattr(llm, "_get_redis", lambda: Mock())
    monkeypatch.setattr(
        llm.Job, "fetch", Mock(return_value=SimpleNamespace(get_status=Mock(return_value=status)))
    )
    payload, done = llm._jobs_status(
        SimpleNamespace(session={}), uuid.uuid4(), {"job_ids": ["job"], "total": 1}
    )
    assert payload["status"] == "cancelled"
    assert done


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [RedisConnectionError, NoSuchJobError])
async def test_sync_reconciliation_distinguishes_missing_jobs_from_unavailable_queue(
    monkeypatch, error
):
    monkeypatch.setattr(sync, "_pool_get_redis", lambda: object())
    monkeypatch.setattr("rq.Worker.all", Mock(return_value=[]))
    monkeypatch.setattr("rq.job.Job.fetch", Mock(side_effect=error))
    row = BackgroundJob(
        job_type="sync",
        status="running",
        rq_job_id="job",
        enqueued_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [row]))
        ),
        flush=AsyncMock(),
    )
    count = await sync._reconcile_stale_jobs(db, [uuid.uuid4()])
    assert count == (0 if error is RedisConnectionError else 1)
    assert row.status == ("running" if error is RedisConnectionError else "failed")
    assert row.result_summary is None
