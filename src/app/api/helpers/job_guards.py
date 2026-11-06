"""Shared guards for API actions that must not race background jobs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob

ACTIVE_MUTATING_JOB_TYPES = ("sync", "run_checks")
ACTIVE_MUTATING_JOB_STATUSES = ("enqueued", "started", "running")
ACTIVE_MUTATING_JOB_LOOKBACK = timedelta(hours=2)


def advisory_lock_key(entity_id: uuid.UUID) -> int:
    """Map a UUID into PostgreSQL's signed 32-bit advisory-lock key space."""
    return int(entity_id.int % (2**31))


async def lock_team_mutation_scope(db: AsyncSession, team_id: uuid.UUID) -> None:
    """Serialize team-scoped mutating actions with sync/check enqueues."""
    bind = db.get_bind()
    if bind is not None and bind.dialect.name != "postgresql":
        return
    await db.execute(select(func.pg_advisory_xact_lock(advisory_lock_key(team_id))))


async def lock_project_mutation_scope(db: AsyncSession, project_id: uuid.UUID) -> None:
    """Serialize project-scoped mutating actions with project sync enqueues."""
    bind = db.get_bind()
    if bind is not None and bind.dialect.name != "postgresql":
        return
    await db.execute(select(func.pg_advisory_xact_lock(advisory_lock_key(project_id))))


async def find_active_team_mutation_job(
    db: AsyncSession,
    team_id: uuid.UUID,
) -> BackgroundJob | None:
    """Return an active sync/run-checks job that would race a team mutation."""
    cutoff = datetime.now(UTC) - ACTIVE_MUTATING_JOB_LOOKBACK
    stmt = (
        select(BackgroundJob)
        .where(
            BackgroundJob.team_id == team_id,
            BackgroundJob.job_type.in_(ACTIVE_MUTATING_JOB_TYPES),
            BackgroundJob.status.in_(ACTIVE_MUTATING_JOB_STATUSES),
            BackgroundJob.enqueued_at >= cutoff,
        )
        .order_by(BackgroundJob.enqueued_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


def active_job_conflict_fields(job: BackgroundJob) -> dict[str, str]:
    """Expose active-job metadata in a stable 409 payload."""
    return {
        "job_id": str(job.id),
        "job_type": job.job_type,
        "job_status": job.status,
    }


def active_job_conflict_message(action: str, job: BackgroundJob) -> str:
    """Return a user-facing conflict message for destructive API actions."""
    return (
        f"Cannot {action} while {job.job_type} is {job.status}. "
        "Wait for the active process to finish, then try again."
    )


__all__ = [
    "ACTIVE_MUTATING_JOB_STATUSES",
    "ACTIVE_MUTATING_JOB_TYPES",
    "active_job_conflict_fields",
    "active_job_conflict_message",
    "advisory_lock_key",
    "find_active_team_mutation_job",
    "lock_project_mutation_scope",
    "lock_team_mutation_scope",
]
