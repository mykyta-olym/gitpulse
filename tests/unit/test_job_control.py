"""Cancellation helpers shared by every "stop this job" path.

`is_terminal_job_status` is the guard that stops a finished job being
reconciled back to active by a late status message, and `_cancel_rq_jobs_sync`
must survive a worker that has already gone away - otherwise cancelling one
stale job aborts the whole batch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.job_control import (
    ACTIVE_JOB_STATUSES,
    TERMINAL_JOB_STATUSES,
    _duration_ms,
    is_terminal_job_status,
)


class TestTerminalStatus:
    @pytest.mark.parametrize("status", sorted(TERMINAL_JOB_STATUSES))
    def test_terminal_statuses_are_recognised(self, status: str) -> None:
        assert is_terminal_job_status(status) is True

    @pytest.mark.parametrize("status", ACTIVE_JOB_STATUSES)
    def test_active_statuses_are_not_terminal(self, status: str) -> None:
        assert is_terminal_job_status(status) is False

    def test_case_is_ignored(self) -> None:
        """Statuses arrive from RQ, the DB and SSE payloads with mixed casing."""
        assert is_terminal_job_status("COMPLETED") is True
        assert is_terminal_job_status("Cancelled") is True

    @pytest.mark.parametrize("status", [None, "", "   ", "unknown"])
    def test_unknown_or_missing_is_not_terminal(self, status: str | None) -> None:
        """Fail open: an unrecognised status must stay reconcilable."""
        assert is_terminal_job_status(status) is False

    def test_the_two_sets_do_not_overlap(self) -> None:
        assert not TERMINAL_JOB_STATUSES & set(ACTIVE_JOB_STATUSES)


class TestDurationMs:
    def test_returns_none_when_the_job_never_started(self) -> None:
        assert _duration_ms(None, datetime.now(UTC)) is None

    def test_computes_elapsed_milliseconds(self) -> None:
        start = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)

        assert _duration_ms(start, start + timedelta(seconds=1.5)) == 1500

    def test_a_clock_going_backwards_clamps_to_zero(self) -> None:
        """Never report a negative duration if timestamps arrive out of order."""
        end = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)

        assert _duration_ms(end + timedelta(seconds=5), end) == 0


class TestRqCancellation:
    @pytest.mark.parametrize(
        "status",
        ["started", "queued", "scheduled", "deferred", "finished", "failed", "canceled", "stopped"],
    )
    def test_rq_enums_use_stop_for_running_jobs_and_preserve_terminal_jobs(
        self, monkeypatch, status
    ):
        from types import SimpleNamespace
        from unittest.mock import Mock

        from rq.job import JobStatus

        import app.services.job_control as jc

        job = SimpleNamespace(get_status=Mock(return_value=JobStatus(status)), cancel=Mock())
        stop = Mock()
        monkeypatch.setattr("app.redis_pool.get_redis", lambda: object())
        monkeypatch.setattr(jc.RQJob, "fetch", Mock(return_value=job))
        monkeypatch.setattr(jc, "send_stop_job_command", stop)
        jc._cancel_rq_jobs_sync(["job-id"])
        assert stop.call_count == (1 if status == "started" else 0)
        assert job.cancel.call_count == (1 if status in {"queued", "scheduled", "deferred"} else 0)

    @pytest.mark.asyncio
    async def test_queue_outage_does_not_mark_sql_job_cancelled(self, monkeypatch):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock, Mock

        from fastapi import HTTPException
        from redis.exceptions import ConnectionError as RedisConnectionError

        from app.models.background_job import BackgroundJob
        from app.services.job_control import cancel_background_jobs

        monkeypatch.setattr("app.redis_pool.get_redis", Mock(side_effect=RedisConnectionError))
        row = BackgroundJob(job_type="sync", status="running", rq_job_id="job-id")
        db = SimpleNamespace(flush=AsyncMock())
        with pytest.raises(HTTPException) as error:
            await cancel_background_jobs(db, [row])
        assert error.value.status_code == 503
        assert row.status == "running"
        assert row.completed_at is None
        db.flush.assert_not_called()

    def test_a_missing_rq_job_does_not_abort_the_batch(self, monkeypatch) -> None:
        """A worker that already exited must not stop the remaining cancels."""
        import app.services.job_control as jc

        seen: list[str] = []

        class _Job:
            @staticmethod
            def fetch(rq_id: str, connection: object) -> object:
                seen.append(rq_id)
                from rq.exceptions import NoSuchJobError

                raise NoSuchJobError("no such job")

        import app.redis_pool as pool

        monkeypatch.setattr(pool, "get_redis", lambda: object())
        monkeypatch.setattr(jc, "RQJob", _Job)
        monkeypatch.setattr(jc, "send_stop_job_command", lambda *a, **k: None)

        jc._cancel_rq_jobs_sync(["a", "b", "c"])

        assert seen == ["a", "b", "c"], "one missing job stopped the batch"
