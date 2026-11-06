"""Tests for webhook secret rotation grace-window helpers."""

from datetime import UTC, datetime, timedelta

from app.api.webhooks import _previous_secret_is_active


def test_previous_secret_requires_future_expiry() -> None:
    now = datetime.now(UTC)

    assert _previous_secret_is_active(now + timedelta(seconds=1), now) is True
    assert _previous_secret_is_active(now, now) is True
    assert _previous_secret_is_active(now - timedelta(seconds=1), now) is False
    assert _previous_secret_is_active(None, now) is False
