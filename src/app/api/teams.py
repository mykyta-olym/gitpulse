"""Team API endpoints."""

import uuid
from contextlib import suppress
from typing import Any

import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select, update

from app.api.errors import (
    check_optimistic_lock,
    raise_conflict,
    raise_not_found,
    raise_unprocessable,
)
from app.api.helpers.job_guards import (
    active_job_conflict_fields,
    active_job_conflict_message,
    find_active_team_mutation_job,
    lock_team_mutation_scope,
)
from app.api.helpers.utils import check_course_access, get_actor
from app.dependencies import ApiAuth, ApiTeacherAuth, DbSession, SettingsDep
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.student import Student
from app.models.team import Team
from app.models.team_member import TeamMember
from app.schemas.students import StudentRead
from app.schemas.teams import TeamCreate, TeamRead, TeamUpdate

logger = structlog.get_logger(__name__)
router = APIRouter()


# -- Teams --


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(team_id: uuid.UUID, request: Request, db: DbSession, _auth: ApiAuth) -> Team:
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")

    # ApiAuth only authenticates; scope to the team's course so a student can't
    # read arbitrary groups by UUID. Bearer tokens + admins unrestricted.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, team=team):
        raise_not_found("Group not found")
    return team


# Create team is nested under courses - see courses router
# But we also provide it here for convenience
@router.post("/", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    settings: SettingsDep,
) -> Team:
    """Create a new team (teacher/admin only)."""
    course_id = data.course_id
    if course_id is None:
        raise_unprocessable("course_id is required")
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify groups in courses you don't teach",
    )
    from app.services.courses import ensure_course_active

    await ensure_course_active(db, course_id)
    team = Team(
        course_id=course_id,
        name=data.name,
        gitlab_group_id=data.gitlab_group_id,
        gitlab_group_path=data.gitlab_group_path,
    )
    db.add(team)
    await db.flush()
    logger.info("team_created", team_id=str(team.id), name=team.name)
    return team


@router.put("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: uuid.UUID,
    data: TeamUpdate,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    settings: SettingsDep,
) -> Team:
    """Update team (teacher/admin only)."""
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")
    course = await db.get(Course, team.course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify groups in courses you don't teach",
    )

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    check_optimistic_lock(team, data.expected_updated_at, label="Group")

    updatable_fields = {"is_active"}
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in updatable_fields:
            setattr(team, key, value)

    await db.flush()
    logger.info("team_updated", team_id=str(team_id))
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    settings: SettingsDep,
) -> None:
    """Delete team (teacher/admin only)."""
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")
    course = await db.get(Course, team.course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify groups in courses you don't teach",
    )

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    # Serialize against sync/check enqueue routes, then refuse destructive
    # changes while a job could still write metrics or project state.
    from app.api.helpers.sync import _reconcile_stale_jobs
    from app.models.background_job import BackgroundJob

    await _reconcile_stale_jobs(db, [team_id])
    await lock_team_mutation_scope(db, team_id)
    active_job = await find_active_team_mutation_job(db, team_id)
    if active_job is not None:
        raise_conflict(
            active_job_conflict_message("delete group", active_job),
            fields=active_job_conflict_fields(active_job),
        )

    # Soft delete
    team.is_active = False

    # Deactivate all team members

    from app.models.team_member import TeamMember

    members_result = await db.execute(
        update(TeamMember)
        .where(TeamMember.team_id == team_id, TeamMember.is_active.is_(True))
        .values(is_active=False)
        .returning(TeamMember.student_id)
    )
    deactivated_member_ids = [str(student_id) for (student_id,) in members_result.all()]
    projects_result = await db.execute(
        update(GitLabProject)
        .where(GitLabProject.team_id == team_id, GitLabProject.is_active.is_(True))
        .values(is_active=False)
        .returning(GitLabProject.id)
    )
    deactivated_project_ids = [str(project_id) for (project_id,) in projects_result.all()]

    # Cancel any pending (enqueued) background jobs for this team
    await db.execute(
        update(BackgroundJob)
        .where(
            BackgroundJob.team_id == team_id,
            BackgroundJob.status == "enqueued",
        )
        .values(status="cancelled")
    )

    await db.flush()

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="team_delete",
        actor=get_actor(request),
        entity_type="team",
        entity_id=team.id,
        detail={
            "summary": f"Team soft-deleted: {team.name}",
            "course_id": str(team.course_id),
            "deactivated_projects": deactivated_project_ids,
            "deactivated_members": deactivated_member_ids,
        },
    )

    logger.info(
        "team_deleted",
        team_id=str(team_id),
        deactivated_project_count=len(deactivated_project_ids),
    )

    _team_id_for_event = str(team_id)
    _course_id_for_event = str(team.course_id)
    await db.commit()
    try:
        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            team_id=team_id,
            course_id=team.course_id,
            student_ids=deactivated_member_ids,
        )
        for _pid in deactivated_project_ids:
            invalidate_cascade(project_id=_pid)
    except Exception:
        logger.debug("team_delete_page_cache_invalidate_failed", exc_info=True)
    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("team", _team_id_for_event, "team_deleted")
        publish_dashboard_update(
            "course",
            _course_id_for_event,
            "team_deleted",
            extra={"team_id": _team_id_for_event},
        )
    with suppress(Exception):
        from app.services.events import enqueue_metrics_refresh

        enqueue_metrics_refresh(_team_id_for_event)


@router.delete("/{team_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_permanent(
    team_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    settings: SettingsDep,
) -> None:
    """Permanently delete team and all associated records (teacher/admin only)."""
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")
    course = await db.get(Course, team.course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify groups in courses you don't teach",
    )

    from app.api.helpers.sync import _reconcile_stale_jobs
    from app.models.background_job import BackgroundJob

    await _reconcile_stale_jobs(db, [team_id])
    await lock_team_mutation_scope(db, team_id)
    active_job = await find_active_team_mutation_job(db, team_id)
    if active_job is not None:
        raise_conflict(
            active_job_conflict_message("permanently delete group", active_job),
            fields=active_job_conflict_fields(active_job),
        )

    from app.services.job_history import delete_job_history

    project_ids = list(
        await db.scalars(select(GitLabProject.id).where(GitLabProject.team_id == team_id))
    )
    student_ids = list(
        await db.scalars(select(TeamMember.student_id).where(TeamMember.team_id == team_id))
    )
    await delete_job_history(
        db,
        or_(BackgroundJob.team_id == team_id, BackgroundJob.project_id.in_(project_ids)),
        require_all=True,
    )

    # Delete the team. Cascade deletes will clean up projects, members, snapshots, etc.
    await db.delete(team)

    _team_id_for_event = str(team_id)
    _course_id_for_event = str(team.course_id)
    await db.commit()
    try:
        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            team_id=team_id,
            course_id=team.course_id,
            student_ids=student_ids,
        )
        for project_id in project_ids:
            invalidate_cascade(project_id=project_id)
    except Exception:
        logger.debug("team_delete_permanent_page_cache_invalidate_failed", exc_info=True)

    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("team", _team_id_for_event, "team_deleted")
        publish_dashboard_update(
            "course",
            _course_id_for_event,
            "team_deleted",
            extra={"team_id": _team_id_for_event},
        )


async def _restore_deleted_rows(db: DbSession, team_id: uuid.UUID) -> tuple[list[str], list[str]]:
    """Reactivate the members and projects the group's latest ``team_delete``
    deactivated - all inactive ones for a legacy delete without that record.
    A project unlinked on its own before the delete stays unlinked: the
    unlink is an explicit override. Returns the restored member and project ids.
    """
    from app.models.audit_log import AuditLog
    from app.models.team_member import TeamMember

    audit_row = (
        await db.execute(
            select(AuditLog)
            .where(
                AuditLog.action == "team_delete",
                AuditLog.entity_type == "team",
                AuditLog.entity_id == team_id,
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    member_ids: list[uuid.UUID] | None = None
    project_ids: list[uuid.UUID] | None = None
    if audit_row is not None:
        detail = audit_row.detail or {}
        member_ids = [uuid.UUID(m) for m in detail.get("deactivated_members", [])]
        project_ids = [uuid.UUID(p) for p in detail.get("deactivated_projects", [])]
    members = await _reactivate(db, TeamMember, TeamMember.student_id, team_id, member_ids)
    projects = await _reactivate(db, GitLabProject, GitLabProject.id, team_id, project_ids)
    return members, projects


async def _reactivate(
    db: DbSession, model: Any, id_col: Any, team_id: uuid.UUID, ids: list[uuid.UUID] | None
) -> list[str]:
    """Set the group's inactive rows of ``model`` active - only ``ids`` when given."""
    if ids is not None and not ids:
        return []
    stmt = update(model).where(model.team_id == team_id, model.is_active.is_(False))
    if ids is not None:
        stmt = stmt.where(id_col.in_(ids))
    res = await db.execute(stmt.values(is_active=True).returning(id_col))
    return [str(row_id) for (row_id,) in res.all()]


async def _refresh_projects(
    db: DbSession, settings: Any, team_id: uuid.UUID, project_ids: list[str]
) -> None:
    """Queue an incremental refresh of each restored project."""
    try:
        from redis import Redis
        from rq import Queue

        conn = Redis.from_url(str(settings.redis_url))
        rq_queue = Queue(connection=conn)
        project_rows = (
            (
                await db.execute(
                    select(GitLabProject).where(
                        GitLabProject.id.in_([uuid.UUID(p) for p in project_ids])
                    )
                )
            )
            .scalars()
            .all()
        )
        for proj in project_rows:
            rq_queue.enqueue(
                "app.workers.sweep._incremental_project_refresh",
                str(proj.id),
                proj.gitlab_project_id,
                job_timeout=300,
            )
    except Exception:
        logger.debug("reactivate_team_sync_enqueue_failed", team_id=str(team_id), exc_info=True)


@router.post(
    "/{team_id}/reactivate",
    status_code=status.HTTP_200_OK,
    name="reactivate_team",
)
async def reactivate_team(
    team_id: uuid.UUID,
    db: DbSession,
    _auth: ApiTeacherAuth,
    request: Request,
    settings: SettingsDep,
) -> JSONResponse:
    """Restore a soft-deleted group (teacher/admin only).

    Reactivates the group and precisely restores the members and projects
    that were deactivated by the *most recent* ``team_delete`` of this group.
    Projects that were individually unlinked *before* the group was deleted
    are intentionally left deactivated (the unlink is an explicit override).
    A background sync is enqueued for each restored project.
    """

    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")
    course = await db.get(Course, team.course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify groups in courses you don't teach",
    )

    if team.is_active:
        return JSONResponse({"status": "already_active", "team_id": str(team_id)})

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, team.course_id)

    # Serialize against sync/check enqueue routes so a restore cannot race a
    # job that is about to write metrics or project state for this group.
    from app.api.helpers.sync import _reconcile_stale_jobs

    await _reconcile_stale_jobs(db, [team_id])
    await lock_team_mutation_scope(db, team_id)
    active_job = await find_active_team_mutation_job(db, team_id)
    if active_job is not None:
        raise_conflict(
            active_job_conflict_message("restore group", active_job),
            fields=active_job_conflict_fields(active_job),
        )

    team.is_active = True
    restored_member_ids, restored_project_ids = await _restore_deleted_rows(db, team_id)

    await db.flush()

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="team_reactivate",
        actor=get_actor(request),
        entity_type="team",
        entity_id=team.id,
        detail={
            "summary": f"Group restored: {team.name}",
            "course_id": str(team.course_id),
            "restored_projects": restored_project_ids,
            "restored_members": restored_member_ids,
        },
    )

    # Enqueue an incremental sync for each restored project so metrics,
    # rankings and checks pick the group back up immediately.
    if restored_project_ids:
        await _refresh_projects(db, settings, team_id, restored_project_ids)

    logger.info(
        "team_reactivated",
        team_id=str(team_id),
        restored_project_count=len(restored_project_ids),
        restored_member_count=len(restored_member_ids),
    )

    _team_id_for_event = str(team_id)
    _course_id_for_event = str(team.course_id)
    await db.commit()
    try:
        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            team_id=team_id,
            course_id=team.course_id,
            student_ids=restored_member_ids,
        )
        for _pid in restored_project_ids:
            invalidate_cascade(project_id=_pid)
    except Exception:
        logger.debug("team_reactivate_page_cache_invalidate_failed", exc_info=True)
    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update("team", _team_id_for_event, "team_reactivated")
        publish_dashboard_update(
            "course",
            _course_id_for_event,
            "team_reactivated",
            extra={"team_id": _team_id_for_event},
        )
    with suppress(Exception):
        from app.services.events import enqueue_metrics_refresh

        enqueue_metrics_refresh(_team_id_for_event)
    return JSONResponse(
        {
            "status": "reactivated",
            "team_id": str(team_id),
            "restored_projects": len(restored_project_ids),
            "restored_members": len(restored_member_ids),
        }
    )


# -- Members --


@router.get("/{team_id}/members", response_model=list[StudentRead])
async def list_members(
    team_id: uuid.UUID, request: Request, db: DbSession, _auth: ApiTeacherAuth
) -> list[Student]:
    # Validate team exists
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")

    # Scope to the team's course so a teacher can't list the members (names +
    # emails) of a group in a course they don't teach. Bearer + admin unrestricted.
    from app.api.dashboard._access import can_manage_via_request

    if not await can_manage_via_request(request, db, team=team):
        raise_not_found("Group not found")

    # Single JOIN query instead of loading members then querying students
    stmt = (
        select(Student)
        .join(TeamMember, TeamMember.student_id == Student.id)
        .where(TeamMember.team_id == team_id, TeamMember.is_active.is_(True))
        .order_by(Student.full_name)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
