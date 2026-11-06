"""RQ worker entry-point.

Start with:
    python -m app.workers.main

The worker listens on three queues in priority order:
    high    - webhook event processing (latency-sensitive)
    default - enrichment and metric jobs
    low     - report generation (CPU-heavy, can wait)

It also starts the built-in RQ scheduler thread (``with_scheduler=True``) so
that delayed jobs enqueued with ``Queue.enqueue_in`` fire on time - e.g. an
email-delivery retry that backs off and re-enqueues itself. There are no
recurring/cron jobs: GitPulse is webhook-driven, and anything that cannot be
event-driven is an explicit manual action.
"""

import contextlib
import logging
import os
import time

from redis import Redis
from rq import Queue, SimpleWorker, Worker
from rq.job import Job

from app.config import get_settings
from app.observability.logging import redact_url_credentials, setup_logging
from app.observability.tracing import setup_tracing

_MAX_RETRIES = 10
_INITIAL_BACKOFF = 2  # seconds


def record_job_failure(job: Job, *_details: object) -> None:
    """Count execution errors across forked workers; leave RQ retry handling intact."""
    from app.observability.metrics import RQ_JOB_FAILURES

    queue = job.origin if job.origin in {"high", "default", "low"} else "other"
    RQ_JOB_FAILURES.labels(queue_name=queue).inc()


def _connect_redis(url: str, logger: logging.Logger) -> Redis:  # type: ignore[type-arg]
    """Connect to Redis with exponential backoff retry."""
    backoff = _INITIAL_BACKOFF
    for attempt in range(1, _MAX_RETRIES + 1):
        conn = Redis.from_url(url, socket_connect_timeout=10, retry_on_timeout=True)
        try:
            conn.ping()
            logger.info("Redis connection verified (attempt %d)", attempt)
            return conn
        except Exception as e:
            if attempt == _MAX_RETRIES:
                logger.error("Cannot connect to Redis after %d attempts: %s", _MAX_RETRIES, e)
                raise SystemExit(1) from e
            logger.warning(
                "Redis connection attempt %d/%d failed: %s - retrying in %ds",
                attempt,
                _MAX_RETRIES,
                e,
                backoff,
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
    raise SystemExit(1)  # unreachable, satisfies type checker


def main() -> None:
    settings = get_settings()
    setup_logging(level=settings.log_level, fmt=settings.log_format)
    setup_tracing(service_name="gitpulse-worker", otlp_endpoint=settings.otlp_endpoint)

    logger = logging.getLogger("rq.worker")
    logger.info(
        "Starting worker  redis=%s  queues=high,default,low",
        redact_url_credentials(settings.redis_url),
    )

    conn = _connect_redis(str(settings.redis_url), logger)

    from app.redis_pool import init_redis_pool

    init_redis_pool(str(settings.redis_url))

    queues = [
        Queue("high", connection=conn),
        Queue("default", connection=conn),
        Queue("low", connection=conn),
    ]

    # In development, flush stale jobs from all queues on startup so
    # that jobs referencing rows from a previous (wiped) database don't
    # linger.  Controlled by FLUSH_QUEUES_ON_START env-var or
    # automatically when APP_ENV == "development".
    flush_queues = os.environ.get(
        "FLUSH_QUEUES_ON_START",
        "1" if settings.is_development else "",
    )
    if flush_queues:
        from rq.job import Job
        from rq.registry import FailedJobRegistry, StartedJobRegistry

        for q in queues:
            stale = q.count
            q.empty()  # type: ignore[no-untyped-call]
            for reg_cls in (FailedJobRegistry, StartedJobRegistry):
                reg = reg_cls(queue=q)
                job_ids = reg.get_job_ids()
                if job_ids:
                    # Use direct ZREM - ExecutionBasedRegistry.remove()
                    # raises NotImplementedError in RQ ≥ 2.x.
                    conn.zrem(reg.key, *job_ids)  # type: ignore[attr-defined]
                    for jid in job_ids:
                        with contextlib.suppress(Exception):
                            Job.fetch(jid, connection=conn).delete()
            if stale:
                logger.info("Flushed %d stale job(s) from queue '%s'", stale, q.name)
        logger.info("Queue flush complete - starting with clean queues")

    worker_cls = SimpleWorker if os.name == "nt" else Worker
    logger.info("Using worker class: %s", worker_cls.__name__)
    worker = worker_cls(
        queues,
        connection=conn,
        exception_handlers=[record_job_failure],
        work_horse_killed_handler=record_job_failure,
    )
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
