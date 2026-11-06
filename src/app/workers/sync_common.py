"""Shared helpers/constants for team + project sync jobs."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Delay before retrying a team lookup when the session pool is cold.
_SESSION_WARMUP_RETRY_DELAY_S = 2


def _get_pipeline_concurrency() -> int:
    """Get pipeline concurrency from config."""
    from app.config import get_settings

    return get_settings().sync_pipeline_concurrency


def _semester_sync_since_iso(course: Any | None) -> str | None:
    """Return the ISO 8601 lower bound for GitLab fetches scoped to a course.

    Returns ``None`` for courses without a configured semester start, in which
    case sync retains its legacy full-history behaviour.
    """
    cs = getattr(course, "settings", None) if course is not None else None
    sem_start = getattr(cs, "semester_start_date", None) if cs is not None else None
    if sem_start is None:
        return None
    return datetime.combine(sem_start, datetime.min.time(), tzinfo=UTC).isoformat()


async def deactivate_orphaned_team_members(session: "AsyncSession", team_id: UUID) -> int:
    """Deactivate a team's members when it has no active GitLab projects left.

    Called right after a project is confirmed deleted on GitLab (a clean 404
    from ``get_project``) and marked ``is_active = False``.  When that was the
    team's *last* active project, its roster is stale: the GitLab home those
    members were attached to no longer exists, so a project page that still
    lists dozens of "members" is showing data that no live project backs.

    Safety properties (this is destructive, so they matter):

    * Only fires when the team has **zero** remaining active projects.  A
      multi-project team that loses one project keeps its full roster.
    * Triggered only by a definitive 404 from the project endpoint (5xx and
      rate-limits are retried/raised upstream, never silently seen as 404),
      so a transient GitLab hiccup cannot mass-deactivate a live roster.
    * CSV-placeholder members (negative ``gitlab_user_id``) are skipped -
      they are managed manually, not sourced from GitLab.
    * Fully reversible: if the project reappears, project discovery
      re-registers it and the next member sync reactivates the members.

    Every deactivation is written to ``membership_changes`` for the audit
    trail.  Returns the number of members deactivated (0 if the team still
    has an active project, so the caller can log meaningfully).
    """

    from app.models.membership_change import MembershipChange
    from app.models.project import GitLabProject
    from app.models.team_member import TeamMember

    active_projects = await session.scalar(
        select(func.count())
        .select_from(GitLabProject)
        .where(
            GitLabProject.team_id == team_id,
            GitLabProject.is_active.is_(True),
        )
    )
    if active_projects and active_projects > 0:
        # Team still has at least one live project - roster stays.
        return 0

    members_stmt = (
        select(TeamMember)
        .options(selectinload(TeamMember.student))
        .where(
            TeamMember.team_id == team_id,
            TeamMember.is_active.is_(True),
        )
    )
    members_res = await session.execute(members_stmt)
    now = datetime.now(UTC)
    deactivated = 0

    for tm in members_res.scalars().all():
        # Preserve manually-imported (CSV) placeholders - they are not
        # backed by a real GitLab account and are managed by hand.
        if tm.student and tm.student.gitlab_user_id and tm.student.gitlab_user_id < 0:
            continue
        tm.is_active = False
        tm.left_at = now
        tm.last_synced_at = now
        session.add(
            MembershipChange(
                team_id=team_id,
                student_id=tm.student_id,
                gitlab_username=tm.student.gitlab_username if tm.student else None,
                change_type="left",
                old_role=tm.gitlab_access_role,
                old_access_level=tm.gitlab_access_level,
                source="sync",
                detected_at=now,
                details="GitLab project deleted - team has no active projects remaining",
            )
        )
        deactivated += 1

    if deactivated:
        await session.commit()
        try:
            from app.workers.progress import publish_dashboard_update

            publish_dashboard_update(
                "team",
                str(team_id),
                "roster_changed",
                extra={"removed": deactivated, "reason": "project_deleted"},
            )
        except Exception:
            logger.debug("roster_event_publish_failed", exc_info=True)

    return deactivated


def gitlab_repo_is_empty(project_info: Any) -> bool:
    """Return True when a GitLab project object describes an empty/absent repo.

    GitLab reports both "the repository was deleted" ("No repository") and
    "the repository exists but has no commits" the same way on the project
    object: ``empty_repo: true`` with a null ``default_branch``.  Either way
    there is no code to sync.  Callers MUST further distinguish a *deleted*
    repo from a *never-started* one before acting destructively (see
    :func:`project_has_stored_commits`).
    """
    if not isinstance(project_info, dict):
        return False
    empty = project_info.get("empty_repo")
    if empty is not None:
        return bool(empty)
    # Older GitLab payloads omit empty_repo - fall back to default_branch.
    return not project_info.get("default_branch")


async def project_has_stored_commits(session: "AsyncSession", project_db_id: UUID) -> bool:
    """Return True if GitPulse already stored at least one commit for a project.

    This is the signal that distinguishes a *deleted* repository (we have
    commits from before it was removed) from a *fresh* project that simply has
    not been pushed to yet (no commits ever).  Only the former should be
    deactivated when the live repo reads empty.
    """

    from app.models.commit import Commit

    sha = await session.scalar(
        select(Commit.sha).where(Commit.project_id == project_db_id).limit(1)
    )
    return sha is not None


async def deactivate_project_and_reconcile(
    session: "AsyncSession",
    *,
    project_db_id: UUID,
    team_id: UUID,
    gitlab_pid: int,
    reason: str,
) -> None:
    """Mark a project inactive (idempotent) and reconcile orphaned members.

    Used for both fully-deleted projects (GitLab 404) and projects whose
    repository was deleted (live repo reads empty but we hold prior commits).
    Deactivation hides the project from active views and rankings without
    destroying its commit/snapshot history, so a re-import or repo restore can
    recover the grading trail. Reversible via
    :func:`reactivate_project_if_repo_returned`.
    """

    from app.models.project import GitLabProject

    res = await session.execute(select(GitLabProject).where(GitLabProject.id == project_db_id))
    proj = res.scalar_one_or_none()
    if proj and proj.is_active:
        proj.is_active = False
        await session.commit()
        logger.info("Deactivated project %d on GitLab (%s)", gitlab_pid, reason)

    orphaned = await deactivate_orphaned_team_members(session, team_id)
    if orphaned:
        logger.info(
            "Deactivated %d orphaned member(s) for team %s after project %d (%s)",
            orphaned,
            team_id,
            gitlab_pid,
            reason,
        )


async def fetch_gitlab_intel_snapshot(
    gl: Any, project_id: int, ref: str | None
) -> dict[str, Any] | None:
    """Fetch a per-project GitLab snapshot and shape it for persistence.

    Stores (a) the "intelligence" trio - ``protectedBranches`` / ``contributors``
    lists + a normalised ``statistics`` dict, shaped exactly like the value the
    project-detail route feeds into ``_build_gl_intel_view`` - and (b) the
    project's member roster (``members`` = all incl. inherited, ``direct_members``
    = directly added), lowercased usernames.

    Persisted on ``GitLabProject.gitlab_intel`` so BOTH the three intelligence
    cards AND the project members table keep working when GitLab is later
    unreachable (expired token / maintenance window). Without the member roster
    the members table cannot tell THIS project's ~5 members apart from the whole
    parent subgroup (~50) and shows every subgroup member.

    Best-effort: each sub-call is independent; a failed one is omitted. Returns
    ``None`` when everything failed (nothing worth persisting - callers must NOT
    clobber a previous good snapshot with an empty one).
    """
    intel: dict[str, Any] = {}

    try:
        pb = await gl.get_protected_branches(project_id)
        if isinstance(pb, list):
            intel["protectedBranches"] = pb
    except Exception:
        logger.debug("gitlab_intel: protected-branches fetch failed for %s", project_id)

    try:
        # Stored raw/unfiltered - the route applies the team-member whitelist on
        # read, identical to how it filters a live fetch.
        contribs = await gl.get_contributors(project_id, ref=ref)
        if isinstance(contribs, list):
            intel["contributors"] = contribs
    except Exception:
        logger.debug("gitlab_intel: contributors fetch failed for %s", project_id)

    try:
        stats = await gl.get_project_statistics(project_id)
        if isinstance(stats, dict) and stats:
            s = stats.get("statistics") or {}
            intel["statistics"] = {
                "commit_count": s.get("commit_count", 0),
                "repository_size": s.get("repository_size", 0),
                "storage_size": s.get("storage_size", 0),
                "open_issues_count": stats.get("open_issues_count", 0),
                "star_count": stats.get("star_count", 0),
                "forks_count": stats.get("forks_count", 0),
                "last_activity_at": stats.get("last_activity_at"),
            }
    except Exception:
        logger.debug("gitlab_intel: statistics fetch failed for %s", project_id)

    # Project member roster - lets the members table scope to THIS project's
    # members instead of the whole parent subgroup when the live fetch is down.
    try:
        all_m = await gl.get_project_members(project_id, include_inherited=True)
        if isinstance(all_m, list):
            intel["members"] = sorted(
                {(m.get("username") or "").lower() for m in all_m if m.get("username")}
            )
    except Exception:
        logger.debug("gitlab_intel: members fetch failed for %s", project_id)

    try:
        direct_m = await gl.get_project_members(project_id, include_inherited=False)
        if isinstance(direct_m, list):
            intel["direct_members"] = sorted(
                {(m.get("username") or "").lower() for m in direct_m if m.get("username")}
            )
    except Exception:
        logger.debug("gitlab_intel: direct-members fetch failed for %s", project_id)

    try:
        milestones = await gl.get_project_milestones(project_id, state="all")
        if isinstance(milestones, list):
            intel["milestones"] = milestones
    except Exception:
        logger.debug("gitlab_intel: milestones fetch failed for %s", project_id)

    try:
        releases = await gl.get_project_releases(project_id)
        if isinstance(releases, list):
            intel["releases"] = releases
    except Exception:
        logger.debug("gitlab_intel: releases fetch failed for %s", project_id)

    try:
        labels = await gl.get_project_labels(project_id)
        if isinstance(labels, list):
            intel["labels"] = labels
    except Exception:
        logger.debug("gitlab_intel: labels fetch failed for %s", project_id)

    if not intel:
        return None
    intel["synced_at"] = datetime.now(UTC).isoformat()
    return intel
