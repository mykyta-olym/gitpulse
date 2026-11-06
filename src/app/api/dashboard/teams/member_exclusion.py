"""Member scoring-exclusion helpers shared by dashboard routes."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.helpers.job_guards import (
    ACTIVE_MUTATING_JOB_STATUSES,
    ACTIVE_MUTATING_JOB_TYPES,
    find_active_team_mutation_job,
    lock_team_mutation_scope,
)
from app.models.background_job import BackgroundJob
from app.models.project import GitLabProject
from app.services.page_cache import invalidate_many

ACTIVE_SCORING_JOB_TYPES = ACTIVE_MUTATING_JOB_TYPES
ACTIVE_JOB_STATUSES = ACTIVE_MUTATING_JOB_STATUSES


async def lock_member_scoring_scope(db: AsyncSession, team_id: uuid.UUID) -> None:
    """Serialize scoring toggles with sync/check enqueue operations for one group."""
    await lock_team_mutation_scope(db, team_id)


def member_base_category(member: Any) -> str:
    """Return the non-excluded filter category for a team member row."""
    if getattr(member, "is_teacher", False):
        return "teacher"
    if getattr(member, "is_mentor", False):
        return "mentor"
    if (getattr(member, "membership_source", "") or "") == "inherited":
        return "inherited"
    return "direct"


def member_visible_category(member: Any) -> str:
    """Return the active row filter category for a member."""
    if getattr(member, "excluded_from_scoring", False):
        return "excluded"
    return member_base_category(member)


def member_can_toggle_scoring(member: Any) -> bool:
    """Teachers and mentors are already excluded by role, so the toggle is meaningless."""
    return not getattr(member, "is_teacher", False) and not getattr(member, "is_mentor", False)


async def find_active_scoring_job(
    db: AsyncSession,
    team_id: uuid.UUID,
) -> BackgroundJob | None:
    """Return an active sync/run-checks job that would race a scoring toggle."""
    return await find_active_team_mutation_job(db, team_id)


async def invalidate_member_scoring_views(
    db: AsyncSession,
    *,
    team_id: uuid.UUID,
    course_id: uuid.UUID,
    student_ids: Iterable[uuid.UUID],
) -> int:
    """Invalidate every cached dashboard fragment affected by a member scoring change."""
    project_stmt = select(GitLabProject.id).where(GitLabProject.team_id == team_id)
    project_ids = [pid for (pid,) in (await db.execute(project_stmt)).all() if pid is not None]

    pairs: list[tuple[str, uuid.UUID]] = [
        ("team", team_id),
        ("course", course_id),
        ("course-analytics", course_id),
        ("course-activity", course_id),
    ]
    pairs.extend(("project", pid) for pid in project_ids)
    pairs.extend(("student", sid) for sid in student_ids)
    return invalidate_many(pairs)


async def recompute_after_member_scoring_toggle(
    db: AsyncSession,
    *,
    team_id: uuid.UUID,
) -> None:
    """Recompute team metrics so exclusion changes affect aggregate cards immediately."""
    from app.compliance.engine import compute_team_metrics

    await compute_team_metrics(db, str(team_id))


__all__ = [
    "ACTIVE_JOB_STATUSES",
    "ACTIVE_SCORING_JOB_TYPES",
    "find_active_scoring_job",
    "invalidate_member_scoring_views",
    "lock_member_scoring_scope",
    "member_base_category",
    "member_can_toggle_scoring",
    "member_visible_category",
    "recompute_after_member_scoring_toggle",
]
