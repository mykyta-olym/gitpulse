"""Webhook configuration & activity reporting.

Centralises the logic that was previously duplicated across
``api/dashboard/home/routes.py`` (per-course attention items) and
``api/dashboard/admin/events.py`` (Event Pipeline page).

A course is considered to have webhooks if it has either:
- a legacy ``CourseSettings.webhook_secret_hash`` set, OR
- at least one active ``WebhookConfiguration`` row.

A course is considered "active" if any of its webhook sources received a
delivery within ``WEBHOOK_INACTIVITY_HOURS``:
- New system: ``WebhookConfiguration.last_used_at`` is recent.
- Legacy system: a ``WebhookEvent`` arrived for one of its GitLab projects.

Brand-new configurations (created within ``WEBHOOK_NEW_CONFIG_GRACE_HOURS``)
are placed in a grace bucket and excluded from the "silent" alert so that
admins are not pinged immediately after creating a configuration.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course_settings import CourseSettings
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.webhook_configuration import WebhookConfiguration
from app.models.webhook_event import WebhookEvent

# Tunable thresholds (kept here so they can be referenced from UI strings too).
WEBHOOK_INACTIVITY_HOURS = 48
WEBHOOK_NEW_CONFIG_GRACE_HOURS = 2


@dataclass(frozen=True)
class WebhookActivityReport:
    """Snapshot of webhook configuration & activity for a set of courses."""

    configured: set[uuid.UUID] = field(default_factory=set)
    """Courses with a legacy secret hash OR at least one active config."""

    active: set[uuid.UUID] = field(default_factory=set)
    """Subset of ``configured`` that received a delivery in the recent window."""

    in_grace: set[uuid.UUID] = field(default_factory=set)
    """Courses with a configuration created within the new-config grace window."""

    silent: set[uuid.UUID] = field(default_factory=set)
    """``configured - active - in_grace`` - courses that should trigger an alert."""

    def has_webhook(self, course_id: uuid.UUID) -> bool:
        return course_id in self.configured


async def compute_webhook_activity(
    db: AsyncSession,
    course_ids: Sequence[uuid.UUID] | None = None,
    *,
    now: datetime | None = None,
) -> WebhookActivityReport:
    """Compute the webhook activity report for the given courses.

    If ``course_ids`` is ``None``, the report is computed across all courses.
    Otherwise it is restricted to the given subset (useful when callers only
    look at active courses).
    """
    now = now or datetime.now(UTC)
    inactivity_cutoff = now - timedelta(hours=WEBHOOK_INACTIVITY_HOURS)
    grace_cutoff = now - timedelta(hours=WEBHOOK_NEW_CONFIG_GRACE_HOURS)

    restrict = course_ids is not None
    course_id_list: list[uuid.UUID] = list(course_ids) if course_ids is not None else []

    # -- Configured courses (legacy hash) --
    legacy_q = select(CourseSettings.course_id).where(
        CourseSettings.webhook_secret_hash.is_not(None),
    )
    if restrict:
        legacy_q = legacy_q.where(CourseSettings.course_id.in_(course_id_list))
    legacy_courses: set[uuid.UUID] = {row[0] for row in (await db.execute(legacy_q)).all()}

    # -- Configured courses (new active config) --
    new_cfg_q = (
        select(WebhookConfiguration.course_id)
        .where(WebhookConfiguration.is_active.is_(True))
        .distinct()
    )
    if restrict:
        new_cfg_q = new_cfg_q.where(WebhookConfiguration.course_id.in_(course_id_list))
    new_cfg_courses: set[uuid.UUID] = {row[0] for row in (await db.execute(new_cfg_q)).all()}

    configured = legacy_courses | new_cfg_courses
    if not configured:
        return WebhookActivityReport()

    configured_list = list(configured)

    # -- Active via new system (recent last_used_at) --
    new_active_q = (
        select(WebhookConfiguration.course_id)
        .where(
            WebhookConfiguration.course_id.in_(configured_list),
            WebhookConfiguration.is_active.is_(True),
            WebhookConfiguration.last_used_at >= inactivity_cutoff,
        )
        .distinct()
    )
    new_active: set[uuid.UUID] = {row[0] for row in (await db.execute(new_active_q)).all()}

    # -- Active via legacy system (recent WebhookEvent on a project of the course) --
    proj_q = (
        select(GitLabProject.gitlab_project_id, Team.course_id)
        .join(Team, GitLabProject.team_id == Team.id)
        .where(
            Team.course_id.in_(configured_list),
            GitLabProject.is_active.is_(True),
            GitLabProject.gitlab_project_id.is_not(None),
        )
    )
    proj_by_course: dict[uuid.UUID, list[int]] = {}
    for gl_pid, cid in (await db.execute(proj_q)).all():
        proj_by_course.setdefault(cid, []).append(gl_pid)

    legacy_active: set[uuid.UUID] = set()
    all_gl_pids = [p for pids in proj_by_course.values() for p in pids]
    if all_gl_pids:
        ev_q = (
            select(WebhookEvent.gitlab_project_id)
            .where(
                WebhookEvent.gitlab_project_id.in_(all_gl_pids),
                WebhookEvent.received_at >= inactivity_cutoff,
            )
            .distinct()
        )
        active_pids = {r[0] for r in (await db.execute(ev_q)).all()}
        legacy_active = {
            cid for cid, pids in proj_by_course.items() if any(p in active_pids for p in pids)
        }

    active = new_active | legacy_active

    # -- Grace window (brand-new configs) --
    grace_q = (
        select(WebhookConfiguration.course_id)
        .where(
            WebhookConfiguration.course_id.in_(configured_list),
            WebhookConfiguration.is_active.is_(True),
            WebhookConfiguration.created_at >= grace_cutoff,
        )
        .distinct()
    )
    in_grace: set[uuid.UUID] = {row[0] for row in (await db.execute(grace_q)).all()}

    silent = configured - active - in_grace

    return WebhookActivityReport(
        configured=configured,
        active=active,
        in_grace=in_grace,
        silent=silent,
    )
