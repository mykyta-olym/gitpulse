"""Course configuration rules and the post-commit refresh workflow."""

import asyncio
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import structlog
from rq import Queue
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import (
    check_optimistic_lock,
    raise_bad_request,
    raise_conflict,
    raise_unprocessable,
)
from app.models.course import Course
from app.models.course_settings import CourseSettings
from app.schemas.courses import CourseConfigurationUpdate, CourseSettingsUpdate, CourseUpdate
from app.utils.constants import DEFAULT_MR_TEMPLATE_SECTIONS, DEFAULT_TEST_FILE_PATTERNS
from app.utils.semester import SemesterDateError, validate_semester_window

logger = structlog.get_logger(__name__)


def invalidate_course_settings_cache(course_id: uuid.UUID, team_ids: Sequence[str]) -> None:
    """Drop SSR fragments whose rendered state depends on course settings."""
    from app.services.page_cache import invalidate_cascade

    invalidate_cascade(course_id=course_id)
    for team_id in team_ids:
        invalidate_cascade(team_id=team_id)


def publish_course_settings_changed(
    course_id: uuid.UUID,
    team_ids: Sequence[str],
    *,
    enabled_checks: list[str] | None,
    settings_updated_at: datetime | None,
) -> None:
    """Notify open course/team pages after settings are committed and cache is fresh."""
    from app.workers.progress import publish_dashboard_update

    extra = {
        "enabled_checks": enabled_checks or [],
        "settings_updated_at": settings_updated_at.isoformat() if settings_updated_at else None,
    }
    for team_id in team_ids:
        publish_dashboard_update("team", team_id, "settings_changed", extra=extra)
    publish_dashboard_update("course", str(course_id), "settings_changed", extra=extra)


def enqueue_course_settings_recompute(team_ids: Sequence[str]) -> int:
    """Enqueue metric recomputation for teams affected by a settings change."""

    from app.config import get_settings as _gs
    from app.redis_pool import get_redis as _pool_get_redis

    settings = _gs()
    queue = Queue("default", connection=_pool_get_redis())
    for team_id in team_ids:
        queue.enqueue(
            "app.workers.metrics_job.compute_metrics",
            team_id,
            job_timeout=settings.rq_default_timeout,
        )
    return len(team_ids)


def validate_settings_update(cs: CourseSettings, update_data: dict[str, Any]) -> None:
    """Reject an update the settings page would not accept (422)."""
    # -- Validate the semester window, the way the settings page does --
    # This endpoint wrote whatever it was sent: an end before the start, or a
    # start in 0204, which silently empties every dashboard of the course.
    if {"semester_start_date", "semester_end_date"} & update_data.keys():
        _stored_start = cs.semester_start_date
        _stored_end = cs.semester_end_date
        try:
            validate_semester_window(
                update_data.get("semester_start_date", _stored_start),
                update_data.get("semester_end_date", _stored_end),
                stored_start=_stored_start,
                stored_end=_stored_end,
            )
        except SemesterDateError as exc:
            raise_unprocessable(str(exc))

    gt = update_data.get("green_threshold")
    yt = update_data.get("yellow_threshold")
    eff_green = float(gt) if gt is not None else cs.green_threshold
    eff_yellow = float(yt) if yt is not None else cs.yellow_threshold
    if eff_green < eff_yellow:
        raise_unprocessable("green_threshold must be >= yellow_threshold")

    # -- Validate branch_pattern regex --
    bp = update_data.get("branch_pattern")
    if bp is not None:
        import re as _re

        try:
            _re.compile(bp)
        except _re.error:
            raise_unprocessable(f"Invalid branch_pattern regex: {bp}")


def rotate_webhook_secret(cs: CourseSettings, raw_secret: str) -> None:
    """Store a client-supplied webhook secret, hashed, keeping the previous one
    valid for the rotation grace window."""
    # Hash webhook_secret if provided (never store plaintext).
    # NOTE: prefer the dedicated POST /courses/{id}/group-webhook endpoint
    # which generates the secret server-side and returns the plaintext
    # exactly once.  This legacy path (client-supplied plaintext) is
    # retained for backwards compatibility with the older settings form
    # and now correctly preserves the *previous* secret for the 24 h
    # rotation grace window - matching the behaviour of the dedicated
    # endpoint.
    from app.security.webhook_auth import compute_webhook_lookup_key, hash_webhook_secret
    from app.services.webhook_configs import ROTATION_GRACE as _ROTATION_GRACE

    _now = datetime.now(UTC)
    _is_first_time = cs.webhook_secret_hash is None
    # Move current -> previous so deliveries authenticated with the
    # old secret keep working until the grace window expires.
    cs.webhook_secret_hash_previous = cs.webhook_secret_hash
    cs.webhook_secret_lookup_previous = cs.webhook_secret_lookup
    cs.webhook_secret_hash = hash_webhook_secret(raw_secret)
    cs.webhook_secret_lookup = compute_webhook_lookup_key(raw_secret)
    if _is_first_time:
        cs.webhook_secret_created_at = _now
        cs.webhook_secret_previous_expires_at = None
    else:
        cs.webhook_secret_rotated_at = _now
        cs.webhook_secret_previous_expires_at = _now + _ROTATION_GRACE


def apply_llm_update(cs: CourseSettings, update_data: dict[str, Any]) -> None:
    """Apply only the submitted LLM fields, preserving disabled modules' config."""
    if "llm_course_type" in update_data:
        cs.llm_course_type = update_data.pop("llm_course_type")
    if "llm_custom_prompt" in update_data:
        prompt = update_data.pop("llm_custom_prompt")
        cs.llm_custom_prompt = (prompt.strip() or None) if prompt else None
    if "llm_resource_urls" in update_data:
        cs.llm_resource_urls = sanitize_resource_urls(update_data.pop("llm_resource_urls"))


async def after_settings_update(db: AsyncSession, course_id: uuid.UUID, cs: CourseSettings) -> None:
    """Commit, then drop cached pages, tell open views and recompute groups."""
    from app.models.team import Team

    teams_result = await db.execute(select(Team.id).where(Team.course_id == course_id))
    team_ids = [str(tid) for (tid,) in teams_result.all()]

    # Commit before publishing SSE. Open course/team/settings pages reload on
    # `settings_changed`; publishing while this transaction is still open lets
    # the immediate reload/live-data fetch read old settings from the DB.
    await db.commit()

    # Page-fragment cache invalidation: settings changes mutate every team's
    # compliance ranking AND every course/analytics block, so drop cached HTML
    # before publishing the live-refresh event that triggers SSR reloads.
    try:
        invalidate_course_settings_cache(course_id, team_ids)
    except Exception:
        logger.debug("settings_page_cache_invalidate_failed", exc_info=True)

    # Notify each team dashboard so Run Checks modal/settings-dependent UI
    # refreshes, and notify course-level pages (settings, detail, activity).
    try:
        publish_course_settings_changed(
            course_id,
            team_ids,
            enabled_checks=cs.enabled_checks,
            settings_updated_at=cs.updated_at,
        )
    except Exception:
        logger.debug("settings_dashboard_notify_failed", exc_info=True)

    if not team_ids:
        return

    try:
        count = await asyncio.to_thread(enqueue_course_settings_recompute, team_ids)
        logger.info(
            "settings_change_recompute_enqueued",
            course_id=str(course_id),
            teams=count,
        )
    except Exception:
        logger.warning("settings_change_recompute_failed", course_id=str(course_id), exc_info=True)


def sanitize_resource_urls(entries: list[Any]) -> list[dict[str, str]]:
    """The AI analysis's resource links: only {url, label} entries with an
    http(s) URL, the URL capped at 500 characters and the label at 100."""
    sanitized: list[dict[str, str]] = []
    for entry in entries:
        if isinstance(entry, dict):
            url = str(entry.get("url", "")).strip()[:500]
            label = str(entry.get("label", "")).strip()[:100]
            if url.startswith(("https://", "http://")):
                sanitized.append({"url": url, "label": label})
    return sanitized


async def apply_course_update(db: AsyncSession, course: Course, data: CourseUpdate) -> None:
    check_optimistic_lock(course, data.expected_updated_at, label="Course")

    updatable_fields = {"code", "name", "description", "academic_year", "semester"}
    # Identity columns are NOT NULL: an explicit null means "no change", not a
    # crash on flush.
    required_fields = {"code", "name", "academic_year", "semester"}
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in updatable_fields and not (value is None and key in required_fields):
            setattr(course, key, value)

    # The semester window, when the request names it - the dialog that moves a
    # course to another term moves its dates in the same save, so the course is
    # never left in summer with winter's dates.
    dates_sent = {"semester_start_date", "semester_end_date"} & data.model_fields_set
    if dates_sent:
        cs = course.settings
        if cs is None:
            cs = CourseSettings(
                course_id=course.id,
                mr_template_required_sections=list(DEFAULT_MR_TEMPLATE_SECTIONS),
                test_file_patterns=list(DEFAULT_TEST_FILE_PATTERNS),
            )
            db.add(cs)
            course.settings = cs
        new_start = (
            data.semester_start_date
            if "semester_start_date" in dates_sent
            else cs.semester_start_date
        )
        new_end = (
            data.semester_end_date if "semester_end_date" in dates_sent else cs.semester_end_date
        )
        try:
            validate_semester_window(
                new_start,
                new_end,
                stored_start=cs.semester_start_date,
                stored_end=cs.semester_end_date,
            )
        except SemesterDateError as exc:
            raise_bad_request(str(exc))
        cs.semester_start_date = new_start
        cs.semester_end_date = new_end


def apply_settings_update(cs: CourseSettings, data: CourseSettingsUpdate) -> None:
    check_optimistic_lock(cs, data.expected_updated_at, label="Course settings")

    update_data = data.model_dump(exclude_unset=True, exclude={"expected_updated_at"})
    validate_settings_update(cs, update_data)
    raw_secret = update_data.pop("webhook_secret", None)
    if raw_secret:
        rotate_webhook_secret(cs, raw_secret)
    apply_llm_update(cs, update_data)
    for key, value in update_data.items():
        setattr(cs, key, value)
    cs.updated_at = datetime.now(UTC)


async def lock_configuration(db: AsyncSession, course: Course) -> None:
    """Serialize edits before comparing their versions, including concurrent saves."""
    await db.refresh(course, with_for_update=True)
    if not course.is_active:
        raise_conflict("This course is archived and is read-only.")
    if course.settings is not None:
        await db.refresh(course.settings, with_for_update=True)


async def save_configuration(
    db: AsyncSession, course: Course, data: CourseConfigurationUpdate, *, actor: str
) -> dict[str, Any]:
    """Persist the whole page atomically, then refresh dependent views once."""
    from app.services.course_checks import (
        apply_check_update,
        audit_check_update,
        prepare_check_updates,
    )

    await lock_configuration(db, course)
    cs = course.settings
    if cs is None:
        raise_bad_request("Course settings not found")
    if (course.updated_at and data.course.expected_updated_at is None) or (
        cs.updated_at and data.settings.expected_updated_at is None
    ):
        raise_conflict("The settings page is missing its version. Please reload.")
    check_optimistic_lock(course, data.course.expected_updated_at, label="Course")
    check_optimistic_lock(cs, data.settings.expected_updated_at, label="Course settings")
    targets = await prepare_check_updates(db, course, data.checks)
    await apply_course_update(db, course, data.course)
    apply_settings_update(cs, data.settings)
    changed = {
        code: apply_check_update(targets[code], code, edit) for code, edit in data.checks.items()
    }
    for code, fields in changed.items():
        await audit_check_update(db, targets[code], code, fields, actor)
    await db.flush()
    result = {
        "ok": True,
        "course_updated_at": course.updated_at.isoformat() if course.updated_at else None,
        "settings_updated_at": cs.updated_at.isoformat() if cs.updated_at else None,
        "check_updated_at": {
            code: target.updated_at.isoformat() if target.updated_at else None
            for code, target in targets.items()
        },
    }
    await after_settings_update(db, course.id, cs)
    return result
