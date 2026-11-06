"""Build the role-filtered recent activity feed for the dashboard."""

import uuid
from collections.abc import Callable, Sequence
from contextlib import suppress
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import ColumnElement, or_, select
from sqlalchemy import and_ as sa_and

from app.api.dashboard._access import _staff_course_ids
from app.api.dashboard._helpers import (
    _format_time_ago,
    logger,
)
from app.dependencies import DbSession
from app.i18n import translate_text
from app.models.audit_log import AuditLog
from app.models.background_job import BackgroundJob
from app.models.course import Course
from app.models.project import GitLabProject
from app.models.team import Team
from app.models.user import User
from app.utils.constants import PAGE_SIZE_REPORTS


def _looks_like_id(actor: str) -> bool:
    """True for an actor that is an opaque identifier rather than a name."""
    a = (actor or "").strip()
    if not a:
        return False
    if a.isdigit():
        return True
    try:
        uuid.UUID(a)
    except ValueError:
        return False
    return True


async def _resolve_id_actors(db: DbSession, actors: list[str | None]) -> dict[str, str]:
    """Map actor ids left by older audit writes to usernames, in one query.

    Rows written before the audit call was corrected stored the session's
    ``user_id`` - a UUID, or GitLab's NUMERIC user id on the OAuth path - so the
    feed rendered them as a bare number ("0001 - ..."). New rows carry the
    username; this keeps the historical ones readable instead of rewriting the
    audit log, which is meant to be immutable.
    """
    ids = {a.strip() for a in actors if a and _looks_like_id(a)}
    if not ids:
        return {}
    numeric = [int(i) for i in ids if i.isdigit()]
    uuids: list[uuid.UUID] = []
    for i in ids:
        if not i.isdigit():
            with suppress(ValueError):
                uuids.append(uuid.UUID(i))
    conditions = []
    if numeric:
        conditions.append(User.gitlab_user_id.in_(numeric))
    if uuids:
        conditions.append(User.id.in_(uuids))
    if not conditions:
        return {}
    rows = (
        await db.execute(
            select(User.id, User.gitlab_user_id, User.username).where(or_(*conditions)),
        )
    ).all()
    resolved: dict[str, str] = {}
    for r in rows:
        if r.username:
            resolved[str(r.id)] = r.username
            if r.gitlab_user_id is not None:
                resolved[str(r.gitlab_user_id)] = r.username
    return resolved


def _humanize_action(action: str) -> str:
    """Last-resort label for an action with no entry in ``_action_labels``.

    The feed used to fall back to the RAW action string, so any audit action
    added without also touching the maps below surfaced to users as
    ``member_exclusion_toggled`` - machine text in a polished widget. Turning
    the identifier into a sentence keeps a new action readable on day one, and
    the explicit label added later just improves the wording.
    """
    text = (action or "").replace("_", " ").replace(".", " ").strip()
    if not text:
        return "Activity"
    return text[:1].upper() + text[1:]


# Audit action prefix -> (icon, icon type). Matched in this order.
_AUDIT_ICONS: dict[str, tuple[str, str]] = {
    "sync": ("refresh-cw", "sync"),
    "sync_team": ("refresh-cw", "sync"),
    "sync_all": ("refresh-cw", "sync"),
    "sync_project": ("refresh-cw", "sync"),
    "run_checks": ("play-circle", "sync"),
    "run_checks_all": ("play-circle", "sync"),
    "check_updated": ("settings", "course"),
    "custom_check_updated": ("settings", "course"),
    "settings_updated": ("settings", "course"),
    "import": ("download", "sync"),
    "course_create": ("plus", "course"),
    "course_import": ("download", "course"),
    "course.create": ("plus", "course"),
    "course.update": ("edit", "course"),
    "course.archive": ("archive", "course"),
    "course.delete": ("trash", "course"),
    "team.create": ("users", "team"),
    "team.add_member": ("user-plus", "team"),
    "team_delete": ("trash", "team"),
    "team_reactivate": ("refresh-cw", "team"),
    "project_delete": ("trash", "team"),
    "project_reactivate": ("refresh-cw", "team"),
    "login": ("log-in", "admin"),
    "admin": ("settings", "admin"),
    "event.replay": ("refresh-cw", "sync"),
    "event.resurrect": ("life-buoy", "sync"),
    "event.processed": ("check-circle", "sync"),
    "event.failed": ("alert-triangle", "sync"),
    "event.purge": ("trash", "sync"),
    "event.delete": ("trash", "sync"),
    "support.create": ("life-buoy", "support"),
    "support.assign": ("user-check", "support"),
    "support.comment": ("message-circle", "support"),
    "support.status": ("check-circle", "support"),
    "support.resolve": ("check-circle", "support"),
    "support.reopen": ("refresh-cw", "support"),
    "course.transfer": ("copy", "course"),
    "course_delete": ("trash", "course"),
    "course_teachers_updated": ("user-check", "course"),
    "custom_check_created": ("plus-circle", "course"),
    "custom_check_deleted": ("trash", "course"),
    "member_exclusion_toggled": ("user-minus", "team"),
    "user_role_update": ("user-check", "admin"),
    "webhook_config.create": ("link-2", "course"),
    "webhook_config.revoke": ("link-2", "course"),
    "webhook_config.rotate": ("refresh-cw", "course"),
    "webhook_secret_changed": ("key", "course"),
    "assistant.connected": ("link", "course"),
    "assistant.disconnected": ("unlink", "course"),
    "assistant.tools_saved": ("settings", "course"),
    "assistant.exercise_prepared": ("git-pull-request", "course"),
    "assistant.token_rejected": ("alert-triangle", "course"),
}
# Human-readable labels so the UI never shows raw dot-notation
_AUDIT_LABELS: dict[str, str] = {
    "sync": "Synced data from GitLab",
    "sync_team": "Group synced from GitLab",
    "sync_all": "All groups synced",
    "run_checks": "Compliance checks triggered",
    "import": "Imported from GitLab",
    "course_create": "Course created",
    "course_import": "Course imported",
    "course.create": "Course created",
    "course.update": "Course updated",
    "course.archive": "Course archived",
    "course.delete": "Course deleted",
    "team.create": "Group created",
    "team.add_member": "Member added to group",
    "team_delete": "Group deleted",
    "team_reactivate": "Group restored",
    "project_delete": "Project unlinked",
    "project_reactivate": "Project restored",
    "check_updated": "Check configuration updated",
    "custom_check_updated": "Custom check updated",
    "login": "User logged in",
    "admin": "Admin action",
    "event.replay": "Events replayed",
    "event.resurrect": "Event resurrected from DLQ",
    "event.processed": "Event processed",
    "event.failed": "Event processing failed",
    "support.create": "Support ticket submitted",
    "support.assign": "Ticket assigned",
    "support.comment": "Comment added to ticket",
    "support.status": "Ticket status changed",
    "support.resolve": "Ticket resolved",
    "support.reopen": "Ticket reopened",
    "course.transfer": "Course transferred to a new semester",
    "course_delete": "Course deleted",
    "course_teachers_updated": "Course teachers updated",
    "custom_check_created": "Custom check created",
    "custom_check_deleted": "Custom check deleted",
    "member_exclusion_toggled": "Member scoring changed",
    "user_role_update": "User role changed",
    "webhook_config.create": "Webhook configuration created",
    "webhook_config.revoke": "Webhook configuration revoked",
    "webhook_config.rotate": "Webhook secret rotated",
    "webhook_secret_changed": "Webhook secret changed",
    "event.purge": "Events purged",
    "event.delete": "Event deleted",
    "run_checks_all": "Compliance checks (all groups)",
    "sync_project": "Project synced from GitLab",
    "assistant.connected": "Assistant bot connected",
    "assistant.disconnected": "Assistant bot disconnected",
    "assistant.tools_saved": "Assistant tools updated",
    "assistant.exercise_prepared": "Assistant exercise prepared",
    "assistant.token_rejected": "GitLab refused the assistant's bot token",
}

# Action prefix -> URL template ({eid} the entity, {tid} the ticket).
_AUDIT_URLS: dict[str, str] = {
    "sync": "/dashboard/courses/{eid}",
    "sync_team": "/dashboard/teams/{eid}",
    "sync_all": "/dashboard/courses/{eid}",
    "run_checks": "/dashboard/teams/{eid}",
    "import": "/dashboard/courses/{eid}",
    "course_create": "/dashboard/courses/{eid}",
    "course_import": "/dashboard/courses/{eid}",
    "course.create": "/dashboard/courses/{eid}",
    "course.update": "/dashboard/courses/{eid}/settings",
    "course.archive": "/dashboard/admin/courses",
    "course.delete": "/dashboard/admin/courses",
    "team.create": "/dashboard/courses/{eid}",
    "team.add_member": "/dashboard/courses/{eid}",
    "team_delete": "/dashboard/teams/{eid}",
    "team_reactivate": "/dashboard/teams/{eid}",
    "project_delete": "/dashboard/projects/{eid}",
    "project_reactivate": "/dashboard/projects/{eid}",
    "check_updated": "/dashboard/courses/{eid}/settings",
    "custom_check_updated": "/dashboard/courses/{eid}/settings",
    "login": "/dashboard/admin/system",
    "admin": "/dashboard/admin/system",
    "event.replay": "/dashboard/admin/events",
    "event.resurrect": "/dashboard/admin/events",
    "event.processed": "/dashboard/admin/events",
    "event.failed": "/dashboard/admin/events",
    "support.create": "/dashboard/support/ticket/{tid}",
    "support.assign": "/dashboard/support/ticket/{tid}",
    "support.comment": "/dashboard/support/ticket/{tid}",
    "support.status": "/dashboard/support/ticket/{tid}",
    "support.resolve": "/dashboard/support/ticket/{tid}",
    "support.reopen": "/dashboard/support/ticket/{tid}",
    "course.transfer": "/dashboard/courses/{eid}",
    "course_delete": "/dashboard/admin/courses",
    "course_teachers_updated": "/dashboard/courses/{eid}/teachers",
    "custom_check_created": "/dashboard/courses/{eid}/settings",
    "custom_check_deleted": "/dashboard/courses/{eid}/settings",
    # entity_id is the TEAM the member belongs to.
    "member_exclusion_toggled": "/dashboard/teams/{eid}",
    "user_role_update": "/dashboard/admin/users",
    "webhook_config.create": "/dashboard/courses/{eid}/settings",
    "webhook_config.revoke": "/dashboard/courses/{eid}/settings",
    "webhook_config.rotate": "/dashboard/courses/{eid}/settings",
    "webhook_secret_changed": "/dashboard/courses/{eid}/settings",
    "assistant.": "/dashboard/courses/{eid}/assistant",
}

# Job-like actions (sync / checks / import / report / enrichment / metrics) are
# surfaced from the BackgroundJob source - the SAME source the admin "Job
# History" reads. Pulled from the audit log as well, the feed showed "phantom"
# rows (e.g. "Synced data from GitLab", "report_generate") with no matching job
# in Job History. The audit log provides only genuine non-job activity (course
# / group / member / settings / support / events).
#
# NB: matched by PREFIX, not exact value - the feed labels job actions via
# ``action.startswith(prefix)``, so variants like ``sync_project`` /
# ``sync_single`` must be excluded too (an exact ``notin_`` list let them leak
# through as "Synced data from GitLab").
_JOB_LIKE_PREFIXES = (
    "sync",
    "run_checks",
    "import",
    "report",
    "enrich",
    "compute_metrics",
    "metrics",
    "membership",
)

# Project link/unlink/restore churn is admin housekeeping, not meaningful
# "latest updates" - and it lingers for days after the project is gone, reading
# as a phantom entry.
_NOISE_ACTIONS = ("project_delete", "project_reactivate")

# Machine actors, humanized.
_MACHINE_ACTORS = {
    "api_token": "Teacher API",
    "system": "System",
    "scheduler": "Scheduler",
    "worker": "Background worker",
    "auto-import": "Course import",
}

# Job type -> (icon, icon type, label).
_JOB_TYPES: dict[str, tuple[str, str, str]] = {
    "sync": ("refresh-cw", "sync", "Data synced from GitLab"),
    "run_checks": ("play-circle", "sync", "Compliance checks completed"),
    "enrichment": ("database", "sync", "Data enrichment completed"),
    "enrich": ("database", "sync", "Data enrichment completed"),
    "membership_sync": ("users", "sync", "Membership synced"),
}

# Audit actions that are states of one entity's life: only the latest shows.
_LIFECYCLE_CATEGORY = {
    "team.create": "team_lifecycle",
    "team_delete": "team_lifecycle",
    "team_reactivate": "team_lifecycle",
    "project_delete": "project_lifecycle",
    "project_reactivate": "project_lifecycle",
    "course_create": "course_lifecycle",
    "course_import": "course_lifecycle",
    "course.create": "course_lifecycle",
    "course.delete": "course_lifecycle",
    "course.archive": "course_lifecycle",
}

# A course sync or Run Checks fans out into per-group jobs; completed ones
# inside this window fold into one "Synced N groups" entry.
_BURST_WINDOW_S = 300.0

T = Callable[[str], str]
Entry = dict[str, Any]


def _entry(
    t: T,
    icon: str,
    icon_type: str,
    action: str,
    detail: str,
    when: datetime,
    url: str | None,
    **internal: Any,
) -> Entry:
    """A feed row by the System actor (jobs and derived course events)."""
    return {
        "icon": icon,
        "icon_type": icon_type,
        "actor": t("System"),
        "action": action,
        "text": f"{t('System')} - {action}",
        "detail": detail,
        "time_ago": _format_time_ago(when),
        "url": url,
        **internal,
        "_sort_ts": when,
    }


# -- The audit log ------------------------------------------------------------


def _event_detail(action: str, d: dict[str, Any], t: T) -> str:
    """Event actions keep their facts under other keys than ``summary``."""
    if action == "event.replay":
        count = d.get("replayed_count")
        event_type = d.get("event_type") or ""
        start = (d.get("start") or "")[:10]
        end = (d.get("end") or "")[:10]
        label = f"{count} {'event' if count == 1 else 'events'}" if count is not None else "events"
        if event_type:
            label += f" ({event_type})"
        parts = [label]
        if start and end:
            try:
                sd, ed = datetime.fromisoformat(start), datetime.fromisoformat(end)
                parts.append(f"{sd.day} {sd.strftime('%b')} -> {ed.day} {ed.strftime('%b')}")
            except Exception:
                logger.debug("event_replay_date_parse_failed", start=start, end=end)
        return " · ".join(parts)
    if action == "event.resurrect":
        reason = (d.get("previous_reason") or "").strip()
        text = t("Re-queued from DLQ")
        if reason:
            text += f" · {reason[:80]}" + ("..." if len(reason) > 80 else "")
        return text
    parts = []
    if d.get("replayed_count"):
        parts.append(f"{d['replayed_count']} events")
    if d.get("event_type"):
        parts.append(str(d["event_type"]))
    if d.get("previous_reason"):
        parts.append(str(d["previous_reason"]))
    return " · ".join(parts)


def _support_detail(d: dict[str, Any], t: T) -> str:
    parts = []
    if d.get("ticket_id"):
        parts.append(f"{t('Ticket')} #{d['ticket_id']}")
    if d.get("assigned_to"):
        parts.append(f"-> {d['assigned_to']}")
    if d.get("status"):
        parts.append(d["status"].replace("_", " ").title())
    return " · ".join(parts)


def _audit_entry(log: AuditLog, role: str, id_actors: dict[str, str], t: T) -> Entry:
    action = log.action or ""
    icon, icon_type, label = "activity", "push", _humanize_action(action)
    for prefix, (ic, it) in _AUDIT_ICONS.items():
        if action.startswith(prefix):
            icon, icon_type = ic, it
            label = _AUDIT_LABELS.get(prefix) or _humanize_action(action)
            break
    label = t(label)

    detail = ""
    if log.detail:
        detail = log.detail.get("summary", "") or log.detail.get("message", "")
        if not detail and action.startswith("event."):
            detail = _event_detail(action, log.detail, t)
        if not detail and action.startswith("support."):
            detail = _support_detail(log.detail, t)

    # Anonymous for students; machine actors humanized.
    if role == "student":
        actor = t("System")
    else:
        actor = (log.actor or "System").strip()
        if _looks_like_id(actor):
            # Never render a bare id: resolve it, or say plainly that the
            # action cannot be attributed.
            actor = id_actors.get(actor) or t("Unknown user")
        machine = _MACHINE_ACTORS.get(actor.lower())
        actor = t(machine) if machine else actor

    url: str | None = None
    eid = str(log.entity_id) if log.entity_id else None
    tid = str(log.detail.get("ticket_id", "")) if log.detail else ""
    for prefix, tpl in _AUDIT_URLS.items():
        if action.startswith(prefix):
            if "{tid}" in tpl and tid:
                url = tpl.replace("{tid}", tid)
            elif "{eid}" in tpl and eid:
                url = tpl.replace("{eid}", eid)
            break

    return {
        "icon": icon,
        "icon_type": icon_type,
        # Actor and action are kept apart as well as combined: the feed renders
        # them on separate lines, GitLab-style (a bold name over the action),
        # and a single pre-joined string cannot be split back apart safely
        # once a name contains " - ".
        "actor": actor,
        "action": label,
        "text": f"{actor} - {label}",
        "detail": detail,
        "time_ago": _format_time_ago(log.timestamp),
        "url": url,
        "_entity_id": eid,
        "_action": action,
        "_sort_ts": log.timestamp,
    }


async def _audit_entries(
    role: str,
    scope_ids: list[uuid.UUID],
    db: DbSession,
    t: T,
    cutoff: datetime,
) -> list[Entry]:
    """Non-job audit rows about the courses in scope, their groups and projects
    (or about nothing in particular), consecutive repeats on one entity folded."""
    stmt = select(AuditLog).where(
        *[~AuditLog.action.like(f"{p}%") for p in _JOB_LIKE_PREFIXES],
        AuditLog.action.notin_(_NOISE_ACTIONS),
        AuditLog.timestamp >= cutoff,
    )
    if scope_ids:
        # Groups, so sync/team actions show; projects too, since a project's
        # lifecycle events carry the project, not the group, as their entity.
        team_ids = (
            await db.execute(select(Team.id).where(Team.course_id.in_(scope_ids)))
        ).scalars()
        project_ids = (
            await db.execute(
                select(GitLabProject.id)
                .join(Team, GitLabProject.team_id == Team.id)
                .where(Team.course_id.in_(scope_ids)),
            )
        ).scalars()
        stmt = stmt.where(
            or_(
                AuditLog.entity_id.in_([*scope_ids, *team_ids, *project_ids]),
                AuditLog.entity_id.is_(None),
            ),
        )
    # Students see no login or admin actions (and, below, no actor names), and
    # nothing of the assistant: its page and its bot are the teachers'.
    if role == "student":
        stmt = stmt.where(
            AuditLog.action.notin_(["login", "admin"]), ~AuditLog.action.like("assistant.%")
        )
    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(PAGE_SIZE_REPORTS)

    rows = list((await db.execute(stmt)).scalars().all())
    id_actors = await _resolve_id_actors(db, [r.actor for r in rows])

    # Consecutive identical actions on the same entity collapse into one row.
    entries: list[Entry] = []
    for log in rows:
        entry = _audit_entry(log, role, id_actors, t)
        prev = entries[-1] if entries else None
        if (
            prev is not None
            and prev["_action"] == entry["_action"]
            and entry["_entity_id"] is not None
            and prev["_entity_id"] == entry["_entity_id"]
        ):
            count = int(prev.get("_count") or 1) + 1
            prev["_count"] = str(count)
            prev["detail"] = t("{n} changes").format(n=count)
        else:
            entries.append(entry)
    return entries


# -- Background jobs ----------------------------------------------------------


def _job_time(job: BackgroundJob) -> datetime | None:
    return job.completed_at or job.enqueued_at


def _bursts(
    jobs: list[BackgroundJob], team_course: dict[uuid.UUID, uuid.UUID]
) -> list[tuple[uuid.UUID, str, list[BackgroundJob]]]:
    """Completed group-scoped sync / run_checks jobs of one course, each within
    the window of the one before: (course, job type, the jobs), two jobs or more.

    Keyed by course AND type, so a course-wide Run Checks folds into "Ran checks
    for N groups" the way a Sync All folds into "Synced N groups". A FAILED job
    never folds - failures appear individually.
    """
    by_course_type: dict[tuple[uuid.UUID, str], list[BackgroundJob]] = {}
    for job in jobs:
        job_type = job.job_type or "sync"
        if job_type not in ("sync", "run_checks") or (job.status or "") != "completed":
            continue
        if job.team_id is None or job.project_id is not None:
            continue
        cid = team_course.get(job.team_id) or job.course_id
        if cid is not None:
            by_course_type.setdefault((cid, job_type), []).append(job)

    bursts = []
    for (cid, job_type), bucket in by_course_type.items():
        bucket.sort(key=lambda j: _job_time(j) or datetime.min.replace(tzinfo=UTC))
        cluster: list[BackgroundJob] = []
        last: datetime | None = None
        for job in bucket:
            ts = _job_time(job)
            if cluster and not (
                last is None or (ts is not None and (ts - last).total_seconds() <= _BURST_WINDOW_S)
            ):
                bursts.append((cid, job_type, cluster))
                cluster = []
            cluster.append(job)
            last = ts or last
        bursts.append((cid, job_type, cluster))
    return [b for b in bursts if len(b[2]) >= 2]


def _burst_entry(
    cid: uuid.UUID, job_type: str, jobs: list[BackgroundJob], course_label: str, t: T
) -> Entry | None:
    latest = max((ts for j in jobs if (ts := _job_time(j)) is not None), default=None)
    if latest is None:
        return None
    detail = course_label
    total_ms = sum(j.duration_ms or 0 for j in jobs)
    if total_ms > 0:
        detail = f"{detail} ({total_ms / 1000:.1f}s)" if detail else f"{total_ms / 1000:.1f}s"
    if job_type == "run_checks":
        icon, action = "play-circle", t("Ran checks for {n} groups").format(n=len(jobs))
    else:
        icon, action = "refresh-cw", t("Synced {n} groups from GitLab").format(n=len(jobs))
    return _entry(
        t,
        icon,
        "sync",
        action,
        detail,
        latest,
        f"/dashboard/courses/{cid}",
        _entity_id=str(cid),
        _action=f"job:{job_type}:aggregate",
    )


def _job_entry(
    job: BackgroundJob,
    role: str,
    team_names: dict[uuid.UUID, str],
    project_names: dict[uuid.UUID, str],
    t: T,
) -> Entry | None:
    job_type = job.job_type or "sync"
    # Internal derived / system jobs (compliance snapshots that feed the
    # compliance charts, leftover scheduled sweeps) are not user-meaningful
    # activity; they stay in the admin Job History. This is the "phantom
    # history" the dashboard used to show.
    if job_type == "compliance_snapshot" or job_type.startswith("scheduled:"):
        return None
    if job_type in _JOB_TYPES:
        icon, icon_type, label = _JOB_TYPES[job_type]
    else:
        # Unknown manual jobs are internal and not actionable for non-admins.
        if job_type.startswith(("scheduled:", "manual:")) and role != "admin":
            return None
        # Friendly fallback: prefix stripped, underscores to spaces, sentence case.
        pretty = job_type.split(":", 1)[-1].replace("_", " ").strip()
        icon, icon_type, label = (
            "activity",
            "sync",
            (pretty[:1].upper() + pretty[1:] if pretty else job_type),
        )

    # A project-scoped run does not read as a whole-group one.
    is_project = job.project_id is not None and job.project_id in project_names
    if is_project and job_type == "sync":
        label = "Project synced from GitLab"
    elif is_project and job_type == "run_checks":
        label = "Project checks completed"

    # A FAILED job reads as a failure, so a sync blocked by an invalid token is
    # visible in the feed instead of silently dropped.
    if (job.status or "") == "failed":
        icon = "alert-triangle"
        label = {
            "sync": "Project sync failed" if is_project else "Sync failed",
            "run_checks": "Compliance checks failed",
            "import": "Import from GitLab failed",
            "enrichment": "Data enrichment failed",
            "enrich": "Data enrichment failed",
        }.get(job_type, f"{label} - failed")

    detail = ""
    url: str | None = None
    if is_project and job.project_id is not None:
        detail = project_names.get(job.project_id, "")
        url = f"/dashboard/projects/{job.project_id}"
    elif job.team_id and job.team_id in team_names:
        detail = team_names[job.team_id]
    elif job.result_summary:
        detail = job.result_summary[:100]
    if url is None:
        if job.team_id:
            url = f"/dashboard/teams/{job.team_id}"
        elif job.course_id:
            url = f"/dashboard/courses/{job.course_id}"
    if job.duration_ms and job.duration_ms >= 1000:
        seconds = f"{job.duration_ms / 1000:.1f}s"
        detail = f"{detail} ({seconds})" if detail else seconds

    return _entry(
        t,
        icon,
        icon_type,
        t(label),
        detail,
        _job_time(job),  # type: ignore[arg-type]  # enqueued_at is NOT NULL
        url,
        _entity_id=str(job.project_id or job.team_id or job.course_id or job.id),
        _action=f"job:project:{job_type}" if is_project else f"job:{job_type}",
    )


async def _job_entries(
    role: str,
    active_ids: list[uuid.UUID],
    db: DbSession,
    t: T,
    cutoff: datetime,
) -> list[Entry]:
    """Completed and failed jobs of the courses in scope, bursts folded.

    Failed ones too, so a failed sync (e.g. an expired GitLab token) surfaces
    here - it used to show only completed jobs, hiding every failure. Same
    two-week window as the audit source, at most 20.
    """
    teams = (
        await db.execute(
            select(Team.id, Team.name, Team.course_id).where(Team.course_id.in_(active_ids)),
        )
    ).all()
    team_names = {r.id: r.name for r in teams}
    team_course = {r.id: r.course_id for r in teams}

    # The courses' jobs and their groups' - and, for admins, system jobs (no
    # group, no course). Scoped even when the courses have no groups yet: the
    # filter used to hang on there being groups, so a teacher whose courses
    # had none saw every course's jobs.
    in_scope: list[ColumnElement[bool]] = [BackgroundJob.course_id.in_(active_ids)]
    if team_names:
        in_scope.append(BackgroundJob.team_id.in_(list(team_names)))
    if role == "admin":
        in_scope.append(sa_and(BackgroundJob.team_id.is_(None), BackgroundJob.course_id.is_(None)))
    stmt = (
        select(BackgroundJob)
        .where(
            BackgroundJob.status.in_(("completed", "failed")),
            BackgroundJob.enqueued_at >= cutoff,
            or_(*in_scope),
        )
        .order_by(
            BackgroundJob.completed_at.desc().nulls_last(),
            BackgroundJob.enqueued_at.desc(),
        )
        .limit(20)
    )
    jobs = list((await db.execute(stmt)).scalars().all())

    # A project-scoped run is named by its project, so a per-project sync does
    # not look like the group's ("System - Data synced from GitLab").
    project_names: dict[uuid.UUID, str] = {}
    project_ids = {j.project_id for j in jobs if j.project_id is not None}
    if project_ids:
        rows = await db.execute(
            select(
                GitLabProject.id,
                GitLabProject.gitlab_project_name,
                GitLabProject.gitlab_project_path,
            ).where(GitLabProject.id.in_(project_ids)),
        )
        project_names = {
            r.id: (
                r.gitlab_project_name
                or (r.gitlab_project_path or "").rsplit("/", 1)[-1]
                or str(r.id)[:8]
            )
            for r in rows.all()
        }

    course_labels = {
        r.id: f"{r.code} - {r.name}"
        for r in (
            await db.execute(
                select(Course.id, Course.code, Course.name).where(Course.id.in_(active_ids)),
            )
        ).all()
    }
    entries: list[Entry] = []
    folded: set[uuid.UUID] = set()
    for cid, job_type, burst in _bursts(jobs, team_course):
        folded.update(j.id for j in burst)
        entry = _burst_entry(cid, job_type, burst, course_labels.get(cid, ""), t)
        if entry is not None:
            entries.append(entry)
    for job in jobs:
        if job.id not in folded and (entry := _job_entry(job, role, team_names, project_names, t)):
            entries.append(entry)
    return entries


# NOTE: the dashboard feed deliberately carries no raw per-project repo events
# (commits, MRs, issues, pipeline runs). It shows *operational* activity
# (syncs, checks, course/group settings changes); the project page is the place
# for repo activity, not the global "what's happening in my groups" widget.


# -- Derived from the courses -------------------------------------------------


def _created_courses(
    entries: list[Entry], active_ids: list[uuid.UUID], courses: Sequence[Course], t: T
) -> list[Entry]:
    """When the feed is still sparse, the newest courses' creation.

    From the courses the caller already holds: re-reading them cost two
    queries (`Course.settings` is a selectin relationship). Courses with no
    `created_at` are dropped, as the SQL this replaced did.
    """
    shown = {e.get("_entity_id") for e in entries if e.get("_entity_id")}
    active = {*active_ids}
    newest = sorted(
        (c for c in courses if c.id in active and c.created_at),
        key=lambda c: c.created_at,
        reverse=True,
    )[:5]
    out: list[Entry] = []
    for c in newest:
        if str(c.id) in shown or len(entries) + len(out) >= 10:
            continue
        out.append(
            _entry(
                t,
                "plus",
                "course",
                t("Course created"),
                f"{c.code} - {c.name}",
                c.created_at,
                f"/dashboard/courses/{c.id}",
            )
        )
    return out


def _archived_courses(
    entries: list[Entry], archived_ids: list[uuid.UUID], courses: Sequence[Course], t: T
) -> list[Entry]:
    """ "Course archived" for archived courses lacking the audit row.

    A course archived before the course.archive audit-write existed has no
    audit row, so the feed never showed its archival. Derived from
    archived_at, skipping courses that already have a real entry.
    """
    shown = {
        e.get("_entity_id")
        for e in entries
        if e.get("_action") == "course.archive" and e.get("_entity_id")
    }
    archived = {*archived_ids}
    return [
        _entry(
            t,
            "archive",
            "course",
            t("Course archived"),
            f"{c.code} - {c.name}",
            c.archived_at,
            "/dashboard/admin/courses",
            _entity_id=str(c.id),
            _action="course.archive",
        )
        for c in courses
        if c.id in archived
        and not c.is_active
        and c.archived_at is not None
        and str(c.id) not in shown
    ]


# -- Passes over the merged feed ----------------------------------------------


def _latest_lifecycle_only(entries: list[Entry]) -> list[Entry]:
    """Of an entity's create / delete / restore rows, only the newest."""
    seen: set[tuple[str, str]] = set()
    out = []
    for entry in entries:
        category = _LIFECYCLE_CATEGORY.get(entry.get("_action") or "")
        eid = entry.get("_entity_id")
        if category and eid:
            if (eid, category) in seen:
                continue
            seen.add((eid, category))
        out.append(entry)
    return out


def _collapse_scheduled(entries: list[Entry]) -> list[Entry]:
    """A run of adjacent same-type scheduled / manual jobs becomes one row.

    Periodic sweeps create a BackgroundJob row even when nothing changed,
    flooding the feed with near-identical entries that push real events out of
    view. The newest row stays, its detail saying how many runs it stands for
    ("(3x)").
    """
    out: list[Entry] = []
    for entry in entries:
        action = str(entry.get("_action") or "")
        if (
            action.startswith(("job:scheduled:", "job:manual:"))
            and out
            and out[-1].get("_action") == entry.get("_action")
        ):
            prev = out[-1]
            runs = int(prev.get("_runs") or 1) + 1
            prev["_runs"] = runs
            base = str(prev.get("_base_detail") or prev.get("detail") or "")
            prev["_base_detail"] = base
            prev["detail"] = f"{base} ({runs}x)" if base else f"{runs}x"
            continue
        out.append(entry)
    return out


def _newest_first(entry: Entry) -> datetime:
    ts = entry.get("_sort_ts")
    return ts if isinstance(ts, datetime) else datetime.min.replace(tzinfo=UTC)


async def _assistant_rows_for_staff(
    entries: list[Entry], scope: list[uuid.UUID], db: DbSession, auth: dict[str, str]
) -> list[Entry]:
    """The assistant's rows only for the courses the reader runs: they link to
    the Assistant page, which a teacher who merely sees a course cannot open
    (students get none of them in the first place)."""
    if not any(str(e.get("_action", "")).startswith("assistant.") for e in entries):
        return entries
    runs = {str(cid) for cid in await _staff_course_ids(db, list(scope), auth)}
    return [
        e
        for e in entries
        if not str(e.get("_action", "")).startswith("assistant.") or e.get("_entity_id") in runs
    ]


async def _build_activity_feed(
    role: str,
    active_ids: list[uuid.UUID],
    db: DbSession,
    _auth: dict[str, str],
    archived_ids: list[uuid.UUID] | None = None,
    locale: str = "sk",
    courses: Sequence[Course] = (),
) -> list[dict[str, Any]]:
    """Build role-filtered recent activity feed.

    ``archived_ids`` are the user's recently-archived courses. Their ids must be
    in scope too, otherwise a ``course.archive`` event (whose entity is a course
    that is, by definition, no longer active) is filtered out and the archive
    never shows in the feed - the exact "auto-archive isn't listed" report.

    ``locale`` translates the labels. They are composed here rather than in the
    template (which renders ``item.text`` verbatim), so without this the whole
    widget stayed English on a Slovak dashboard.
    """

    def t(s: str) -> str:
        return translate_text(locale, s)

    # "Latest updates" means recent: without a window the feed kept months-old
    # rows once activity went quiet, which reads as stale.
    cutoff = datetime.now(UTC) - timedelta(days=14)

    feed: list[Entry] = []
    scope = [*active_ids, *(archived_ids or [])]
    try:
        feed += await _assistant_rows_for_staff(
            await _audit_entries(role, scope, db, t, cutoff), scope, db, _auth
        )
    except Exception:
        logger.debug("audit_log query failed, table may not exist yet")
    if active_ids:
        try:
            feed += await _job_entries(role, active_ids, db, t, cutoff)
        except Exception:
            logger.debug("background_jobs activity synthesis failed", exc_info=True)
    if len(feed) < 3 and active_ids:
        feed += _created_courses(feed, active_ids, courses, t)
    if archived_ids:
        feed += _archived_courses(feed, archived_ids, courses, t)

    feed.sort(key=_newest_first, reverse=True)
    feed = _collapse_scheduled(_latest_lifecycle_only(feed))[:PAGE_SIZE_REPORTS]

    # Internal keys out. The sort timestamp is PROMOTED rather than dropped:
    # `time_ago` is a phrase this module chose, and the reader's "Use relative
    # times" and "Time format" can only be applied client-side, to a `<time>`
    # element carrying the instant itself. Both callers render a template with
    # this list, so a datetime here is never serialised.
    for item in feed:
        item["timestamp"] = item.pop("_sort_ts", None)
        item.pop("_runs", None)
        item.pop("_base_detail", None)
    return feed
