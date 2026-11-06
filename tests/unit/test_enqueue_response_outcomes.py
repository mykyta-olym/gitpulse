"""Queue acknowledgements must describe the persisted outcome, including failure."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from starlette.requests import Request

from app.api import sync
from app.models.team import Team


@pytest.mark.parametrize("action", ["group-sync", "project-sync", "group-checks"])
@pytest.mark.parametrize("outcome", ["accepted", "unavailable", "exception"])
async def test_enqueue_response_matches_persisted_job(monkeypatch, action, outcome):
    team = SimpleNamespace(id=uuid4(), course_id=uuid4(), name="Group A", is_active=True)
    project = SimpleNamespace(
        id=uuid4(),
        team_id=team.id,
        is_active=True,
        gitlab_project_name="Project A",
        gitlab_project_path="group/project-a",
    )
    jobs = []

    async def flush():
        for job in jobs:
            if job.id is None:
                job.id = uuid4()
            if job.status is None:
                job.status = "enqueued"

    db = MagicMock()
    db.get = AsyncMock(side_effect=lambda model, _id: team if model is Team else project)
    db.add = Mock(side_effect=jobs.append)
    db.flush = AsyncMock(side_effect=flush)
    db.commit = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.execute.return_value.scalar_one_or_none.return_value = None
    for name, value in [
        ("_has_active_rq_workers", True),
        ("require_gitlab_ready", None),
        ("_reconcile_stale_jobs", 0),
        ("_lock_team_job_scope", None),
        ("_recently_synced_team_ids", set()),
        ("_get_active_run_checks_job", None),
        ("_get_active_sync_job", None),
    ]:
        monkeypatch.setattr(sync, name, AsyncMock(return_value=value))
    monkeypatch.setattr(
        "app.api.dashboard._access.can_manage_via_request", AsyncMock(return_value=True)
    )
    monkeypatch.setattr("app.services.courses.ensure_course_active", AsyncMock())
    audit = AsyncMock()
    monkeypatch.setattr(sync, "write_audit", audit)
    monkeypatch.setattr(sync, "get_actor", lambda *_args, **_kwargs: "admin")
    enqueue = Mock(return_value="rq-123" if outcome == "accepted" else None)
    if outcome == "exception":
        enqueue.side_effect = ConnectionError("Queue unavailable")
    if action == "group-sync":
        monkeypatch.setattr(sync, "enqueue_sync_job", enqueue)
        result = await sync.trigger_sync(team.id, db, "admin", Request({"type": "http"}))
    elif action == "project-sync":
        monkeypatch.setattr("app.services.events.enqueue_project_sync_job", enqueue)
        result = await sync.trigger_project_sync(project.id, db, "admin", Request({"type": "http"}))
    else:
        monkeypatch.setattr("app.services.events.enqueue_run_checks_job", enqueue)
        result = await sync.run_selected_checks(
            team.id, db, "admin", Request({"type": "http"}), check_codes=["R01"]
        )
    (job,) = jobs
    assert result.job_id == job.id
    assert result.status == job.status == ("enqueued" if outcome == "accepted" else "failed")
    if outcome == "accepted":
        assert "enqueued" in result.message
        assert job.rq_job_id == "rq-123"
    else:
        assert result.message == job.error_message
        assert "Failed to enqueue" in result.message
        assert "enqueued" not in result.message
    assert audit.await_args.kwargs["detail"]["status"] == result.status
    db.commit.assert_awaited_once()
    enqueue.assert_called_once()
