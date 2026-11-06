"""Preserved compliance history and the shared support form anonymisation."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.compliance_history import (
    ComplianceHistoryService,
    ComplianceSnapshot,
    WeeklyComplianceTrend,
)
from app.services.support_forms import _anonymize_text


def _settings():
    from app.config import Settings

    return Settings(
        database_url="postgresql+asyncpg://test:test@localhost/test",
        secret_key="test-secret-key-minimum-16-chars",
        teacher_api_token="test-token",
        app_env="test",
        _env_file=None,
        _env_prefix="__TEST__",
    )


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock()
    return db


# -- compliance history ------------------------------------------------------------


class TestComplianceSnapshot:
    def test_improvement_against_the_previous_week(self) -> None:
        snapshot = ComplianceSnapshot(
            course_id=1,
            team_id=1,
            student_id=1,
            week_number=5,
            snapshot_date=datetime.now(UTC).date(),
            overall_score=0.85,
            prev_week_score=0.70,
        )
        assert snapshot.improvement_delta == pytest.approx(0.15)
        assert snapshot.improvement_pct == pytest.approx(21.43, rel=0.01)

    def test_no_previous_week_means_no_improvement(self) -> None:
        snapshot = ComplianceSnapshot(
            course_id=1,
            team_id=1,
            student_id=1,
            week_number=1,
            snapshot_date=datetime.now(UTC).date(),
            overall_score=0.75,
            prev_week_score=None,
        )
        assert snapshot.improvement_delta is None
        assert snapshot.improvement_pct is None

    def test_weekly_trend(self) -> None:
        trend = WeeklyComplianceTrend(
            week_number=5,
            week_start=date(2026, 2, 10),
            avg_score=0.78,
            median_score=0.80,
            min_score=0.55,
            max_score=0.95,
            std_dev=0.12,
            students_count=25,
            improved_count=15,
            declined_count=5,
            unchanged_count=5,
        )
        assert trend.week_number == 5
        assert trend.improved_count == 15


@pytest.mark.asyncio
async def test_the_current_week_is_a_teaching_week(mock_db) -> None:
    week = await ComplianceHistoryService(mock_db).current_week(1)
    assert 1 <= week <= 16


# -- support feedback ----------------------------------------------------------------


class TestSupportAnonymisation:
    @pytest.mark.parametrize(
        ("text", "gone", "marker"),
        [
            ("Contact john.doe@university.edu for help", "john.doe@university.edu", "[EMAIL]"),
            ("Thanks @johndoe for the help", "@johndoe", "[MENTION]"),
            (
                "See https://gitlab.com/myproject for details",
                "https://gitlab.com/myproject",
                "[URL]",
            ),
            ("Student AB12345678 submitted late", "AB12345678", "[ID]"),
        ],
    )
    def test_free_text_is_anonymised(self, text, gone, marker) -> None:
        result = _anonymize_text(text)
        assert gone not in result
        assert marker in result

    def test_every_identifier_in_one_text_is_anonymised(self) -> None:
        result = _anonymize_text("Student AB12345 (@jsmith, jsmith@uni.edu) see https://docs.com")
        for marker in ("[ID]", "[MENTION]", "[EMAIL]", "[URL]"):
            assert marker in result


# -- configuration -------------------------------------------------------------------


def test_the_settings_left_are_the_support_and_compliance_ones() -> None:
    settings = _settings()
    assert settings.support_anonymize_free_text is True
    assert settings.compliance_auto_snapshot is True
    for gone in (
        "feature_pilot_telemetry",
        "telemetry_retention_days",
        "telemetry_anonymize_support",
    ):
        assert not hasattr(settings, gone), f"{gone} is back"
