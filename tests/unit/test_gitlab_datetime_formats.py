"""GitLab sends two different datetime shapes and both must parse.

The REST API returns ISO 8601, but webhook payloads render
``object_attributes`` timestamps through Rails' default ``to_s``:
"2025-10-15 10:00:00 UTC", with a space separator and a named zone.
``datetime.fromisoformat`` rejects that shape, so it used to parse as None and
every webhook-delivered merge request and issue stored NULL
created_at/updated_at/merged_at.

The knock-on effect was worse than the missing timestamps: the out-of-order
guard compares the stored timestamp against the incoming one, and a stored
None makes it conclude "not stale". A late "open" redelivery could then
un-merge a merged MR, which flips the author's R10/R11 scoring.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.utils.time_utils import parse_gitlab_datetime
from app.workers.processors._common import is_stale_update


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # The webhook shape that used to return None.
        ("2025-10-15 10:00:00 UTC", datetime(2025, 10, 15, 10, 0, 0, tzinfo=UTC)),
        (
            "2025-10-15 10:00:00.123 UTC",
            datetime(2025, 10, 15, 10, 0, 0, 123000, tzinfo=UTC),
        ),
        # REST API shapes, which must keep working.
        ("2025-10-15T10:00:00.000Z", datetime(2025, 10, 15, 10, 0, 0, tzinfo=UTC)),
        ("2025-10-15T10:00:00Z", datetime(2025, 10, 15, 10, 0, 0, tzinfo=UTC)),
        ("2025-10-15 10:00:00 +0000", datetime(2025, 10, 15, 10, 0, 0, tzinfo=UTC)),
        # A naive value is assumed UTC rather than rejected.
        ("2025-10-15 10:00:00", datetime(2025, 10, 15, 10, 0, 0, tzinfo=UTC)),
    ],
)
def test_every_shape_gitlab_sends_parses(raw: str, expected: datetime) -> None:
    assert parse_gitlab_datetime(raw) == expected


def test_a_non_utc_offset_is_preserved_not_flattened() -> None:
    parsed = parse_gitlab_datetime("2025-10-15T10:00:00+02:00")
    assert parsed is not None
    assert parsed.utcoffset() is not None
    assert parsed.utcoffset().total_seconds() == 7200  # type: ignore[union-attr]


@pytest.mark.parametrize("raw", ["", None, "garbage", "not a date UTC", "2025-13-45 99:00:00 UTC"])
def test_unparseable_input_still_yields_none(raw: str | None) -> None:
    assert parse_gitlab_datetime(raw) is None


def test_parsed_webhook_timestamp_makes_the_stale_guard_work() -> None:
    """The regression this bug actually caused, end to end in miniature.

    A merge is stored, then an older "open" redelivery arrives. With the
    webhook shape parsing to None, `stored` was None and the guard reported
    "not stale", so the stale payload applied and un-merged the MR.
    """
    stored = parse_gitlab_datetime("2025-10-15 11:00:00 UTC")
    stale_incoming = parse_gitlab_datetime("2025-10-15 10:30:00 UTC")

    assert stored is not None, "a stored webhook timestamp must not be None"
    assert stale_incoming is not None

    assert is_stale_update(stored, stale_incoming) is True

    # A genuinely newer delivery must still be applied.
    newer = parse_gitlab_datetime("2025-10-15 12:00:00 UTC")
    assert is_stale_update(stored, newer) is False
