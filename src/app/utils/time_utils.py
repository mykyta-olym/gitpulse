"""Timezone-aware datetime helpers."""

from __future__ import annotations

from datetime import UTC, date, datetime


def now_utc() -> datetime:
    return datetime.now(UTC)


def parse_gitlab_datetime(dt_str: str | None) -> datetime | None:
    """Parse a GitLab datetime string to a timezone-aware datetime.

    GitLab is not consistent about this. The REST API returns ISO 8601
    ("2025-10-15T10:00:00.000Z", "2025-10-15T10:00:00+02:00"), but webhook
    payloads render ``object_attributes`` timestamps through Rails' default
    ``to_s``, which produces "2025-10-15 10:00:00 UTC" - a space separator and
    a named zone. ``fromisoformat`` rejects that, and returning None for it
    silently stored NULL created_at/updated_at/merged_at for every
    webhook-delivered merge request and issue. That in turn disabled the
    out-of-order guard, which needs the stored timestamp to recognise a stale
    replay, letting a late "open" delivery un-merge a merged MR.
    """
    if not dt_str:
        return None
    text = dt_str.strip()
    parsed: datetime | None
    try:
        parsed = datetime.fromisoformat(text)
    except (ValueError, TypeError):
        parsed = _parse_named_zone(text)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


# Webhook timestamps only ever carry UTC here: GitLab renders them from a
# UTC-normalised value, so the suffix is informational.
_NAMED_ZONE_FORMATS = (
    "%Y-%m-%d %H:%M:%S %Z",
    "%Y-%m-%d %H:%M:%S.%f %Z",
)


def _parse_named_zone(text: str) -> datetime | None:
    """Parse the Rails ``to_s`` shape GitLab uses in webhook payloads."""
    for fmt in _NAMED_ZONE_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def get_current_week(semester_start: date, now: date | None = None) -> int:
    """Compute current academic week number (1-indexed).

    Returns 0 if ``now`` is before ``semester_start``.
    """
    if now is None:
        now = datetime.now(UTC).date()
    delta = (now - semester_start).days
    if delta < 0:
        return 0
    return (delta // 7) + 1
