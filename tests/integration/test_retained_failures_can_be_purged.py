"""Cleanup uses real RQ records, results and retry transactions in Redis."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from redis import Redis
from rq import Queue
from rq.job import Job, JobStatus
from rq.registry import FailedJobRegistry
from rq.results import Result

from app.config import get_settings
from app.services import job_history as history_service

pytestmark = pytest.mark.integration


@pytest.fixture
def history(monkeypatch):
    connection = Redis.from_url(str(get_settings().redis_url))
    prefix = f"purge-test-{uuid.uuid4()}"
    registry = FailedJobRegistry(prefix, connection=connection)
    monkeypatch.setattr(history_service, "QUEUES", (prefix,))
    monkeypatch.setattr(history_service, "get_redis", lambda: connection)
    monkeypatch.setattr("app.observability.job_diagnostics.QUEUES", (prefix,))
    monkeypatch.setattr("app.observability.job_diagnostics.get_redis", lambda: connection)
    jobs = []

    def create(status=JobStatus.FAILED, age=48):
        job = Job.create(
            "app.workers.sync_job.full_sync",
            connection=connection,
            id=f"{prefix}-{len(jobs)}",
            origin=prefix,
            status=status,
        )
        job.created_at = datetime.now(UTC) - timedelta(days=10)
        job.ended_at = datetime.now(UTC) - timedelta(hours=age)
        job.save()
        # Include a stale failed-registry membership for retried/active jobs.
        registry.add(job, ttl=86400)
        Result.create(job, Result.Type.FAILED, ttl=86400, exc_string="ValueError: fixture")
        jobs.append(job)
        return job

    yield connection, registry, create
    # Never flush a shared database; delete only this test's own records.
    with connection.pipeline() as pipe:
        for job in jobs:
            pipe.delete(job.key, job.dependents_key, job.dependencies_key, Result.get_key(job.id))
        pipe.delete(registry.key)
        pipe.execute()
    connection.close()


def test_purge_covers_more_than_the_display_window_and_preserves_other_states(history):
    connection, registry, create = history
    old = [create() for _ in range(130)]
    recent = create(age=1)
    preserved = [
        create(status=status)
        for status in (
            JobStatus.QUEUED,
            JobStatus.STARTED,
            JobStatus.SCHEDULED,
            JobStatus.DEFERRED,
            JobStatus.FINISHED,
            JobStatus.CANCELED,
        )
    ]
    queue = Queue(registry.name, connection=connection)
    connection.rpush(queue.key, preserved[0].id)
    counter_key = "gitpulse:metrics:rq_job_failures_total"
    counter = connection.hgetall(counter_key)
    assert history_service._remove_rq_history(
        set(), datetime.now(UTC) - timedelta(hours=24), True
    ) == ({j.id for j in old}, set())
    assert all(not connection.exists(j.key, Result.get_key(j.id)) for j in old)
    assert all(connection.exists(j.key, Result.get_key(j.id)) == 2 for j in [recent, *preserved])
    assert registry.get_job_ids(cleanup=False) == [j.id for j in [recent, *preserved]]
    assert history_service._remove_rq_history(set(), None, True) == ({recent.id}, set())
    assert history_service._remove_rq_history(set(), None, True) == (set(), set())
    assert connection.hgetall(counter_key) == counter
    assert queue.job_ids == [preserved[0].id]
    connection.delete(queue.key)


def test_retry_between_read_and_delete_preserves_job_and_results(history, monkeypatch):
    connection, registry, create = history
    job = create()
    delete = Job.delete

    def retry_before_delete(self, *args, **kwargs):
        self.set_status(JobStatus.QUEUED)
        return delete(self, *args, **kwargs)

    monkeypatch.setattr(Job, "delete", retry_before_delete)
    assert history_service._remove_rq_history(set(), None, True) == (set(), set())
    assert Job.fetch(job.id, connection=connection).get_status() == JobStatus.QUEUED
    assert connection.exists(Result.get_key(job.id))
    assert registry.get_job_ids(cleanup=False) == [job.id]


def test_age_cleanup_keeps_undated_orphans_but_all_cleanup_removes_them(history):
    connection, registry, create = history
    job = create()
    connection.delete(job.key)
    assert history_service._remove_rq_history(
        set(), datetime.now(UTC) - timedelta(hours=24), True
    ) == (set(), set())
    assert history_service._remove_rq_history(set(), None, True) == ({job.id}, set())
    assert not registry.get_job_ids(cleanup=False)
    assert not connection.exists(Result.get_key(job.id))


@pytest.fixture
async def journal(history):
    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.models.background_job import BackgroundJob

    _, registry, _ = history
    engine = create_async_engine(str(get_settings().database_url))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            yield session
    finally:
        async with factory() as session:
            await session.execute(
                delete(BackgroundJob).where(BackgroundJob.rq_job_id.startswith(registry.name))
            )
            await session.commit()
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", [JobStatus.FAILED, JobStatus.FINISHED, JobStatus.CANCELED, JobStatus.STOPPED]
)
async def test_selected_cleanup_removes_both_stores_and_does_not_reappear(history, journal, status):
    import json
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.api.dashboard.admin.system import admin_delete_jobs, build_jobs_payload
    from app.models.background_job import BackgroundJob
    from app.observability import job_diagnostics

    connection, registry, create = history
    rq_job = create(status=status)
    row = BackgroundJob(job_type="sync", status="failed", rq_job_id=rq_job.id)
    journal.add(row)
    await journal.commit()
    request = SimpleNamespace(json=AsyncMock(return_value={"ids": [str(row.id)]}))
    response = await admin_delete_jobs(request, journal, None, None, None)
    assert json.loads(response.body) == {
        "status": "deleted",
        "database_deleted": 1,
        "redis_deleted": 1,
        "deleted": 1,
        "skipped": 0,
    }
    assert not connection.exists(rq_job.key, Result.get_key(rq_job.id))
    assert not registry.get_job_ids(cleanup=False)
    failures = job_diagnostics._read()
    payload = await build_jobs_payload(journal, None, None, 50, 0, failures=failures)
    assert all(r.get("rq_job_id") != rq_job.id for r in payload["jobs"])
    assert (
        json.loads((await admin_delete_jobs(request, journal, None, None, None)).body)["deleted"]
        == 0
    )


@pytest.mark.asyncio
async def test_cleanup_preserves_retried_jobs_even_when_sql_is_terminal(history, journal):
    from fastapi import HTTPException
    from sqlalchemy import select

    from app.models.background_job import BackgroundJob

    connection, _, create = history
    rq_job = create(status=JobStatus.QUEUED)
    row = BackgroundJob(job_type="sync", status="failed", rq_job_id=rq_job.id)
    journal.add(row)
    await journal.commit()
    result = await history_service.delete_job_history(journal, BackgroundJob.id == row.id)
    assert result == {"database_deleted": 0, "redis_deleted": 0, "deleted": 0, "skipped": 1}
    assert (
        await journal.scalar(select(BackgroundJob.id).where(BackgroundJob.id == row.id)) == row.id
    )
    assert connection.exists(rq_job.key, Result.get_key(rq_job.id)) == 2
    with pytest.raises(HTTPException) as error:
        await history_service.delete_job_history(
            journal, BackgroundJob.id == row.id, require_all=True
        )
    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_redis_outage_preserves_sql_and_retry_is_safe(history, journal, monkeypatch):
    from unittest.mock import Mock

    from fastapi import HTTPException
    from redis.exceptions import ConnectionError as RedisConnectionError
    from sqlalchemy import select

    from app.models.background_job import BackgroundJob

    connection, _, create = history
    rq_job = create()
    row = BackgroundJob(job_type="sync", status="failed", rq_job_id=rq_job.id)
    journal.add(row)
    await journal.commit()
    with monkeypatch.context() as offline:
        offline.setattr(history_service, "get_redis", Mock(side_effect=RedisConnectionError))
        with pytest.raises(HTTPException) as error:
            await history_service.delete_job_history(journal, BackgroundJob.id == row.id)
        assert error.value.status_code == 503
    assert (
        await journal.scalar(select(BackgroundJob.id).where(BackgroundJob.id == row.id)) == row.id
    )
    assert connection.exists(rq_job.key, Result.get_key(rq_job.id)) == 2
    result = await history_service.delete_job_history(journal, BackgroundJob.id == row.id)
    assert result["database_deleted"] == result["redis_deleted"] == 1
    await journal.commit()


@pytest.mark.asyncio
async def test_sql_rollback_keeps_journal_and_cleanup_is_retryable(history, journal):
    from sqlalchemy import select

    from app.models.background_job import BackgroundJob

    connection, _, create = history
    rq_job = create()
    row = BackgroundJob(job_type="sync", status="failed", rq_job_id=rq_job.id)
    journal.add(row)
    await journal.commit()
    row_id = row.id
    assert (await history_service.delete_job_history(journal, BackgroundJob.id == row_id))[
        "deleted"
    ] == 1
    await journal.rollback()
    assert (
        await journal.scalar(select(BackgroundJob.id).where(BackgroundJob.id == row_id)) == row_id
    )
    assert not connection.exists(rq_job.key, Result.get_key(rq_job.id))
    result = await history_service.delete_job_history(journal, BackgroundJob.id == row_id)
    assert result == {"database_deleted": 1, "redis_deleted": 0, "deleted": 1, "skipped": 0}
    await journal.commit()


@pytest.mark.asyncio
async def test_global_purge_preserves_rq_history_for_sql_jobs_outside_its_filter(history, journal):
    from app.models.background_job import BackgroundJob

    connection, _, create = history
    active, recent = create(), create()
    journal.add_all(
        [
            BackgroundJob(job_type="sync", status="running", rq_job_id=active.id),
            BackgroundJob(job_type="sync", status="failed", rq_job_id=recent.id),
        ]
    )
    await journal.commit()
    result = await history_service.delete_job_history(
        journal, BackgroundJob.id == uuid.uuid4(), include_failures=True
    )
    assert result["deleted"] == 0
    assert connection.exists(active.key, recent.key) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["course", "team", "project"])
@pytest.mark.parametrize("outcome", ["success", "offline", "active"])
async def test_permanent_domain_cleanup_is_scoped_and_cache_follows_commit(
    history, journal, monkeypatch, kind, outcome
):
    from unittest.mock import Mock

    from fastapi import HTTPException
    from redis.exceptions import ConnectionError as RedisConnectionError
    from sqlalchemy import delete, select
    from starlette.requests import Request

    from app.api.courses import permanently_delete_course
    from app.api.projects import delete_project_permanent
    from app.api.teams import delete_team_permanent
    from app.models.background_job import BackgroundJob
    from app.models.course import Course
    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.services import page_cache

    connection, registry, create = history
    course = Course(
        code=uuid.uuid4().hex[:12],
        name="Cleanup fixture",
        academic_year="2026/2027",
        is_active=False,
    )
    journal.add(course)
    await journal.flush()
    team = Team(course_id=course.id, name="Cleanup fixture")
    journal.add(team)
    await journal.flush()
    project = GitLabProject(
        team_id=team.id,
        gitlab_project_id=uuid.uuid4().int % (2**62),
        gitlab_project_path=registry.name,
    )
    journal.add(project)
    await journal.flush()
    course_id, team_id, project_id = course.id, team.id, project.id
    target = create(status=JobStatus.QUEUED if outcome == "active" else JobStatus.FAILED)
    unrelated = create()
    row = BackgroundJob(
        job_type="sync", status="failed", project_id=project_id, rq_job_id=target.id
    )
    journal.add(row)
    await journal.commit()
    row_id = row.id
    monkeypatch.setattr(page_cache, "get_redis", lambda: connection)
    cache_keys = [("course", course_id), ("team", team_id), ("project", project_id)]
    for cache_kind, scope_id in cache_keys:
        page_cache.set_cached(cache_kind, scope_id, "fixture", "cached body")
    committed = []
    invalidate = page_cache.invalidate_cascade

    def invalidate_after_commit(**kwargs):
        committed.append(not journal.in_transaction())
        return invalidate(**kwargs)

    monkeypatch.setattr(page_cache, "invalidate_cascade", invalidate_after_commit)
    request = Request({"type": "http", "headers": [], "method": "DELETE", "path": "/fixture"})

    async def remove():
        if kind == "course":
            await permanently_delete_course(course_id, request, journal, "api_token")
        elif kind == "team":
            await delete_team_permanent(team_id, journal, "api_token", request, get_settings())
        else:
            await delete_project_permanent(project_id, request, journal, "api_token")

    try:
        if outcome == "success":
            await remove()
            assert (
                await journal.scalar(select(BackgroundJob.id).where(BackgroundJob.id == row_id))
                is None
            )
            assert not connection.exists(target.key, Result.get_key(target.id))
            assert all(page_cache.get_cached(k, i, "fixture") is None for k, i in cache_keys)
            assert committed
            assert all(committed)
        else:
            with monkeypatch.context() as unavailable:
                if outcome == "offline":
                    unavailable.setattr(
                        history_service, "get_redis", Mock(side_effect=RedisConnectionError)
                    )
                with pytest.raises(HTTPException) as error:
                    await remove()
                assert error.value.status_code == (503 if outcome == "offline" else 409)
            await journal.rollback()
            assert (
                await journal.scalar(select(BackgroundJob.id).where(BackgroundJob.id == row_id))
                == row_id
            )
            assert connection.exists(target.key, Result.get_key(target.id)) == 2
            assert all(
                page_cache.get_cached(k, i, "fixture") == "cached body" for k, i in cache_keys
            )
        assert connection.exists(unrelated.key, Result.get_key(unrelated.id)) == 2
    finally:
        await journal.rollback()
        await journal.execute(delete(Course).where(Course.id == course_id))
        await journal.commit()
        for cache_kind, scope_id in cache_keys:
            page_cache.invalidate(cache_kind, scope_id)
