"""Semester-end auto-archive sweep.

There is no cron/scheduler daemon (workers run ``with_scheduler=False``), so this
sweep runs OPPORTUNISTICALLY from the staff dashboard, throttled by a Redis lock.
It archives every ACTIVE course whose semester ended more than
``semester_grace_days`` ago - unless the course opted out via
``CourseSettings.skip_auto_archive`` or the feature is disabled
(``semester_auto_archive_enabled``). Idempotent: archived courses are
``is_active=False`` and excluded by the query, so re-running is a no-op.

The dashboard calls :func:`archive_due_courses` INLINE with its own throwaway
session (``async_session_ctx``) rather than enqueuing a worker job - the worker
path (fork + ``asyncio.run`` + re-init engine) was an extra, hard-to-observe
failure surface, and this maintenance is cheap and idempotent.

This is what makes the "Auto-archive due / Auto-archives <date>" badge in Course
Settings and the dashboard "archive recommended" hint actually happen; before,
the UI promised an archive that nothing ever performed.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.config import Settings

logger = logging.getLogger(__name__)


async def archive_due_courses(session: AsyncSession, settings: Settings) -> int:
    """Archive every active course whose semester ended > grace days ago.

    Operates on the given ``session`` and commits per-course. Returns the number
    of courses archived. Safe to call repeatedly (idempotent).
    """
    from app.models.course import Course
    from app.models.course_settings import CourseSettings
    from app.services.courses import archive_course
    from app.utils.semester import is_semester_over

    if not settings.semester_auto_archive_enabled:
        return 0
    grace = settings.semester_grace_days
    weeks = settings.semester_default_length_weeks
    today = datetime.now(UTC).date()

    rows = (
        await session.execute(
            select(Course, CourseSettings)
            .outerjoin(CourseSettings, CourseSettings.course_id == Course.id)
            .where(Course.is_active.is_(True))
        )
    ).all()

    archived = 0
    for course, cs in rows:
        if cs is not None and getattr(cs, "skip_auto_archive", False):
            continue
        if not is_semester_over(cs, grace, weeks, today=today):
            continue
        try:
            # archive_course flushes; commit per-course so one failure does not
            # roll back the courses already archived in this sweep.
            await archive_course(session, course.id)
            await session.commit()
            archived += 1
            logger.info("auto_archived_course code=%s id=%s", course.code, course.id)
        except Exception:
            await session.rollback()
            logger.warning("auto_archive_failed id=%s", course.id, exc_info=True)
    if archived:
        logger.info("auto_archive_sweep_done archived=%d", archived)
    return archived
