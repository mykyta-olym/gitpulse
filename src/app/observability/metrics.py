"""Prometheus metrics definitions and collectors.

Metrics are scraped at ``GET /metrics`` (see health.py).
All metric names follow Prometheus naming conventions.

Two kinds live here. The API's own (requests, page cache, pool, queue gauges)
are prometheus_client metrics. Production runs the API as four uvicorn
processes, and Prometheus reaches one of them per scrape, so each process
keeps its values in ``PROMETHEUS_MULTIPROC_DIR`` and ``render_latest`` adds
them up - without it every scrape read a different process's counters and
Prometheus saw thousands of counter resets a day. The workers' metrics are
``Shared*`` ones kept in Redis (see shared_metrics.py).
"""

import logging
import os
from typing import Any, cast

# The directory has to exist before the first metric below opens its file.
# The API's /tmp is a tmpfs, so a container start empties it.
if _multiproc_dir := os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
    os.makedirs(_multiproc_dir, exist_ok=True)

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector

from app.observability.shared_metrics import (
    SharedCounter,
    SharedHistogram,
    SharedMetricsCollector,
)

logger = logging.getLogger(__name__)

# -- Application info --
# A gauge rather than an Info: Info does not work across processes.
APP_INFO = Gauge(
    "app_info",
    "Application build info",
    ["version", "service"],
    multiprocess_mode="mostrecent",
)

# -- Webhook metrics --
WEBHOOK_RECEIVED = Counter(
    "webhook_events_received_total",
    "Total webhook events received",
    ["event_type"],
)

WEBHOOK_PROCESSED = SharedCounter(
    "webhook_events_processed_total",
    "Total webhook events processed by worker",
    ["event_type", "status"],
)

WEBHOOK_PROCESSING_DURATION = SharedHistogram(
    "webhook_processing_duration_seconds",
    "Time to process webhook events in the worker",
    ["event_type"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0, 60.0],
)

# -- RQ queue metrics --
# Set from Redis by whichever process answers the scrape; the latest is the truth.
RQ_QUEUE_DEPTH = Gauge(
    "rq_queue_depth",
    "Current number of jobs in RQ queue",
    ["queue_name"],
    multiprocess_mode="mostrecent",
)

RQ_FAILED_JOBS = Gauge(
    "rq_failed_jobs",
    "Failed job records retained in RQ, not a count of recent failures",
    multiprocess_mode="mostrecent",
)

RQ_JOB_FAILURES = SharedCounter(
    "rq_job_failures_total", "RQ job execution errors, including retry attempts", ["queue_name"]
)

RQ_WORKERS_ACTIVE = Gauge(
    "rq_workers_active",
    "Number of active RQ workers",
    multiprocess_mode="mostrecent",
)

# -- GitLab API metrics --
GITLAB_API_REQUESTS = SharedCounter(
    "gitlab_api_requests_total",
    "GitLab API requests made",
    ["endpoint", "status"],
)

GITLAB_API_DURATION = SharedHistogram(
    "gitlab_api_duration_seconds",
    "GitLab API request duration",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0, 60.0],
)

# -- Metrics computation --
METRICS_COMPUTE_DURATION = SharedHistogram(
    "metrics_compute_duration_seconds",
    "Time to compute team metrics",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

METRICS_COMPUTE_TOTAL = SharedCounter(
    "metrics_compute_total",
    "Total number of metrics computations",
    ["status"],
)

# -- Enrichment metrics --
ENRICHMENT_TOTAL = SharedCounter(
    "enrichment_jobs_total",
    "Total enrichment jobs (issue/MR re-fetch from GitLab API)",
    ["entity_type", "status"],
)

ENRICHMENT_DURATION = SharedHistogram(
    "enrichment_duration_seconds",
    "Enrichment job duration (time spent calling GitLab API)",
    ["entity_type"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)
# -- Request metrics --
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 5.0, 10.0, 15.0, 30.0, 60.0],
)

# -- Database pool metrics --
# The pool of the process that answered the latest scrape.
DB_POOL_SIZE = Gauge("db_pool_size", "SQLAlchemy pool size", multiprocess_mode="mostrecent")
DB_POOL_CHECKED_IN = Gauge(
    "db_pool_checked_in",
    "SQLAlchemy connections checked in (idle)",
    multiprocess_mode="mostrecent",
)
DB_POOL_CHECKED_OUT = Gauge(
    "db_pool_checked_out",
    "SQLAlchemy connections checked out (active)",
    multiprocess_mode="mostrecent",
)
DB_POOL_OVERFLOW = Gauge(
    "db_pool_overflow", "SQLAlchemy pool overflow count", multiprocess_mode="mostrecent"
)

SESSION_STORE_FALLBACK_TOTAL = Counter(
    "session_store_fallback_total",
    "Total Redis session store fallbacks to stateless cookies",
    ["reason"],
)

# Page-fragment cache (HTMX lazy partials, see app.services.page_cache)
PAGE_CACHE_HITS = Counter(
    "page_cache_hits_total",
    "HTMX page-fragment cache hits",
    ["kind"],
)

PAGE_CACHE_MISSES = Counter(
    "page_cache_misses_total",
    "HTMX page-fragment cache misses",
    ["kind"],
)

PAGE_CACHE_INVALIDATIONS = Counter(
    "page_cache_invalidations_total",
    "HTMX page-fragment cache keys evicted by cascade or write-path",
    ["kind"],
)

_SHARED = SharedMetricsCollector()
if not _multiproc_dir:
    REGISTRY.register(_SHARED)


def render_latest() -> bytes:
    """The text a scrape of /metrics answers, from every process."""
    if not _multiproc_dir:
        return generate_latest(REGISTRY)
    registry = CollectorRegistry()
    MultiProcessCollector(registry)  # type: ignore[no-untyped-call]
    # The answering process's own CPU, memory and start time (API Uptime).
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)
    registry.register(_SHARED)
    return generate_latest(registry)


def collect_db_pool_metrics() -> None:
    """Update DB pool gauges from the current engine's pool status.

    Called periodically (e.g. from health check or a background task).
    """
    try:
        from app.db.session import get_engine

        engine = get_engine()
        pool = cast(Any, engine.pool)
        DB_POOL_SIZE.set(pool.size())
        DB_POOL_CHECKED_IN.set(pool.checkedin())
        DB_POOL_CHECKED_OUT.set(pool.checkedout())
        DB_POOL_OVERFLOW.set(max(0, pool.overflow()))
    except Exception:
        logger.debug("Could not collect DB pool metrics", exc_info=True)


def collect_rq_queue_metrics() -> None:
    """Update RQ queue depth gauges from Redis.

    Called from the health check or a scheduled job.
    """
    try:
        from rq import Queue
        from rq.worker import Worker

        from app.redis_pool import get_redis as _pool_get_redis

        conn = _pool_get_redis()
        for name in ("high", "default", "low"):
            q = Queue(name, connection=conn)
            RQ_QUEUE_DEPTH.labels(queue_name=name).set(len(q))
            RQ_JOB_FAILURES.labels(queue_name=name).inc(0)

        # Failed jobs across all queues
        from rq.registry import FailedJobRegistry

        total_failed = 0
        for name in ("high", "default", "low"):
            q = Queue(name, connection=conn)
            registry = FailedJobRegistry(queue=q)
            total_failed += len(registry)
        RQ_FAILED_JOBS.set(total_failed)

        # Active workers
        workers = Worker.all(connection=conn)
        RQ_WORKERS_ACTIVE.set(len(workers))
    except Exception:
        logger.debug("Could not collect RQ metrics", exc_info=True)
