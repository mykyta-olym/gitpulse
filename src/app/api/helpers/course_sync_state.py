"""A course's sync state - one reading for the sync-status poll and the SSE stream.

The two rebuilt it from the same recent jobs with rules that had drifted: the
poll took each group's NEWEST job, the stream merged its jobs by priority, so a
stale ``running`` row left by a crashed worker outranked the fresher
``completed`` (the row stuck on SYNCING), and an older ``completed`` outranked a
newer ``failed``. The course page listens to the stream and falls back to the
poll, so its badges flipped between the two answers. Both read this now.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.api.helpers.sync import _reconcile_stale_jobs, recent_sync_jobs_stmt
from app.dependencies import DbSession
from app.models.course import Course
from app.models.team import Team

# A group whose newest job finished this recently still counts as active on
# the stream: the per-group workflow leaves a 2-5 s gap between one group
# finishing and the next batch being enqueued, and without it the stream's
# debounced `complete` - and the client's verify call - ended the progress
# bar while the sync was still running.
_RECENT_FINISH = timedelta(seconds=15)
_FINISHED = ("completed", "failed", "cancelled")


@dataclass
class CourseSyncState:
    teams: list[Team]
    team_metrics: dict[uuid.UUID, Any]
    # The newest sync job's status per group (team-wide jobs only).
    status_by_team: dict[uuid.UUID, str] = field(default_factory=dict)
    # "Retrying (2/3)..." from a group's running job.
    note_by_team: dict[uuid.UUID, str] = field(default_factory=dict)
    # Only projects whose newest project-scoped job is still running or
    # queued: a finished one drops out, so the page restores the row's normal
    # badge instead of the default SYNCING paint for unknown states.
    status_by_project: dict[uuid.UUID, str] = field(default_factory=dict)
    # Groups whose newest job finished within _RECENT_FINISH.
    recently_finished: set[uuid.UUID] = field(default_factory=set)
    # The earliest enqueue among the running/queued jobs: the server-side
    # start of the current Sync All, which anchors the progress bar's timer.
    earliest_active_enqueued: datetime | None = None
    member_counts: dict[uuid.UUID, int] = field(default_factory=dict)

    def count(self, status: str) -> int:
        return sum(1 for s in self.status_by_team.values() if s == status)

    def project_count(self, status: str) -> int:
        return sum(1 for s in self.status_by_project.values() if s == status)

    @property
    def in_flight(self) -> int:
        return self.count("running") + self.count("enqueued")


async def course_sync_state(session: DbSession, course: Course) -> CourseSyncState:
    """Read the course's groups, their latest metrics and recent sync jobs."""
    from app.api.dashboard._stats import latest_team_metric_map
    from app.api.dashboard.courses.overview import group_contributors

    teams = list(
        (
            await session.execute(
                select(Team).where(Team.course_id == course.id).order_by(Team.name)
            )
        ).scalars()
    )
    team_ids = [t.id for t in teams]
    if team_ids:
        # Reconcile stale BGjobs with actual RQ state
        await _reconcile_stale_jobs(session, team_ids)
    state = CourseSyncState(teams, await latest_team_metric_map(session, team_ids))
    if not team_ids:
        return state

    grace = datetime.now(UTC) - _RECENT_FINISH
    seen_projects: set[uuid.UUID] = set()
    # Newest first: the first row seen for a group or a project is its newest job.
    for team_id, project_id, status, completed_at, enqueued_at, summary in (
        await session.execute(recent_sync_jobs_stmt(team_ids))
    ).all():
        status = "running" if status == "started" else status
        earliest = state.earliest_active_enqueued
        if (
            status in ("running", "enqueued")
            and enqueued_at is not None
            and (earliest is None or enqueued_at < earliest)
        ):
            state.earliest_active_enqueued = enqueued_at
        if team_id is None:
            continue
        if project_id is not None:
            if project_id not in seen_projects:
                seen_projects.add(project_id)
                if status in ("running", "enqueued"):
                    state.status_by_project[project_id] = status
            continue
        if team_id in state.status_by_team:
            continue
        state.status_by_team[team_id] = status
        if status == "running" and summary and summary.startswith("Retrying"):
            state.note_by_team[team_id] = summary
        if status in _FINISHED and completed_at is not None and completed_at >= grace:
            state.recently_finished.add(team_id)

    state.member_counts = await group_contributors(session, course, team_ids)
    return state


def last_updated(metric: Any, status: str | None) -> tuple[str | None, str | None]:
    """A group's "Last Updated" cell: its metrics' time, or what its sync is doing."""
    if metric and metric.computed_at:
        return (
            metric.computed_at.strftime("%Y-%m-%d %H:%M"),
            metric.computed_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    label = {
        "running": "Sync in progress...",
        "enqueued": "Sync queued...",
        "completed": "Sync completed",
        "failed": "Sync failed",
        "cancelled": "Sync cancelled",
    }.get(status or "")
    return label, None
