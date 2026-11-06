"""Admin background-job presentation contracts."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.api.dashboard.admin.system import (
    _background_job_scope,
    _job_op_row,
)


def _job(**overrides: object) -> SimpleNamespace:
    values = {
        "job_type": "sync",
        "project_id": None,
        "course_id": None,
        "team_id": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_sync_scope_prefers_the_most_specific_persisted_context() -> None:
    assert _background_job_scope(_job(project_id="p", course_id="c", team_id="t")) == "project"
    assert _background_job_scope(_job(course_id="c", team_id="t")) == "course"
    assert _background_job_scope(_job(team_id="t")) == "group"


def test_non_sync_and_unscoped_jobs_have_no_sync_scope() -> None:
    assert _background_job_scope(_job(job_type="run_checks", team_id="t")) is None
    assert _background_job_scope(_job()) is None


def test_job_row_resolves_context_and_does_not_expose_internal_sort_state() -> None:
    job = _job(
        id=uuid.uuid4(),
        course_id=uuid.uuid4(),
        rq_job_id="rq-1",
        status="failed",
        result_summary=None,
        error_message="GitLab unavailable",
        enqueued_at=datetime.now(UTC),
        started_at=None,
        completed_at=None,
        duration_ms=None,
    )
    row = _job_op_row(job, {}, {job.course_id: "DEVOPS"})
    assert row["course_name"] == "DEVOPS"
    assert row["scope"] == "course"
    assert row["error_message"] == "GitLab unavailable"
    assert "_sort" not in row
