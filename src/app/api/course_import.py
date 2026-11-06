"""GitLab group import endpoints for courses.

Split out of ``courses.py`` (SRP): all ``/import/gitlab-group*`` and
``/check-import-duplicate`` routes plus their teacher-enrichment helper
live here. The router is mounted back onto the main courses router via
``router.include_router(...)``.
"""

import asyncio
import contextlib
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy import func as sa_func
from sqlalchemy import or_ as sa_or
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import (
    raise_bad_request,
    raise_service_unavailable,
)
from app.api.helpers.utils import get_actor
from app.config import get_settings
from app.dependencies import ApiTeacherAuth, DbSession
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.schemas.courses import (
    CourseImportDuplicateCheckResponse,
    GitLabGroupImportRequest,
    GitLabGroupImportResponse,
)
from app.security.course_roles import (
    set_course_membership,
)
from app.services.audit import write_audit

logger = structlog.get_logger(__name__)
router = APIRouter()


async def _enrich_teacher_users(
    db: AsyncSession,
    teacher_usernames: list[str],
) -> None:
    """Fetch avatar, full_name, email, gitlab_user_id from GitLab for teacher users."""
    if not teacher_usernames:
        return
    from app.models.user import User
    from app.services.gitlab.client import GitLabClient

    settings = get_settings()
    if not settings.gitlab_api_token.strip():
        return

    # Find teacher User rows that need enrichment

    stmt = (
        select(User)
        .where(
            sa_or(
                User.gitlab_username.in_(teacher_usernames),
                User.username.in_(teacher_usernames),
            ),
            sa_or(
                User.avatar_url.is_(None),
                User.avatar_url == "",
                User.full_name.is_(None),
                User.email.is_(None),
                User.email == "PRIVATE",
                User.gitlab_user_id.is_(None),
            ),
        )
        .limit(50)
    )
    result = await db.execute(stmt)
    users = list(result.scalars().all())
    if not users:
        return

    try:
        async with GitLabClient(
            base_url=str(settings.gitlab_url),
            private_token=settings.gitlab_api_token,
            timeout=settings.gitlab_api_timeout_seconds,
            max_retries=settings.gitlab_api_max_retries,
        ) as gl:
            for user in users:
                search_name = user.gitlab_username or user.username
                if not search_name:
                    continue
                try:
                    results = await gl._get_list("/users", params={"username": search_name})
                    if not results:
                        continue
                    gl_user = results[0]
                    if not user.gitlab_user_id and gl_user.get("id"):
                        user.gitlab_user_id = gl_user["id"]
                    if not user.full_name:
                        name = gl_user.get("name")
                        if name and name != search_name:
                            user.full_name = name
                    if not user.email or user.email == "PRIVATE":
                        email = (
                            gl_user.get("email")
                            or gl_user.get("public_email")
                            or gl_user.get("commit_email")
                        )
                        if not email:
                            from app.services.arena_email import lookup_email

                            email = await lookup_email(search_name, settings)
                        if email:
                            user.email = email
                    avatar = gl_user.get("avatar_url")
                    if avatar and not user.avatar_url:
                        user.avatar_url = avatar
                except Exception:
                    logger.debug("enrich_teacher_failed", username=search_name)
        await db.commit()
    except Exception:
        logger.warning("enrich_teachers_batch_failed", exc_info=True)


def _import_params(data: GitLabGroupImportRequest, teacher_usernames: list[str] | None) -> Any:
    from app.services.gitlab_import.service import GitLabGroupImportParams

    return GitLabGroupImportParams(
        group_url=data.group_url,
        target_course_id=data.target_course_id,
        course_code=data.course_code,
        course_name=data.course_name,
        academic_year=data.academic_year,
        semester=data.semester,
        include_subgroups=data.include_subgroups,
        teacher_usernames=teacher_usernames,
        one_team_per_project=data.one_team_per_project,
        semester_start_date=data.semester_start_date,
        semester_end_date=data.semester_end_date,
    )


async def _make_owner(db: Any, course_id: uuid.UUID, actor_name: str) -> bool:
    """The importing user owns the course the import created."""
    from app.models.user import User

    user_stmt = (
        select(User)
        .where((User.gitlab_username == actor_name) | (User.username == actor_name))
        .limit(1)
    )
    creator = (await db.execute(user_stmt)).scalar_one_or_none()
    if not creator:
        return False
    await set_course_membership(db, creator.id, course_id, "owner")
    return True


def _enrichment_names(teachers_detected: list[str]) -> list[str]:
    """The detected teachers and the configured GitLab admins - the users
    whose avatar, name and email are fetched after an import."""
    names = list(teachers_detected)
    for _au in get_settings().gitlab_admin_usernames or []:
        if _au and _au.strip() and _au.strip() not in names:
            names.append(_au.strip())
    return names


async def _active_teams(db: Any, course_id: uuid.UUID) -> list[Any]:
    from app.models.team import Team

    stmt = (
        select(Team)
        .where(Team.course_id == course_id, Team.is_active.is_(True))
        .order_by(Team.name)
    )
    return list((await db.execute(stmt)).scalars().all())


async def _enqueue_team_syncs(db: Any, teams: list[Any], course_id: uuid.UUID) -> tuple[int, int]:
    """Queue a sync for each imported group - (enqueued, skipped).

    Pass 1 writes the BackgroundJob rows and COMMITS them, so a worker never
    starts before its row exists; pass 2 hands them to RQ. A group whose row
    another transaction holds (FOR UPDATE SKIP LOCKED avoids deadlocks
    between parallel imports), or with a sync already in flight, is skipped.
    Both imports run this; the streamed one used to take no lock.
    """
    from app.models.team import Team
    from app.services.events import enqueue_sync_job

    skipped = 0
    jobs: list[tuple[Any, BackgroundJob]] = []
    for team in teams:
        lock_stmt = select(Team).where(Team.id == team.id).with_for_update(skip_locked=True)
        if not (await db.execute(lock_stmt)).scalar_one_or_none():
            skipped += 1
            continue
        existing_stmt = (
            select(BackgroundJob)
            .where(
                BackgroundJob.team_id == team.id,
                BackgroundJob.job_type == "sync",
                BackgroundJob.status.in_(["enqueued", "started", "running"]),
            )
            .order_by(BackgroundJob.enqueued_at.desc())
            .limit(1)
        )
        if (await db.execute(existing_stmt)).scalar_one_or_none():
            skipped += 1
            continue
        job = BackgroundJob(job_type="sync", team_id=team.id)
        db.add(job)
        await db.flush()  # assign PK
        jobs.append((team, job))
    if jobs:
        await db.commit()

    enqueued = 0
    for team, job in jobs:
        try:
            rq_job_id = enqueue_sync_job(str(team.id), str(job.id), course_id=str(course_id))
            if rq_job_id:
                job.rq_job_id = rq_job_id
                enqueued += 1
            else:
                job.status = "failed"
                job.error_message = "Failed to enqueue sync job."
        except (ConnectionError, TimeoutError, OSError) as exc:
            logger.exception("failed_to_enqueue_sync_for_team", team_id=str(team.id))
            job.status = "failed"
            job.error_message = f"Failed to enqueue sync job: {type(exc).__name__}"
        await db.flush()
    return enqueued, skipped


@router.post("/import/gitlab-group", response_model=GitLabGroupImportResponse)
async def import_gitlab_group_course(
    data: GitLabGroupImportRequest,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> GitLabGroupImportResponse:
    """Create/update a course by importing a GitLab group hierarchy."""
    settings = get_settings()
    if not settings.gitlab_api_token.strip():
        raise_bad_request("GitLab API token is not configured (set GITLAB_API_TOKEN).")

    # Block the import outright if the configured token is invalid/expired -
    # otherwise it fails deep inside the import with a confusing 500.
    from app.api.helpers.sync import require_gitlab_ready

    await require_gitlab_ready()

    from app.services.gitlab_import.service import import_gitlab_group_to_course

    try:
        result = await import_gitlab_group_to_course(
            db,
            gitlab_base_url=str(settings.gitlab_url),
            gitlab_api_token=settings.gitlab_api_token,
            params=_import_params(data, data.teacher_usernames),
        )
    except ValueError as exc:
        raise_bad_request(str(exc))
    except Exception as exc:
        logger.error("gitlab_group_import_failed", error=str(exc))
        raise_service_unavailable(
            "GitLab is currently unreachable. Cannot import group. Please try again later."
        )

    logger.info(
        "gitlab_group_import_completed",
        course_id=str(result.course_id),
        course_code=result.course_code,
        course_academic_year=result.course_academic_year,
        course_semester=result.course_semester,
        group_path=result.group_path,
        created_course=result.created_course,
        teams_created=result.teams_created,
        students_created=result.students_created,
        projects_created=result.projects_created,
        projects_deactivated=result.projects_deactivated,
    )

    await write_audit(
        db,
        action="course_import",
        actor=get_actor(request),
        entity_type="course",
        entity_id=result.course_id,
        detail={
            "summary": (
                f"Imported from GitLab: {result.group_path}"
                f" - {result.teams_created} groups,"
                f" {result.projects_created} projects"
            ),
            "group_path": result.group_path,
            "teams_created": result.teams_created,
            "projects_created": result.projects_created,
            "projects_deactivated": result.projects_deactivated,
        },
    )

    if result.created_course:
        actor_name = get_actor(request)
        if actor_name and actor_name != "session":
            try:
                await _make_owner(db, result.course_id, actor_name)
            except Exception:
                logger.warning(
                    "import_auto_owner_failed",
                    course_id=str(result.course_id),
                    exc_info=True,
                )

    # import_gitlab_group_to_course only flushes: commit, so the Course,
    # Teams, Projects and Students are visible to the workers the syncs start.
    await db.commit()
    await _enrich_teacher_users(db, _enrichment_names(result.teachers_detected))

    enqueued = skipped = 0
    if data.auto_sync:
        teams = await _active_teams(db, result.course_id)
        enqueued, skipped = await _enqueue_team_syncs(db, teams, result.course_id)

    return GitLabGroupImportResponse(
        course_id=result.course_id,
        course_code=result.course_code,
        course_academic_year=result.course_academic_year,
        course_semester=result.course_semester,
        course_name=result.course_name,
        group_path=result.group_path,
        created_course=result.created_course,
        teams_created=result.teams_created,
        teams_updated=result.teams_updated,
        students_created=result.students_created,
        students_updated=result.students_updated,
        memberships_created=result.memberships_created,
        projects_created=result.projects_created,
        projects_updated=result.projects_updated,
        projects_deactivated=result.projects_deactivated,
        teachers_detected=result.teachers_detected,
        sync_jobs_enqueued=enqueued,
        sync_jobs_skipped=skipped,
        warnings=result.warnings or [],
    )


def _course_summary(course: Course, teams: int, students: int, projects: int) -> dict[str, Any]:
    return {
        "id": course.id,
        "code": course.code,
        "name": course.name,
        "academic_year": course.academic_year,
        "semester": course.semester,
        "team_count": teams,
        "student_count": students,
        "project_count": projects,
    }


def _active_team_ids(course_id: uuid.UUID) -> Any:
    from app.models.team import Team

    return select(Team.id).where(Team.course_id == course_id, Team.is_active.is_(True))


async def _course_counts(db: Any, course_id: uuid.UUID) -> tuple[int, int, int]:
    """Active groups, distinct active students and projects of a course."""
    from app.models.project import GitLabProject as Project
    from app.models.team import Team
    from app.models.team_member import TeamMember

    team_count = (
        await db.execute(
            select(func.count()).where(Team.course_id == course_id, Team.is_active.is_(True))
        )
    ).scalar() or 0
    student_count = (
        await db.execute(
            select(func.count(func.distinct(TeamMember.student_id))).where(
                TeamMember.team_id.in_(_active_team_ids(course_id)),
                TeamMember.is_active.is_(True),
                TeamMember.is_teacher.is_(False),
                TeamMember.is_mentor.is_(False),
            )
        )
    ).scalar() or 0
    project_count = (
        await db.execute(
            select(func.count()).where(Project.team_id.in_(_active_team_ids(course_id)))
        )
    ).scalar() or 0
    return team_count, student_count, project_count


async def _overlap_in_target(db: Any, course: Course, group_path: str) -> dict[str, Any] | None:
    """Importing into a chosen course: only its groups and projects whose
    GitLab path the import would actually touch."""
    from app.models.project import GitLabProject as Project
    from app.models.team import Team

    teams_result = await db.execute(
        select(Team.id, Team.name, Team.gitlab_group_id, Team.gitlab_group_path)
        .where(
            Team.course_id == course.id,
            Team.is_active.is_(True),
            Team.gitlab_group_path.isnot(None),
        )
        .order_by(Team.name)
        .limit(20)
    )
    import_path = group_path.lower()
    matching_teams = []
    for row in teams_result:
        team_path = (row.gitlab_group_path or "").lower()
        # Overlap: the same path, or either one inside the other.
        if not (
            team_path == import_path
            or import_path.startswith(team_path + "/")
            or team_path.startswith(import_path + "/")
        ):
            continue
        t_proj_q = await db.execute(select(func.count()).where(Project.team_id == row.id))
        matching_teams.append(
            {
                "name": row.name,
                "gitlab_group_id": row.gitlab_group_id,
                "project_count": t_proj_q.scalar() or 0,
            }
        )
    overlapping_projects = (
        await db.execute(
            select(func.count()).where(
                Project.team_id.in_(_active_team_ids(course.id)),
                Project.is_active.is_(True),
                (
                    Project.gitlab_project_path.ilike(group_path + "/%")
                    | Project.gitlab_project_path.ilike(group_path)
                ),
            )
        )
    ).scalar() or 0
    if not matching_teams and overlapping_projects == 0:
        return None
    return {
        "has_duplicate": True,
        "matching_course": _course_summary(course, *await _course_counts(db, course.id)),
        "matching_teams": matching_teams,
    }


async def _same_course(db: Any, data: GitLabGroupImportRequest) -> dict[str, Any] | None:
    """A new course: the existing one with the same code, year and semester
    (the import service's own match), with its groups."""
    from app.models.project import GitLabProject as Project
    from app.models.team import Team

    course = (
        await db.execute(
            select(Course).where(
                Course.code == data.course_code,
                Course.academic_year == data.academic_year,
                Course.semester == data.semester,
            )
        )
    ).scalar_one_or_none()
    if not course:
        return None
    team_count, _, project_count = await _course_counts(db, course.id)
    team_rows = (
        await db.execute(
            select(Team.id, Team.name, Team.gitlab_group_id)
            .where(Team.course_id == course.id, Team.is_active.is_(True))
            .order_by(Team.name)
            .limit(20)
        )
    ).all()
    proj_counts: dict[uuid.UUID, int] = {}
    if team_rows:
        count_q = await db.execute(
            select(Project.team_id, func.count())
            .where(Project.team_id.in_([r.id for r in team_rows]), Project.is_active.is_(True))
            .group_by(Project.team_id)
        )
        proj_counts = {row[0]: row[1] for row in count_q.all()}
    return {
        "has_duplicate": True,
        "matching_course": _course_summary(course, team_count, 0, project_count),
        "matching_teams": [
            {
                "name": row.name,
                "gitlab_group_id": row.gitlab_group_id,
                "project_count": proj_counts.get(row.id, 0),
            }
            for row in team_rows
        ],
    }


async def _projects_in_other_courses(
    db: Any, group_path: str, exclude_course_id: Any
) -> list[dict[str, Any]]:
    """Active projects under the imported path that belong to another course."""
    from app.models.project import GitLabProject as Project
    from app.models.team import Team

    cross_stmt = (
        select(
            Project.gitlab_project_path,
            Project.gitlab_project_name,
            Course.code.label("course_code"),
            Team.name.label("team_name"),
        )
        .join(Team, Project.team_id == Team.id)
        .join(Course, Team.course_id == Course.id)
        .where(
            Project.gitlab_project_path.ilike(group_path + "/%"),
            Project.is_active.is_(True),
        )
    )
    if exclude_course_id:
        cross_stmt = cross_stmt.where(Course.id != exclude_course_id)
    return [
        {
            "gitlab_project_path": crow.gitlab_project_path,
            "gitlab_project_name": crow.gitlab_project_name,
            "current_course_code": crow.course_code,
            "current_team_name": crow.team_name,
        }
        for crow in await db.execute(cross_stmt.limit(20))
    ]


@router.post("/check-import-duplicate", response_model=CourseImportDuplicateCheckResponse)
async def check_import_duplicate(
    data: GitLabGroupImportRequest,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> CourseImportDuplicateCheckResponse:
    """Check if an import would hit existing data (duplicate detection).

    Returns info about matching courses/teams so the UI can warn the user
    before they start a potentially redundant import.
    """
    group_path: str | None = None
    try:
        from app.services.gitlab_import.service import extract_group_path_from_input

        group_path = extract_group_path_from_input(data.group_url, get_settings().gitlab_url)
    except ValueError as exc:
        raise_bad_request(str(exc) or "Enter a valid GitLab group or project URL/path.")
    except Exception:
        logger.debug("group_path_extraction_failed", exc_info=True)
        raise_bad_request("Enter a valid GitLab group or project URL/path.")

    result: dict[str, Any] = {"has_duplicate": False}
    if data.target_course_id:
        course = await db.get(Course, data.target_course_id)
        if course and group_path:
            result.update(await _overlap_in_target(db, course, group_path) or {})
    else:
        result.update(await _same_course(db, data) or {})

    if group_path:
        try:
            # Same-course duplicates are shown above; this is the rest.
            exclude = data.target_course_id or (
                result["matching_course"]["id"] if result.get("matching_course") else None
            )
            cross_projects = await _projects_in_other_courses(db, group_path, exclude)
            if cross_projects:
                result["has_duplicate"] = True
                result["cross_course_projects"] = cross_projects
        except Exception:
            # If group_url parsing fails, skip cross-course check
            logger.debug("cross_course_check_skipped", exc_info=True)

    return CourseImportDuplicateCheckResponse.model_validate(result)


def _importer_usernames(request: Request, data: GitLabGroupImportRequest) -> tuple[list[str], Any]:
    """The teachers to import with, the importing user always among them so
    they keep access to the course they import - and that user's session."""
    from app.security.session_auth import get_current_session

    settings = get_settings()
    usernames: list[str] = list(data.teacher_usernames or [])
    session_data = get_current_session(
        request,
        settings.secret_key,
        max_age=settings.session_max_age_seconds,
        app_base_url=settings.app_base_url,
        session_absolute_max_age=settings.session_absolute_max_age_seconds,
    )
    if session_data:
        for key in ("gitlab_username", "user"):
            uname = session_data.get(key, "").strip()
            if uname and uname not in usernames:
                usernames.append(uname)
    return usernames, session_data


async def _students_total(db: Any, course_id: uuid.UUID) -> int:
    """Distinct active students in the course's active groups."""
    from app.models.team_member import TeamMember

    cnt = await db.execute(
        select(sa_func.count(sa_func.distinct(TeamMember.student_id))).where(
            TeamMember.team_id.in_(_active_team_ids(course_id)),
            TeamMember.is_active.is_(True),
            TeamMember.is_teacher.is_(False),
            TeamMember.is_mentor.is_(False),
        )
    )
    return cnt.scalar() or 0


def _done_event(result: Any, students_total: int, sync_jobs: int) -> dict[str, Any]:
    return {
        "type": "done",
        "course_id": str(result.course_id),
        "course_code": result.course_code,
        "course_academic_year": result.course_academic_year,
        "course_semester": result.course_semester,
        "course_name": result.course_name,
        "teams_created": result.teams_created,
        "teams_updated": result.teams_updated,
        "students_created": result.students_created,
        "students_updated": result.students_updated,
        "students_total": students_total,
        "teachers_created": result.teachers_created,
        # The detected list: root-group teachers may have no TeamMember row.
        "teachers_total": len(result.teachers_detected),
        "teachers_list": result.teachers_detected,
        "projects_created": result.projects_created,
        "projects_updated": result.projects_updated,
        "projects_deactivated": result.projects_deactivated,
        "sync_jobs_enqueued": sync_jobs,
    }


@router.post("/import/gitlab-group/stream")
async def import_gitlab_group_course_stream(
    request: Request,
    data: GitLabGroupImportRequest,
    _auth: ApiTeacherAuth,
) -> StreamingResponse:
    """Stream import progress as Server-Sent Events.

    Unlike most endpoints this does **not** use the DI ``DbSession``.
    The DI session is an async-generator whose cleanup runs inside
    Starlette's middleware cancel-scope - if the client disconnects
    mid-stream (e.g. page reload after import finishes) the
    ``CancelledError`` prevents proper connection return and causes the
    *"garbage collector cleaning up non-checked-in connection"* leak.

    Instead we use :func:`async_session_ctx` (the cancellation-safe
    context manager) inside the background task, exactly like the
    ``sync-stream`` endpoint does.
    """
    settings = get_settings()
    if not settings.gitlab_api_token.strip():
        raise_bad_request("GitLab API token is not configured (set GITLAB_API_TOKEN).")

    # Block the import outright when the token is invalid/expired.
    from app.api.helpers.sync import require_gitlab_ready

    await require_gitlab_ready()

    importer_usernames, session_data = _importer_usernames(request, data)
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    # Set once import data is committed - after this point the task
    # must NOT be cancelled even if the SSE client disconnects,
    # otherwise sync-enqueue and the "done" event are lost.
    import_committed = asyncio.Event()
    task = asyncio.create_task(
        _run_streamed_import(data, importer_usernames, session_data, queue, import_committed)
    )

    async def event_generator() -> AsyncIterator[str]:
        keepalive_interval = 15
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=keepalive_interval)
                except TimeoutError:
                    # Send SSE comment as keepalive to prevent upstream
                    # proxy timeouts (university reverse proxy, Caddy).
                    yield ": keepalive\n\n"
                    continue
                payload = f"data: {json.dumps(event)}\n\n"
                yield payload
                if event.get("type") in ("done", "error"):
                    break
        finally:
            if not task.done() and not import_committed.is_set():
                # Only cancel the task if import data has NOT been
                # committed yet.  After commit, let the task complete
                # so sync jobs are properly enqueued.
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


async def _run_streamed_import(
    data: GitLabGroupImportRequest,
    importer_usernames: list[str],
    session_data: Any,
    queue: asyncio.Queue[dict[str, Any]],
    import_committed: asyncio.Event,
) -> None:
    """The import behind the stream: progress events to ``queue``, then
    "done" - sent BEFORE the slow sync-enqueue and teacher-enrichment phase,
    which can run 1-2 s with no events while the upstream proxy closes an idle
    connection (the client then got a network error instead of the result).
    The task finishes that phase after the stream has closed."""
    from app.db.session import async_session_ctx
    from app.services.gitlab_import.service import import_gitlab_group_to_course

    settings = get_settings()

    async def on_progress(event: dict[str, Any]) -> None:
        await queue.put(event)

    try:
        async with async_session_ctx() as db:
            result = await import_gitlab_group_to_course(
                db,
                gitlab_base_url=str(settings.gitlab_url),
                gitlab_api_token=settings.gitlab_api_token,
                params=_import_params(data, importer_usernames or None),
                on_progress=on_progress,
            )
            logger.info(
                "gitlab_group_import_completed",
                course_id=str(result.course_id),
                teams_created=result.teams_created,
                students_created=result.students_created,
                projects_created=result.projects_created,
                projects_deactivated=result.projects_deactivated,
            )
            # import_gitlab_group_to_course only flushes: commit, so the
            # Course, CourseSettings, Teams, Projects and Students exist
            # before a sync worker looks for them (it gave up on a missing
            # Team after one retry, and the group never got its metrics).
            await db.commit()
            import_committed.set()

            if result.created_course and session_data:
                try:
                    actor_name = (
                        session_data.get("gitlab_username", "").strip()
                        or session_data.get("user", "").strip()
                    )
                    if actor_name and await _make_owner(db, result.course_id, actor_name):
                        await db.commit()
                except Exception:
                    logger.warning(
                        "import_stream_auto_owner_failed",
                        course_id=str(result.course_id),
                        exc_info=True,
                    )

            # Counted before any sync runs, so the toast's number is not the
            # one a first completed sync has already deactivated students from.
            students_total = await _students_total(db, result.course_id)
            teams = await _active_teams(db, result.course_id) if data.auto_sync else []
            await queue.put(_done_event(result, students_total, len(teams)))

            if teams:
                enqueued, _ = await _enqueue_team_syncs(db, teams, result.course_id)
                logger.info(
                    "import_stream_sync_enqueued",
                    course_id=str(result.course_id),
                    sync_jobs_enqueued=enqueued,
                )
            await _enrich_teacher_users(db, _enrichment_names(result.teachers_detected))

    except asyncio.CancelledError:
        logger.warning(
            "import_stream_task_cancelled",
            committed=import_committed.is_set(),
        )
        # If data was already committed, the import succeeded but
        # the SSE client disconnected (e.g. upstream proxy timeout).
        # Do NOT re-raise - let the task end cleanly so sync jobs
        # already enqueued are preserved.
        if not import_committed.is_set():
            raise
    except Exception:
        logger.error("import_stream_error", exc_info=True)
        msg = "Import failed. Check server logs for details."
        await queue.put({"type": "error", "message": msg})
