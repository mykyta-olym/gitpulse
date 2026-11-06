"""RQ history is bounded, role restricted, and contains no job payloads."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.observability import job_diagnostics as diagnostics


def job(**changes):
    values = {
        "id": "f93aa78e-05f9-41a0-92ae-af07110ada18",
        "func_name": "app.workers.sync_job.full_sync",
        "origin": "default",
        "_exc_info": "ValueError: password=secret-student-value\n",
        "latest_result": lambda: None,
        "ended_at": datetime(2026, 7, 1, tzinfo=UTC),
        "last_heartbeat": None,
        "created_at": datetime(2026, 4, 1, tzinfo=UTC),
        "get_status": lambda **kw: "failed",
    }
    values.update(changes)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("trace", "expected"),
    [
        (
            "AttributeError: module 'app.workers.sweep' has no attribute 'periodic_enrich_all'",
            "Retired scheduled job",
        ),
        ("Moved to FailedJobRegistry, due to AbandonedJobError", "Worker interrupted"),
        ("rq.timeouts.JobTimeoutException: exceeded 300s", "Job timed out"),
        (
            "httpx.HTTPStatusError: Client error '401 Unauthorized' for url 'https://private'",
            "GitLab access denied",
        ),
        ("httpx.HTTPStatusError: Client error '403 Forbidden'", "GitLab access denied"),
        ("httpx.HTTPStatusError: Client error '404 Not Found'", "GitLab resource unavailable"),
        ("httpx.HTTPStatusError: Server error '502 Bad Gateway'", "GitLab request failed"),
        (
            "asyncpg.exceptions.UndefinedColumnError: column abc is missing",
            "Database schema mismatch",
        ),
        ("ValueError: arbitrary private data", "Job execution failed"),
    ],
)
def test_causes_and_remediation_from_real_exception_formats(trace, expected):
    row = diagnostics._row(
        job(_exc_info=trace, func_name="app.workers.sweep.run_tracked_scheduled")
    )
    assert row["cause"] == expected
    assert row["hint"]


def test_reference_contains_identifiers_and_app_frames_without_payload_or_source_lines():
    trace = """Traceback (most recent call last):
  File "/app/src/app/workers/sync_job.py", line 100, in full_sync
    password = 'hidden-password'
  File "/venv/site-packages/httpx/client.py", line 22, in send
    Authorization: Bearer hidden-token
httpx.HTTPStatusError: Client error '401 Unauthorized' for url 'https://user:pw@host/?token=hidden-token'
[parameters: ('private-student-name',)]
"""
    row = diagnostics._row(job(_exc_info=trace))
    assert "src/app/workers/sync_job.py:100 (full_sync)" in row["reference"]
    assert "httpx.HTTPStatusError" in row["reference"]
    assert row["id"] in row["reference"]
    for private in (
        "hidden-password",
        "hidden-token",
        "private-student-name",
        "user:pw",
        "httpx/client",
    ):
        assert private not in str(row)


def test_metadata_is_not_trusted_and_interrupted_jobs_use_last_activity():
    heartbeat = datetime(2026, 4, 16, tzinfo=UTC)
    row = diagnostics._row(
        job(
            func_name="https://user:secret@host",
            id="<script>",
            origin="secret",
            ended_at=None,
            last_heartbeat=heartbeat,
        )
    )
    assert row["function"] == "Unknown task"
    assert row["id"] == row["queue"] == "-"
    assert row["observed_at"] == heartbeat
    assert "secret" not in str(row)


def test_current_rq_result_is_used_before_the_registry_fallback():
    row = diagnostics._row(
        job(latest_result=lambda: SimpleNamespace(exc_string="TimeoutError: private-url"))
    )
    assert row["cause"] == "Job timed out"
    assert "private-url" not in str(row)


def test_reads_are_bounded_missing_and_retried_jobs_are_skipped_and_newest_is_first(monkeypatch):
    connection = object()
    monkeypatch.setattr(diagnostics, "get_redis", lambda: connection)
    calls = []

    class Registry:
        count = 2000

        def __init__(self, name, **kwargs):
            self.name = name
            assert kwargs["connection"] is connection

        def get_job_ids(self, **kwargs):
            calls.append(kwargs)
            return [self.name]

    def fetch(ids, **kwargs):
        index = diagnostics.QUEUES.index(ids[0])
        return [
            None,
            job(get_status=lambda **kw: "finished"),
            job(ended_at=datetime(2026, 7, 1, tzinfo=UTC) + timedelta(days=index)),
        ]

    monkeypatch.setattr(diagnostics, "FailedJobRegistry", Registry)
    monkeypatch.setattr(diagnostics.Job, "fetch_many", fetch)
    result = diagnostics._read()
    assert result.total == 6000
    assert len(result.rows) == 3
    assert result.rows[0]["observed_at"].day == 3
    assert calls == [{"start": -100, "cleanup": False}] * 3


@pytest.mark.asyncio
async def test_unavailable_history_is_not_reported_as_no_failures(monkeypatch):
    def unavailable():
        raise ConnectionError("private redis endpoint")

    monkeypatch.setattr(diagnostics, "_read", unavailable)
    result = await diagnostics.snapshot()
    assert not result.available
    assert not result.rows


@pytest.mark.asyncio
async def test_history_deadline_does_not_hold_the_status_page(monkeypatch):
    async def deadline(awaitable, **kwargs):
        awaitable.close()
        assert kwargs["timeout"] == 2
        raise TimeoutError

    monkeypatch.setattr(diagnostics.asyncio, "wait_for", deadline)
    assert not (await diagnostics.snapshot()).available


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["student", "teacher", "admin"])
async def test_bookmark_redirect_never_reads_queue_history(monkeypatch, role):
    from app.api.dashboard.home.routes import router
    from app.dependencies import require_dashboard_auth

    read = AsyncMock()
    monkeypatch.setattr(diagnostics, "snapshot", read)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_dashboard_auth] = lambda: {"role": role, "user": "test"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/status")
    assert response.status_code == 303
    read.assert_not_awaited()
    assert "secret-student-value" not in response.text


def test_missing_history_and_available_history_have_different_shared_states():
    from app.main import templates

    template = templates.env.get_template("partials/admin/_system_failure_info.html")
    for available in (True, False):
        html = template.render(
            t=lambda text: text, failure_history={"available": available, "total": 0}
        )
        assert ("Retained failed jobs" in html) == available
        assert ("Failure history is unavailable. Refresh to try again." in html) != available
