"""Unknown GitLab photographs use initials without speculative network requests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.api.dashboard.students.profile import _student_avatar


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [None, "https://git.example.com/uploads/photo.jpg"])
async def test_student_avatar_uses_only_stored_photo(url: str | None) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = url
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    student = SimpleNamespace(gitlab_user_id=42, gitlab_username="learner")

    avatar = await _student_avatar(db, student, {"user": "teacher"})  # type: ignore[arg-type]

    assert avatar == url


@pytest.mark.asyncio
async def test_student_own_session_photo_remains_available() -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = None
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    student = SimpleNamespace(gitlab_user_id=42, gitlab_username="learner")

    avatar = await _student_avatar(
        db,  # type: ignore[arg-type]
        student,  # type: ignore[arg-type]
        {
            "user": "learner",
            "gitlab_username": "learner",
            "avatar_url": "https://git.example.com/photo.jpg",
        },
    )

    assert avatar == "https://git.example.com/photo.jpg"
