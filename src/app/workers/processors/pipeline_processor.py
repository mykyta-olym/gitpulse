"""Process GitLab pipeline webhook events."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merge_request import MergeRequest
from app.models.pipeline import Pipeline
from app.models.project import GitLabProject
from app.utils.time_utils import parse_gitlab_datetime

logger = logging.getLogger(__name__)


_TERMINAL_STATUSES = frozenset({"success", "failed", "canceled", "skipped"})


def _parse_coverage(val: Any) -> float | None:
    """Parse GitLab's pipeline ``coverage`` (str/float/None) into a percentage."""
    if val is None or val == "":
        return None
    try:
        return round(float(val), 2)
    except (TypeError, ValueError):
        return None


_TEST_JOB_TOKENS = (
    "test",
    "spec",
    "pytest",
    "junit",
    "jest",
    "mocha",
    "rspec",
    "phpunit",
    "verify",
    "coverage",
)


def _is_test_build(build: dict[str, Any]) -> bool:
    name = (build.get("name", "") or "").lower()
    stage = (build.get("stage", "") or "").lower()
    return any(tok in name or tok in stage for tok in _TEST_JOB_TOKENS)


def _extract_coverage(obj: dict[str, Any], builds: list[dict[str, Any]]) -> float | None:
    """Return GitLab coverage from the pipeline object or coverage-reporting job.

    GitLab's MR widget can show "Test coverage 91.00% from 1 job" even when the
    pipeline webhook's ``object_attributes.coverage`` is blank. In that case the
    numeric value lives on one of the webhook ``builds`` entries. Prefer a
    successful test/coverage job, then any test job, then any successful job that
    reported coverage.
    """
    object_coverage = _parse_coverage(obj.get("coverage"))
    if object_coverage is not None:
        return object_coverage

    successful_test: list[float] = []
    any_test: list[float] = []
    successful_any: list[float] = []
    any_coverage: list[float] = []

    for build in builds:
        coverage = _parse_coverage(build.get("coverage"))
        if coverage is None:
            continue
        status = (build.get("status") or "").lower()
        is_test = _is_test_build(build)
        any_coverage.append(coverage)
        if status == "success":
            successful_any.append(coverage)
        if is_test:
            any_test.append(coverage)
            if status == "success":
                successful_test.append(coverage)

    for bucket in (successful_test, any_test, successful_any, any_coverage):
        if bucket:
            return bucket[0]
    return None


def _is_status_regression(prev_status: str | None, new_status: str) -> bool:
    """True when an incoming event would regress a finished pipeline.

    GitLab does not guarantee webhook ordering; a stale ``running`` event can
    arrive after ``success``. Block terminal -> non-terminal transitions so the
    per-commit CI icon / R12 health don't flap. Terminal -> terminal is allowed
    so genuine retries (``failed`` -> ``success``) still land.
    """
    return prev_status in _TERMINAL_STATUSES and new_status not in _TERMINAL_STATUSES


async def process_pipeline_event(
    session: AsyncSession,
    payload: dict[str, Any],
    gitlab_project_id: int,
) -> None:
    """Upsert pipeline and link to MR if applicable."""
    obj = payload.get("object_attributes", {})
    if not obj:
        return

    # Find project
    stmt = select(GitLabProject).where(GitLabProject.gitlab_project_id == gitlab_project_id)
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        return

    pipeline_id = obj.get("id")
    if not pipeline_id:
        return

    ref = obj.get("ref", "")
    status = obj.get("status", "created")
    sha = obj.get("sha")
    source = obj.get("source", "")
    duration = obj.get("duration")
    queued_duration = obj.get("queued_duration")

    # Detect test jobs from the builds array. We match common test-job
    # naming conventions across ecosystems so a green pipeline that runs
    # tests under any of these labels still satisfies R12.
    builds = payload.get("builds", [])
    has_test_job = False
    test_job_status = None
    for build in builds:
        if _is_test_build(build):
            has_test_job = True
            build_status = build.get("status")
            # Prefer a successful test job over a failed one
            if build_status == "success" or test_job_status is None:
                test_job_status = build_status

    # Try to link to MR via merge_request_iid, ref (branch name), or target_branch
    mr_id = None
    # A branch pipeline carries `"merge_request": null`, not no key at all.
    mr_iid = obj.get("merge_request_iid") or (payload.get("merge_request") or {}).get("iid")
    if mr_iid:
        # Best match: pipeline explicitly linked to MR by GitLab
        mr_iid_stmt = (
            select(MergeRequest.id)
            .where(
                MergeRequest.project_id == project.id,
                MergeRequest.gitlab_iid == mr_iid,
            )
            .limit(1)
        )
        mr_iid_result = await session.execute(mr_iid_stmt)
        mr_id = mr_iid_result.scalar_one_or_none()

    if mr_id is None and ref:
        # First try: pipeline ref matches MR source_branch (pre-merge CI)
        mr_stmt = (
            select(MergeRequest.id)
            .where(
                MergeRequest.project_id == project.id,
                MergeRequest.source_branch == ref,
            )
            .order_by(
                MergeRequest.updated_at.desc().nulls_last(),
                MergeRequest.created_at.desc().nulls_last(),
                MergeRequest.gitlab_iid.desc(),
            )
            .limit(1)
        )
        mr_result = await session.execute(mr_stmt)
        mr_id = mr_result.scalar_one_or_none()

        # Second try: pipeline ref matches MR target_branch for merged MRs
        # (post-merge pipeline on default branch triggered by the merge)
        # Constrain to MRs merged within the last hour to avoid false matches
        if mr_id is None and sha:
            pipeline_time = parse_gitlab_datetime(obj.get("created_at")) or datetime.now(UTC)
            time_window = pipeline_time - timedelta(hours=1)
            mr_target_stmt = (
                select(MergeRequest.id)
                .where(
                    MergeRequest.project_id == project.id,
                    MergeRequest.target_branch == ref,
                    MergeRequest.state == "merged",
                    MergeRequest.merged_at >= time_window,
                )
                .order_by(
                    MergeRequest.merged_at.desc().nulls_last(),
                    MergeRequest.gitlab_iid.desc(),
                )
                .limit(1)
            )
            mr_target_result = await session.execute(mr_target_stmt)
            mr_id = mr_target_result.scalar_one_or_none()

    # Upsert pipeline
    p_stmt = select(Pipeline).where(
        Pipeline.project_id == project.id,
        Pipeline.gitlab_pipeline_id == pipeline_id,
    )
    p_result = await session.execute(p_stmt)
    pipeline = p_result.scalar_one_or_none()

    _prev_status = pipeline.status if pipeline is not None else None
    if pipeline is None:
        pipeline = Pipeline(
            project_id=project.id,
            gitlab_pipeline_id=pipeline_id,
        )
        session.add(pipeline)

    # Identity fields are immutable for a given pipeline id - always safe to set.
    pipeline.merge_request_id = mr_id
    pipeline.ref = ref
    pipeline.sha = sha
    pipeline.source = source
    pipeline.created_at = parse_gitlab_datetime(obj.get("created_at")) or pipeline.created_at

    # -- Guard against out-of-order / re-delivered pipeline events --
    # GitLab does NOT guarantee webhook ordering, and a pipeline emits several
    # events (created -> running -> success). A stale in-progress event arriving
    # after a terminal one must not regress the status (which powers the
    # per-commit CI icon) nor blank the job/finish data we already captured.
    # Terminal -> terminal always applies, so genuine retries still land.
    if not _is_status_regression(_prev_status, status):
        pipeline.status = status
        pipeline.has_test_job = has_test_job
        pipeline.test_job_status = test_job_status
        pipeline.total_jobs = len(builds)
        if duration is not None:
            pipeline.duration_seconds = duration
        if queued_duration is not None:
            pipeline.queued_duration_seconds = queued_duration
        _finished = parse_gitlab_datetime(obj.get("finished_at"))
        if _finished is not None:
            pipeline.finished_at = _finished

    # Coverage is sticky: an in-progress (or coverage-less) event must never
    # erase a value we already measured. Only a real number overwrites it.
    _cov = _extract_coverage(obj, builds)
    if _cov is not None:
        pipeline.coverage = _cov

    await session.flush()

    logger.debug(
        "Pipeline upserted: project=%d pipeline=%d status=%s ref=%s test_job=%s",
        gitlab_project_id,
        pipeline_id,
        status,
        ref,
        has_test_job,
    )
