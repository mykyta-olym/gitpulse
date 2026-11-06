"""A webhook event that fails processing is recorded as failed.

The failure path rolled the session back and then read ``event.retry_count``.
The rollback had expired the event, so that read was a lazy load - IO an async
session cannot do - and it raised MissingGreenlet inside the error handler. A
failing event therefore never got its retry count, its stored error or the
dead-letter queue: it stayed unprocessed with no trace of why, and was retried
for ever. Replayed on a database clone: six attempts at a broken payload left
retry_count=0 before the fix, and the event in the DLQ after it.
"""

from __future__ import annotations

import inspect

from app.workers import event_processor


def test_the_event_is_reread_after_the_rollback() -> None:
    src = inspect.getsource(event_processor._process_async)
    rollback = src.index("await session.rollback()")
    refresh = src.index("await session.refresh(event)", rollback)
    record = src.index("await _record_failure(", rollback)
    assert rollback < refresh < record, (
        "the failure is recorded on an expired event again - MissingGreenlet"
    )


def test_the_failure_is_counted_and_dead_lettered() -> None:
    src = inspect.getsource(event_processor._record_failure)
    assert "event.retry_count = (event.retry_count or 0) + 1" in src
    assert "event.processing_error = error_text" in src
    assert "event.dead_letter_at = datetime.now(UTC)" in src
