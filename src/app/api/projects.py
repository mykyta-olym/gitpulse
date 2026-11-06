"""GitLab project registration endpoints."""

import hashlib
import json as _json
import uuid
from contextlib import suppress
from typing import Any

import structlog
from fastapi import APIRouter, Query, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import raise_conflict, raise_not_found
from app.api.helpers.job_guards import (
    active_job_conflict_fields,
    active_job_conflict_message,
    find_active_team_mutation_job,
    lock_project_mutation_scope,
    lock_team_mutation_scope,
)
from app.config import get_settings
from app.dependencies import ApiTeacherAuth, DbSession
from app.models.project import GitLabProject
from app.models.team import Team
from app.schemas.projects import (
    ProjectRead,
    ProjectRegister,
    ProjectRegistered,
)
from app.security.webhook_auth import (
    compute_webhook_lookup_key,
    generate_webhook_secret,
    hash_webhook_secret,
)

logger = structlog.get_logger(__name__)
router = APIRouter()

# GitLab "intelligence" panels (protected branches, contributors, statistics,
# milestones, releases, labels) serve data that changes only on a sync. The
# project page re-fetches them on every visit, and the browser can't cache the
# responses because apiCall() defaults to `no-store` AND the responses carried
# no cache headers. Serve them with private HTTP caching + a content-derived
# ETag so repeat visits (and other tabs) come from the browser cache and only
# revalidate cheaply (304) once the max-age lapses. A data-changing refresh on
# the client bypasses the cache (fetch `cache: 'reload'`) so freshness is kept.
_INTEL_CACHE_MAX_AGE = 300  # seconds (matches the client-side sessionStorage TTL)


def _cached_json(
    request: Request,
    data: Any,
    *,
    max_age: int = _INTEL_CACHE_MAX_AGE,
) -> Response:
    """Return ``data`` as JSON with private caching + ETag revalidation.

    The ETag is a hash of the payload, so it is correct regardless of whether
    the data came from the stored snapshot or a live GitLab call: identical
    content -> identical ETag -> a conditional request gets a bodyless 304.
    """
    body = _json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
    etag = 'W/"' + hashlib.sha256(body.encode("utf-8")).hexdigest()[:20] + '"'
    headers = {"Cache-Control": f"private, max-age={max_age}", "ETag": etag}
    if_none_match = request.headers.get("if-none-match", "")
    if if_none_match and etag in {tok.strip() for tok in if_none_match.split(",")}:
        return Response(status_code=304, headers=headers)
    return JSONResponse(data, headers=headers)


async def _get_project_with_access(
    project_id: uuid.UUID,
    db: "AsyncSession",
    auth_kind: str,
    request: Request,
) -> GitLabProject:
    """Load project and verify the caller has access to its course."""
    project = await db.get(GitLabProject, project_id)
    if not project:
        raise_not_found("Project not found")
    team = await db.get(Team, project.team_id)
    if not team:
        raise_not_found("Group not found")
    from app.models.course import Course

    course = await db.get(Course, team.course_id)
    if not course:
        raise_not_found("Course not found")
    from app.api.helpers.utils import check_course_access

    await check_course_access(
        course,
        auth_kind,
        request,
        db,
        action_label="modify projects in courses you don't teach",
    )
    return project


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    request: Request,
    db: DbSession,
    auth_kind: ApiTeacherAuth,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[GitLabProject]:
    """List registered GitLab projects scoped to caller's courses."""
    from app.api.helpers.utils import _resolve_caller
    from app.models.course_membership import CourseMembership

    caller, role = await _resolve_caller(request, db, auth_kind)
    if role == "admin" or auth_kind == "api_token":
        stmt = select(GitLabProject).offset(skip).limit(limit)
    else:
        if not caller:
            from app.api.errors import raise_forbidden

            raise_forbidden("User not found")
        # Teacher: only projects in courses they teach
        course_ids_sub = select(CourseMembership.course_id).where(
            CourseMembership.user_id == caller.id,
            CourseMembership.role.in_(("owner", "teacher")),
        )
        stmt = (
            select(GitLabProject)
            .join(Team, GitLabProject.team_id == Team.id)
            .where(Team.course_id.in_(course_ids_sub))
            .offset(skip)
            .limit(limit)
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/{team_id}/projects",
    response_model=ProjectRegistered,
    status_code=status.HTTP_201_CREATED,
    name="register_project",
    # Override prefix: this is under /api/v1/teams/{team_id}/projects
)
async def register_project(
    team_id: uuid.UUID,
    data: ProjectRegister,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> ProjectRegistered:
    """Register a GitLab project (teacher/admin only)."""
    team = await db.get(Team, team_id)
    if not team:
        raise_not_found("Group not found")

    from app.api.helpers.utils import check_course_access
    from app.models.course import Course

    course = await db.get(Course, team.course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="register projects in courses you don't teach",
    )

    from app.services.courses import ensure_course_active
    from app.services.page_cache import invalidate_cascade

    await ensure_course_active(db, course.id)

    # Check if project already registered
    from app.db.repositories.project_repo import ProjectRepository

    project_repo = ProjectRepository(db)
    existing = await project_repo.get_by_gitlab_id(data.gitlab_project_id)
    if existing:
        if existing.is_active:
            if existing.team_id == team_id:
                raise_conflict("This project is already linked to this group")
            raise_conflict("This GitLab project is already linked to another group")
        # Soft-deleted: same team -> reactivate, different team -> reassign
        previous_team = await db.get(Team, existing.team_id)
        existing.is_active = True
        existing.team_id = team_id
        existing.gitlab_project_path = data.gitlab_project_path
        existing.gitlab_project_name = data.gitlab_project_name
        # Rotate the webhook secret on reactivation
        secret = generate_webhook_secret()
        secret_hash = hash_webhook_secret(secret)
        existing.webhook_secret_hash = secret_hash
        existing.webhook_secret_lookup = compute_webhook_lookup_key(secret)
        await db.flush()
        await db.commit()
        invalidate_cascade(project_id=existing.id, team_id=team.id, course_id=course.id)
        if previous_team and previous_team.id != team.id:
            invalidate_cascade(team_id=previous_team.id, course_id=previous_team.course_id)

        settings = get_settings()
        webhook_url = f"{settings.app_base_url.rstrip('/')}/api/v1/webhooks/gitlab"

        setup_instructions = (
            f"1. Go to GitLab project Settings -> Webhooks\n"
            f"2. URL: {webhook_url}\n"
            f"3. Secret token: {secret}\n"
            "4. Trigger: Push events, Issues events, Merge request events, "
            "Note events, Pipeline events\n"
            f"5. Enable SSL verification\n"
            f"6. Click 'Add webhook'"
        )

        logger.info(
            "project_reactivated",
            project_id=str(existing.id),
            gitlab_project_id=data.gitlab_project_id,
            team_id=str(team_id),
        )

        return ProjectRegistered(
            id=existing.id,
            team_id=existing.team_id,
            gitlab_project_id=existing.gitlab_project_id,
            gitlab_project_path=existing.gitlab_project_path,
            gitlab_project_name=existing.gitlab_project_name,
            is_active=existing.is_active,
            last_synced_at=existing.last_synced_at,
            created_at=existing.created_at,
            webhook_secret=secret,
            webhook_url=webhook_url,
            setup_instructions=setup_instructions,
        )

    # Generate webhook secret
    secret = generate_webhook_secret()
    secret_hash = hash_webhook_secret(secret)
    secret_lookup = compute_webhook_lookup_key(secret)

    project = GitLabProject(
        team_id=team.id,
        gitlab_project_id=data.gitlab_project_id,
        gitlab_project_path=data.gitlab_project_path,
        gitlab_project_name=data.gitlab_project_name,
        webhook_secret_hash=secret_hash,
        webhook_secret_lookup=secret_lookup,
    )
    db.add(project)
    await db.flush()
    await db.commit()
    invalidate_cascade(project_id=project.id, team_id=team.id, course_id=course.id)

    settings = get_settings()
    webhook_url = f"{settings.app_base_url.rstrip('/')}/api/v1/webhooks/gitlab"

    setup_instructions = (
        f"1. Go to GitLab project Settings -> Webhooks\n"
        f"2. URL: {webhook_url}\n"
        f"3. Secret token: {secret}\n"
        "4. Trigger: Push events, Issues events, Merge request events, "
        "Note events, Pipeline events\n"
        f"5. Enable SSL verification\n"
        f"6. Click 'Add webhook'"
    )

    logger.info(
        "project_registered",
        project_id=str(project.id),
        gitlab_project_id=data.gitlab_project_id,
        team_id=str(team_id),
    )

    return ProjectRegistered(
        id=project.id,
        team_id=project.team_id,
        gitlab_project_id=project.gitlab_project_id,
        gitlab_project_path=project.gitlab_project_path,
        gitlab_project_name=project.gitlab_project_name,
        is_active=project.is_active,
        last_synced_at=project.last_synced_at,
        created_at=project.created_at,
        webhook_secret=secret,
        webhook_url=webhook_url,
        setup_instructions=setup_instructions,
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="delete_project",
)
async def delete_project(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> None:
    """Soft-delete/unlink a project (teacher/admin only)."""
    project = await _get_project_with_access(project_id, db, _auth, request)
    if not project.is_active:
        logger.info("project_soft_delete_noop_inactive", project_id=str(project_id))
        return

    if project.team_id:
        from app.services.courses import ensure_course_active

        team = await db.get(Team, project.team_id)
        if team is not None:
            await ensure_course_active(db, team.course_id)

    from app.api.helpers.sync import _reconcile_stale_jobs

    await _reconcile_stale_jobs(db, [project.team_id])
    await lock_team_mutation_scope(db, project.team_id)
    await lock_project_mutation_scope(db, project.id)
    active_job = await find_active_team_mutation_job(db, project.team_id)
    if active_job is not None:
        raise_conflict(
            active_job_conflict_message("unlink project", active_job),
            fields=active_job_conflict_fields(active_job),
        )

    project.is_active = False
    await db.flush()

    from app.api.helpers.utils import get_actor
    from app.services.audit import write_audit

    await write_audit(
        db,
        action="project_delete",
        actor=get_actor(request),
        entity_type="project",
        entity_id=project.id,
        detail={
            "summary": f"Project unlinked: {project.gitlab_project_path}",
            "team_id": str(project.team_id),
        },
    )
    logger.info("project_soft_deleted", project_id=str(project_id))

    _course_id_for_event: uuid.UUID | None = None
    from app.models.team import Team as _Team

    _team = await db.get(_Team, project.team_id)
    _course_id_for_event = _team.course_id if _team else None

    _project_id_for_event = str(project.id)
    _team_id_for_event = str(project.team_id)
    await db.commit()
    try:
        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            project_id=project.id,
            team_id=project.team_id,
            course_id=_course_id_for_event,
        )
    except Exception:
        logger.debug("project_delete_page_cache_invalidate_failed", exc_info=True)
    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update(
            "team",
            _team_id_for_event,
            "project_unlinked",
            extra={"project_id": _project_id_for_event},
        )
        if _course_id_for_event is not None:
            publish_dashboard_update(
                "course",
                str(_course_id_for_event),
                "project_unlinked",
                extra={"project_id": _project_id_for_event, "team_id": _team_id_for_event},
            )

    # The Group Summary cards (avg score, traffic-light status, pipeline pass
    # rate) are served from the latest stored TeamMetricSnapshot, which is only
    # rebuilt by a metrics recompute - not by the unlink itself. Without this,
    # the page list/count update but the headline numbers stay frozen on the
    # unlinked project's old contribution. Enqueue a recompute (the compliance
    # engine excludes is_active=False projects); when it lands it publishes a
    # `metrics_computed` SSE nudge so the open page refreshes the cards live.
    with suppress(Exception):
        from app.services.events import enqueue_metrics_refresh

        enqueue_metrics_refresh(_team_id_for_event)


@router.delete("/{project_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_permanent(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> None:
    """Permanently delete project and all associated records (teacher/admin only)."""
    project = await _get_project_with_access(project_id, db, _auth, request)

    from app.api.helpers.sync import _reconcile_stale_jobs
    from app.models.background_job import BackgroundJob

    await _reconcile_stale_jobs(db, [project.team_id])
    await lock_team_mutation_scope(db, project.team_id)
    await lock_project_mutation_scope(db, project.id)
    active_job = await find_active_team_mutation_job(db, project.team_id)
    if active_job is not None:
        raise_conflict(
            active_job_conflict_message("permanently delete project", active_job),
            fields=active_job_conflict_fields(active_job),
        )

    from app.services.job_history import delete_job_history

    await delete_job_history(db, BackgroundJob.project_id == project_id, require_all=True)

    # Delete project. Database FK ON DELETE CASCADE will clean up pipelines, commits, MRs, etc.
    await db.delete(project)

    _course_id_for_event: uuid.UUID | None = None
    from app.models.team import Team as _Team

    _team = await db.get(_Team, project.team_id)
    _course_id_for_event = _team.course_id if _team else None

    _project_id_for_event = str(project.id)
    _team_id_for_event = str(project.team_id)
    await db.commit()
    try:
        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            project_id=project.id,
            team_id=project.team_id,
            course_id=_course_id_for_event,
        )
    except Exception:
        logger.debug("project_delete_permanent_page_cache_invalidate_failed", exc_info=True)

    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update(
            "team",
            _team_id_for_event,
            "project_unlinked",
            extra={"project_id": _project_id_for_event},
        )
        if _course_id_for_event is not None:
            publish_dashboard_update(
                "course",
                str(_course_id_for_event),
                "project_unlinked",
                extra={"project_id": _project_id_for_event, "team_id": _team_id_for_event},
            )


@router.post(
    "/{project_id}/reactivate",
    status_code=status.HTTP_200_OK,
    name="reactivate_project",
)
async def reactivate_project(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> JSONResponse:
    """Reactivate a soft-deleted project (teacher/admin only).

    Sets ``is_active = True`` and enqueues a background sync to refresh
    project data from GitLab. A teacher who can unlink a project may also
    restore it; course-access is still enforced below.
    """
    from app.models.project import GitLabProject

    project = await db.get(GitLabProject, project_id)
    if not project:
        raise_not_found("Project not found")

    from app.api.helpers.utils import check_course_access, get_actor
    from app.models.course import Course
    from app.models.team import Team

    team = await db.get(Team, project.team_id)
    if team:
        course = await db.get(Course, team.course_id)
        if course:
            await check_course_access(
                course,
                _auth,
                request,
                db,
                action_label="reactivate projects in courses you don't teach",
            )

    if project.is_active:
        return JSONResponse({"status": "already_active", "project_id": str(project_id)})

    # A project cannot be restored on its own while its parent group is
    # deleted - that would leave an active project orphaned under an
    # archived group (it would be hidden everywhere the group is hidden and
    # excluded from the course aggregate, yet appear "active"). Restoring
    # the group is the correct action: reactivate_team brings back every
    # project that the group-delete deactivated.
    if team is not None and not team.is_active:
        raise_conflict(
            "This project's group is deleted. Restore the group to bring its projects back.",
            fields={"team_id": "The parent group is deleted - restore the group instead."},
        )

    if team is not None:
        from app.services.courses import ensure_course_active

        await ensure_course_active(db, team.course_id)

    project.is_active = True
    await db.flush()

    from app.services.audit import write_audit

    await write_audit(
        db,
        action="project_reactivate",
        actor=get_actor(request),
        entity_type="project",
        entity_id=project.id,
        detail={
            "summary": f"Project reactivated: {project.gitlab_project_path}",
            "team_id": str(project.team_id),
        },
    )
    logger.info("project_reactivated", project_id=str(project_id))

    from app.models.background_job import BackgroundJob
    from app.services.events import enqueue_project_sync_job

    course_id_str: str | None = str(team.course_id) if team and team.course_id else None

    job = BackgroundJob(
        job_type="sync",
        team_id=project.team_id,
        project_id=project.id,
    )
    db.add(job)
    await db.flush()

    job_id: str | None = str(job.id)
    try:
        rq_job_id = enqueue_project_sync_job(str(project.id), str(job.id), course_id_str)
        if rq_job_id:
            job.rq_job_id = rq_job_id
        else:
            job.status = "failed"
            job.error_message = "Failed to enqueue job (Redis unavailable)"
            job_id = None
        await db.flush()
    except Exception:
        logger.debug("reactivate_sync_enqueue_failed", project_id=str(project_id), exc_info=True)
        job.status = "failed"
        job.error_message = "Failed to enqueue job (Redis unavailable)"
        await db.flush()
        job_id = None

    _project_id_for_event = str(project.id)
    _team_id_for_event = str(project.team_id)
    _course_id_for_event = team.course_id if team and team.course_id else None
    await db.commit()
    try:
        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            project_id=project.id,
            team_id=project.team_id,
            course_id=team.course_id if team else None,
        )
    except Exception:
        logger.debug("project_reactivate_page_cache_invalidate_failed", exc_info=True)
    with suppress(Exception):
        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update(
            "team",
            _team_id_for_event,
            "project_reactivated",
            extra={"project_id": _project_id_for_event},
        )
        if _course_id_for_event is not None:
            publish_dashboard_update(
                "course",
                str(_course_id_for_event),
                "project_reactivated",
                extra={"project_id": _project_id_for_event, "team_id": _team_id_for_event},
            )

    # Recompute the team metric snapshot now so the Group Summary cards reflect
    # the restored project immediately from already-stored data, instead of
    # waiting for the enqueued GitLab sync to finish fetching. The recompute
    # publishes its own `metrics_computed` SSE nudge when it lands.
    with suppress(Exception):
        from app.services.events import enqueue_metrics_refresh

        enqueue_metrics_refresh(_team_id_for_event)

    return JSONResponse({"status": "reactivated", "project_id": str(project_id), "job_id": job_id})


# -- GitLab Intelligence Endpoints --


@router.get("/{project_id}/gitlab/protected-branches", name="project_protected_branches")
async def get_protected_branches(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Response:
    """List protected branches from the last synced project snapshot."""
    project = await _get_project_with_access(project_id, db, _auth, request)
    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    data = stored.get("protectedBranches")
    return _cached_json(request, data if isinstance(data, list) else [])


@router.get("/{project_id}/gitlab/contributors", name="project_contributors")
async def get_contributors(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Response:
    """List repository contributors with commit counts, filtered to team members."""
    project = await _get_project_with_access(project_id, db, _auth, request)

    # Load team members' identifiers for filtering
    from app.models.student import Student
    from app.models.team_member import TeamMember

    stmt = (
        select(Student.full_name, Student.email, Student.gitlab_username)
        .join(TeamMember, TeamMember.student_id == Student.id)
        .where(
            TeamMember.team_id == project.team_id,
            TeamMember.is_teacher.is_(False),
            TeamMember.is_mentor.is_(False),
            TeamMember.is_active.is_(True),
        )
    )
    rows = (await db.execute(stmt)).all()
    member_names: set[str] = set()
    member_emails: set[str] = set()
    # Canonical-name lookup: emails and lowercased GitLab usernames -> student.full_name.
    # GitLab's contributor list returns the git author display name (often a
    # generic placeholder like "student" for shared test accounts). When we can
    # match by email or username, prefer the human-readable full_name from
    # GitPulse so the widget shows "Ivan Kolosovskyi" instead of "student".
    canonical_by_email: dict[str, str] = {}
    canonical_by_name: dict[str, str] = {}
    for row in rows:
        if row.full_name:
            member_names.add(row.full_name.lower().strip())
        if row.email:
            member_emails.add(row.email.lower().strip())
            if row.full_name:
                canonical_by_email[row.email.lower().strip()] = row.full_name
        if row.gitlab_username:
            uname = row.gitlab_username.lower().strip()
            member_names.add(uname)
            if row.full_name:
                canonical_by_name[uname] = row.full_name

    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    data = stored.get("contributors")
    filtered: list[dict[str, object]] = []
    if isinstance(data, list):
        for c in data:
            if not isinstance(c, dict):
                continue
            raw_name = (c.get("name") or "").strip()
            raw_email = (c.get("email") or "").lower().strip()
            name_key = raw_name.lower()
            if name_key in member_names or raw_email in member_emails:
                # Rewrite generic / placeholder display names with the
                # canonical student full_name when we can identify them.
                canonical = canonical_by_email.get(raw_email) or canonical_by_name.get(name_key)
                if canonical and canonical != raw_name:
                    c = {**c, "name": canonical, "raw_name": raw_name}
                filtered.append(c)
    # Fallback: GitLab's /repository/contributors only counts commits on the
    # default branch. Student work commonly lives on feature branches and the
    # default branch can sit at 0 commits. When the stored contributor snapshot
    # has no team-member matches, aggregate from the locally-synced
    # `git_commits` table (populated by sync/webhooks, never by this endpoint).
    if not filtered:
        from app.models.commit import Commit
        from app.models.course_settings import CourseSettings
        from app.models.team import Team as _Team
        from app.utils.semester import semester_floor_utc

        # Semester scope: contributors must reflect *current semester* activity
        # only. Without this the panel keeps listing students who left after
        # last semester and the aggregate commit/additions/deletions inflate.
        _cs_stmt = (
            select(CourseSettings)
            .join(_Team, _Team.course_id == CourseSettings.course_id)
            .where(_Team.id == project.team_id)
        )
        _cs = (await db.execute(_cs_stmt)).scalar_one_or_none()
        _sem_floor = semester_floor_utc(_cs)

        _commit_conds: list[Any] = [Commit.project_id == project.id]
        if _sem_floor is not None:
            _commit_conds.append(Commit.committed_at >= _sem_floor)

        db_stmt = (
            select(
                func.coalesce(Commit.author_name, Commit.author_email).label("name"),
                Commit.author_email.label("email"),
                func.count(Commit.sha.distinct()).label("commits"),
                func.coalesce(func.sum(Commit.additions), 0).label("additions"),
                func.coalesce(func.sum(Commit.deletions), 0).label("deletions"),
            )
            .where(*_commit_conds)
            .group_by(Commit.author_name, Commit.author_email)
            .order_by(func.count(Commit.sha.distinct()).desc())
        )
        db_rows = (await db.execute(db_stmt)).all()
        for db_row in db_rows:
            raw_name = (db_row.name or "").strip()
            raw_email = (db_row.email or "").lower().strip()
            name_key = raw_name.lower()
            if name_key in member_names or raw_email in member_emails:
                canonical = canonical_by_email.get(raw_email) or canonical_by_name.get(name_key)
                display_name = canonical or raw_name
                filtered.append(
                    {
                        "name": display_name,
                        "email": raw_email,
                        "commits": int(db_row.commits or 0),
                        "additions": int(db_row.additions or 0),
                        "deletions": int(db_row.deletions or 0),
                        **({"raw_name": raw_name} if canonical and canonical != raw_name else {}),
                    }
                )
    return _cached_json(request, filtered)


@router.get("/{project_id}/gitlab/statistics", name="project_statistics")
async def get_statistics(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Response:
    """Get project statistics from the last synced project snapshot."""
    project = await _get_project_with_access(project_id, db, _auth, request)
    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    stats = stored.get("statistics")
    return _cached_json(request, stats if isinstance(stats, dict) else {})


@router.get("/{project_id}/gitlab/milestones", name="project_milestones")
async def get_milestones(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
    state: str = Query("all", pattern="^(active|closed|all)$"),
) -> Response:
    """List project milestones from the last synced project snapshot."""
    project = await _get_project_with_access(project_id, db, _auth, request)
    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    data = stored.get("milestones")
    milestones = data if isinstance(data, list) else []
    if state != "all":
        milestones = [m for m in milestones if isinstance(m, dict) and m.get("state") == state]
    return _cached_json(request, milestones)


@router.get("/{project_id}/gitlab/releases", name="project_releases")
async def get_releases(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Response:
    """List project releases from the last synced project snapshot."""
    project = await _get_project_with_access(project_id, db, _auth, request)
    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    data = stored.get("releases")
    return _cached_json(request, data if isinstance(data, list) else [])


@router.get("/{project_id}/gitlab/labels", name="project_labels")
async def get_labels(
    project_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Response:
    """List project labels from the last synced project snapshot."""
    project = await _get_project_with_access(project_id, db, _auth, request)
    stored = project.gitlab_intel if isinstance(project.gitlab_intel, dict) else {}
    data = stored.get("labels")
    return _cached_json(request, data if isinstance(data, list) else [])
