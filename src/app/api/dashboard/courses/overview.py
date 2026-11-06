"""What the course page's Groups table reads: contributors, sync state, projects."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.api.dashboard._stats import team_contributor_counts
from app.dependencies import DbSession
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team


async def group_contributors(
    db: DbSession,
    course: Course,
    team_ids: list[uuid.UUID],
) -> dict[uuid.UUID, int]:
    """Each group's contributors this semester - the Groups table's column, for
    the page and for its live refresh alike.

    The refresh counted them over all time, by another route (the whitelist
    sent to Postgres as ~900 bind parameters), so the first refresh replaced
    every group's semester count with a larger all-time one. Only commits from
    the current semester count: last semester's authors would pad the numbers
    forever. The whitelist is a subquery here, not a bind list.
    """
    from app.utils.semester import semester_floor_utc

    return await team_contributor_counts(
        db,
        team_ids,
        commit_since=semester_floor_utc(course.settings if course else None),
    )


async def team_sync_states(
    db: DbSession,
    active_team_ids: list[uuid.UUID],
) -> tuple[dict[uuid.UUID, str], dict[str, int]]:
    """Each active group's sync state and the running/queued/failed/cancelled
    counts. Only active groups: an archived group is excluded from sync, so its
    historical jobs must not show up in the counters."""
    sync_status_by_team: dict[uuid.UUID, str] = {}
    if active_team_ids:
        # Reconcile stale BGjobs with actual RQ state
        from app.api.helpers.sync import _reconcile_stale_jobs, recent_sync_jobs_stmt

        await _reconcile_stale_jobs(db, active_team_ids)

        jobs_stmt = recent_sync_jobs_stmt(active_team_ids).where(BackgroundJob.project_id.is_(None))
        jobs_result = await db.execute(jobs_stmt)
        for team_id, _project_id, status, *_ in jobs_result.all():
            if team_id is not None and team_id not in sync_status_by_team:
                sync_status_by_team[team_id] = "running" if status == "started" else status

    states = list(sync_status_by_team.values())
    counts = {
        "sync_running_count": states.count("running"),
        "sync_queued_count": states.count("enqueued"),
        "sync_failed_count": states.count("failed"),
        "sync_cancelled_count": states.count("cancelled"),
    }
    return sync_status_by_team, counts


async def team_projects(
    db: DbSession,
    teams: list[Team],
    can_edit: bool,
) -> dict[uuid.UUID, list[GitLabProject]]:
    """The projects under each group, for the expandable tree.

    Teachers and admins keep soft-deleted/unlinked projects in the tree
    (dimmed, restorable); students only see active projects. GitLab renames a
    project to ``<path>-<hash>-deletion_scheduled-<id>`` when it is scheduled
    for deletion on GitLab's side. Those tombstones are not teacher-managed
    "unlinked" projects and must never appear as restorable ghost rows, so
    they are filtered out of every listing.
    """
    by_team: dict[uuid.UUID, list[GitLabProject]] = {}
    if not teams:
        return by_team
    proj_stmt = select(GitLabProject).where(
        GitLabProject.team_id.in_([t.id for t in teams]),
        ~GitLabProject.gitlab_project_path.contains("deletion_scheduled", autoescape=True),
    )
    if not can_edit:
        proj_stmt = proj_stmt.where(GitLabProject.is_active.is_(True))
    # Order by path (globally unique) instead of display name to
    # keep duplicate-named projects in a stable, deterministic order.
    proj_stmt = proj_stmt.order_by(
        GitLabProject.is_active.desc(),
        GitLabProject.gitlab_project_path,
    )
    proj_result = await db.execute(proj_stmt)
    # Defense-in-depth: when multiple rows share the same path (data
    # drift from a deleted+recreated GitLab project), keep one row -
    # prefer an active row, then the latest gitlab_project_id - so the
    # UI never shows ghost rows.
    seen_paths: dict[tuple[uuid.UUID, str], GitLabProject] = {}
    for proj in proj_result.scalars().all():
        key = (proj.team_id, proj.gitlab_project_path or str(proj.id))
        existing = seen_paths.get(key)
        if existing is None or (bool(proj.is_active), proj.gitlab_project_id or 0) > (
            bool(existing.is_active),
            existing.gitlab_project_id or 0,
        ):
            seen_paths[key] = proj
    for proj in seen_paths.values():
        by_team.setdefault(proj.team_id, []).append(proj)
    return by_team


def light_counts(active_teams: list[Team], team_metrics: dict[uuid.UUID, Any]) -> tuple[int, int]:
    """Green and red groups by their latest metrics snapshot."""
    green = red = 0
    for t in active_teams:
        snap = team_metrics.get(t.id)
        if snap and snap.overall_traffic_light:
            tl = snap.overall_traffic_light.upper()
            if tl == "GREEN":
                green += 1
            elif tl == "RED":
                red += 1
    return green, red


_LIGHT_ORDER = {"RED": 0, "YELLOW": 1, "GREEN": 2}


def by_light(teams: list[Team], team_metrics: dict[uuid.UUID, Any]) -> list[Team]:
    """RED first, then YELLOW, GREEN, and the groups without a light (?sort=status)."""

    def key(t: Team) -> int:
        snap = team_metrics.get(t.id)
        tl = (snap.overall_traffic_light or "").upper() if snap else ""
        return _LIGHT_ORDER.get(tl, 3)

    return sorted(teams, key=key)


def stale_metrics_days(team_metrics: dict[uuid.UUID, Any], active_teams: list[Team]) -> int | None:
    """Days since the oldest active group's metrics, when that is over a week.

    Only the metrics of active groups matter; an archived group's frozen
    snapshot must not trigger a false "data is stale" banner forever.
    """
    active_ids = {t.id for t in active_teams}
    computed = [
        tm.computed_at
        for tid, tm in team_metrics.items()
        if tid in active_ids and tm and tm.computed_at
    ]
    if not computed:
        return None
    age = datetime.now(UTC) - min(computed)
    return age.days if age > timedelta(days=7) else None


def never_synced_count(
    active_teams: list[Team],
    projects: dict[uuid.UUID, list[GitLabProject]],
) -> int:
    """Active groups whose members or every active project never synced."""
    count = 0
    for team in active_teams:
        active_projs = [p for p in projects.get(team.id, []) if p.is_active]
        if team.members_synced_at is None or (
            active_projs and all(p.last_synced_at is None for p in active_projs)
        ):
            count += 1
    return count
