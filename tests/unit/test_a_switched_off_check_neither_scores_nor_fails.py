"""A check the course switched off is neither scored, counted nor failed.

The defaults leave R09, R11 and R13 off. Without a weekly plan the engine added
up the remaining scores without dividing by their weight (0.85), so a student
who passed every enabled check scored 85 %. It also counted the three switched
off checks in "5/13" and listed "Check disabled" among the student's failing
checks on the dashboard. The weekly path already divided by the weight of the
checks it scored; both paths now do.
"""

from __future__ import annotations

import pytest

from app.compliance.engine import _score
from app.compliance.types import CheckResult

_DEFAULT_ON = {
    "R01": 0.08,
    "R02": 0.06,
    "R03": 0.10,
    "R04": 0.08,
    "R05": 0.05,
    "R06": 0.12,
    "R07": 0.12,
    "R08": 0.10,
    "R10": 0.07,
    "R12": 0.07,
}


def _on(code: str, weight: float, *, passed: bool = True) -> CheckResult:
    return CheckResult(
        check_id=code,
        name=code,
        passed=passed,
        detail="ok" if passed else f"{code} missing",
        weight=weight,
        score=weight if passed else 0.0,
    )


def _off(code: str) -> CheckResult:
    return CheckResult(
        check_id=code, name=code, passed=False, detail="Check disabled", enabled=False
    )


def _defaults(*, failing: str | None = None) -> list[CheckResult]:
    return [_on(c, w, passed=c != failing) for c, w in _DEFAULT_ON.items()] + [
        _off("R09"),
        _off("R11"),
        _off("R13"),
    ]


def test_passing_every_enabled_default_check_scores_full() -> None:
    score, passed, total, bottlenecks = _score(_defaults(), None)
    assert score == pytest.approx(1.0)
    assert (passed, total) == (10, 10)
    assert bottlenecks == []


def test_the_score_divides_by_the_weight_of_the_enabled_checks() -> None:
    score, passed, total, bottlenecks = _score(_defaults(failing="R07"), None)
    assert score == pytest.approx((0.85 - 0.12) / 0.85)
    assert (passed, total) == (9, 10)
    assert bottlenecks == ["R07 missing"]


def test_a_weekly_plan_skips_an_expected_check_the_course_switched_off() -> None:
    checks = [_on("R01", 0.5), _on("R02", 0.5, passed=False), _off("R09")]
    score, passed, total, bottlenecks = _score(checks, {"R01", "R09"})
    assert (score, passed, total, bottlenecks) == (1.0, 1, 1, [])


def test_nothing_enabled_scores_nothing_and_counts_nothing() -> None:
    score, passed, total, bottlenecks = _score([_off("R01"), _off("R02")], None)
    # checks_total == 0 is what turns the traffic light GRAY (no data).
    assert (score, passed, total, bottlenecks) == (1.0, 0, 0, [])
