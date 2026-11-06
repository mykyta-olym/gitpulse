"""The course Activity Monitor's numbers - read once, for the page and its refresh.

The refresh had its own copy of every query, and they had drifted: it took each
group's ``latest_status`` from the newest pipeline of any state, where the page
deliberately skips in-flight ones (a running pipeline that never reports back,
common without pipeline webhooks, would otherwise mask the real result for
good) - so the badge the page drew turned "running" on the first refresh.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import case, func, select

from app.dependencies import DbSession
from app.models.course import Course
from app.models.merge_request import MergeRequest
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.models.team import Team
from app.utils.constants import PAGE_SIZE_FEED

_IN_FLIGHT = ("running", "pending", "created")


@dataclass
class CourseActivity:
    """Pipeline health and MR activity of a course's groups."""

    projects: list[GitLabProject]
    pipeline_stats: dict[str, int]
    # One row per group, in the teams' order: the group, its project count,
    # pipeline totals and health, latest finished status and recent MR count.
    rows: list[dict[str, Any]]
    mr_cutoff: datetime


def _semester_floor(course: Course) -> datetime | None:
    from app.utils.semester import semester_floor_utc

    return semester_floor_utc(course.settings if course else None)


async def course_activity(db: DbSession, course: Course, teams: list[Team]) -> CourseActivity:
    """The numbers both the page and its refresh show, for these groups."""
    team_ids = [t.id for t in teams]
    projects: list[GitLabProject] = []
    if team_ids:
        # Live projects only: soft-deleted (unlinked) projects and GitLab
        # "deletion_scheduled" tombstones must not inflate project_count or
        # pipeline health totals - those headline numbers describe the
        # working course, so an unlinked project drops out immediately.
        p_stmt = (
            select(GitLabProject)
            .where(
                GitLabProject.team_id.in_(team_ids),
                GitLabProject.is_active.is_(True),
                ~GitLabProject.gitlab_project_path.contains("deletion_scheduled", autoescape=True),
            )
            .order_by(GitLabProject.team_id, GitLabProject.gitlab_project_name)
        )
        projects = list((await db.execute(p_stmt)).scalars().all())

    # MRs of the last 30 days, but never from before the semester started:
    # without the clamp a course whose semester began <30 days ago would still
    # surface MRs from old template / fork projects.
    floor = _semester_floor(course)
    cutoff = datetime.now(UTC) - timedelta(days=30)
    if floor is not None and floor > cutoff:
        cutoff = floor

    pipeline_stats = {"passed": 0, "failed": 0, "running": 0, "pending": 0, "other": 0}
    health: dict[uuid.UUID, dict[str, Any]] = {
        t.id: {"passed": 0, "failed": 0, "total": 0, "latest_status": None} for t in teams
    }
    mr_counts: dict[uuid.UUID, int] = {t.id: 0 for t in teams}
    if projects:
        await _pipeline_health(db, projects, floor, pipeline_stats, health)
        await _count_mrs(db, projects, cutoff, mr_counts)

    per_team: dict[uuid.UUID, int] = defaultdict(int)
    for p in projects:
        per_team[p.team_id] += 1
    rows = []
    for team in teams:
        h = health.get(team.id, {})
        total, passed = h.get("total", 0), h.get("passed", 0)
        rows.append(
            {
                "team": team,
                "project_count": per_team[team.id],
                "pipeline_total": total,
                "pipeline_passed": passed,
                "pipeline_failed": h.get("failed", 0),
                "health_pct": round((passed / total * 100) if total > 0 else 0),
                "latest_status": h.get("latest_status"),
                "mr_count": mr_counts.get(team.id, 0),
            }
        )
    return CourseActivity(projects, pipeline_stats, rows, cutoff)


async def _pipeline_health(
    db: DbSession,
    projects: list[GitLabProject],
    floor: datetime | None,
    stats: dict[str, int],
    health: dict[uuid.UUID, dict[str, Any]],
) -> None:
    """Fill the course's latest-pipeline stats and each group's health.

    Only runs from the current semester count: a legacy success/failed pipeline
    from last term would otherwise keep distorting group health forever.
    """
    project_ids = [p.id for p in projects]
    team_of = {p.id: p.team_id for p in projects}
    window: list[Any] = [Pipeline.created_at >= floor] if floor is not None else []

    # Per-group totals via SQL GROUP BY
    agg_stmt = (
        select(
            GitLabProject.team_id,
            func.count().label("total"),
            func.count(case((Pipeline.status == "success", 1))).label("passed"),
            func.count(case((Pipeline.status == "failed", 1))).label("failed"),
        )
        .join(Pipeline, Pipeline.project_id == GitLabProject.id)
        .where(GitLabProject.id.in_(project_ids), *window)
        .group_by(GitLabProject.team_id)
    )
    for row in (await db.execute(agg_stmt)).all():
        if row.team_id in health:
            health[row.team_id].update(total=row.total, passed=row.passed, failed=row.failed)

    # The latest pipeline per project, of any state, for the course stats.
    for _project_id, status in await _latest_per_project(db, project_ids, window):
        status = status.lower() if status else "other"
        if status == "success":
            stats["passed"] += 1
        elif status == "failed":
            stats["failed"] += 1
        elif status == "running":
            stats["running"] += 1
        elif status in ("pending", "created"):
            stats["pending"] += 1
        else:
            stats["other"] += 1

    # The latest FINISHED pipeline per project for the group's badge: a stale
    # running pipeline on GitLab - common when pipeline webhooks aren't
    # configured and a manual re-sync re-fetches the same status - must not
    # permanently mask the real health signal.
    finished = [Pipeline.status.notin_(_IN_FLIGHT), *window]
    for project_id, status in await _latest_per_project(db, project_ids, finished):
        team_id = team_of.get(project_id)
        if team_id and not health[team_id]["latest_status"]:
            health[team_id]["latest_status"] = status.lower() if status else "other"


async def _latest_per_project(
    db: DbSession,
    project_ids: list[uuid.UUID],
    where: list[Any],
) -> list[tuple[uuid.UUID, str | None]]:
    rn = (
        func.row_number()
        .over(
            partition_by=Pipeline.project_id,
            order_by=(Pipeline.created_at.desc().nulls_last(), Pipeline.gitlab_pipeline_id.desc()),
        )
        .label("rn")
    )
    sub = (
        select(
            Pipeline.project_id,
            Pipeline.status,
            Pipeline.created_at,
            Pipeline.gitlab_pipeline_id,
            rn,
        )
        .where(Pipeline.project_id.in_(project_ids), *where)
        .subquery()
    )
    result = await db.execute(
        select(sub.c.project_id, sub.c.status)
        .where(sub.c.rn == 1)
        .order_by(sub.c.created_at.desc().nulls_last(), sub.c.gitlab_pipeline_id.desc())
    )
    return [(r.project_id, r.status) for r in result.all()]


async def _count_mrs(
    db: DbSession,
    projects: list[GitLabProject],
    cutoff: datetime,
    counts: dict[uuid.UUID, int],
) -> None:
    """Each group's merge requests since ``cutoff``."""
    team_of = {p.id: p.team_id for p in projects}
    stmt = (
        select(MergeRequest.project_id, func.count().label("cnt"))
        .where(
            MergeRequest.project_id.in_([p.id for p in projects]),
            MergeRequest.created_at >= cutoff,
        )
        .group_by(MergeRequest.project_id)
    )
    for row in (await db.execute(stmt)).all():
        tid = team_of.get(row.project_id)
        if tid:
            counts[tid] += row.cnt


async def recent_mrs(
    db: DbSession,
    projects: list[GitLabProject],
    cutoff: datetime,
) -> list[dict[str, Any]]:
    """The newest merge requests since ``cutoff`` - or, when there are none,
    the newest at all - as the page's Recent Activity list."""
    if not projects:
        return []
    by_id = {p.id: p for p in projects}
    cols = select(
        MergeRequest.project_id,
        MergeRequest.title,
        MergeRequest.gitlab_iid,
        MergeRequest.state,
        MergeRequest.created_at,
        MergeRequest.merged_at,
    ).where(MergeRequest.project_id.in_(list(by_id)))
    newest = MergeRequest.created_at.desc()
    rows = (
        await db.execute(
            cols.where(MergeRequest.created_at >= cutoff).order_by(newest).limit(PAGE_SIZE_FEED)
        )
    ).all()
    if not rows:
        rows = (await db.execute(cols.order_by(newest).limit(PAGE_SIZE_FEED))).all()
    out = []
    for r in rows:
        proj = by_id.get(r.project_id)
        out.append(
            {
                "type": "mr",
                "title": r.title,
                "iid": r.gitlab_iid,
                "state": r.state,
                "project_path": proj.gitlab_project_path if proj else "",
                "project_name": proj.gitlab_project_name if proj else "Unknown",
                "team_id": proj.team_id if proj else None,
                "created_at": r.created_at,
                "merged_at": r.merged_at,
            }
        )
    return out
