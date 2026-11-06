"""Unit tests for semester lifecycle helpers and presets."""

from datetime import date
from types import SimpleNamespace

from app.utils.semester import get_effective_semester_end, is_semester_over
from app.utils.semester_presets import PRESETS, find_preset, get_presets


class TestGetEffectiveSemesterEnd:
    def test_returns_none_for_none_settings(self) -> None:
        assert get_effective_semester_end(None, default_length_weeks=14) is None

    def test_prefers_explicit_end_date(self) -> None:
        cs = SimpleNamespace(
            semester_start_date=date(2026, 2, 9),
            semester_end_date=date(2026, 6, 26),
        )
        assert get_effective_semester_end(cs, default_length_weeks=14) == date(2026, 6, 26)

    def test_falls_back_to_start_plus_default(self) -> None:
        cs = SimpleNamespace(
            semester_start_date=date(2026, 2, 9),
            semester_end_date=None,
        )
        # 2026-02-09 + 14 weeks = 2026-05-18
        assert get_effective_semester_end(cs, default_length_weeks=14) == date(2026, 5, 18)

    def test_returns_none_when_no_dates(self) -> None:
        cs = SimpleNamespace(semester_start_date=None, semester_end_date=None)
        assert get_effective_semester_end(cs, default_length_weeks=14) is None


class TestIsSemesterOver:
    def test_none_settings_never_over(self) -> None:
        assert is_semester_over(None, grace_days=14, default_length_weeks=14) is False

    def test_open_ended_course_never_over(self) -> None:
        cs = SimpleNamespace(semester_start_date=None, semester_end_date=None)
        assert is_semester_over(cs, grace_days=14, default_length_weeks=14) is False

    def test_within_grace_not_over(self) -> None:
        cs = SimpleNamespace(
            semester_start_date=date(2026, 2, 9),
            semester_end_date=date(2026, 6, 26),
        )
        # 5 days after end -> inside 14-day grace
        assert (
            is_semester_over(cs, grace_days=14, default_length_weeks=14, today=date(2026, 7, 1))
            is False
        )

    def test_past_grace_is_over(self) -> None:
        cs = SimpleNamespace(
            semester_start_date=date(2026, 2, 9),
            semester_end_date=date(2026, 6, 26),
        )
        # 30 days after end -> past 14-day grace
        assert (
            is_semester_over(cs, grace_days=14, default_length_weeks=14, today=date(2026, 7, 30))
            is True
        )

    def test_uses_fallback_end_when_explicit_missing(self) -> None:
        cs = SimpleNamespace(
            semester_start_date=date(2025, 9, 22),
            semester_end_date=None,
        )
        # fallback end = 2025-09-22 + 14 weeks = 2025-12-29, + 14 grace = 2026-01-12
        assert (
            is_semester_over(cs, grace_days=14, default_length_weeks=14, today=date(2026, 1, 13))
            is True
        )
        assert (
            is_semester_over(cs, grace_days=14, default_length_weeks=14, today=date(2026, 1, 10))
            is False
        )


class TestSemesterPresets:
    def test_presets_non_empty(self) -> None:
        assert len(PRESETS) >= 4

    def test_presets_have_bilingual_labels(self) -> None:
        for p in PRESETS:
            assert p.label_en
            assert p.label_sk
            assert p.start_date < p.end_date

    def test_find_preset(self) -> None:
        got = find_preset("tuke-fei-ss-2025-2026")
        assert got is not None
        assert got.start_date == date(2026, 2, 16)
        assert find_preset("does-not-exist") is None

    def test_get_presets_json_shape(self) -> None:
        for d in get_presets():
            assert set(d.keys()) >= {
                "id",
                "label_en",
                "label_sk",
                "start_date",
                "end_date",
                "academic_year",
                "semester",
            }
            # ISO-format dates
            date.fromisoformat(d["start_date"])
            date.fromisoformat(d["end_date"])
            # semester must match Course.semester vocabulary
            assert d["semester"] in {"winter", "summer"}

    def test_preset_ids_unique(self) -> None:
        ids = [p.id for p in PRESETS]
        assert len(ids) == len(set(ids))

    def test_get_presets_hides_fully_past_semesters(self) -> None:
        # Before any semester ends: all presets are offered.
        early = get_presets(today=date(2025, 1, 1))
        assert len(early) == len(PRESETS)
        # Mid-2026: the 2025/2026 semesters have ended, only 2026/2027 remain.
        mid = get_presets(today=date(2026, 7, 12))
        assert mid, "current+future presets must remain"
        assert all(d["academic_year"] == "2026/2027" for d in mid)
        # A preset is offered up to and including its end_date (inclusive).
        on_end = get_presets(today=date(2026, 2, 13))
        assert any(d["id"] == "tuke-fei-ws-2025-2026" for d in on_end)

    def test_skip_auto_archive_respected(self) -> None:
        """is_semester_over stays True if end passed; sweep-level skip flag
        is separately enforced by the worker, not by the helper itself.

        This test documents the contract: the helper reports semester
        status regardless of the opt-out flag - callers (the sweep) are
        responsible for honouring ``skip_auto_archive``.
        """
        cs = SimpleNamespace(
            semester_start_date=date(2026, 2, 9),
            semester_end_date=date(2026, 6, 26),
            skip_auto_archive=True,  # helper must ignore this field
        )
        assert (
            is_semester_over(
                cs,
                grace_days=14,
                default_length_weeks=14,
                today=date(2026, 8, 1),
            )
            is True
        )
