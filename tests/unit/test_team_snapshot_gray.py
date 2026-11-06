"""A team must not read GREEN for a week in which nothing was evaluated.

When a week has no expected checks, every member snapshot carries
``checks_total == 0`` with a deliberately non-penalising ``weighted_score`` of
1.0. Averaging those produced a GREEN team light, claiming the whole group was
fully compliant for a week where zero checks ran - the team-level version of the
per-student bug fixed alongside it.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.compliance.engine import _build_team_snapshot


@dataclass
class _Team:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    course_id: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class _Cs:
    green_threshold: float = 0.8
    yellow_threshold: float = 0.5


@dataclass
class _Snap:
    weighted_score: float
    checks_total: int
    traffic_light: str
    checks_passed: int = 0
    mrs_created: int = 0
    student_id: uuid.UUID = field(default_factory=uuid.uuid4)
    bottlenecks: list[str] = field(default_factory=list)


def _build(snaps: list[_Snap]):
    return _build_team_snapshot(_Team(), _Cs(), datetime.now(UTC), snaps, [], [])


class TestTeamTrafficLight:
    def test_nothing_expected_team_is_gray_not_green(self) -> None:
        # Every member "scored" 1.0 but zero checks ran -> previously GREEN.
        snaps = [_Snap(1.0, 0, "GRAY") for _ in range(3)]
        assert _build(snaps).overall_traffic_light == "GRAY"

    def test_real_evaluation_still_green(self) -> None:
        snaps = [_Snap(0.95, 13, "GREEN") for _ in range(3)]
        assert _build(snaps).overall_traffic_light == "GREEN"

    def test_real_evaluation_still_red(self) -> None:
        snaps = [_Snap(0.10, 13, "RED") for _ in range(2)]
        assert _build(snaps).overall_traffic_light == "RED"

    def test_partial_evaluation_uses_thresholds(self) -> None:
        # One member had checks -> the team was measured, normal rules apply.
        snaps = [_Snap(1.0, 0, "GRAY"), _Snap(0.2, 13, "RED")]
        assert _build(snaps).overall_traffic_light == "YELLOW"
