"""Unit tests for the webhook out-of-order guard (is_stale_update).

GitLab does not guarantee webhook ordering and re-delivers on failure, so a
stale ``update`` event can arrive after a terminal one (an MR ``merge`` or an
issue ``close``). The guard must drop the stale payload so ``state`` is not
regressed. Shared by the MR and issue processors.
"""

from datetime import UTC, datetime, timedelta

from app.workers.processors._common import is_stale_update

_T2 = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
_T1 = _T2 - timedelta(minutes=5)


class TestIsStaleUpdate:
    def test_older_incoming_is_stale(self) -> None:
        # Stored a newer (merge/close) event at T2; an update from T1 arrives late.
        assert is_stale_update(_T2, _T1) is True

    def test_newer_incoming_is_not_stale(self) -> None:
        assert is_stale_update(_T1, _T2) is False

    def test_equal_timestamps_not_stale(self) -> None:
        # Idempotent re-apply (e.g. full sync of an unchanged entity) must proceed.
        assert is_stale_update(_T2, _T2) is False

    def test_missing_stored_never_blocks(self) -> None:
        # New entity / legacy row with no stored updated_at -> always apply.
        assert is_stale_update(None, _T1) is False

    def test_missing_incoming_never_blocks(self) -> None:
        # Payload without updated_at -> never block on a comparison we cannot make.
        assert is_stale_update(_T2, None) is False
