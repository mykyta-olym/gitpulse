"""Sync and background job endpoints."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from fastapi import APIRouter, Body, Request
from sqlalchemy import and_, func, or_, select

from app.api.errors import (
    raise_conflict,
    raise_not_found,
    raise_service_unavailable,
)
from app.api.helpers.sync import (
    ACTIVE_RUN_CHECK_STATUSES,
    ACTIVE_SYNC_STATUSES,
    RUN_CHECKS_ACTIVE_WINDOW,
    SYNC_FRESHNESS_TTL,
    _active_run_checks_team_ids,
    _active_sync_team_ids,
    _advisory_lock_key,
    _get_active_run_checks_job,
    _get_active_sync_job,
    _has_active_rq_workers,
    _lock_team_job_scope,
    _recently_synced_team_ids,
    _reconcile_stale_jobs,
    require_gitlab_ready,
)
from app.api.helpers.utils import get_actor
from app.api.sync_stream import router as _sync_stream_router
from app.config import get_settings
from app.dependencies import ApiAuth, ApiTeacherAuth, DbSession, _validate_session
from app.models.background_job import BackgroundJob
from app.models.team import Team
from app.schemas.jobs import JobEnqueued
from app.schemas.sync import (
    ActiveSyncCourse,
    ActiveSyncsResponse,
    CourseRunChecksStatusResponse,
    CourseSyncStatusResponse,
    SyncAllResponse,
    TeamSyncStatus,
)
from app.services.audit import write_audit
from app.services.events import enqueue_sync_job
from app.services.gitlab.token_health import cached_status as _gitlab_cached_status

logger = structlog.get_logger(__name__)

# Strong references to fire-and-forget background tasks so the GC doesn't
# cancel them before they finish (see ``asyncio.create_task`` docs).
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()
router = APIRouter()
router.include_router(_sync_stream_router)


@router.post("/teams/{team_id}/sync", response_model=JobEnqueued, status_code=202)
async def trigger_sync(
    team_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    force: bool = False,
) -> JobEnqueued:
    """Trigger a full API sync (teacher/admin only).

    Short-circuits with a ``skipped_fresh`` response if the last successful
    sync for this team completed within ``SYNC_FRESHNESS_TTL``.  Pass
    ``?force=true`` to bypass the freshness guard.
    """
    if not await _has_active_rq_workers():
        raise_service_unavailable(
            "No active background worker. Start worker process and retry sync."
        )

    await require_gitlab_ready()

    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")

    # Authorize against THIS team's course, not just the global teacher role.
    # Denial returns the same 404 as a missing group so a teacher who does not
    # belong to the course can't enumerate or sync foreign teams by UUID.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, team=team):
        raise_not_found("Group not found")

    if not team.is_active:
        raise_conflict("Cannot sync a deactivated group")

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    # Reconcile stale BGjobs before checking
    await _reconcile_stale_jobs(db, [team_id])

    # Freshness short-circuit
    if not force and (await _recently_synced_team_ids(db, [team_id])):
        return JobEnqueued(
            job_id=uuid.UUID(int=0),
            job_type="sync",
            status="skipped_fresh",
            message=f"Group {team.name} already up-to-date.",
        )

    # Acquire advisory lock to prevent TOCTOU race between checking
    # for existing jobs and creating a new one.
    # Uses PostgreSQL pg_advisory_xact_lock - released when txn ends.
    await _lock_team_job_scope(db, team_id)

    active_checks = await _get_active_run_checks_job(db, team_id)
    if active_checks:
        raise_conflict(f"Cannot sync group {team.name} while compliance checks are running.")

    # Check for already running/enqueued sync for this team. Project-scoped
    # syncs also block a group-wide sync because both refresh overlapping
    # GitLab objects and write the same metric inputs.
    existing_stmt = select(BackgroundJob).where(
        BackgroundJob.team_id == team_id,
        BackgroundJob.job_type == "sync",
        BackgroundJob.status.in_(ACTIVE_SYNC_STATUSES),
    )
    existing_result = await db.execute(existing_stmt)
    existing_job = existing_result.scalar_one_or_none()
    if existing_job:
        return JobEnqueued(
            job_id=existing_job.id,
            job_type="sync",
            status=existing_job.status,
            message=f"Sync already {existing_job.status} for group {team.name}",
        )

    # Create job record
    job = BackgroundJob(
        job_type="sync",
        team_id=team.id,
    )
    db.add(job)
    await db.flush()

    # Enqueue
    try:
        rq_job_id = enqueue_sync_job(str(team.id), str(job.id), str(team.course_id))
        if rq_job_id:
            job.rq_job_id = rq_job_id
        else:
            job.status = "failed"
            job.error_message = "Failed to enqueue job (Redis unavailable)"
        await db.flush()
    except Exception:
        logger.error("failed_to_enqueue_sync", team_id=str(team_id), exc_info=True)
        job.status = "failed"
        job.error_message = "Failed to enqueue job (Redis unavailable)"
        await db.flush()

    logger.info("sync_triggered", team_id=str(team_id), job_id=str(job.id))

    await write_audit(
        db,
        action="sync_team",
        actor=get_actor(request, fallback="api_token"),
        entity_type="team",
        entity_id=team_id,
        detail={"summary": f"Sync triggered for {team.name}", "status": job.status},
    )
    await db.commit()

    return JobEnqueued(
        job_id=job.id,
        job_type="sync",
        status=job.status,
        message=job.error_message or f"Sync enqueued for group {team.name}",
    )


@router.post("/projects/{project_id}/sync", response_model=JobEnqueued, status_code=202)
async def trigger_project_sync(
    project_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
) -> JobEnqueued:
    """Trigger a GitLab API sync for a single project (teacher/admin only).

    Unlike :func:`trigger_sync` (which syncs the whole team/group), this
    endpoint refreshes only the issues, MRs, MR notes, pipelines and
    commits for the given project. Member sync and project discovery are
    skipped - those remain team-scoped operations.
    """
    from app.models.project import GitLabProject
    from app.services.events import enqueue_project_sync_job

    if not await _has_active_rq_workers():
        raise_service_unavailable(
            "No active background worker. Start worker process and retry sync."
        )

    await require_gitlab_ready()

    project = await db.get(GitLabProject, project_id)
    if not project:
        raise_not_found("Project not found")

    # Authorize against the project's owning team/course (resolved inside the
    # helper). 404-on-denial keeps foreign project UUIDs unenumerable.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, project=project):
        raise_not_found("Project not found")

    if not project.is_active:
        raise_conflict("Cannot sync a deactivated project")

    team = await db.get(Team, project.team_id) if project.team_id else None
    if team and not team.is_active:
        raise_conflict("Cannot sync a project under a deactivated group")

    if team is not None:
        from app.services.courses import ensure_course_active

        await ensure_course_active(db, team.course_id)

    # Reconcile stale BGjobs (including project-scoped ones owned by
    # this team) before the dedup check below, so a crashed-worker
    # "running" row from an old sync does not permanently block new
    # project syncs (and does not keep painting a stuck SYNCING badge).
    if project.team_id:
        await _reconcile_stale_jobs(db, [project.team_id])
        await _lock_team_job_scope(db, project.team_id)
        active_checks = await _get_active_run_checks_job(db, project.team_id)
        if active_checks:
            raise_conflict(
                "Cannot sync this project while compliance checks are running for its group."
            )

    # Advisory lock keyed on project id to prevent concurrent enqueues.
    await db.execute(select(func.pg_advisory_xact_lock(_advisory_lock_key(project_id))))

    # Skip if this exact project sync is already running.
    existing_project_stmt = select(BackgroundJob).where(
        BackgroundJob.project_id == project_id,
        BackgroundJob.job_type == "sync",
        BackgroundJob.status.in_(ACTIVE_SYNC_STATUSES),
    )
    existing_project = (await db.execute(existing_project_stmt)).scalar_one_or_none()
    if existing_project:
        return JobEnqueued(
            job_id=existing_project.id,
            job_type="sync",
            status=existing_project.status,
            message=f"Sync already {existing_project.status} for this project",
        )
    if project.team_id:
        active_sync = await _get_active_sync_job(db, project.team_id)
        if active_sync and active_sync.project_id is None:
            return JobEnqueued(
                job_id=active_sync.id,
                job_type="sync",
                status=active_sync.status,
                message="Group sync already running - project will be refreshed as part of it",
            )
        if active_sync:
            raise_conflict("Cannot sync this project while another project sync is running.")

    course_id_str: str | None = str(team.course_id) if team and team.course_id else None

    job = BackgroundJob(
        job_type="sync",
        team_id=project.team_id,
        project_id=project.id,
    )
    db.add(job)
    await db.flush()

    try:
        rq_job_id = enqueue_project_sync_job(str(project.id), str(job.id), course_id_str)
        if rq_job_id:
            job.rq_job_id = rq_job_id
        else:
            job.status = "failed"
            job.error_message = "Failed to enqueue job (Redis unavailable)"
        await db.flush()
    except Exception:
        logger.error("failed_to_enqueue_project_sync", project_id=str(project_id), exc_info=True)
        job.status = "failed"
        job.error_message = "Failed to enqueue job (Redis unavailable)"
        await db.flush()

    logger.info("project_sync_triggered", project_id=str(project_id), job_id=str(job.id))

    project_label = (
        project.gitlab_project_name
        or (project.gitlab_project_path or "").rsplit("/", 1)[-1]
        or str(project.id)
    )
    await write_audit(
        db,
        action="sync_project",
        actor=get_actor(request, fallback="api_token"),
        entity_type="project",
        entity_id=project_id,
        detail={
            "summary": f"Project sync triggered for {project_label}",
            "status": job.status,
            "team_id": str(project.team_id) if project.team_id else None,
        },
    )
    await db.commit()

    return JobEnqueued(
        job_id=job.id,
        job_type="sync",
        status=job.status,
        message=job.error_message or f"Sync enqueued for project {project_label}",
    )


@router.post("/teams/{team_id}/run-checks", response_model=JobEnqueued, status_code=202)
async def run_selected_checks(
    team_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    check_codes: list[str] | None = Body(None, embed=True),
) -> JobEnqueued:
    """Run specific compliance checks for a team (teacher/admin only).

    Parameters
    ----------
    check_codes:
        Optional list of check codes to evaluate (e.g. ``["R01", "R03"]``).
        When ``None`` or empty, **all** enabled checks are evaluated
        (ignoring weekly-deadline filters).
    """
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")
    if not team.is_active:
        raise_conflict("Cannot run checks on a deactivated group")

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    # Normalise: empty list -> None (= all checks)
    codes: list[str] | None = check_codes or None
    await _reconcile_stale_jobs(db, [team.id])
    await _lock_team_job_scope(db, team.id)

    active_sync = await _get_active_sync_job(db, team.id)
    if active_sync:
        raise_conflict(f"Cannot run checks for group {team.name} while sync is running.")

    # -- Deduplication: reject if a run_checks job is already active for this team --
    stale_cutoff = datetime.now(UTC) - RUN_CHECKS_ACTIVE_WINDOW
    existing_running = (
        await db.execute(
            select(BackgroundJob)
            .where(
                BackgroundJob.team_id == team.id,
                BackgroundJob.job_type == "run_checks",
                BackgroundJob.status.in_(ACTIVE_RUN_CHECK_STATUSES),
                BackgroundJob.enqueued_at > stale_cutoff,
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if existing_running:
        return JobEnqueued(
            job_id=existing_running.id,
            job_type="run_checks",
            status=existing_running.status,
            message=f"Checks already running for group {team.name}",
        )

    # Create a background job record
    job = BackgroundJob(
        job_type="run_checks",
        team_id=team.id,
    )
    db.add(job)
    await db.flush()

    try:
        from app.services.events import enqueue_run_checks_job

        rq_job_id = enqueue_run_checks_job(str(team.id), str(job.id), codes)
        if rq_job_id:
            job.rq_job_id = rq_job_id
        else:
            job.status = "failed"
            job.error_message = "Failed to enqueue run-checks job (Redis unavailable)"
        await db.flush()
    except Exception:
        logger.error("failed_to_enqueue_run_checks", team_id=str(team_id), exc_info=True)
        job.status = "failed"
        job.error_message = "Failed to enqueue run-checks job"
        await db.flush()

    label = ", ".join(codes) if codes else "all checks"
    logger.info(
        "run_checks_triggered",
        team_id=str(team_id),
        job_id=str(job.id),
        check_codes=codes,
    )

    await write_audit(
        db,
        action="run_checks",
        actor=get_actor(request, fallback="api_token"),
        entity_type="team",
        entity_id=team_id,
        detail={
            "summary": f"Run checks ({label}) for {team.name}",
            "check_codes": codes,
            "status": job.status,
        },
    )
    await db.commit()

    return JobEnqueued(
        job_id=job.id,
        job_type="run_checks",
        status=job.status,
        message=job.error_message or f"Checks enqueued for group {team.name} ({label})",
    )


@router.post("/courses/{course_id}/run-checks", response_model=SyncAllResponse, status_code=202)
async def run_selected_checks_all(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    check_codes: list[str] | None = Body(None, embed=True),
) -> SyncAllResponse:
    """Fan-out compliance checks to every active group in a course.

    Mirrors :func:`run_selected_checks` but enqueues one ``run_checks`` job
    per active team in the course.  If sync or another check run is already
    active for any group, the request is rejected to avoid partial fan-out.
    Empty / missing ``check_codes`` means "all enabled checks".
    """
    from app.models.course import Course as CourseModel

    course = await db.get(CourseModel, course_id)
    if not course:
        raise_not_found("Course not found")

    if not course.is_active:
        raise_conflict("This course is archived and read-only. Reactivate it to run checks.")

    codes: list[str] | None = check_codes or None

    team_stmt = (
        select(Team)
        .where(Team.course_id == course_id, Team.is_active.is_(True))
        .order_by(Team.name)
    )
    teams = list((await db.execute(team_stmt)).scalars().all())

    if not teams:
        return SyncAllResponse(
            enqueued=0, skipped=0, failed=0, message="No active groups in course."
        )

    team_ids = [team.id for team in teams]
    reconciled = await _reconcile_stale_jobs(db, team_ids)
    if reconciled:
        await db.commit()

    for team_id in sorted(team_ids, key=str):
        await _lock_team_job_scope(db, team_id)

    active_sync_team_ids = await _active_sync_team_ids(db, team_ids)
    if active_sync_team_ids:
        raise_conflict("Cannot run course checks while sync is active for one or more groups.")

    active_checks_team_ids = await _active_run_checks_team_ids(db, team_ids)
    if active_checks_team_ids:
        raise_conflict("Cannot start another course check run while checks are already active.")

    enqueued = 0
    skipped = 0
    failed = 0

    # -- Pass 1: create BackgroundJob rows for teams without an active run --
    # active_checks_team_ids (computed above with identical criteria - same
    # job_type, ACTIVE_RUN_CHECK_STATUSES and active window) already holds every
    # group with an in-flight run-checks job, so membership is tested in memory
    # instead of issuing one SELECT per group (was an N+1 over the course's
    # groups). The guard above raises on a non-empty set, so this is empty in
    # practice; the check stays as defensive belt-and-suspenders.
    jobs_to_enqueue: list[tuple[Team, BackgroundJob]] = []
    for team in teams:
        if team.id in active_checks_team_ids:
            skipped += 1
            continue
        job = BackgroundJob(job_type="run_checks", team_id=team.id)
        db.add(job)
        await db.flush()
        jobs_to_enqueue.append((team, job))

    if jobs_to_enqueue:
        await db.commit()  # workers must see rows before enqueue

    # -- Pass 2: enqueue to RQ --
    from app.services.events import enqueue_run_checks_job

    for team, job in jobs_to_enqueue:
        try:
            rq_job_id = enqueue_run_checks_job(str(team.id), str(job.id), codes)
            if rq_job_id:
                job.rq_job_id = rq_job_id
                enqueued += 1
            else:
                job.status = "failed"
                job.error_message = "Failed to enqueue run-checks job (Redis unavailable)"
                failed += 1
        except (ConnectionError, TimeoutError, OSError):
            logger.exception("run_checks_all_enqueue_failed", team_id=str(team.id))
            job.status = "failed"
            job.error_message = "Failed to enqueue run-checks job (Redis unavailable)"
            failed += 1
        await db.flush()

    label = ", ".join(codes) if codes else "all checks"
    logger.info(
        "run_checks_all_triggered",
        course_id=str(course_id),
        enqueued=enqueued,
        skipped=skipped,
        failed=failed,
        check_codes=codes,
    )
    await write_audit(
        db,
        action="run_checks_all",
        actor=get_actor(request, fallback="api_token"),
        entity_type="course",
        entity_id=course_id,
        detail={
            "summary": f"Run checks ({label}) for {enqueued} groups "
            f"({skipped} skipped, {failed} failed)",
            "enqueued": enqueued,
            "skipped": skipped,
            "failed": failed,
            "check_codes": codes,
        },
    )
    await db.commit()

    return SyncAllResponse(
        enqueued=enqueued,
        skipped=skipped,
        failed=failed,
        message=f"Checks enqueued for {enqueued} groups "
        f"({skipped} already running, {failed} failed) - {label}.",
    )


@router.get(
    "/courses/{course_id}/run-checks-status",
    response_model=CourseRunChecksStatusResponse,
)
async def get_course_run_checks_status(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> CourseRunChecksStatusResponse:
    """Return aggregate run-checks status for all active groups in a course."""
    from app.models.course import Course as CourseModel

    course = await db.get(CourseModel, course_id)
    if not course:
        raise_not_found("Course not found")

    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, course=course):
        raise_not_found("Course not found")

    team_stmt = select(Team.id).where(
        Team.course_id == course_id,
        Team.is_active.is_(True),
    )
    team_ids = [team_id for (team_id,) in (await db.execute(team_stmt)).all()]
    total_groups = len(team_ids)
    if not team_ids:
        return CourseRunChecksStatusResponse(
            status="completed",
            total_groups=0,
            progress=100,
            result_summary="No active groups in course.",
        )

    cutoff = datetime.now(UTC) - RUN_CHECKS_ACTIVE_WINDOW
    rows = (
        await db.execute(
            select(BackgroundJob.team_id, BackgroundJob.status)
            .where(
                BackgroundJob.team_id.in_(team_ids),
                BackgroundJob.job_type == "run_checks",
                BackgroundJob.status.in_(
                    (*ACTIVE_RUN_CHECK_STATUSES, "completed", "failed", "cancelled")
                ),
                BackgroundJob.enqueued_at > cutoff,
            )
            .order_by(BackgroundJob.team_id, BackgroundJob.enqueued_at.desc())
        )
    ).all()
    latest_status_by_team: dict[uuid.UUID, str] = {}
    for team_id, status in rows:
        if team_id not in latest_status_by_team:
            latest_status_by_team[team_id] = str(status or "").lower()
    statuses = list(latest_status_by_team.values())
    queued = sum(1 for status in statuses if status == "enqueued")
    running = sum(1 for status in statuses if status in {"started", "running"})
    active = queued + running

    if active:
        completed = max(0, total_groups - active)
        progress = round(completed / total_groups * 100) if total_groups else 0
        return CourseRunChecksStatusResponse(
            status="running",
            running_count=running,
            queued_count=queued,
            active_count=active,
            total_groups=total_groups,
            progress=progress,
            result_summary=(
                f"Checks running for {active}/{total_groups} groups "
                f"({running} active, {queued} queued)."
            ),
        )

    failed = sum(1 for status in statuses if status == "failed")
    cancelled = sum(1 for status in statuses if status == "cancelled")
    if failed:
        return CourseRunChecksStatusResponse(
            status="failed",
            total_groups=total_groups,
            progress=100,
            error_message=f"Checks failed for {failed} group(s).",
        )
    if cancelled:
        return CourseRunChecksStatusResponse(
            status="cancelled",
            total_groups=total_groups,
            progress=100,
            result_summary=f"Checks cancelled for {cancelled} group(s).",
        )

    return CourseRunChecksStatusResponse(
        status="completed",
        total_groups=total_groups,
        progress=100,
        result_summary=f"Checks completed for {total_groups} groups.",
    )


async def _discover_course_teams_async(course_id: uuid.UUID) -> None:
    """Discover new GitLab subgroups for a course and upsert them as teams.

    Fire-and-forget background task launched from /sync-all so the API
    response can return immediately instead of blocking on 10-20 s of
    GitLab API roundtrips.  Uses its own DB session because the request
    scope ends before this coroutine completes.

    Newly created teams will be synced on the NEXT /sync-all invocation.
    For the current call we accept a small consistency lag in exchange
    for instant user feedback.
    """
    from app.db.session import async_session_ctx
    from app.models.course_settings import CourseSettings

    try:
        async with async_session_ctx() as db:
            cs_result = await db.execute(
                select(CourseSettings).where(CourseSettings.course_id == course_id)
            )
            cs = cs_result.scalar_one_or_none()
            if not cs or not cs.gitlab_group_path:
                return

            settings = get_settings()
            from app.services.gitlab.client import GitLabClient
            from app.services.gitlab_import.persistence import (
                _collect_subgroups,
                _derive_team_name,
                _upsert_team,
            )
            from app.services.gitlab_import.service import select_team_group_records

            async with GitLabClient(
                base_url=str(settings.gitlab_url),
                private_token=settings.gitlab_api_token,
            ) as gl_client:
                root_group = await gl_client.get_group(cs.gitlab_group_path)
                if not root_group:
                    return
                root_group_id = root_group.get("id")
                if not root_group_id:
                    return
                subgroups = await _collect_subgroups(gl_client, int(root_group_id))
                group_records = [root_group, *subgroups]
                projects = await gl_client.get_group_projects(
                    int(root_group_id),
                    include_subgroups=True,
                    include_archived=False,
                )
                project_namespace_paths = {
                    ns for p in projects if (ns := (p.get("namespace", {}) or {}).get("full_path"))
                }
                team_records = select_team_group_records(
                    group_records,
                    root_group_id=int(root_group_id),
                    project_namespace_paths=project_namespace_paths,
                )
                _discovered = 0
                for gr in team_records:
                    gr_id = gr.get("id")
                    gr_path = gr.get("full_path") or str(gr_id)
                    if not gr_id:
                        continue
                    _, created = await _upsert_team(
                        db=db,
                        course_id=course_id,
                        name=_derive_team_name(gr),
                        gitlab_group_id=int(gr_id),
                        gitlab_group_path=str(gr_path),
                    )
                    if created:
                        _discovered += 1
                if _discovered:
                    await db.commit()
                    logger.info(
                        "sync_all_discovered_teams",
                        course_id=str(course_id),
                        count=_discovered,
                    )
    except Exception:
        logger.warning("sync_all_team_discovery_failed", course_id=str(course_id), exc_info=True)


async def _create_sync_jobs(
    db: DbSession,
    teams: list[Team],
    course_id: uuid.UUID,
    fresh_ids: set[uuid.UUID],
    active_sync_team_ids: set[uuid.UUID],
) -> tuple[list[tuple[Team, BackgroundJob]], int, int]:
    """Pass 1 of a Sync All: a BackgroundJob row per group that needs a sync,
    COMMITTED before anything is enqueued - otherwise the first group's RQ job
    can fire before the request commits, the worker cannot find its row, and
    the group shows N/A on the dashboard although it synced fine.

    Groups synced within the TTL are counted ``already_fresh``; groups with a
    sync in flight (a project-scoped one refreshes overlapping data too) are
    ``skipped``. Returns the jobs and those two counts.
    """
    jobs: list[tuple[Team, BackgroundJob]] = []
    already_fresh = skipped = 0
    for team in teams:
        if team.id in fresh_ids:
            already_fresh += 1
            continue
        if team.id in active_sync_team_ids:
            skipped += 1
            continue
        # Tagged with course_id so Job History shows these per-team jobs as a
        # "Course sync" (the whole course was synced), not as if the teacher
        # had synced each group individually. A single-group sync leaves
        # course_id unset and stays labelled "Group sync".
        job = BackgroundJob(job_type="sync", team_id=team.id, course_id=course_id)
        db.add(job)
        await db.flush()  # assign PK
        jobs.append((team, job))
    if jobs:
        await db.commit()
    return jobs, already_fresh, skipped


async def _enqueue_sync_jobs(
    db: DbSession,
    jobs: list[tuple[Team, BackgroundJob]],
    course_id: uuid.UUID,
) -> tuple[int, int]:
    """Pass 2: hand each committed job to RQ. Returns (enqueued, failed)."""
    enqueued = failed = 0
    for team, job in jobs:
        try:
            rq_job_id = enqueue_sync_job(str(team.id), str(job.id), str(course_id))
            if rq_job_id:
                job.rq_job_id = rq_job_id
                enqueued += 1
            else:
                job.status = "failed"
                job.error_message = "Failed to enqueue sync job."
                failed += 1
        except (ConnectionError, TimeoutError, OSError):
            logger.exception("sync_all_enqueue_failed", team_id=str(team.id))
            job.status = "failed"
            job.error_message = "Failed to enqueue sync job (Redis unavailable)"
            failed += 1
        await db.flush()
    return enqueued, failed


def _sync_all_message(enqueued: int, skipped: int, failed: int, already_fresh: int) -> str:
    if enqueued == 0 and already_fresh > 0 and skipped == 0 and failed == 0:
        return (
            f"All {already_fresh} groups already up-to-date "
            f"(synced within {int(SYNC_FRESHNESS_TTL.total_seconds() // 60)} min)."
        )
    return (
        f"Sync enqueued for {enqueued} groups, {skipped} already running, "
        f"{already_fresh} up-to-date, {failed} failed."
    )


@router.post("/courses/{course_id}/sync-all", response_model=SyncAllResponse, status_code=202)
async def trigger_sync_all(
    course_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    force: bool = False,
) -> SyncAllResponse:
    """Trigger a full sync for ALL active teams in a course (teacher/admin only).

    Enqueues individual sync jobs for every active team that does not already
    have a running or enqueued sync job.  Teams whose last successful sync
    completed within ``SYNC_FRESHNESS_TTL`` are reported as ``already_fresh``
    and skipped - pass ``?force=true`` to bypass that guard.
    """
    if not await _has_active_rq_workers():
        raise_service_unavailable(
            "No active background worker. Start worker process and retry sync."
        )

    await require_gitlab_ready()

    from app.models.course import Course as CourseModel

    course = await db.get(CourseModel, course_id)
    if not course:
        raise_not_found("Course not found")

    # Authorize against THIS course before enqueuing a course-wide sync.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, course=course):
        raise_not_found("Course not found")

    if not course.is_active:
        raise_conflict("This course is archived and read-only. Reactivate it to sync.")

    # -- Discover new teams (subgroups) from GitLab --
    # If the course has a gitlab_group_path, fetch subgroups and create
    # teams for any that are not yet in the DB.
    #
    # PERFORMANCE: this previously ran INLINE before enqueuing - for large
    # courses the GitLab API roundtrips (get_group + recursive
    # _collect_subgroups + paginated get_group_projects) added 10-20 s of
    # latency between the user's click and the first per-team enqueue,
    # which the user perceived as "nothing happens for 20 s after pressing
    # Sync".  Discovery is now fire-and-forget on a background task with
    # its own DB session - newly discovered teams are picked up on the
    # next /sync-all invocation.  The user gets instant feedback because
    # the response now returns within ~100 ms of the request reaching the
    # handler.
    _discovery_task = asyncio.create_task(_discover_course_teams_async(course_id))
    _BACKGROUND_TASKS.add(_discovery_task)
    _discovery_task.add_done_callback(_BACKGROUND_TASKS.discard)

    # Get all active teams
    team_stmt = (
        select(Team)
        .where(Team.course_id == course_id, Team.is_active.is_(True))
        .order_by(Team.name)
    )
    team_result = await db.execute(team_stmt)
    teams = list(team_result.scalars().all())

    if not teams:
        return SyncAllResponse(
            enqueued=0,
            skipped=0,
            failed=0,
            message="No active groups in course.",
        )

    # Reconcile stale BGjobs before checking which teams need syncing
    reconciled = await _reconcile_stale_jobs(db, [t.id for t in teams])
    if reconciled:
        await db.commit()  # persist reconciliation so loop sees clean state

    for team_id in sorted((t.id for t in teams), key=str):
        await _lock_team_job_scope(db, team_id)

    active_checks_team_ids = await _active_run_checks_team_ids(db, [t.id for t in teams])
    if active_checks_team_ids:
        raise_conflict("Cannot sync course groups while compliance checks are running.")

    # Freshness short-circuit: skip teams already synced within the TTL window
    # unless the caller explicitly requested a forced re-sync.
    fresh_ids: set[uuid.UUID] = set()
    if not force:
        fresh_ids = await _recently_synced_team_ids(db, [t.id for t in teams])

    # Batch the "is a sync already in flight for this group?" check into a
    # single query over all groups (was an N+1: one SELECT per group). Each
    # per-group query only ever matched that group's own pre-existing jobs, and
    # the new rows we add below don't exist yet when their own group is checked,
    # so the up-front batched set is exactly equivalent. Project-scoped syncs
    # refresh overlapping data, so sync-all must not enqueue a group-wide sync on
    # top of an active one.
    active_sync_team_ids = await _active_sync_team_ids(db, [t.id for t in teams])

    jobs_to_enqueue, already_fresh, skipped = await _create_sync_jobs(
        db, teams, course_id, fresh_ids, active_sync_team_ids
    )
    enqueued, failed = await _enqueue_sync_jobs(db, jobs_to_enqueue, course_id)

    logger.info(
        "sync_all_triggered",
        course_id=str(course_id),
        enqueued=enqueued,
        skipped=skipped,
        failed=failed,
        already_fresh=already_fresh,
        force=force,
    )

    await write_audit(
        db,
        action="sync_all",
        actor=get_actor(request, fallback="api_token"),
        entity_type="course",
        entity_id=course_id,
        detail={
            "summary": f"Sync triggered for {enqueued} teams "
            f"({skipped} skipped, {failed} failed, {already_fresh} up-to-date)",
            "enqueued": enqueued,
            "skipped": skipped,
            "failed": failed,
            "already_fresh": already_fresh,
            "force": force,
        },
    )
    await db.commit()

    return SyncAllResponse(
        enqueued=enqueued,
        skipped=skipped,
        failed=failed,
        already_fresh=already_fresh,
        message=_sync_all_message(enqueued, skipped, failed, already_fresh),
    )


@router.get("/courses/{course_id}/sync-status", response_model=CourseSyncStatusResponse)
async def get_course_sync_status(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiAuth,
) -> CourseSyncStatusResponse:
    """Get current sync status and metrics for all teams in a course.

    Used by the frontend to poll for live updates during sync operations.
    """
    from app.api.helpers.course_sync_state import course_sync_state, last_updated
    from app.models.course import Course

    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, course=course):
        raise_not_found("Course not found")
    state = await course_sync_state(db, course)

    teams_status: list[TeamSyncStatus] = []
    for team in state.teams:
        tm = state.team_metrics.get(team.id)
        sync_state = state.status_by_team.get(team.id)
        updated, updated_iso = last_updated(tm, sync_state)
        teams_status.append(
            TeamSyncStatus(
                team_id=str(team.id),
                team_name=team.name,
                member_count=state.member_counts.get(team.id, 0),
                sync_status=sync_state,
                avg_score=tm.avg_weighted_score if tm else None,
                traffic_light=tm.overall_traffic_light if tm else None,
                last_updated=updated,
                last_updated_iso=updated_iso,
                sync_note=state.note_by_team.get(team.id),
            )
        )

    # Progress. Denominator = ALL groups in the course (what the reader sees
    # in the Groups table): a 3-min "burst" window used to give "2/4 groups
    # done" banners on 8-group courses that nobody could reconcile with the
    # table. Numerator = groups not running or queued - done, whether they
    # succeeded or failed: "N groups, M still working, N-M done".
    total = len(state.teams)
    done = max(0, total - state.in_flight)
    total_students = 0
    if state.teams:
        from app.api.dashboard._stats import total_distinct_contributors
        from app.utils.semester import semester_floor_utc as _sem_floor_utc

        _sem_floor = _sem_floor_utc(course.settings if course else None)
        total_students = await total_distinct_contributors(
            db, [t.id for t in state.teams], commit_since=_sem_floor
        )

    return CourseSyncStatusResponse(
        sync_running_count=state.count("running"),
        sync_queued_count=state.count("enqueued"),
        sync_failed_count=state.count("failed"),
        sync_cancelled_count=state.count("cancelled"),
        # Match the stream's between-batch grace window. Project-only work
        # has its own tracker and must not create a second course-wide bar.
        has_active_sync=state.in_flight > 0 or bool(state.recently_finished),
        total_students=total_students,
        synced_groups=done if total > 0 else None,
        total_groups=total if total > 0 else None,
        progress=round(done / total * 100) if total > 0 and state.in_flight > 0 else None,
        teams=teams_status,
        sync_status_by_project={str(pid): s for pid, s in state.status_by_project.items()},
        project_sync_running_count=state.project_count("running"),
        project_sync_queued_count=state.project_count("enqueued"),
        # cached_status() is a pure in-process/Redis read (NO network probe), so
        # the sync-status poll never blocks on a GitLab round-trip. The flag is
        # poisoned by GitLabClient on the first 401, so the banner still appears.
        gitlab_token_ok=(_gitlab_cached_status() != "unauthorized"),
    )


@router.get("/sync/active")
async def get_active_syncs(
    request: Request,
    db: DbSession,
    _auth: ApiAuth,
) -> ActiveSyncsResponse:
    """List courses with currently running/queued sync jobs.

    Allows the global job bar to discover in-progress syncs on any page
    (admin, user management, etc.) even when the browser's localStorage
    has no record of them - e.g. sync started in another tab / device
    or by a scheduled background job.

    Course staff see the same courses they can track through the
    course sync poll and stream; admins and API keys can track all courses.
    """
    from app.api.dashboard._access import _staff_course_ids
    from app.models.course import Course

    cutoff = datetime.now(UTC) - timedelta(hours=2)
    grace = datetime.now(UTC) - timedelta(seconds=15)

    # Reconcile stale jobs first. Without this, syncs whose worker
    # was killed (e.g. during a deploy) sit forever in `running`
    # status, the global progress bar shows them as "active", and
    # nothing else triggers reconciliation because the SSE stream is
    # only opened from the course page. Polling `/sync/active`
    # happens on every page, so it is the natural place to clean up.
    team_ids_stmt = (
        select(BackgroundJob.team_id)
        .where(
            BackgroundJob.job_type == "sync",
            BackgroundJob.project_id.is_(None),
            BackgroundJob.team_id.is_not(None),
            BackgroundJob.status.in_(("enqueued", "started", "running")),
            BackgroundJob.enqueued_at >= cutoff,
        )
        .distinct()
    )
    stale_team_ids = [tid for (tid,) in (await db.execute(team_ids_stmt)).all() if tid]
    if stale_team_ids:
        try:
            await _reconcile_stale_jobs(db, stale_team_ids)
        except Exception:  # pragma: no cover - reconcile is best-effort
            logger.debug("active_syncs_reconcile_failed", exc_info=True)

    # Include `completed` jobs inside the 15 s grace window so brief lulls
    # between the last team finishing and the client fetching this
    # endpoint do not make the progress bar vanish prematurely.
    stmt = (
        select(
            Team.course_id,
            Course.name,
            Course.code,
            BackgroundJob.status,
            BackgroundJob.enqueued_at,
        )
        .join(Team, BackgroundJob.team_id == Team.id)
        .join(Course, Team.course_id == Course.id)
        .where(
            BackgroundJob.job_type == "sync",
            BackgroundJob.project_id.is_(None),
            or_(
                BackgroundJob.status.in_(("enqueued", "started", "running")),
                and_(
                    BackgroundJob.status.in_(("completed", "failed", "cancelled")),
                    BackgroundJob.completed_at >= grace,
                ),
            ),
            BackgroundJob.enqueued_at >= cutoff,
        )
    )
    rows = (await db.execute(stmt)).all()

    per_course: dict[uuid.UUID, dict[str, Any]] = {}
    for course_id, name, code, status, enqueued_at in rows:
        bucket = per_course.setdefault(
            course_id,
            {
                "course_id": str(course_id),
                "name": name,
                "code": code,
                "running": 0,
                "queued": 0,
                "started_at_ms": None,
            },
        )
        if status in ("running", "started"):
            bucket["running"] = int(bucket["running"]) + 1
        elif status == "enqueued":
            bucket["queued"] = int(bucket["queued"]) + 1
        # Recent terminal jobs keep the course visible between batches.
        if enqueued_at is not None:
            # Track the earliest enqueue time so the client can tell
            # whether a dismissed bar refers to this run or a later one.
            ts_ms = int(enqueued_at.timestamp() * 1000)
            prev = bucket["started_at_ms"]
            if prev is None or ts_ms < prev:
                bucket["started_at_ms"] = ts_ms

    if per_course and _auth == "session":
        session_data = _validate_session(request, get_settings()) or {}
        visible_ids = await _staff_course_ids(db, list(per_course), session_data)
        per_course = {cid: data for cid, data in per_course.items() if cid in visible_ids}

    return ActiveSyncsResponse(
        courses=[ActiveSyncCourse(**data) for data in per_course.values()],
    )


# -- SSE stream for course sync status --
