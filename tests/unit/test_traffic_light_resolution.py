"""A week with nothing expected must read GRAY (N/A), not GREEN.

When ``expected_checks`` for a week is empty, the engine deliberately keeps the
weighted score at 1.0 so students are not penalised for checks not yet
introduced. But it also reported GREEN, claiming every student was fully
compliant for a week in which zero checks ran - while the telemetry layer
already treated ``checks_total == 0`` as N/A. The two disagreed; GRAY is the
neutral state both the snapshot columns and the badge macro already support.
"""

from dataclasses import dataclass

from app.compliance.engine import _resolve_traffic_light


@dataclass
class _Cs:
    green_threshold: float = 0.8
    yellow_threshold: float = 0.5


class TestResolveTrafficLight:
    def test_nothing_expected_is_gray_not_green(self) -> None:
        # Previously returned GREEN: score 1.0 with zero checks evaluated.
        assert _resolve_traffic_light(1.0, 0, _Cs()) == "GRAY"

    def test_gray_wins_even_over_a_zero_score(self) -> None:
        # No checks ran, so it is "no data" - never RED either.
        assert _resolve_traffic_light(0.0, 0, _Cs()) == "GRAY"

    def test_normal_thresholds_unchanged(self) -> None:
        cs = _Cs()
        assert _resolve_traffic_light(1.0, 13, cs) == "GREEN"
        assert _resolve_traffic_light(0.8, 13, cs) == "GREEN"
        assert _resolve_traffic_light(0.65, 13, cs) == "YELLOW"
        assert _resolve_traffic_light(0.5, 13, cs) == "YELLOW"
        assert _resolve_traffic_light(0.2, 13, cs) == "RED"
