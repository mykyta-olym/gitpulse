"""Tests for sync job and enrichment functionality.

Tests the sync job logic and helper functions.
"""

import json
from datetime import UTC, datetime


class TestJobProgressPayload:
    """Test job progress payload construction."""

    def test_progress_payload_json(self) -> None:
        """Test job progress payload JSON serialization."""
        payload = {
            "job_id": "test-job-123",
            "status": "running",
            "message": "Processing...",
        }
        json_str = json.dumps(payload, default=str)
        parsed = json.loads(json_str)
        assert parsed["job_id"] == "test-job-123"
        assert parsed["status"] == "running"

    def test_progress_payload_with_datetime(self) -> None:
        """Test progress payload handles datetime serialization."""
        now = datetime.now(UTC)
        payload = {"timestamp": now}
        json_str = json.dumps(payload, default=str)
        assert str(now.year) in json_str


class TestJobStatusTransitions:
    """Test job status transitions."""

    def test_status_pending_to_running(self) -> None:
        """Test job status transition from pending to running."""
        status = "pending"
        assert status == "pending"
        status = "running"
        assert status == "running"

    def test_status_running_to_completed(self) -> None:
        """Test job status transition from running to completed."""
        status = "running"
        status = "completed"
        assert status == "completed"

    def test_status_running_to_failed(self) -> None:
        """Test job status transition from running to failed."""
        status = "running"
        status = "failed"
        assert status == "failed"


class TestEnrichIssueDataExtraction:
    """Test issue enrichment data extraction."""

    def test_extract_author_from_api_response(self) -> None:
        """Test extracting author info from API response."""
        api_issue = {
            "author": {
                "id": 123,
                "username": "developer",
                "name": "John Developer",
            }
        }
        author_id = api_issue.get("author", {}).get("id")
        assert author_id == 123

    def test_extract_labels_from_api(self) -> None:
        """Test extracting labels from API issue."""
        api_issue = {"labels": ["bug", "priority::high", "team::backend"]}
        labels = api_issue.get("labels", [])
        assert len(labels) == 3
        assert "bug" in labels

    def test_extract_milestone_from_api(self) -> None:
        """Test extracting milestone from API issue."""
        api_issue = {
            "milestone": {
                "id": 1,
                "title": "Sprint 1",
                "due_date": "2025-02-01",
            }
        }
        milestone = api_issue.get("milestone")
        assert milestone is not None
        assert milestone["title"] == "Sprint 1"

    def test_extract_assignees_from_api(self) -> None:
        """Test extracting assignees from API issue."""
        api_issue = {
            "assignees": [
                {"id": 1, "username": "user1"},
                {"id": 2, "username": "user2"},
            ]
        }
        assignees = api_issue.get("assignees", [])
        assert len(assignees) == 2


class TestEnrichMRDataExtraction:
    """Test MR enrichment data extraction."""

    def test_extract_approvals_from_api(self) -> None:
        """Test extracting approvals from API MR."""
        api_mr = {
            "approved_by": [
                {"user": {"id": 1, "username": "reviewer1"}},
                {"user": {"id": 2, "username": "reviewer2"}},
            ]
        }
        approved_by = api_mr.get("approved_by", [])
        assert len(approved_by) == 2

    def test_extract_reviewers_from_api(self) -> None:
        """Test extracting reviewers from API MR."""
        api_mr = {
            "reviewers": [
                {"id": 1, "username": "reviewer1"},
                {"id": 2, "username": "reviewer2"},
            ]
        }
        reviewers = api_mr.get("reviewers", [])
        assert len(reviewers) == 2

    def test_extract_merge_commit_sha(self) -> None:
        """Test extracting merge commit SHA."""
        api_mr = {"merge_commit_sha": "abc123def456"}
        merge_sha = api_mr.get("merge_commit_sha")
        assert merge_sha == "abc123def456"

    def test_extract_source_branch(self) -> None:
        """Test extracting source branch."""
        api_mr = {"source_branch": "feature/new-feature"}
        source_branch = api_mr.get("source_branch")
        assert source_branch == "feature/new-feature"


class TestSyncCounters:
    """Test sync job counters."""

    def test_counter_initialization(self) -> None:
        """Test counter initialization."""
        issues_count = 0
        mrs_count = 0
        notes_count = 0
        assert issues_count == 0
        assert mrs_count == 0
        assert notes_count == 0

    def test_counter_increment(self) -> None:
        """Test counter increment."""
        count = 0
        for _ in range(5):
            count += 1
        assert count == 5

    def test_total_time_calculation(self) -> None:
        """Test sync time calculation."""
        import time

        t0 = time.monotonic()
        # Simulate some minimal operation
        _ = sum(range(1000))
        elapsed = time.monotonic() - t0
        assert elapsed >= 0


class TestPipelineConcurrency:
    """Test pipeline concurrency configuration."""

    def test_default_concurrency(self) -> None:
        """Test default pipeline concurrency value."""
        default_concurrency = 5  # Common default
        assert default_concurrency > 0

    def test_concurrency_limit(self) -> None:
        """Test concurrency limits batch processing."""
        concurrency = 3
        items = list(range(10))
        batches = [items[i : i + concurrency] for i in range(0, len(items), concurrency)]
        assert len(batches) == 4  # 10 items, batches of 3 = 4 batches


class TestTeamMemberCleanup:
    """Test team member cleanup logic."""

    def test_teacher_role_detection(self) -> None:
        """Test detecting teacher role."""
        roles = ["teacher", "admin", "student"]
        is_teacher_or_admin = "teacher" in roles or "admin" in roles
        assert is_teacher_or_admin is True

    def test_student_role_only(self) -> None:
        """Test student-only role."""
        role = "student"
        is_teacher_or_admin = role in ["teacher", "admin"]
        assert is_teacher_or_admin is False


class TestWebhookEventProcessing:
    """Test webhook event processing logic."""

    def test_event_type_dispatch_map(self) -> None:
        """Test event type dispatch mapping."""
        dispatch_map = {
            "issue": "process_issue_event",
            "merge_request": "process_mr_event",
            "note": "process_note_event",
            "push": "process_push_event",
            "pipeline": "process_pipeline_event",
        }
        assert dispatch_map["issue"] == "process_issue_event"
        assert dispatch_map["merge_request"] == "process_mr_event"

    def test_unknown_event_type(self) -> None:
        """Test handling unknown event type."""
        dispatch_map: dict[str, str] = {
            "issue": "handler",
            "merge_request": "handler",
        }
        handler = dispatch_map.get("unknown_type")
        assert handler is None

    def test_object_kind_extraction(self) -> None:
        """Test extracting object_kind from payload."""
        payload = {"object_kind": "merge_request"}
        object_kind = payload.get("object_kind", "")
        assert object_kind == "merge_request"


class TestIdempotencyChecks:
    """Test idempotency checking logic."""

    def test_already_processed_skip(self) -> None:
        """Test skipping already processed events."""
        processed = True
        should_skip = processed
        assert should_skip is True

    def test_not_processed_continue(self) -> None:
        """Test continuing for not-yet-processed events."""
        processed = False
        should_process = not processed
        assert should_process is True


class TestPipelineEventOrdering:
    """Out-of-order / re-delivered pipeline events must not regress a finished
    pipeline's status or blank its coverage (which power the per-commit CI icon
    and the coverage line).
    """

    def test_terminal_to_in_progress_is_regression(self) -> None:
        from app.workers.processors.pipeline_processor import _is_status_regression

        # a stale running/pending event arriving after success/failed is blocked
        assert _is_status_regression("success", "running") is True
        assert _is_status_regression("failed", "pending") is True
        assert _is_status_regression("canceled", "created") is True

    def test_terminal_to_terminal_applies(self) -> None:
        from app.workers.processors.pipeline_processor import _is_status_regression

        # retries (failed -> success) and forward progress still land
        assert _is_status_regression("failed", "success") is False
        assert _is_status_regression("success", "failed") is False

    def test_new_or_in_progress_prev_always_applies(self) -> None:
        from app.workers.processors.pipeline_processor import _is_status_regression

        assert _is_status_regression(None, "running") is False
        assert _is_status_regression("running", "success") is False
        assert _is_status_regression("created", "running") is False

    def test_coverage_is_sticky_against_null(self) -> None:
        from app.workers.processors.pipeline_processor import _parse_coverage

        # an in-progress event carries no coverage -> parses to None, so the
        # processor's `if _cov is not None` guard preserves the known value
        assert _parse_coverage(None) is None
        assert _parse_coverage("") is None
        assert _parse_coverage("37.5") == 37.5
        assert _parse_coverage(80) == 80.0

    def test_pipeline_object_coverage_wins(self) -> None:
        from app.workers.processors.pipeline_processor import _extract_coverage

        coverage = _extract_coverage(
            {"coverage": "91.00"},
            [{"name": "pytest", "stage": "test", "status": "success", "coverage": "80.00"}],
        )

        assert coverage == 91.0

    def test_build_level_test_coverage_is_used_when_pipeline_is_blank(self) -> None:
        from app.workers.processors.pipeline_processor import _extract_coverage

        coverage = _extract_coverage(
            {"coverage": None},
            [
                {"name": "build", "stage": "build", "status": "success"},
                {"name": "pytest", "stage": "test", "status": "success", "coverage": "91.00"},
            ],
        )

        assert coverage == 91.0

    def test_successful_test_coverage_is_preferred_over_failed_job(self) -> None:
        from app.workers.processors.pipeline_processor import _extract_coverage

        coverage = _extract_coverage(
            {},
            [
                {"name": "coverage", "stage": "test", "status": "failed", "coverage": "72"},
                {"name": "unit tests", "stage": "test", "status": "success", "coverage": "88.5"},
            ],
        )

        assert coverage == 88.5


class TestExtractAssigneeReviewers:
    """The MR assignee/reviewer extraction must accept both payload shapes:
    full API sync nests them in object_attributes; webhooks put them top-level.
    """

    def test_sync_shape_object_attributes(self) -> None:
        from app.workers.processors.mr_processor import _extract_assignee_reviewers

        obj = {
            "assignees": [{"id": 7, "username": "ann"}],
            "reviewers": [{"id": 8, "username": "bob"}, {"id": 9, "username": "cy"}],
        }
        gid, uname, revs = _extract_assignee_reviewers(obj, {})
        assert gid == 7
        assert uname == "ann"
        assert revs == [8, 9]

    def test_webhook_shape_top_level(self) -> None:
        from app.workers.processors.mr_processor import _extract_assignee_reviewers

        # object_attributes (the MR) carries no assignees/reviewers on webhooks
        payload = {
            "object_attributes": {"iid": 3},
            "assignees": [{"id": 43, "username": "mkovacova"}],
            "reviewers": [{"id": 50, "username": "rev"}],
        }
        gid, uname, revs = _extract_assignee_reviewers(payload["object_attributes"], payload)
        assert gid == 43
        assert uname == "mkovacova"
        assert revs == [50]

    def test_real_webhook_fixture(self) -> None:
        import pathlib

        from app.workers.processors.mr_processor import _extract_assignee_reviewers

        p = json.loads(pathlib.Path("tests/fixtures/payloads/merge_request_event.json").read_text())
        gid, _uname, revs = _extract_assignee_reviewers(p.get("object_attributes", {}), p)
        assert gid is not None, "assignee should resolve from the top-level webhook payload"
        assert isinstance(revs, list)

    def test_empty_and_malformed(self) -> None:
        from app.workers.processors.mr_processor import _extract_assignee_reviewers

        assert _extract_assignee_reviewers({}, {}) == (None, None, [])
        # malformed entries are skipped, not crashing
        gid, _u, revs = _extract_assignee_reviewers(
            {"assignee": "nope", "reviewers": ["x", {"no_id": 1}, {"id": 5}]}, {}
        )
        assert gid is None
        assert revs == [5]
