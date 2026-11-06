"""Course lifecycle operations: clone, archive, activate."""

import copy
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import structlog
from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.models.team import Team
from app.models.webhook_configuration import WebhookConfiguration
from app.services.job_control import cancel_jobs_for_course
from app.utils.academic_period import AcademicPeriod

logger = structlog.get_logger(__name__)


async def ensure_course_active(db: AsyncSession, course_id: uuid.UUID) -> None:
    """Raise 409 if the course is archived (read-only).

    Guards course-scoped mutations (sync, run-checks, settings, group creation)
    so an archived course cannot be changed - and so a mutation attempted right
    after someone else archived the course returns a clear "archived" error the
    UI turns into the read-only banner + toast. Reactivating the course clears
    this. A missing course is left to the caller's own 404 handling.
    """
    course = await db.get(Course, course_id)
    if course is not None and not course.is_active:
        raise HTTPException(
            status_code=409,
            detail=(
                "This course is archived and read-only. "
                "Reactivate it from the course settings to make changes."
            ),
        )


async def clone_course(
    db: AsyncSession,
    source_course_id: uuid.UUID,
    new_academic_year: str,
    new_semester: str,
) -> Course:
    """Clone a course for a new semester.

    Copies Course + CourseSettings + custom checks + the classroom
    assistant's tool settings (not its bot token).
    Does NOT copy teams/students.  Deadlines are cleared (semester-specific)
    but the weekly_deadlines structure is preserved (check expectations
    remain valid across semesters).
    """
    source = await db.get(Course, source_course_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source course not found")

    new_course = Course(
        code=source.code,
        name=source.name,
        description=source.description,
        academic_year=new_academic_year,
        semester=new_semester,
        is_active=True,
        cloned_from_id=source.id,
    )
    db.add(new_course)
    await db.flush()

    # Deep-copy settings (excluding PK, FK, and semester-specific dates)
    if source.settings:
        src = source.settings
        new_settings = CourseSettings(
            course_id=new_course.id,
            branch_pattern=src.branch_pattern,
            mr_template_required_sections=list(src.mr_template_required_sections),
            min_reviews_per_mr=src.min_reviews_per_mr,
            min_review_word_count=src.min_review_word_count,
            min_distinct_mrs_reviewed=src.min_distinct_mrs_reviewed,
            weight_issue_ownership=src.weight_issue_ownership,
            weight_branch_naming=src.weight_branch_naming,
            weight_mr_issue_link=src.weight_mr_issue_link,
            weight_mr_template=src.weight_mr_template,
            weight_test_changes=src.weight_test_changes,
            weight_review_count=src.weight_review_count,
            weight_review_duty=src.weight_review_duty,
            weight_response_complete=src.weight_response_complete,
            weight_approvals=src.weight_approvals,
            weight_merge_by_author=src.weight_merge_by_author,
            weight_closure=src.weight_closure,
            weight_pipeline_health=src.weight_pipeline_health,
            weight_commit_quality=src.weight_commit_quality,
            green_threshold=src.green_threshold,
            yellow_threshold=src.yellow_threshold,
            test_file_patterns=list(src.test_file_patterns),
            enabled_checks=list(src.enabled_checks),
            # Semester-specific fields: clear dates but keep structure
            weekly_deadlines=copy.deepcopy(src.weekly_deadlines or []),
            mr_creation_deadline=None,
            merge_deadline=None,
            semester_start_date=None,
            # Previously missing fields
            check_configs=copy.deepcopy(src.check_configs or {}),
            gitlab_group_path=src.gitlab_group_path,
            # webhook_secret intentionally NOT copied (must be unique per course)
        )
        db.add(new_settings)
        await db.flush()

        # Clone custom checks
        from app.models.custom_check import CustomCheck

        stmt = (
            select(CustomCheck)
            .where(CustomCheck.course_id == source_course_id)
            .order_by(CustomCheck.sort_order, CustomCheck.check_code)
        )
        result = await db.execute(stmt)
        for cc in result.scalars().all():
            new_cc = CustomCheck(
                course_id=new_course.id,
                check_code=cc.check_code,
                name=cc.name,
                description=cc.description,
                category=cc.category,
                evaluation_rule=copy.deepcopy(cc.evaluation_rule),
                weight=cc.weight,
                is_active=cc.is_active,
                sort_order=cc.sort_order,
                created_by="clone",
            )
            db.add(new_cc)
    else:
        db.add(CourseSettings(course_id=new_course.id))

    await db.flush()

    # The classroom assistant's tools carry over; its bot token does not.
    from app.services.assistant.account import carry_over

    await carry_over(db, source_course_id, new_course.id)

    # Clone CourseMembership rows (staff roles only; not students)
    from app.models.course_membership import CourseMembership

    cm_stmt = select(CourseMembership).where(
        CourseMembership.course_id == source_course_id,
        CourseMembership.role.in_(("owner", "teacher")),
    )
    cm_result = await db.execute(cm_stmt)
    for cm in cm_result.scalars().all():
        db.add(
            CourseMembership(
                user_id=cm.user_id,
                course_id=new_course.id,
                role=cm.role,
            )
        )

    logger.info(
        "course_cloned",
        source_id=str(source_course_id),
        new_id=str(new_course.id),
        year=new_academic_year,
        semester=new_semester,
    )
    return new_course


_TRANSFER_CARRY_MODES = ("all", "selected", "none")
_TRANSFER_WEBHOOK_MODES = ("move", "fresh", "none")


@dataclass
class TransferResult:
    """Outcome of :func:`transfer_course` - everything the UI reports back."""

    course: Course
    teams_carried: int
    webhooks_moved: int
    webhooks_created: int
    webhook_secrets: list[dict[str, str]]
    sync_enqueued: int
    source_archived: bool


def _year_delta(source_year: str, new_year: str) -> int:
    """Academic-year distance, e.g. '2025/2026' -> '2026/2027' = 1."""
    try:
        return int(new_year.split("/")[0]) - int(source_year.split("/")[0])
    except (ValueError, IndexError):
        return 0


def _whole_weeks(years: int) -> timedelta:
    """``years`` academic years as a whole number of weeks (52 or 53 each).

    A course runs on a weekly rhythm: a deadline on the Friday of week 5 has
    to land on the Friday of week 5 next year. Adding calendar years moves it
    to a Saturday (365 days is 52 weeks and a day), which is how a transferred
    course used to get its deadlines on the weekend.
    """
    return timedelta(weeks=round(years * 365.2425 / 7))


def _shift(value: Any, delta: timedelta) -> Any:
    """Move a date, a datetime or an ISO string by ``delta``; anything else as is."""
    if not delta or value is None:
        return value
    if isinstance(value, (date, datetime)):
        return value + delta
    if isinstance(value, str) and value:
        try:
            return (datetime.fromisoformat(value) + delta).isoformat()
        except ValueError:
            return value
    return value


def _retune_transferred_settings(
    new_settings: CourseSettings,
    src_settings: CourseSettings | None,
    *,
    target: AcademicPeriod | None,
    same_semester: bool,
    years: int,
    start: date | None = None,
    end: date | None = None,
) -> None:
    """Give the transferred course the dates of the term it moves into.

    The semester window, most certain first:

    1. the dates the Transfer dialog sent (``start`` / ``end``) - the teacher's;
    2. the official TUKE dates of the target term, when the calendar has it;
    3. the source's own window moved by whole weeks, for the same term a year
       (or more) on - the university's year barely moves, so that is a good
       guess and stays editable.

    Otherwise the window stays empty, as for any new course.

    Every deadline then moves by exactly as much as the semester start did, so
    "Friday of week 5" is still the Friday of week 5 - including across a
    change of term, now that the new term's start is known rather than
    guessed. With no start to measure from, the dated parts of the per-week
    deadlines are dropped (the week structure and expected checks are
    term-agnostic and kept).
    """
    if src_settings is None:
        return
    src_start = src_settings.semester_start_date
    official = target.official_dates() if target is not None else None
    fallback_delta = _whole_weeks(years) if same_semester and years else None

    if start is not None or end is not None:
        new_start, new_end = start, end
    elif official is not None:
        new_start, new_end = official
    elif fallback_delta is not None:
        new_start = _shift(src_start, fallback_delta)
        new_end = _shift(src_settings.semester_end_date, fallback_delta)
    else:
        new_start, new_end = None, None
    new_settings.semester_start_date = new_start
    new_settings.semester_end_date = new_end

    if src_start is not None and new_start is not None:
        delta: timedelta | None = new_start - src_start
    else:
        delta = fallback_delta

    entries = new_settings.weekly_deadlines or []
    retuned: list[Any] = []
    if delta is not None:
        new_settings.mr_creation_deadline = _shift(src_settings.mr_creation_deadline, delta)
        new_settings.merge_deadline = _shift(src_settings.merge_deadline, delta)
        for entry in entries:
            if isinstance(entry, dict):
                entry = dict(entry)
                for k in ("mr_deadline", "merge_deadline"):
                    if entry.get(k):
                        entry[k] = _shift(entry[k], delta)
            retuned.append(entry)
    else:
        new_settings.mr_creation_deadline = None
        new_settings.merge_deadline = None
        for entry in entries:
            if isinstance(entry, dict):
                entry = {
                    k: v for k, v in entry.items() if k not in ("mr_deadline", "merge_deadline")
                }
            retuned.append(entry)
    # Reassign (never mutate in place) so SQLAlchemy's change tracking sees
    # the new JSON value without flag_modified.
    new_settings.weekly_deadlines = retuned


async def transfer_course(
    db: AsyncSession,
    source_course_id: uuid.UUID,
    new_academic_year: str,
    new_semester: str,
    *,
    carry_mode: str = "all",
    team_ids: list[uuid.UUID] | None = None,
    webhook_mode: str = "move",
    archive_source: bool = True,
    enqueue_sync: bool = True,
    actor: str = "system",
    actor_user_id: uuid.UUID | None = None,
    semester_start_date: date | None = None,
    semester_end_date: date | None = None,
) -> TransferResult:
    """Transfer a course into a new semester - the full reactivation flow.

    Built ON TOP of :func:`clone_course` (settings + custom checks + staff)
    and adds what a real semester carry-over needs:

    * ``carry_mode``: ``all`` carries every active group, ``selected`` only
      the given ``team_ids`` (validated to belong to the source course),
      ``none`` starts the new semester with an empty course. Carried groups
      are FRESH rows pointing at the same GitLab subgroups - members,
      projects and metrics are rebuilt by the initial sync, history stays
      with the old course.
    * ``webhook_mode``: ``move`` re-points the source's ACTIVE webhook
      configurations to the new course - the GitLab-side hooks (URL+secret,
      resolved to a course purely through the configuration) keep working
      with ZERO manual steps, which is the right default when the university
      groups don't change. ``fresh`` creates new configurations with new
      one-time secrets (returned in the result); ``none`` skips webhooks.
    * dates: see :func:`_retune_transferred_settings`.
    * ``archive_source`` archives the old course afterwards (its remaining
      webhook configs get deactivated there - deliberately AFTER the move).
    * ``enqueue_sync`` enqueues the initial sync for the carried groups.
    """
    if carry_mode not in _TRANSFER_CARRY_MODES:
        raise HTTPException(status_code=400, detail="carry_mode must be all|selected|none")
    if webhook_mode not in _TRANSFER_WEBHOOK_MODES:
        raise HTTPException(status_code=400, detail="webhook_mode must be move|fresh|none")

    source = await db.get(Course, source_course_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source course not found")
    src_settings = source.settings
    same_semester = source.semester == new_semester
    years = _year_delta(source.academic_year, new_academic_year)

    new_course = await clone_course(db, source_course_id, new_academic_year, new_semester)
    # Read the clone's settings row with a query of its own. `new_course.settings`
    # is a relationship on an object this session just created: touching it
    # lazy-loads, which an async session cannot do - every transfer ended in a
    # 500 (MissingGreenlet) right here, after the clone was already flushed.
    new_settings = await db.scalar(
        select(CourseSettings).where(CourseSettings.course_id == new_course.id)
    )
    if new_settings is not None:
        try:
            target: AcademicPeriod | None = AcademicPeriod(new_academic_year, new_semester)
        except ValueError:
            target = None
        _retune_transferred_settings(
            new_settings,
            src_settings,
            target=target,
            same_semester=same_semester,
            years=years,
            start=semester_start_date,
            end=semester_end_date,
        )

    # -- Groups --
    teams_carried = 0
    if carry_mode != "none":
        teams_q = select(Team).where(Team.course_id == source_course_id, Team.is_active.is_(True))
        teams = list((await db.scalars(teams_q)).all())
        if carry_mode == "selected":
            wanted = set(team_ids or [])
            teams = [t for t in teams if t.id in wanted]
            if len(teams) != len(wanted):
                raise HTTPException(
                    status_code=400,
                    detail="One or more selected groups do not belong to this course",
                )
        for t in teams:
            db.add(
                Team(
                    course_id=new_course.id,
                    name=t.name,
                    gitlab_group_id=t.gitlab_group_id,
                    gitlab_group_path=t.gitlab_group_path,
                )
            )
            teams_carried += 1
        await db.flush()

    # -- Webhooks --
    webhooks_moved = 0
    webhooks_created = 0
    webhook_secrets: list[dict[str, str]] = []
    if webhook_mode != "none":
        cfg_q = select(WebhookConfiguration).where(
            WebhookConfiguration.course_id == source_course_id,
            WebhookConfiguration.is_active.is_(True),
        )
        configs = list((await db.scalars(cfg_q)).all())
        if webhook_mode == "move":
            for cfg in configs:
                cfg.course_id = new_course.id
                webhooks_moved += 1
            await db.flush()
        else:
            from app.services.webhook_configs import create_configuration

            for cfg in configs:
                created = await create_configuration(
                    db,
                    course_id=new_course.id,
                    name=cfg.name,
                    scope_type=cfg.scope_type,
                    gitlab_group_id=cfg.gitlab_group_id,
                    gitlab_group_path=cfg.gitlab_group_path,
                    gitlab_project_ids=list(cfg.gitlab_project_ids or []),
                    description=cfg.description,
                    actor_user_id=actor_user_id,
                    actor_label=actor,
                )
                webhook_secrets.append({"name": cfg.name, "secret": created.plaintext})
                webhooks_created += 1

    # -- Archive the source (AFTER the webhook move, so its deactivation only
    #    touches configs that intentionally stayed behind) --
    if archive_source:
        await archive_course(db, source_course_id, actor=actor)

    # -- Initial sync for the carried groups --
    sync_enqueued = 0
    if enqueue_sync and teams_carried:
        sync_enqueued = await _enqueue_team_syncs(db, new_course.id)

    try:
        from app.services.audit import write_audit

        await write_audit(
            db,
            action="course.transfer",
            actor=actor,
            entity_type="course",
            entity_id=new_course.id,
            detail={
                "summary": (
                    f"{source.code} transferred to {new_academic_year} {new_semester}: "
                    f"{teams_carried} groups, webhooks={webhook_mode}"
                ),
                "source_course_id": str(source_course_id),
                "carry_mode": carry_mode,
                "webhook_mode": webhook_mode,
            },
        )
    except Exception:
        logger.warning("course_transfer_audit_failed", course_id=str(new_course.id), exc_info=True)

    logger.info(
        "course_transferred",
        source_id=str(source_course_id),
        new_id=str(new_course.id),
        teams=teams_carried,
        webhooks_moved=webhooks_moved,
        webhooks_created=webhooks_created,
        sync_enqueued=sync_enqueued,
    )
    return TransferResult(
        course=new_course,
        teams_carried=teams_carried,
        webhooks_moved=webhooks_moved,
        webhooks_created=webhooks_created,
        webhook_secrets=webhook_secrets,
        sync_enqueued=sync_enqueued,
        source_archived=archive_source,
    )


async def archive_course(
    db: AsyncSession, course_id: uuid.UUID, *, actor: str = "system"
) -> Course:
    """Set is_active=False and archived_at=now(). Cancel all running jobs.

    ``actor`` records WHO archived it in the audit log (``"system"`` for the
    semester-end auto-archive sweep, the username for a manual archive) so the
    dashboard "Follow the latest updates" feed can surface it.
    """
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Set lock timeout to avoid blocking on import transactions
    try:
        await db.execute(text("SET LOCAL lock_timeout = '200ms'"))
        course.is_active = False
        course.archived_at = datetime.now(UTC)
        await db.flush()
    except (OperationalError, DBAPIError) as e:
        err_msg = str(e).lower()
        if "lock" in err_msg and ("timeout" in err_msg or "not available" in err_msg):
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Course is currently being imported. Please wait for import to complete.",
            ) from e
        raise

    # Cancel all pending/running background jobs for this course's teams
    cancelled = await _cancel_course_jobs(db, course_id)
    if cancelled:
        logger.info("course_jobs_cancelled", course_id=str(course_id), count=cancelled)

    # Deactivate all webhook configurations so the auth lookup ignores them
    # while the course is archived.  Configs are preserved (not deleted) so
    # they can be re-enabled if the course is reactivated.
    deactivated = await _deactivate_course_webhooks(db, course_id)
    if deactivated:
        logger.info(
            "course_webhooks_deactivated",
            course_id=str(course_id),
            count=deactivated,
        )

    # Audit trail so the archive surfaces in "Follow the latest updates"
    # (mapped to the "course.archive" action). Best-effort - never block the
    # archive on an audit-write hiccup.
    try:
        from app.services.audit import write_audit

        await write_audit(
            db,
            action="course.archive",
            actor=actor,
            entity_type="course",
            entity_id=course_id,
            detail={"summary": f"{course.code} - {course.name}"},
        )
    except Exception:
        logger.warning("course_archive_audit_failed", course_id=str(course_id), exc_info=True)

    logger.info("course_archived", course_id=str(course_id), actor=actor)
    return course


async def activate_course(db: AsyncSession, course_id: uuid.UUID) -> Course:
    """Set is_active=True and clear archived_at. Auto-syncs all teams.

    Also flips ``CourseSettings.skip_auto_archive`` to True so the
    semester-end auto-archive sweep does not immediately re-archive the
    course on its next run (common when reactivating past the semester
    end date to finish grading).  Teachers can manually toggle the flag
    back off from the course settings page.
    """
    course = await db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.is_active = True
    course.archived_at = None

    # Opt this course out of the next auto-archive pass.
    cs = (
        await db.execute(select(CourseSettings).where(CourseSettings.course_id == course_id))
    ).scalar_one_or_none()
    if cs is not None:
        cs.skip_auto_archive = True

    await db.flush()

    # Auto-sync all teams in this course on activation
    await _enqueue_team_syncs(db, course_id)

    # Archiving switched every webhook configuration off, and reactivation
    # deliberately leaves them off - the operator decides which scopes still
    # apply (see _deactivate_course_webhooks). Nothing said so, though, so a
    # reactivated course looks live while GitLab deliveries keep coming back
    # 401 - which is exactly how it was found here: archive, reactivate, and
    # every webhook was refused with no hint of why. Name the number.
    still_off = await db.scalar(
        select(func.count())
        .select_from(WebhookConfiguration)
        .where(
            WebhookConfiguration.course_id == course_id,
            WebhookConfiguration.is_active.is_(False),
        )
    )
    if still_off:
        logger.info(
            "course_activated_webhooks_still_disabled",
            course_id=str(course_id),
            count=still_off,
            msg=(
                "Course reactivated with webhook configurations left disabled by the "
                "archive. GitLab deliveries stay 401 until they are re-enabled in "
                "course settings."
            ),
        )

    logger.info("course_activated", course_id=str(course_id))
    return course


async def _deactivate_course_webhooks(db: AsyncSession, course_id: uuid.UUID) -> int:
    """Deactivate all webhook configurations for a course on archive.

    Sets ``is_active=False`` on every active WebhookConfiguration row owned
    by the course.  The webhook authentication lookup filters on
    ``is_active``, so deactivated configs will reject incoming webhooks
    with 401.  Rows are preserved (never deleted) so audit trail and
    previous-secret rotation grace state remain intact.  When the course
    is reactivated the configurations stay deactivated and must be
    re-enabled manually from the settings page (intentional - operators
    decide which scopes are still relevant after archive).

    Returns the number of configurations deactivated.
    """
    stmt = select(WebhookConfiguration).where(
        WebhookConfiguration.course_id == course_id,
        WebhookConfiguration.is_active.is_(True),
    )
    rows = (await db.scalars(stmt)).all()
    if not rows:
        return 0
    for cfg in rows:
        cfg.is_active = False
    await db.flush()
    return len(rows)


async def _cancel_course_jobs(db: AsyncSession, course_id: uuid.UUID) -> int:
    """Cancel all enqueued/running background jobs for a course.

    Returns the number of jobs cancelled.
    """
    return await cancel_jobs_for_course(db, course_id, reason="Cancelled: course archived")


async def _has_pending_sync(db: AsyncSession, team_id: uuid.UUID) -> bool:
    """Check if a sync job is already enqueued or running for this team."""
    existing = await db.execute(
        select(BackgroundJob.id)
        .where(
            BackgroundJob.team_id == team_id,
            BackgroundJob.job_type == "sync",
            BackgroundJob.status.in_(["enqueued", "started", "running"]),
        )
        .limit(1)
    )
    return existing.scalar_one_or_none() is not None


async def _enqueue_team_syncs(db: AsyncSession, course_id: uuid.UUID) -> int:
    """Enqueue sync + metrics refresh for all teams in a course."""
    teams_q = select(Team).where(Team.course_id == course_id, Team.is_active.is_(True))
    teams = (await db.scalars(teams_q)).all()
    if not teams:
        return 0

    count = 0
    try:
        from app.services.events import enqueue_metrics_refresh, enqueue_sync_job

        for team in teams:
            # Skip if a sync is already enqueued or running for this team
            if await _has_pending_sync(db, team.id):
                continue

            # Create a lightweight background job record for the sync
            job = BackgroundJob(
                team_id=team.id,
                course_id=course_id,
                job_type="sync",
                status="enqueued",
            )
            db.add(job)
            await db.flush()
            enqueue_sync_job(str(team.id), str(job.id), course_id=str(course_id))
            enqueue_metrics_refresh(str(team.id))
            count += 1
    except Exception:
        logger.warning(
            "course_activate_sync_enqueue_failed",
            course_id=str(course_id),
            exc_info=True,
        )

    if count:
        logger.info("course_activate_syncs_enqueued", course_id=str(course_id), count=count)
    return count
