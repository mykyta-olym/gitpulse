"""Bounded, read-only RQ failure history for administrators.

Only identifiers, exception types and source locations leave Redis. Job arguments,
exception messages, source lines and locals can contain credentials or student data.
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog
from rq.job import Job
from rq.registry import FailedJobRegistry

from app.redis_pool import get_redis

logger = structlog.get_logger(__name__)
LIMIT = 100
QUEUES = ("high", "default", "low")


@dataclass
class FailureLog:
    available: bool = True
    total: int = 0
    rows: list[dict[str, Any]] = field(default_factory=list)


def _cause(trace: str, function: str) -> tuple[str, str]:
    if (
        function == "app.workers.sweep.run_tracked_scheduled"
        and "app.workers.sweep' has no attribute" in trace
    ):
        return (
            "Retired scheduled job",
            "This job used a removed scheduler. "
            "Use webhooks or an explicit sync instead of retrying it.",
        )
    if "AbandonedJobError" in trace:
        return (
            "Worker interrupted",
            "Check worker restarts and memory limits, then sync the affected scope if needed.",
        )
    if "JobTimeoutException" in trace or "TimeoutError" in trace:
        return "Job timed out", "Check the task duration and GitLab availability before retrying."
    status = re.search(r"HTTPStatusError:.*?\b(\d{3})\b", trace)
    if status:
        if status[1] in {"401", "403"}:
            return "GitLab access denied", "Check the course GitLab token and its permissions."
        if status[1] == "404":
            return "GitLab resource unavailable", "Check that the project exists and is accessible."
        return "GitLab request failed", "Check GitLab availability and rate limits before retrying."
    if "UndefinedColumnError" in trace or "UndefinedTableError" in trace:
        return (
            "Database schema mismatch",
            "Check database migrations and the deployed worker version.",
        )
    return (
        "Job execution failed",
        "Use the job reference and source location to find the worker log.",
    )


def _row(job: Job) -> dict[str, Any]:
    result = job.latest_result()
    # Retained records can predate RQ Results. Their loaded exception field
    # keeps the history readable without calling the deprecated exc_info property.
    trace = (result.exc_string if result else job._exc_info) or ""
    # Accept metadata as identifiers, never render arbitrary strings stored in a job.
    function = str(job.func_name or "")
    function = function if re.fullmatch(r"app\.[\w.]{1,160}", function) else "Unknown task"
    cause, hint = _cause(trace, function)
    job_id = str(job.id)
    job_id = job_id if re.fullmatch(r"[\w-]{1,100}", job_id) else "-"
    exceptions = re.findall(r"^([\w.]+(?:Error|Exception|Failure|Timeout))(?::|$)", trace, re.M)
    locations = re.findall(r'File "[^"\n]*?(src/app/[\w/]+\.py)", line (\d+), in ([\w<>]+)', trace)
    reference = "\n".join(
        [job_id, function, exceptions[-1] if exceptions else cause]
        + [f"{path}:{line} ({name})" for path, line, name in locations[-5:]]
    )
    return {
        "id": job_id,
        "function": function,
        "queue": job.origin if job.origin in QUEUES else "-",
        "observed_at": job.ended_at or job.last_heartbeat or job.created_at,
        "cause": cause,
        "hint": hint,
        "reference": reference,
    }


def _read() -> FailureLog:
    connection = get_redis()
    result = FailureLog()
    for name in QUEUES:
        registry = FailedJobRegistry(name, connection=connection)
        result.total += registry.count
        # RQ orders by retention expiry. Read a bounded tail from each queue,
        # then order the displayed records by their actual last activity.
        ids = registry.get_job_ids(start=-LIMIT, cleanup=False)
        for job in Job.fetch_many(ids, connection=connection):
            if job is not None and job.get_status(refresh=False) == "failed":
                result.rows.append(_row(job))
    result.rows.sort(
        key=lambda row: row["observed_at"] or datetime.min.replace(tzinfo=UTC), reverse=True
    )
    result.rows = result.rows[:LIMIT]
    return result


async def snapshot() -> FailureLog:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_read), timeout=2)
    except Exception:
        logger.warning("queue_failure_history_unavailable", exc_info=True)
        return FailureLog(available=False)
