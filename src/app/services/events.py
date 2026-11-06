"""Event service - enqueue async jobs onto RQ queues.

Queue topology
--------------
    high    - webhook event processing (latency-sensitive)
    default - enrichment, metrics, sync
    low     - LLM analysis

All enqueue functions are fire-and-forget from the caller's perspective.
If Redis is down the webhook is still persisted in the DB; the periodic
sweep will pick it up later.
"""

import logging
import threading

from redis.exceptions import RedisError
from rq import Queue, Retry

from app.config import get_settings

logger = logging.getLogger(__name__)

_queues: dict[str, Queue] = {}
_queues_lock = threading.Lock()


def _get_queue(name: str = "default") -> Queue:
    """Lazy-initialise and cache an RQ Queue (thread-safe).

    If a cached Queue's Redis connection is dead, reconnects automatically.
    Works in both the web server (shared pool available) and RQ workers
    (no pool - falls back to a standalone Redis connection).
    """
    # Check existing connection health outside the lock to avoid blocking
    # all queue operations during Redis latency spikes.
    cached_q = _queues.get(name)
    if cached_q is not None:
        try:
            cached_q.connection.ping()
            return cached_q
        except (RedisError, OSError):
            logger.warning("Redis connection for queue '%s' is stale - reconnecting", name)

    with _queues_lock:
        # Re-check under lock (another thread may have reconnected)
        if name in _queues:
            try:
                _queues[name].connection.ping()
            except (RedisError, OSError):
                del _queues[name]

        if name not in _queues:
            try:
                from app.redis_pool import get_redis as _pool_get_redis

                conn = _pool_get_redis()
            except RuntimeError:
                # Pool not initialised (running inside an RQ worker)
                from redis import Redis

                settings = get_settings()
                conn = Redis.from_url(
                    str(settings.redis_url),
                    socket_timeout=settings.redis_socket_timeout_seconds,
                )
            _queues[name] = Queue(name, connection=conn)

        # Read INSIDE the lock: another thread reconnecting a stale queue does
        # ``del _queues[name]`` under this same lock, so an unsynchronised read
        # after releasing it could hit that window and raise KeyError (which
        # _enqueue would swallow into a dropped job).
        return _queues[name]


def get_queue(name: str = "default") -> Queue:
    """Public API: get (or create) a cached RQ Queue by name."""
    return _get_queue(name)


# Total sync attempts (1 initial + retries) before a group is declared failed.
# Kept as a single source of truth: enqueue uses ``max_retries`` below, and the
# sync worker derives "attempt N/M" from RQ's ``retries_left`` against this same
# ceiling so the UI can show "Retrying (2/3)". Auth/token errors are NEVER
# retried (they are not transient) - the worker forces retries_left to 0.
SYNC_MAX_ATTEMPTS = 3


def _retry(max_retries: int = 3) -> Retry:
    """Exponential backoff: 10s -> 30s -> 90s."""
    return Retry(max=max_retries, interval=[10, 30, 90])


def _enqueue(
    queue_name: str,
    task_path: str,
    *args: object,
    timeout_attr: str = "job_timeout_event_seconds",
    max_retries: int = 2,
    description: str = "",
) -> str | None:
    """Generic fire-and-forget enqueue with consistent error handling.

    Returns the job id on success, ``None`` on failure (logged + swept later).
    """
    try:
        settings = get_settings()
        timeout = getattr(settings, timeout_attr)
        # max_retries <= 0 means "never auto-retry" (RQ's Retry rejects max<1).
        # Sync jobs opt out of retry: an auth/GitLab failure is not transient,
        # so retrying just re-runs the same doomed job, which flips the
        # BackgroundJob row running<->failed and makes the progress bar flap
        # ("finished, then restarted itself"). A failed sync must fail once
        # and surface the error instead of looping.
        retry = _retry(max_retries) if max_retries > 0 else None
        job = _get_queue(queue_name).enqueue(
            task_path,
            *args,
            job_timeout=timeout,
            retry=retry,
        )
        logger.debug("Enqueued %s -> %s", description or task_path, job.id)
        return str(job.id)
    except Exception:
        logger.exception("Failed to enqueue %s", description or task_path)
        return None


# -- Job 1: process_event --


def enqueue_event_processing(event_id: str) -> str | None:
    """Enqueue a webhook event for async processing on the HIGH queue."""
    return _enqueue(
        "high",
        "app.workers.event_processor.process_event",
        event_id,
        timeout_attr="job_timeout_event_seconds",
        max_retries=3,
        description=f"process_event({event_id})",
    )


# -- Job 2: enrich_issue --


def enqueue_enrich_issue(project_gitlab_id: int, issue_iid: int) -> str | None:
    """Enqueue issue enrichment from GitLab API."""
    return _enqueue(
        "default",
        "app.workers.enrich_issue.enrich_issue",
        project_gitlab_id,
        issue_iid,
        timeout_attr="job_timeout_event_seconds",
        description=f"enrich_issue({project_gitlab_id}, {issue_iid})",
    )


# -- Job 3: enrich_mr --


def enqueue_enrich_mr(project_gitlab_id: int, mr_iid: int) -> str | None:
    """Enqueue MR enrichment from GitLab API (diff, approvals, notes)."""
    return _enqueue(
        "default",
        "app.workers.enrich_mr.enrich_mr",
        project_gitlab_id,
        mr_iid,
        timeout_attr="job_timeout_enrich_seconds",
        description=f"enrich_mr({project_gitlab_id}, {mr_iid})",
    )


# -- Job 4: compute_metrics --


def enqueue_metrics_refresh(team_id: str) -> str | None:
    """Enqueue compliance metrics recomputation for a team."""
    return _enqueue(
        "default",
        "app.workers.metrics_job.compute_metrics",
        team_id,
        timeout_attr="job_timeout_report_seconds",
        description=f"compute_metrics({team_id})",
    )


# -- Sync job (existing) --


def enqueue_sync_job(team_id: str, job_id: str, course_id: str | None = None) -> str | None:
    """Enqueue full GitLab API sync for a team."""
    return _enqueue(
        "default",
        "app.workers.sync_job.full_sync",
        team_id,
        job_id,
        course_id,
        timeout_attr="job_timeout_sync_seconds",
        # Bounded, VISIBLE retry: the worker surfaces "Retrying (N/M)" per
        # attempt and only declares the group failed after all attempts.
        # Auth/token failures are not retried (worker zeroes retries_left).
        max_retries=SYNC_MAX_ATTEMPTS - 1,
        description=f"sync({team_id})",
    )


def enqueue_project_sync_job(
    project_id: str, job_id: str, course_id: str | None = None
) -> str | None:
    """Enqueue GitLab API sync for a single project."""
    return _enqueue(
        "default",
        "app.workers.sync_project_job.sync_single_project",
        project_id,
        job_id,
        course_id,
        timeout_attr="job_timeout_sync_seconds",
        # Bounded, VISIBLE retry (see enqueue_sync_job).
        max_retries=SYNC_MAX_ATTEMPTS - 1,
        description=f"project_sync({project_id})",
    )


def enqueue_run_checks_job(
    team_id: str,
    job_id: str,
    check_codes: list[str] | None = None,
) -> str | None:
    """Enqueue selective compliance check evaluation.

    Parameters
    ----------
    check_codes:
        Specific check codes to evaluate (e.g. ``["R01", "R03"]``).
        ``None`` means evaluate all enabled checks (ignoring weekly deadlines).
    """
    return _enqueue(
        "high",
        "app.workers.metrics_job.compute_metrics_selective",
        team_id,
        job_id,
        check_codes,
        timeout_attr="job_timeout_report_seconds",
        description=f"run_checks({team_id})",
    )


# -- Classroom assistant --


def enqueue_assistant_event(event_id: str) -> str | None:
    """Hand a processed webhook event to the classroom assistant."""
    return _enqueue(
        "default",
        "app.workers.assistant_job.run_assistant",
        event_id,
        timeout_attr="job_timeout_event_seconds",
        description=f"assistant({event_id})",
    )


def enqueue_assistant_exercise(
    course_id: str, project_ids: list[str], actor: str, job_id: str
) -> str | None:
    """Prepare the issues and merge requests exercise for these projects;
    ``job_id`` is its BackgroundJob, which the top bar follows.

    Not retried: a run that stops part-way is finished by running it again,
    which skips the students who already have their issue.
    """
    return _enqueue(
        "default",
        "app.workers.assistant_job.prepare_exercise",
        course_id,
        project_ids,
        actor,
        job_id,
        timeout_attr="job_timeout_report_seconds",
        max_retries=0,
        description=f"assistant_exercise({course_id})",
    )
