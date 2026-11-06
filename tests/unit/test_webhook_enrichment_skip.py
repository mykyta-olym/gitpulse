"""A re-delivered webhook must not pay for the GitLab fetch a second time.

GitLab re-delivers webhooks on failure, so duplicates are routine. The diff and
approvals of an MR whose ``updated_at`` has not moved are immutable - the bulk
sync already relies on that - so refetching them per duplicate delivery is two
wasted live API calls each time.

The skip must not become a trap: a delivery that follows a FAILED fetch has the
same timestamp as what we stored, so skipping on the timestamp alone would
starve that MR of enrichment permanently.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.merge_request import MergeRequest
from app.workers.processors.mr_processor import _enrichment_is_redundant

STORED = datetime(2026, 7, 20, 10, 0, 0, tzinfo=UTC)


def _mr(updated: datetime | None, changed_files: list[str] | None) -> MergeRequest:
    mr = MergeRequest(project_id=None, gitlab_id=1, gitlab_iid=1)
    mr.updated_at = updated
    mr.changed_files = changed_files
    return mr


def test_a_duplicate_delivery_of_an_enriched_mr_is_skipped() -> None:
    mr = _mr(STORED, ["src/a.py", "tests/test_a.py"])

    assert _enrichment_is_redundant(mr, STORED) is True


def test_a_real_update_still_enriches() -> None:
    mr = _mr(STORED, ["src/a.py"])

    assert _enrichment_is_redundant(mr, STORED + timedelta(hours=1)) is False


def test_an_mr_never_successfully_enriched_is_not_skipped() -> None:
    """The trap: same timestamp, but the previous fetch failed.

    changed_files is what enrichment populates, so an empty one means the last
    attempt did not succeed and this delivery must be allowed to retry.
    """
    assert _enrichment_is_redundant(_mr(STORED, []), STORED) is False
    assert _enrichment_is_redundant(_mr(STORED, None), STORED) is False


def test_a_brand_new_mr_is_always_enriched() -> None:
    assert _enrichment_is_redundant(None, STORED) is False


def test_a_payload_without_a_timestamp_is_never_skipped() -> None:
    """Without an incoming timestamp there is nothing to prove equality against."""
    assert _enrichment_is_redundant(_mr(STORED, ["src/a.py"]), None) is False


def test_a_stored_mr_with_no_timestamp_is_not_skipped() -> None:
    assert _enrichment_is_redundant(_mr(None, ["src/a.py"]), STORED) is False
