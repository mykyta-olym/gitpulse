"""Job 1: process_event - dispatch a single webhook event to its type processor.

Idempotency
-----------
- Layer 1 (event dedup): The event row already exists; we skip if ``processed``
  is True.
- Layer 2 (entity upsert): Each type processor uses INSERT ... ON CONFLICT UPDATE
  semantics via SQLAlchemy merge/upsert patterns.
- Job-level dedup lock via ``@idempotent_job``.

Retry strategy
--------------
RQ Retry with exponential intervals: 10 s -> 30 s -> 90 s (3 attempts).
On final failure the event is marked ``processing_error`` and lands in the RQ
FailedJobRegistry for manual inspection.
"""

import asyncio
import logging
import time
import traceback
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from app.observability.metrics import WEBHOOK_PROCESSED, WEBHOOK_PROCESSING_DURATION
from app.utils.constants import (
    MAX_ERROR_MSG_LEN,
    MAX_TITLE_LEN,
    MAX_TRACEBACK_HEAD,
    MAX_TRACEBACK_TAIL,
)
from app.workers.idempotency import idempotent_job

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_EventHandler = Callable[..., Awaitable[None]]


@idempotent_job
def process_event(event_id: str) -> None:
    """RQ job: process a single webhook event by ID."""
    asyncio.run(_process_async(event_id))


# Event types we receive but intentionally ignore (no processing needed).
# "subgroup" arrives from group-level webhooks; we accept it (so it is never an
# unhandled-kind warning) but do not act on it - team creation is a deliberate
# manual action, not an automatic side effect.
_IGNORABLE_KINDS = frozenset({"deployment", "release", "wiki_page", "build", "subgroup"})


def _handlers() -> dict[str, _EventHandler]:
    from app.workers.processors.issue_processor import process_issue_event
    from app.workers.processors.mr_processor import process_mr_event
    from app.workers.processors.note_processor import process_note_event
    from app.workers.processors.pipeline_processor import process_pipeline_event
    from app.workers.processors.push_processor import process_push_event

    return {
        "issue": process_issue_event,
        # Confidential issues/notes carry the same payload shape as their
        # public counterparts, so route them through the same processors - a
        # confidential issue is still student work we must capture.
        "confidential_issue": process_issue_event,
        "merge_request": process_mr_event,
        "note": process_note_event,
        "confidential_note": process_note_event,
        "push": process_push_event,
        "tag_push": process_push_event,
        "pipeline": process_pipeline_event,
    }


async def _process_async(event_id: str) -> None:
    from app.config import get_settings
    from app.db.session import async_session_ctx, dispose_engine, init_engine
    from app.models.webhook_event import WebhookEvent
    from app.observability.tracing import get_tracer

    settings = get_settings()
    init_engine(str(settings.database_url))

    t0 = time.monotonic()
    _span_ctx = None
    try:
        async with async_session_ctx() as session:
            event = await session.get(WebhookEvent, event_id)
            if event is None:
                logger.error("Event %s not found - stale job?", event_id)
                return

            # Already processed -> idempotent skip
            if event.processed:
                logger.info("Event %s already processed - skipping", event_id)
                return

            payload = event.payload or {}
            object_kind = event.gitlab_object_kind or payload.get("object_kind", "")

            # Start OTel span for processing
            tracer = get_tracer()
            if tracer:
                _span_ctx = tracer.start_as_current_span(
                    "process_event",
                    attributes={
                        "app.event_id": event_id,
                        "app.object_kind": object_kind,
                        "app.project_id": event.gitlab_project_id,
                        "app.correlation_id": str(event.correlation_id or ""),
                    },
                )
                _span_ctx.__enter__()

            # Handle ignorable event types: mark processed without error
            if object_kind in _IGNORABLE_KINDS:
                event.processed = True
                event.processed_at = datetime.now(UTC)
                await session.commit()
                logger.debug("Ignored event kind=%s (known-ignorable)", object_kind)
                return

            # Member events: trigger immediate team membership sync
            if object_kind == "member":
                await _process_member_event(session, event, payload)
                elapsed = time.monotonic() - t0
                WEBHOOK_PROCESSED.labels(event_type="member", status="ok").inc()
                WEBHOOK_PROCESSING_DURATION.labels(event_type="member").observe(elapsed)
                logger.info("Processed member event %s in %.3fs", event_id, elapsed)
                return

            handler = _handlers().get(object_kind)
            if handler is None:
                logger.warning("No handler for object_kind=%s", object_kind)
                event.processed = True
                event.processing_error = f"unhandled_kind:{object_kind}"
                await session.commit()
                return

            try:
                await handler(session, payload, event.gitlab_project_id)
                event.processed = True
                event.processed_at = datetime.now(UTC)
                if settings.feature_event_pipeline:
                    from app.services.audit import write_audit

                    await write_audit(
                        session,
                        action="event.processed",
                        entity_type="webhook_event",
                        entity_id=event.id,
                        detail={"object_kind": object_kind, "project_id": event.gitlab_project_id},
                        correlation_id=event.correlation_id,
                    )
                await session.commit()
                await _after_processed(session, event, payload, object_kind, event_id)

                elapsed = time.monotonic() - t0
                WEBHOOK_PROCESSED.labels(event_type=object_kind, status="ok").inc()
                WEBHOOK_PROCESSING_DURATION.labels(event_type=object_kind).observe(elapsed)
                logger.info(
                    "Processed event %s (%s) in %.3fs",
                    event_id,
                    object_kind,
                    elapsed,
                )
            except Exception:
                await session.rollback()
                # The rollback expired the event; reading its retry_count
                # lazily is IO an async session cannot do (MissingGreenlet),
                # so the failure was never recorded - no retry count, no
                # stored error, never the dead-letter queue. Re-read it.
                await session.refresh(event)
                await _record_failure(session, event, object_kind, event_id, settings)
                await session.commit()
                WEBHOOK_PROCESSED.labels(event_type=object_kind, status="error").inc()
                logger.exception("Failed to process event %s", event_id)
                # Don't re-raise if moved to DLQ (no more retries needed)
                if event.dead_letter_at is not None:
                    return
                raise  # let RQ retry
    finally:
        if _span_ctx is not None:
            with suppress(Exception):
                _span_ctx.__exit__(None, None, None)
        await dispose_engine()


async def _process_member_event(
    session: "AsyncSession", event: Any, payload: dict[str, Any]
) -> None:
    """Membership changed in GitLab: mark the event processed, sync the team's
    members now, then refresh what shows the roster."""
    event.processed = True
    event.processed_at = datetime.now(UTC)
    await session.commit()
    await _sync_members_on_member_event(session, payload, event.gitlab_project_id)
    with suppress(Exception):
        await _invalidate_project_cache(event.gitlab_project_id)
    with suppress(Exception):
        await _enqueue_project_intel_refresh(event.gitlab_project_id)
    with suppress(Exception):
        await _invalidate_page_cache(session, event.gitlab_project_id)
    with suppress(Exception):
        await _notify_dashboard_update(session, event.gitlab_project_id, "member")


async def _after_processed(
    session: "AsyncSession",
    event: Any,
    payload: dict[str, Any],
    object_kind: str,
    event_id: str,
) -> None:
    """The best-effort side-effects of a processed event.

    The event is already ``processed=True`` and committed, so it will NOT be
    retried by the next sweep. These are observability/cache niceties: one
    that raises is logged as a WARNING (with a Prometheus counter ops can
    alert on) and does NOT bubble - bubbling would land in the caller's except,
    which would needlessly increment retry_count although the canonical event
    row is persisted.
    """
    project_id = event.gitlab_project_id

    async def _safe(coro: Awaitable[Any], name: str) -> None:
        try:
            await coro
        except Exception:
            WEBHOOK_PROCESSED.labels(
                event_type=object_kind, status=f"sideeffect_failed:{name}"
            ).inc()
            logger.warning(
                "post_commit_sideeffect_failed event=%s name=%s",
                event_id,
                name,
                exc_info=True,
            )

    # Purge the stale GitLab API cache for this project.
    await _safe(_invalidate_project_cache(project_id), "invalidate_cache")
    # Keep the project page's stored GitLab intelligence (protected branches,
    # contributors, stats) fresh, so it is never fetched on page load.
    await _safe(_enqueue_project_intel_refresh(project_id), "enqueue_project_intel")
    # The payload carries basic data; the enrichment jobs fetch the full
    # details (notes, diff stats, approvals, time tracking) - seconds after
    # the event rather than at the 24 h periodic sweep.
    await _safe(
        _enqueue_immediate_enrichment(payload, object_kind, project_id), "enqueue_enrichment"
    )
    # Event-driven metrics: recompute the affected team.
    await _safe(_enqueue_metrics_for_project(session, project_id), "enqueue_metrics")
    # Drop the stale page HTML so the next request renders fresh metrics.
    await _safe(_invalidate_page_cache(session, project_id), "invalidate_page_cache")
    # Push the update to connected dashboards.
    await _safe(_notify_dashboard_update(session, project_id, object_kind), "notify_dashboard")
    # A push from an unknown committer may mean a new member.
    if object_kind == "push":
        await _safe(
            _maybe_sync_members_on_push(session, payload, project_id), "sync_members_on_push"
        )
    # The classroom assistant answers in GitLab, from its own job.
    await _safe(_enqueue_assistant(session, event, object_kind), "enqueue_assistant")


async def _enqueue_assistant(session: "AsyncSession", event: Any, object_kind: str) -> None:
    """Queue the classroom assistant when the event's course runs a tool for it."""
    from app.services.assistant.events import wants
    from app.services.events import enqueue_assistant_event

    if await wants(session, event.gitlab_project_id, object_kind):
        enqueue_assistant_event(str(event.id))


async def _record_failure(
    session: "AsyncSession", event: Any, object_kind: str, event_id: str, settings: Any
) -> None:
    """Count the failed attempt, keep the traceback (head = root cause, tail =
    final error), move the event to the dead-letter queue after the last
    retry, and audit it."""
    event.retry_count = (event.retry_count or 0) + 1
    full_tb = traceback.format_exc()
    if len(full_tb) > MAX_ERROR_MSG_LEN:
        error_text = full_tb[:MAX_TRACEBACK_HEAD] + "\n...\n" + full_tb[-MAX_TRACEBACK_TAIL:]
    else:
        error_text = full_tb
    event.processing_error = error_text

    dlq_threshold = settings.dlq_max_retries
    if settings.feature_event_pipeline and event.retry_count >= dlq_threshold:
        event.dead_letter_at = datetime.now(UTC)
        event.dead_letter_reason = f"Max retries ({dlq_threshold}) exceeded"
        logger.warning(
            "Event %s moved to DLQ after %d retries",
            event_id,
            event.retry_count,
        )

    await session.merge(event)

    if settings.feature_event_pipeline:
        try:
            from app.services.audit import write_audit

            await write_audit(
                session,
                action="event.failed",
                entity_type="webhook_event",
                entity_id=event.id,
                detail={
                    "object_kind": object_kind,
                    "retry_count": event.retry_count,
                    "error": error_text[:MAX_TITLE_LEN],
                    "moved_to_dlq": event.dead_letter_at is not None,
                },
                correlation_id=event.correlation_id,
            )
        except Exception:
            logger.warning(
                "audit_write_failed_in_error_handler event_id=%s",
                event_id,
                exc_info=True,
            )


async def _resolve_team_id(session: "AsyncSession", gitlab_project_id: int) -> Any:
    """Return the internal team_id owning a GitLab project, or ``None``.

    Consolidates the ``select(GitLabProject.team_id)`` lookup shared by every
    post-commit side-effect (metrics enqueue, dashboard notify, member syncs).

    Four of those side-effects run for a single event, so the same lookup was
    issued repeatedly per webhook - measured at twice per merge-request event,
    which is 2000 identical statements across a 1000-event burst. The answer
    cannot change while one event is being handled, so it is memoised on the
    session. ``_process_async`` opens one session per event, which scopes the
    cache to exactly that event: a project moved to another team is picked up
    by the next event rather than being cached process-wide.
    """

    from app.models.project import GitLabProject

    cache: dict[int, Any] | None = getattr(session, "_gp_team_id_cache", None)
    if cache is None:
        cache = {}
        session._gp_team_id_cache = cache  # type: ignore[attr-defined]
    elif gitlab_project_id in cache:
        return cache[gitlab_project_id]

    result = await session.execute(
        select(GitLabProject.team_id).where(GitLabProject.gitlab_project_id == gitlab_project_id)
    )
    team_id = result.scalar_one_or_none()
    cache[gitlab_project_id] = team_id
    return team_id


async def _enqueue_metrics_for_project(session: "AsyncSession", gitlab_project_id: int) -> None:
    """Look up the team that owns this project and enqueue metrics recomputation.

    Bursts of webhooks from the same team (e.g. CI pipeline emitting 10
    events in 2s) would otherwise enqueue 10 identical metrics jobs.
    RQ deduplicates by function+args, but each enqueue still hits Redis.
    A short SETNX-based debounce per team coalesces the burst into a
    single enqueue without losing eventual recomputation (the job itself
    is idempotent).
    """
    try:
        team_id = await _resolve_team_id(session, gitlab_project_id)
        if team_id is None:
            return

        # 2s burst-coalescing debounce: if a metrics job was already
        # enqueued for this team within the last 2 seconds, skip the
        # duplicate Redis round-trip. Best-effort - any failure falls
        # through to the unconditional enqueue.
        try:
            from app.redis_pool import get_redis

            conn = get_redis()
            if conn is not None:
                key = f"metrics_enqueue_debounce:{team_id}"
                # SET NX EX 2 returns truthy only when the key was created.
                if not conn.set(key, "1", nx=True, ex=2):
                    logger.debug(
                        "Event-driven metrics enqueue debounced for team %s (project %d)",
                        team_id,
                        gitlab_project_id,
                    )
                    return
        except Exception:
            # Redis hiccup -> fall back to unconditional enqueue.
            logger.debug("metrics_enqueue_debounce_skipped", exc_info=True)

        from app.services.events import enqueue_metrics_refresh

        enqueue_metrics_refresh(str(team_id))
        logger.debug(
            "Event-driven metrics enqueued for team %s (project %d)",
            team_id,
            gitlab_project_id,
        )
    except Exception:
        logger.debug("Event-driven metrics enqueue skipped (non-critical)", exc_info=True)


async def _invalidate_project_cache(gitlab_project_id: int) -> None:
    """Invalidate cached GitLab API responses for a project after webhook processing."""
    from app.config import get_settings

    try:
        settings = get_settings()
        if not settings.feature_gitlab_cache:
            return

        from app.services.gitlab.cache import GitLabAPICache

        cache = GitLabAPICache(str(settings.redis_url))
        await cache.connect()
        try:
            await cache.invalidate_project(gitlab_project_id)
        finally:
            await cache.close()
        logger.debug("Cache invalidated for project %d", gitlab_project_id)
    except Exception:
        logger.debug("Cache invalidation skipped (non-critical)", exc_info=True)


async def _enqueue_project_intel_refresh(gitlab_project_id: int) -> None:
    """Queue a debounced refresh of the stored GitLab intelligence snapshot."""
    try:
        try:
            from app.redis_pool import get_redis

            conn = get_redis()
            if conn is not None:
                key = f"project_intel_refresh_debounce:{gitlab_project_id}"
                if not conn.set(key, "1", nx=True, ex=10):
                    logger.debug(
                        "Project intel refresh debounced for GitLab project %d",
                        gitlab_project_id,
                    )
                    return
        except Exception:
            logger.debug("project_intel_refresh_debounce_skipped", exc_info=True)

        from app.config import get_settings
        from app.services.events import get_queue as _get_queue
        from app.workers.sweep import _SWEEP_RETRY

        settings = get_settings()
        _get_queue("default").enqueue(
            "app.workers.sweep.refresh_project_gitlab_intel",
            gitlab_project_id,
            job_timeout=settings.job_timeout_event_seconds,
            retry=_SWEEP_RETRY,
        )
        logger.debug("Queued project intel refresh for GitLab project %d", gitlab_project_id)
    except Exception:
        logger.debug("Project intel refresh enqueue skipped (non-critical)", exc_info=True)


async def _notify_dashboard_update(
    session: "AsyncSession",
    gitlab_project_id: int,
    object_kind: str,
) -> None:
    """Publish dashboard update notifications for the team and course that own this project."""
    try:
        team_id = await _resolve_team_id(session, gitlab_project_id)
        if team_id is None:
            return

        from app.workers.progress import publish_dashboard_update

        publish_dashboard_update(
            "team",
            str(team_id),
            f"webhook_{object_kind}",
            extra={"gitlab_project_id": gitlab_project_id},
        )

        # Also notify the course-level stream
        from app.models.team import Team

        team = await session.get(Team, team_id)
        if team and team.course_id:
            publish_dashboard_update(
                "course",
                str(team.course_id),
                f"webhook_{object_kind}",
                # team_name lets the course page show a teacher toast naming the
                # group whose webhook just arrived, without a second lookup.
                extra={
                    "team_id": str(team_id),
                    "team_name": team.name,
                    "gitlab_project_id": gitlab_project_id,
                },
            )
    except Exception:
        logger.debug("Dashboard notification skipped (non-critical)", exc_info=True)


async def _invalidate_page_cache(
    session: "AsyncSession",
    gitlab_project_id: int,
) -> None:
    """Drop cached project / team / course / analytics / student page fragments.

    Looks up the project's owning team and course, then cascades the
    invalidation across every page-cache scope that depends on this
    project's data so the next dashboard request renders fresh HTML
    instead of serving up to 60 s-old metrics.
    """

    from app.models.project import GitLabProject
    from app.models.team import Team
    from app.models.team_member import TeamMember

    try:
        stmt = select(GitLabProject.id, GitLabProject.team_id).where(
            GitLabProject.gitlab_project_id == gitlab_project_id,
        )
        result = await session.execute(stmt)
        row = result.first()
        if row is None:
            return
        project_id, team_id = row
        course_id: Any = None
        student_ids: list[Any] = []
        if team_id is not None:
            team = await session.get(Team, team_id)
            if team is not None:
                course_id = team.course_id
            member_stmt = select(TeamMember.student_id).where(
                TeamMember.team_id == team_id,
                TeamMember.left_at.is_(None),
            )
            member_result = await session.execute(member_stmt)
            student_ids = [sid for (sid,) in member_result.all() if sid is not None]

        from app.services.page_cache import invalidate_cascade

        invalidate_cascade(
            project_id=project_id,
            team_id=team_id,
            course_id=course_id,
            student_ids=student_ids,
        )
    except Exception:
        # Cache invalidation is best-effort - the 60 s TTL will self-heal.
        logger.debug("page_cache invalidation skipped (non-critical)", exc_info=True)


async def _maybe_sync_members_on_push(
    session: "AsyncSession",
    payload: dict[str, Any],
    gitlab_project_id: int,
) -> None:
    """Trigger on-demand membership sync when a push comes from an unknown user.

    GitPulse is webhook-driven (no periodic scheduler), so this is the real-time
    path: it enqueues a membership sync job immediately when a push from a new
    contributor is detected, instead of waiting for the next manual sync.
    """

    from app.models.student import Student
    from app.models.team_member import TeamMember

    try:
        user_id = payload.get("user_id")
        if not user_id:
            return

        # Find the team for this project
        team_id = await _resolve_team_id(session, gitlab_project_id)
        if team_id is None:
            return

        # Check if this gitlab user is already a known member of the team
        stmt_member = (
            select(TeamMember.student_id)
            .join(Student, TeamMember.student_id == Student.id)
            .where(
                TeamMember.team_id == team_id,
                Student.gitlab_user_id == int(user_id),
            )
        )
        existing = (await session.execute(stmt_member)).scalar_one_or_none()
        if existing is not None:
            return  # Known member - no sync needed

        # Unknown pusher -> enqueue immediate membership sync for this team
        logger.info(
            "Unknown gitlab_user_id=%s pushed to project %d - enqueuing member sync for team %s",
            user_id,
            gitlab_project_id,
            team_id,
        )

        from app.config import get_settings
        from app.services.events import get_queue as _get_queue

        try:
            queue = _get_queue("default")
            queue.enqueue(
                "app.workers.sweep.sync_single_team_members",
                str(team_id),
                job_timeout=get_settings().job_timeout_event_seconds,
            )
        except Exception:
            logger.debug("Could not enqueue on-demand member sync", exc_info=True)
    except Exception:
        logger.debug("Push-based member sync check skipped (non-critical)", exc_info=True)


async def _sync_members_on_member_event(
    session: "AsyncSession",
    payload: dict[str, Any],
    gitlab_project_id: int,
) -> None:
    """Trigger immediate membership sync when GitLab sends a member event.

    GitLab fires 'member' webhooks on user_add_to_team / user_remove_from_team.
    We find the team owning this project and enqueue a sync job.
    """
    try:
        team_id = await _resolve_team_id(session, gitlab_project_id)
        if team_id is None:
            return

        from app.config import get_settings
        from app.services.events import get_queue as _get_queue

        queue = _get_queue("default")
        queue.enqueue(
            "app.workers.sweep.sync_single_team_members",
            str(team_id),
            job_timeout=get_settings().job_timeout_event_seconds,
        )
        logger.info(
            "Member event for project %d - enqueued sync for team %s",
            gitlab_project_id,
            team_id,
        )
    except Exception:
        logger.debug("Member event sync skipped (non-critical)", exc_info=True)


async def _enqueue_immediate_enrichment(
    payload: dict[str, Any],
    object_kind: str,
    gitlab_project_id: int,
) -> None:
    """Enqueue enrichment immediately after webhook processing.

    Webhook payloads contain only basic data; the enrichment jobs re-fetch
    from the GitLab API to get notes, diff stats, approvals, time tracking,
    etc.  Without this, data would only reach full fidelity after the next
    periodic sweep (up to 24 h).

    Note: MR processor already does inline enrichment (changes + approvals),
    but ``enrich_mr`` additionally fetches notes and review activities.
    """
    from app.services.events import enqueue_enrich_issue, enqueue_enrich_mr

    try:
        obj = payload.get("object_attributes", {})
        iid = obj.get("iid")
        if not iid:
            return

        # confidential_issue is dispatched through the same issue processor
        # (it is still student work); enrich it on the same immediate path so
        # it reaches full fidelity in seconds instead of the next full sync.
        if object_kind in ("issue", "confidential_issue"):
            enqueue_enrich_issue(gitlab_project_id, int(iid))
            logger.debug(
                "Immediate enrich_issue enqueued: project=%d iid=%d",
                gitlab_project_id,
                iid,
            )
        elif object_kind == "merge_request":
            enqueue_enrich_mr(gitlab_project_id, int(iid))
            logger.debug(
                "Immediate enrich_mr enqueued: project=%d iid=%d",
                gitlab_project_id,
                iid,
            )
    except Exception:
        logger.debug("Immediate enrichment enqueue skipped (non-critical)", exc_info=True)
