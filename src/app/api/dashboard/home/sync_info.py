"""Per-course sync status used by dashboard course cards."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.dependencies import DbSession
from app.models.background_job import BackgroundJob
from app.models.team import Team


async def _load_course_sync_info(
    active_ids: list[uuid.UUID],
    db: DbSession,
) -> dict[uuid.UUID, dict[str, int]]:
    """Per-course sync status used by dashboard course cards.

    Returns ``{course_id: {"running": R, "queued": Q, "total": T,
    "synced": S}}`` where R+Q = teams currently busy, T = total teams in
    the course, S = teams not in flight (so the initial card render
    matches the X/Y banner emitted by SSE - no flicker on page load).

    Only courses with at least one busy team are included.  Single-
    project syncs (``project_id IS NOT NULL``) are excluded so a 10 s
    project sync does not flash the whole course card.
    """
    info: dict[uuid.UUID, dict[str, int]] = {}
    if not active_ids:
        return info

    # Self-heal stale background jobs older than 1 hour.
    #
    # This belongs on a read path because a crashed worker is exactly what it
    # heals - a dead worker cannot reap its own jobs, so something a reader
    # touches has to. What it must not do is WRITE on every render. The UPDATE
    # was unconditional: every dashboard load took row locks on
    # background_jobs and wrote WAL for a set that is almost always empty, and
    # simultaneous loads contended on the same rows for no reason.
    #
    # Look first, and write only when there is something to heal. The check is
    # a single indexed row.
    stale_cutoff = datetime.now(UTC) - timedelta(hours=1)
    stale_predicate = (
        BackgroundJob.status.in_(["enqueued", "started", "running"]),
        BackgroundJob.enqueued_at < stale_cutoff,
    )
    has_stale = (
        await db.execute(select(BackgroundJob.id).where(*stale_predicate).limit(1))
    ).first()
    if has_stale is not None:
        from sqlalchemy import update

        await db.execute(
            update(BackgroundJob)
            .where(*stale_predicate)
            .values(
                status="failed",
                completed_at=datetime.now(UTC),
                error_message="Job timed out / worker crashed (stale state auto-healed)",
            )
        )
        await db.flush()

    sync_cutoff = datetime.now(UTC) - timedelta(hours=2)
    sync_stmt = (
        select(Team.course_id, BackgroundJob.status, func.count())
        .select_from(BackgroundJob)
        .join(Team, BackgroundJob.team_id == Team.id)
        .where(
            BackgroundJob.job_type == "sync",
            BackgroundJob.project_id.is_(None),
            Team.course_id.in_(active_ids),
            BackgroundJob.status.in_(["enqueued", "started", "running"]),
            BackgroundJob.enqueued_at >= sync_cutoff,
        )
        .group_by(Team.course_id, BackgroundJob.status)
    )
    for cid, status, cnt in (await db.execute(sync_stmt)).all():
        bucket = info.setdefault(cid, {"running": 0, "queued": 0})
        if status == "running":
            bucket["running"] += cnt
        elif status == "enqueued":
            bucket["queued"] += cnt

    if info:
        totals_stmt = (
            select(Team.course_id, func.count(Team.id))
            .where(Team.course_id.in_(list(info.keys())))
            .group_by(Team.course_id)
        )
        for cid, total in (await db.execute(totals_stmt)).all():
            bucket = info[cid]
            bucket["total"] = int(total or 0)
            bucket["synced"] = max(0, bucket["total"] - bucket["running"] - bucket["queued"])

    return info
