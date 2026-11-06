"""'Your progress' on the student dashboard counts the student's own work.

The Open MRs card counted the student's own open merge requests, while the
'Your progress' panel beside it counted every open merge request of the group,
so the same student read 1 on the card and 3 in the panel. The failed pipelines
in that panel were the whole group's as well.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

import pytest

from app.api.dashboard.home import context


class _Result:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value

    def scalars(self) -> Any:
        return SimpleNamespace(all=lambda: self._value)


class _Db:
    """Answers the student lookup, then the student's groups."""

    def __init__(self, *answers: Any) -> None:
        self._answers = list(answers)

    async def execute(self, *_args: object, **_kwargs: object) -> _Result:
        return _Result(self._answers.pop(0))


@pytest.mark.asyncio
async def test_open_mrs_and_failed_pipelines_are_the_students_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    student = SimpleNamespace(id=uuid.uuid4(), gitlab_user_id=4242)
    team = SimpleNamespace(id=uuid.uuid4(), course_id=uuid.uuid4(), name="tim-01")
    conditions: dict[str, Any] = {}

    async def count(_db: object, _team_ids: object, _model: object, cond: Any, what: str) -> int:
        conditions[what] = cond.compile()
        return 0

    async def no_scores(*_args: object) -> tuple[list[float], dict[Any, Any]]:
        return [], {}

    async def no_deadline(*_args: object) -> None:
        return None

    monkeypatch.setattr(context, "_count_in_teams", count)
    monkeypatch.setattr(context, "_compliance_scores", no_scores)
    monkeypatch.setattr(context, "_next_deadline", no_deadline)

    out = await context._build_student_context(
        [team.course_id],
        _Db(student, [team]),  # type: ignore[arg-type]
        {"gitlab_username": "student"},
    )

    assert out["team_ids"] == [str(team.id)]
    open_mrs = conditions["open MRs"]
    assert "merge_requests.author_id" in str(open_mrs)
    assert "merge_requests.author_gitlab_id" in str(open_mrs)
    assert 4242 in open_mrs.params.values()
    pipelines = conditions["failed pipelines"]
    assert "merge_requests.author_id" in str(pipelines)
    assert "merge_requests.source_branch = pipelines.ref" in str(pipelines)
