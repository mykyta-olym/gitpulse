"""Server-Sent Events stream for course-level sync status."""

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import suppress
from datetime import UTC

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.errors import raise_not_found
from app.api.helpers.course_sync_state import course_sync_state, last_updated
from app.dependencies import ApiAuth, DbSession
from app.models.course import Course
from app.redis_pool import get_redis as _pool_get_redis
from app.services.gitlab.token_health import cached_status as _gitlab_cached_status

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/courses/{course_id}/sync-stream", name="course_sync_stream")
async def course_sync_stream(
    course_id: uuid.UUID,
    request: Request,
    _auth: ApiAuth,
) -> StreamingResponse:
    """Stream course sync status via Server-Sent Events.

    Replaces client-side polling with a server-push model.
    The server polls the DB every 2s and pushes updates.
    Also subscribes to Redis pub/sub channels for faster notification
    when individual sync jobs complete.

    Events emitted:
      - ``data`` with JSON matching CourseSyncStatusResponse schema
      - Named ``complete`` event when all syncs finish (``has_active_sync=false``)
      - Heartbeat comments every 15s

    Note: This endpoint intentionally avoids the ``db: DbSession``
    FastAPI dependency.  The DI-injected session's cleanup runs inside
    Starlette's middleware cancel scope; when the streaming response
    starts, that scope is cancelled and ``session.close()`` raises
    ``CancelledError``, leaking the underlying asyncpg connection.
    We use ``async_session_ctx`` instead so the session is closed
    *before* we return the ``StreamingResponse``.
    """
    from app.db.session import async_session_ctx

    async with async_session_ctx() as _init_session:
        course = await _init_session.get(Course, course_id)
        if not course:
            raise_not_found("Course not found")

        # Authorize: this stream exposes each team's avg score and traffic
        # light, so a student (or any logged-in user) must not be able to watch
        # a foreign course's live sync feed by UUID. Same model as the team /
        # course dashboard streams - bearer tokens and admins unrestricted,
        # everyone else only courses they may view. 404-on-denial keeps foreign
        # course UUIDs unenumerable.
        from app.api.dashboard._access import can_manage_via_request

        if not await can_manage_via_request(request, _init_session, course=course):
            raise_not_found("Course not found")

    return StreamingResponse(
        _sync_events(request, course),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "identity",
        },
    )


async def _sync_snapshot(session: DbSession, course: Course) -> dict[str, object]:
    """The stream's payload: the poll's (``get_course_sync_status``), plus the
    timer anchor, ISO times and what the stream needs to spot finished groups."""
    state = await course_sync_state(session, course)
    teams_data = []
    for team in state.teams:
        tm = state.team_metrics.get(team.id)
        ss = state.status_by_team.get(team.id)
        label, label_iso = last_updated(tm, ss)
        teams_data.append(
            {
                "team_id": str(team.id),
                "team_name": team.name,
                "member_count": state.member_counts.get(team.id, 0),
                "sync_status": ss,
                "avg_score": tm.avg_weighted_score if tm else None,
                "traffic_light": tm.overall_traffic_light if tm else None,
                "last_updated": label,
                "last_updated_iso": label_iso,
                "sync_note": state.note_by_team.get(team.id),
            }
        )

    running, queued = state.count("running"), state.count("enqueued")
    result: dict[str, object] = {
        "sync_running_count": running,
        "sync_queued_count": queued,
        "sync_failed_count": state.count("failed"),
        "sync_cancelled_count": state.count("cancelled"),
        # A group that finished a moment ago keeps the sync active, so the
        # stream's debounce and the client's verify call don't end it during
        # the lull between batches. Team-wide jobs only: project syncs have
        # their own row badge and page, and lighting the course bar for a
        # 10-20 s project run made it flicker.
        "has_active_sync": running > 0 or queued > 0 or bool(state.recently_finished),
        "teams": teams_data,
        "sync_status_by_project": {str(pid): s for pid, s in state.status_by_project.items()},
        "project_sync_running_count": state.project_count("running"),
        "project_sync_queued_count": state.project_count("enqueued"),
        "gitlab_token_ok": _gitlab_cached_status() != "unauthorized",
    }
    # Authoritative server-side start of the active Sync All run (ms since
    # epoch), so the client anchors the elapsed timer to the server clock
    # instead of a per-page timestamp.
    earliest = state.earliest_active_enqueued
    if earliest is not None and (running > 0 or queued > 0):
        if earliest.tzinfo is None:
            earliest = earliest.replace(tzinfo=UTC)
        result["started_at_ms"] = int(earliest.timestamp() * 1000)

    if state.teams:
        from app.api.dashboard._stats import total_distinct_contributors
        from app.utils.semester import semester_floor_utc

        result["total_students"] = await total_distinct_contributors(
            session,
            [t.id for t in state.teams],
            commit_since=semester_floor_utc(course.settings if course else None),
        )
    else:
        result["total_students"] = 0

    # Progress: every group in the course is the denominator (what the Groups
    # table shows); the groups not running or queued are done.
    total = len(state.teams)
    if total > 0 and state.in_flight > 0:
        done = max(0, total - state.in_flight)
        result["synced_groups"] = done
        result["total_groups"] = total
        result["progress"] = round(done / total * 100)

    # For the stream's group-completion toasts; popped before sending.
    result["_team_completed_set"] = {
        tid for tid, s in state.status_by_team.items() if s == "completed"
    }
    result["_team_name_map"] = {t.id: t.name for t in state.teams}
    return result


async def _sync_events(request: Request, course: Course) -> AsyncIterator[str]:
    """SSE generator: polls DB + listens to Redis pub/sub."""
    from app.db.session import async_session_ctx

    # Redis pub/sub listener for fast completion detection
    redis_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=200)
    redis_task: asyncio.Task[None] | None = None

    try:
        redis_task = asyncio.create_task(_redis_course_listener(str(course.id), redis_queue))
    except Exception:
        logger.debug("Redis pub/sub for course sync stream unavailable")

    poll_interval = 2
    heartbeat_counter = 0
    prev_hash = ""
    _consecutive_errors = 0
    _max_backoff = 30  # cap retry delay at 30 s
    # Track completed teams for group-level toast notifications.
    # Seed with the initial snapshot so we don't flood toasts on connect.
    _prev_completed_teams: set[uuid.UUID] | None = None
    # Debounce `complete` emission: the per-group sync workflow can have
    # brief windows (1-2 s between batches) where running + queued both
    # hit zero in the DB before the next batch is enqueued.  Emitting
    # `complete` on the first zero snapshot makes the client kill the
    # progress bar prematurely.  Require N consecutive zero snapshots
    # before declaring the sync truly done, including for streams that
    # are opened *during* such a zero-window (new client connects just
    # as the workers are cycling batches).
    _consecutive_inactive = 0
    _required_inactive = 3  # 3 x 2 s = 6 s stable inactive window

    try:
        while True:
            if await request.is_disconnected():
                break

            # Drain Redis events (triggers early refresh)
            redis_triggered = False
            while not redis_queue.empty():
                try:
                    redis_queue.get_nowait()
                    redis_triggered = True
                except asyncio.QueueEmpty:
                    break

            # Build snapshot with a cancellation-safe session context.
            snapshot = None
            try:
                async with async_session_ctx() as session:
                    snapshot = await _sync_snapshot(session, course)
                _consecutive_errors = 0  # reset on success
            except Exception:
                _consecutive_errors += 1
                if _consecutive_errors <= 3:
                    logger.exception("sync_stream_snapshot_error")
                elif _consecutive_errors == 4:
                    logger.warning(
                        "sync_stream_snapshot_error (suppressing further tracebacks)",
                    )
                # else: silently retry

            if snapshot is None:
                backoff = min(poll_interval * (2 ** (_consecutive_errors - 1)), _max_backoff)
                await asyncio.sleep(backoff)
                continue

            is_active = snapshot["has_active_sync"]
            if is_active:
                _consecutive_inactive = 0
            else:
                _consecutive_inactive += 1

            # Detect newly completed teams for group-level toast
            _raw_completed = snapshot.pop("_team_completed_set", set())
            cur_completed: set[uuid.UUID] = (
                _raw_completed if isinstance(_raw_completed, set) else set()
            )
            _raw_names = snapshot.pop("_team_name_map", {})
            team_name_map: dict[uuid.UUID, str] = _raw_names if isinstance(_raw_names, dict) else {}
            newly_completed = (
                cur_completed - _prev_completed_teams
                if _prev_completed_teams is not None
                else set()
            )
            if newly_completed:
                names = [team_name_map.get(tid, "?") for tid in newly_completed]
                snapshot["completed_group"] = (
                    names[0] if len(names) == 1 else ", ".join(sorted(names))
                )
            _prev_completed_teams = cur_completed

            # Only send data frame if snapshot changed (avoid dup pushes)
            snap_hash = json.dumps(snapshot, sort_keys=True, default=str)
            if snap_hash != prev_hash or redis_triggered:
                prev_hash = snap_hash
                yield f"data: {json.dumps(snapshot, default=str)}\n\n"

            # Emit `complete` ONLY after N consecutive inactive
            # snapshots (prevents the between-group zero-window race,
            # including on streams opened *during* the zero-window).
            # Evaluated outside the hash-changed guard so stable-zero
            # snapshots still count toward the debounce even when the
            # payload hasn't changed.
            if not is_active and _consecutive_inactive >= _required_inactive:
                yield f"event: complete\ndata: {json.dumps(snapshot, default=str)}\n\n"
                return

            # Heartbeat
            heartbeat_counter += poll_interval
            if heartbeat_counter >= 15:
                heartbeat_counter = 0
                yield ": heartbeat\n\n"

            await asyncio.sleep(poll_interval)

    finally:
        if redis_task and not redis_task.done():
            redis_task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await redis_task


async def _redis_course_listener(
    course_id: str,
    queue: asyncio.Queue[str],
) -> None:
    """Listen to Redis pub/sub for any sync job progress in a course.

    Subscribes to a pattern channel ``course_sync:{course_id}`` so the SSE
    generator can do an early refresh when a job completes.
    """
    try:
        conn = _pool_get_redis()
        pubsub = conn.pubsub()
        channel = f"course_sync:{course_id}"
        pubsub.subscribe(channel)

        try:
            while True:
                message = await asyncio.to_thread(pubsub.get_message, timeout=2)
                if message and message["type"] == "message":
                    payload = (
                        message["data"].decode()
                        if isinstance(message["data"], bytes)
                        else str(message["data"])
                    )
                    with suppress(asyncio.QueueFull):
                        queue.put_nowait(payload)
                await asyncio.sleep(0.1)
        finally:
            pubsub.unsubscribe(channel)
            pubsub.close()
            conn.close()
    except Exception:
        logger.debug("Redis pub/sub course listener ended for %s", course_id)
