"""The staff dashboard's Quick Access sidebar: groups, projects, their health."""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, noload

from app.dependencies import DbSession
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.team_metric_snapshot import TeamMetricSnapshot


async def _build_quick_access(
    db: DbSession,
    active_ids: list[uuid.UUID],
) -> tuple[list[Team], list[GitLabProject], dict[uuid.UUID, dict[str, Any]]]:
    """Five groups, five projects and the health of their teams.

    Only teams with at least one active student (skip empty/template teams),
    the most recently computed first.
    """
    # Subquery: latest computed_at per team
    latest_metric_sq = (
        select(
            TeamMetricSnapshot.team_id,
            func.max(TeamMetricSnapshot.computed_at).label("latest_computed"),
        )
        .group_by(TeamMetricSnapshot.team_id)
        .subquery()
    )

    # Only teams that have at least one active student member
    # (skip empty/template teams). Prefer recently active ones.
    has_students_sq = (
        select(TeamMember.team_id)
        .where(
            TeamMember.is_active.is_(True),
            TeamMember.is_teacher.is_(False),
            TeamMember.is_mentor.is_(False),
        )
        .group_by(TeamMember.team_id)
        .having(func.count(TeamMember.student_id) > 0)
        .subquery()
    )
    qa_stmt = (
        select(Team)
        .options(
            noload(Team.members),
            noload(Team.projects),
            joinedload(Team.course),
        )
        .join(has_students_sq, Team.id == has_students_sq.c.team_id)
        .outerjoin(latest_metric_sq, Team.id == latest_metric_sq.c.team_id)
        .where(Team.course_id.in_(active_ids), Team.is_active.is_(True))
        .order_by(
            latest_metric_sq.c.latest_computed.desc().nullslast(),
            Team.name,
        )
        .limit(5)
    )
    qa_result = await db.execute(qa_stmt)
    qa_teams = list(qa_result.scalars().all())

    # Dedup: the "Subgroups and Projects" tab should surface projects from
    # teams that aren't already visible in the "Groups" tab - otherwise the
    # two tabs show largely the same entities (1 team == 1 project in most
    # teaching setups). Exclude team_ids already shown above AT THE DB
    # LEVEL so we don't waste the limit on duplicates. If Groups already
    # covers everything, fall back to the newest projects overall.
    _qa_team_ids_shown = {t.id for t in qa_teams}

    qa_proj_stmt = (
        select(GitLabProject)
        .join(Team, GitLabProject.team_id == Team.id)
        .join(has_students_sq, Team.id == has_students_sq.c.team_id)
        .outerjoin(latest_metric_sq, Team.id == latest_metric_sq.c.team_id)
        .where(
            Team.course_id.in_(active_ids),
            Team.is_active.is_(True),
            GitLabProject.is_active.is_(True),
        )
        .order_by(
            latest_metric_sq.c.latest_computed.desc().nullslast(),
            GitLabProject.gitlab_project_name,
        )
    )
    if _qa_team_ids_shown:
        qa_proj_stmt = qa_proj_stmt.where(Team.id.notin_(_qa_team_ids_shown))
    qa_proj_stmt = qa_proj_stmt.limit(5)

    qa_proj_result = await db.execute(qa_proj_stmt)
    qa_projects = list(qa_proj_result.scalars().all())

    # Fallback: if the dedup produced nothing (e.g. only ≤5 teams exist
    # total and they're all already in the Groups tab), show the newest
    # projects regardless - better to repeat than to show an empty tab.
    if not qa_projects:
        fallback_stmt = (
            select(GitLabProject)
            .join(Team, GitLabProject.team_id == Team.id)
            .join(has_students_sq, Team.id == has_students_sq.c.team_id)
            .outerjoin(latest_metric_sq, Team.id == latest_metric_sq.c.team_id)
            .where(
                Team.course_id.in_(active_ids),
                Team.is_active.is_(True),
                GitLabProject.is_active.is_(True),
            )
            .order_by(
                latest_metric_sq.c.latest_computed.desc().nullslast(),
                GitLabProject.gitlab_project_name,
            )
            .limit(5)
        )
        qa_projects = list((await db.execute(fallback_stmt)).scalars().all())

    relevant_team_ids: set[uuid.UUID] = {t.id for t in qa_teams} | {
        p.team_id for p in qa_projects if p.team_id
    }
    qa_team_meta = await _team_health(db, relevant_team_ids) if relevant_team_ids else {}
    return qa_teams, qa_projects, qa_team_meta


async def _team_health(
    db: DbSession,
    team_ids: set[uuid.UUID],
) -> dict[uuid.UUID, dict[str, Any]]:
    """Each team's traffic light, group score and member count from its latest
    TeamMetricSnapshot - so the sidebar list informs rather than decorates."""
    meta_sq = (
        select(
            TeamMetricSnapshot.team_id,
            func.max(TeamMetricSnapshot.computed_at).label("latest_computed"),
        )
        .where(TeamMetricSnapshot.team_id.in_(team_ids))
        .group_by(TeamMetricSnapshot.team_id)
        .subquery()
    )
    meta_stmt = select(
        TeamMetricSnapshot.team_id,
        TeamMetricSnapshot.overall_traffic_light,
        TeamMetricSnapshot.avg_weighted_score,
        TeamMetricSnapshot.member_count,
    ).join(
        meta_sq,
        (TeamMetricSnapshot.team_id == meta_sq.c.team_id)
        & (TeamMetricSnapshot.computed_at == meta_sq.c.latest_computed),
    )
    meta_result = await db.execute(meta_stmt)
    meta: dict[uuid.UUID, dict[str, Any]] = {}
    for _tid, _tl, _score, _mc in meta_result.all():
        meta[_tid] = {
            "traffic_light": (_tl or "GRAY").lower(),
            "score_pct": round((_score or 0.0) * 100),
            "member_count": int(_mc or 0),
        }
    return meta
