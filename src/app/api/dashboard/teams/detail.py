"""What the group page reads about its projects' commits and analyses."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from app.dependencies import DbSession
from app.models.commit import Commit
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.student import Student
from app.utils.constants import PAGE_SIZE_REPORTS


def _commit_window(course: Course | None) -> list[Any]:
    """Commits of the current semester only."""
    from app.utils.semester import semester_floor_utc

    floor: datetime | None = semester_floor_utc(course.settings if course else None)
    return [Commit.committed_at >= floor] if floor is not None else []


async def llm_analyses(db: DbSession, projects: list[GitLabProject]) -> list[Any]:
    """The latest AI analyses of the merge requests in the group's projects."""
    if not projects:
        return []
    from app.models.llm_log import LLMAnalysisLog

    stmt = (
        select(LLMAnalysisLog)
        .where(LLMAnalysisLog.project_id.in_([p.id for p in projects]))
        .order_by(LLMAnalysisLog.analysis_timestamp.desc())
        .limit(PAGE_SIZE_REPORTS)
    )
    return list((await db.execute(stmt)).scalars().all())


async def template_only_projects(
    db: DbSession,
    course: Course | None,
    projects: list[GitLabProject],
    students: list[Student],
) -> set[uuid.UUID]:
    """Projects with commits this semester but none from the group's students.

    Both sides are restricted to the semester. Otherwise a project that only
    ever received pre-semester template commits would be flagged template-only
    every term forever, even after current students start contributing (the
    legacy template commits would keep it on the "has commits" side).
    """
    if not projects:
        return set()
    project_ids = [p.id for p in projects]
    window = _commit_window(course)

    has_commits_stmt = (
        select(Commit.project_id).where(Commit.project_id.in_(project_ids), *window).distinct()
    )
    with_commits = {r[0] for r in (await db.execute(has_commits_stmt)).all()}

    # A commit is a student's when its author resolved to one (author_id), or
    # by the raw GitLab id of a known student.
    gitlab_ids = {s.gitlab_user_id for s in students if s.gitlab_user_id is not None}
    by_student = (
        (Commit.author_id.is_not(None)) | (Commit.author_gitlab_id.in_(gitlab_ids))
        if gitlab_ids
        else Commit.author_id.is_not(None)
    )
    has_student_stmt = (
        select(Commit.project_id)
        .where(Commit.project_id.in_(project_ids), by_student, *window)
        .distinct()
    )
    with_students = {r[0] for r in (await db.execute(has_student_stmt)).all()}
    return with_commits - with_students


async def student_primary_projects(
    db: DbSession,
    course: Course | None,
    projects: list[GitLabProject],
    students: list[Student],
) -> dict[uuid.UUID, uuid.UUID]:
    """Each student's main project - the one they committed to most this
    semester - for the way back from their profile."""
    if not projects:
        return {}
    if len(projects) == 1:
        # Single project - all members belong to it
        return {s.id: projects[0].id for s in students}
    stmt = (
        select(Commit.author_id, Commit.project_id, func.count().label("cnt"))
        .where(
            Commit.project_id.in_([p.id for p in projects]),
            Commit.author_id.is_not(None),
            *_commit_window(course),
        )
        .group_by(Commit.author_id, Commit.project_id)
        .order_by(func.count().desc())
    )
    primary: dict[uuid.UUID, uuid.UUID] = {}
    for author_id, project_id, _cnt in (await db.execute(stmt)).all():
        if author_id and author_id not in primary:
            primary[author_id] = project_id
    return primary
