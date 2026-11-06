"""Tests for app.utils.time_utils module."""

from datetime import UTC, date, datetime


class TestNowUtc:
    """Tests for now_utc function."""

    def test_returns_datetime(self) -> None:
        from app.utils.time_utils import now_utc

        result = now_utc()
        assert isinstance(result, datetime)

    def test_has_utc_timezone(self) -> None:
        from app.utils.time_utils import now_utc

        result = now_utc()
        assert result.tzinfo is not None
        assert result.tzinfo == UTC


class TestParseGitlabDatetime:
    """Tests for parse_gitlab_datetime function."""

    def test_none_input(self) -> None:
        from app.utils.time_utils import parse_gitlab_datetime

        result = parse_gitlab_datetime(None)
        assert result is None

    def test_empty_string(self) -> None:
        from app.utils.time_utils import parse_gitlab_datetime

        result = parse_gitlab_datetime("")
        assert result is None

    def test_iso_with_z_suffix(self) -> None:
        from app.utils.time_utils import parse_gitlab_datetime

        result = parse_gitlab_datetime("2025-10-15T10:00:00.000Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 15
        assert result.hour == 10
        assert result.tzinfo is not None

    def test_iso_with_plus_offset(self) -> None:
        from app.utils.time_utils import parse_gitlab_datetime

        result = parse_gitlab_datetime("2025-10-15T10:00:00+02:00")
        assert result is not None
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 15
        assert result.tzinfo is not None

    def test_invalid_format(self) -> None:
        from app.utils.time_utils import parse_gitlab_datetime

        result = parse_gitlab_datetime("not-a-date")
        assert result is None

    def test_malformed_iso(self) -> None:
        from app.utils.time_utils import parse_gitlab_datetime

        result = parse_gitlab_datetime("2025-13-45T99:99:99")
        assert result is None


class TestGetCurrentWeek:
    """Tests for get_current_week function."""

    def test_first_day_is_week_one(self) -> None:
        from app.utils.time_utils import get_current_week

        start = date(2026, 2, 16)
        assert get_current_week(start, now=date(2026, 2, 16)) == 1

    def test_day_before_start_is_zero(self) -> None:
        from app.utils.time_utils import get_current_week

        start = date(2026, 2, 16)
        assert get_current_week(start, now=date(2026, 2, 15)) == 0

    def test_second_week(self) -> None:
        from app.utils.time_utils import get_current_week

        start = date(2026, 2, 16)
        assert get_current_week(start, now=date(2026, 2, 23)) == 2

    def test_end_of_first_week(self) -> None:
        from app.utils.time_utils import get_current_week

        start = date(2026, 2, 16)
        assert get_current_week(start, now=date(2026, 2, 22)) == 1

    def test_week_twelve(self) -> None:
        from app.utils.time_utils import get_current_week

        start = date(2026, 2, 16)
        assert get_current_week(start, now=date(2026, 5, 4)) == 12

    def test_defaults_to_today(self) -> None:
        from app.utils.time_utils import get_current_week

        start = date(2020, 1, 1)
        result = get_current_week(start)
        assert result > 0
