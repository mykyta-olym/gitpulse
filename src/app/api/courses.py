"""Course CRUD API endpoints."""

import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Request, status
from sqlalchemy import select

from app.api.errors import (
    raise_bad_request,
    raise_not_found,
    raise_service_unavailable,
)
from app.api.helpers.utils import check_course_access, course_staff_emails, get_actor
from app.config import get_settings
from app.db.repositories.base import BaseRepository
from app.dependencies import ApiAdminAuth, ApiAuth, ApiTeacherAuth, DbSession
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.schemas.courses import (
    CourseCreate,
    CourseRead,
    CourseSettingsRead,
    CourseSettingsUpdate,
    CourseTransferRequest,
    CourseTransferResponse,
    CourseUpdate,
)
from app.security.course_roles import (
    set_course_membership,
)
from app.services import course_settings as configuration
from app.services.audit import write_audit
from app.utils.constants import DEFAULT_MR_TEMPLATE_SECTIONS, DEFAULT_TEST_FILE_PATTERNS

logger = structlog.get_logger(__name__)
router = APIRouter()

# GitLab group import routes live in a dedicated module (SRP).
from app.api.course_import import router as _gitlab_import_router  # noqa: E402

router.include_router(_gitlab_import_router)


@router.get("/", response_model=list[CourseRead])
async def list_courses(db: DbSession, _auth: ApiAuth) -> list[Course]:
    repo = BaseRepository(db, Course)
    return await repo.get_all(is_active=True)


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate, db: DbSession, _auth: ApiTeacherAuth, request: Request
) -> Course:
    """Create a new course (teacher/admin only)."""
    # Prevent duplicate courses with same code + year + semester
    dup_stmt = select(Course).where(
        Course.code == data.code,
        Course.academic_year == data.academic_year,
        Course.semester == data.semester,
    )
    dup_result = await db.execute(dup_stmt)
    existing = dup_result.scalar_one_or_none()
    if existing:
        raise_bad_request(
            f"Course {data.code} ({data.academic_year} / {data.semester}) already exists"
        )

    course = Course(
        code=data.code,
        name=data.name,
        description=data.description,
        academic_year=data.academic_year,
        semester=data.semester,
    )
    db.add(course)
    await db.flush()

    # Auto-create default settings
    settings = CourseSettings(
        course_id=course.id,
        mr_template_required_sections=list(DEFAULT_MR_TEMPLATE_SECTIONS),
        test_file_patterns=list(DEFAULT_TEST_FILE_PATTERNS),
        semester_start_date=data.semester_start_date,
        semester_end_date=data.semester_end_date,
    )
    db.add(settings)
    await db.flush()

    logger.info("course_created", course_id=str(course.id), code=course.code)

    # Create owner membership for the creating user
    if _auth == "session":
        try:
            from app.models.user import User

            actor_name = get_actor(request)
            if actor_name and actor_name != "session":
                user_stmt = (
                    select(User)
                    .where((User.gitlab_username == actor_name) | (User.username == actor_name))
                    .limit(1)
                )
                creator = (await db.execute(user_stmt)).scalar_one_or_none()
                if creator:
                    await set_course_membership(db, creator.id, course.id, "owner")
        except Exception:
            logger.warning(
                "auto_owner_failed",
                course_id=str(course.id),
                exc_info=True,
            )

    await write_audit(
        db,
        action="course_create",
        actor=_auth,
        entity_type="course",
        entity_id=course.id,
        detail={"summary": f"Course created: {course.code} - {course.name}"},
    )

    return course


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course_id: uuid.UUID, db: DbSession, _auth: ApiAuth) -> Course:
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    return course


@router.put("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: uuid.UUID,
    data: CourseUpdate,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Course:
    """Update course (teacher/admin only)."""
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")

    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify courses you don't teach",
    )

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, course_id)

    await configuration.lock_configuration(db, course)
    await configuration.apply_course_update(db, course, data)

    try:
        await db.flush()
    except Exception as exc:
        detail = str(getattr(exc, "orig", exc))
        if "uq_courses_code_year_semester" in detail:
            raise_bad_request("A course with the same code, year, and semester already exists")
        raise
    logger.info("course_updated", course_id=str(course_id))
    # The course, group, student and project pages cache their rendered body
    # for a minute, headers included - which carry the code, the name and the
    # period badge. A rename or a move to another term must not keep showing
    # the old one.
    try:
        from app.models.team import Team

        team_rows = await db.scalars(select(Team.id).where(Team.course_id == course_id))
        team_ids = [str(tid) for tid in team_rows]
        configuration.invalidate_course_settings_cache(course_id, team_ids)
    except Exception:
        logger.debug("course_update_cache_invalidate_failed", exc_info=True)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> None:
    """Archive/delete course (teacher/admin only)."""
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")

    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify courses you don't teach",
    )

    # Soft delete - just archive

    course.is_active = False
    course.archived_at = datetime.now(UTC)
    await db.flush()

    await write_audit(
        db,
        action="course_delete",
        actor=get_actor(request),
        entity_type="course",
        entity_id=course.id,
        detail={"summary": f"Course archived: {course.code} - {course.name}"},
    )

    # Notify course staff
    from app.services.email_notifications import notify_course_archived

    actor_name = get_actor(request)
    for _email in await course_staff_emails(db, course_id):
        notify_course_archived(
            course_code=course.code,
            course_name=course.name,
            archived_by=actor_name,
            to_email=_email,
        )

    logger.info("course_deleted", course_id=str(course_id))


@router.get("/{course_id}/settings", response_model=CourseSettingsRead)
async def get_course_settings(
    course_id: uuid.UUID, db: DbSession, _auth: ApiAuth
) -> CourseSettings:
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    if not course.settings:
        raise_not_found("Course settings not found")
    return course.settings


@router.put("/{course_id}/settings", response_model=CourseSettingsRead)
async def update_course_settings(
    course_id: uuid.UUID,
    data: CourseSettingsUpdate,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> CourseSettings:
    """Update course settings (teacher/admin only)."""
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    if not course.settings:
        raise_not_found("Course settings not found")

    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify courses you don't teach",
    )

    from app.services.courses import ensure_course_active

    await ensure_course_active(db, course_id)

    await configuration.lock_configuration(db, course)
    cs = course.settings
    configuration.apply_settings_update(cs, data)

    await db.flush()
    logger.info("course_settings_updated", course_id=str(course_id))
    await configuration.after_settings_update(db, course_id, cs)
    return cs


# -- Course Lifecycle (multi-tenant) --


@router.post(
    "/{course_id}/transfer",
    response_model=CourseTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def transfer_course_endpoint(
    course_id: uuid.UUID,
    data: CourseTransferRequest,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> CourseTransferResponse:
    """Carry a course over to a new semester (teacher/admin only).

    Superset of /clone: optionally carries groups (all / a selected subset /
    none), re-points or re-issues the webhook configurations, auto-retunes
    semester dates, archives the source and enqueues the initial sync.
    """
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify courses you don't teach",
    )

    settings = get_settings()
    if not settings.feature_multi_tenant:
        raise_service_unavailable("Multi-tenant feature is disabled")

    # The schema has already normalised both (see AcademicYear / Semester).
    academic_year = data.academic_year
    # The target term must be free: a second course with the same code in the
    # same term is refused by a unique constraint, and meeting it half-way
    # through the clone surfaced as a server error instead of a sentence.
    duplicate = await db.scalar(
        select(Course.id).where(
            Course.code == course.code,
            Course.academic_year == academic_year,
            Course.semester == data.semester,
        )
    )
    if duplicate is not None:
        raise_bad_request(f"Course {course.code} already exists in {academic_year} {data.semester}")

    from app.services.courses import transfer_course

    result = await transfer_course(
        db,
        course_id,
        academic_year,
        data.semester,
        carry_mode=data.carry_mode,
        team_ids=data.team_ids,
        webhook_mode=data.webhook_mode,
        archive_source=data.archive_source,
        enqueue_sync=data.enqueue_sync,
        actor=get_actor(request),
        semester_start_date=data.semester_start_date,
        semester_end_date=data.semester_end_date,
    )
    return CourseTransferResponse(
        id=result.course.id,
        code=result.course.code,
        academic_year=result.course.academic_year,
        semester=result.course.semester,
        teams_carried=result.teams_carried,
        webhooks_moved=result.webhooks_moved,
        webhooks_created=result.webhooks_created,
        webhook_secrets=result.webhook_secrets,
        sync_enqueued=result.sync_enqueued,
        source_archived=result.source_archived,
    )


@router.post("/{course_id}/archive", response_model=CourseRead)
async def archive_course(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Course:
    """Archive course (teacher/admin only)."""
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify courses you don't teach",
    )

    from app.services.courses import archive_course as _archive

    result = await _archive(db, course_id)
    try:
        await write_audit(
            db,
            action="course.archive",
            actor=get_actor(request),
            entity_type="course",
            entity_id=course_id,
            detail={"summary": f"Course archived: {result.code}"},
        )
    except Exception:
        logger.warning("audit_write_failed", endpoint="archive_course", exc_info=True)

    # Notify course staff
    from app.services.email_notifications import notify_course_archived

    actor_name = get_actor(request)
    for _email in await course_staff_emails(db, course_id):
        notify_course_archived(
            course_code=result.code,
            course_name=result.name,
            archived_by=actor_name,
            to_email=_email,
        )

    return result


@router.post("/{course_id}/activate", response_model=CourseRead)
async def activate_course(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiTeacherAuth,
) -> Course:
    """Activate course (teacher/admin only)."""
    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")
    await check_course_access(
        course,
        _auth,
        request,
        db,
        action_label="modify courses you don't teach",
    )

    from app.services.courses import activate_course as _activate

    result = await _activate(db, course_id)
    try:
        await write_audit(
            db,
            action="course.update",
            actor=get_actor(request),
            entity_type="course",
            entity_id=course_id,
            detail={"summary": f"Course re-activated: {result.code}"},
        )
    except Exception:
        logger.warning("audit_write_failed", endpoint="activate_course", exc_info=True)

    # Notify course staff
    from app.services.email_notifications import notify_course_reactivated

    actor_name = get_actor(request)
    for _email in await course_staff_emails(db, course_id):
        notify_course_reactivated(
            course_code=result.code,
            course_name=result.name,
            reactivated_by=actor_name,
            course_id=course_id,
            to_email=_email,
        )

    return result


@router.delete("/{course_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def permanently_delete_course(
    course_id: uuid.UUID,
    request: Request,
    db: DbSession,
    _auth: ApiAdminAuth,
) -> None:
    """Permanently delete course and all related data (admin only)."""
    from app.models.team import Team

    course = await db.get(Course, course_id)
    if not course:
        raise_not_found("Course not found")

    if course.is_active:
        raise_bad_request("Cannot delete active course. Archive it first.")

    course_code = course.code

    # Delete background_jobs that reference this course or its teams
    team_ids = (await db.scalars(select(Team.id).where(Team.course_id == course_id))).all()

    from sqlalchemy import or_

    from app.models.project import GitLabProject
    from app.models.team_member import TeamMember
    from app.services.job_history import delete_job_history

    project_ids = list(
        await db.scalars(select(GitLabProject.id).where(GitLabProject.team_id.in_(team_ids)))
    )
    student_ids = list(
        await db.scalars(select(TeamMember.student_id).where(TeamMember.team_id.in_(team_ids)))
    )
    await delete_job_history(
        db,
        or_(
            BackgroundJob.course_id == course_id,
            BackgroundJob.team_id.in_(team_ids),
            BackgroundJob.project_id.in_(project_ids),
        ),
        require_all=True,
    )

    await db.delete(course)
    await db.flush()

    try:
        await write_audit(
            db,
            action="course.delete",
            actor=get_actor(request),
            detail={"summary": f"Course permanently deleted: {course_code}"},
        )
    except Exception:
        logger.warning("audit_write_failed", endpoint="permanently_delete_course", exc_info=True)
    await db.commit()
    from app.services.page_cache import invalidate_cascade

    invalidate_cascade(course_id=course_id, student_ids=student_ids)
    for team_id in team_ids:
        invalidate_cascade(team_id=team_id)
    for project_id in project_ids:
        invalidate_cascade(project_id=project_id)
    logger.info("course_permanently_deleted", course_id=str(course_id))
