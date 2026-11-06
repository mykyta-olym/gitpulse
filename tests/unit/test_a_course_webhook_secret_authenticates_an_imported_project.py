"""A course's webhook secret authenticates its imported projects.

The import gives every project a secret of its own that nobody ever sees.
The receiver used to stop at that secret, so a webhook configuration (the
only secret the Settings page issues) answered 401 to every delivery from an
imported project - found by running the classroom assistant against a real
GitLab. The project's own secret is still tried first, and a token that
matches nothing is still refused.
"""

import uuid
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app.api import webhooks
from app.models.course import Course
from app.models.team import Team
from app.security.webhook_auth import compute_webhook_lookup_key, hash_webhook_secret

OWN = "whsec_" + "a" * 48
COURSE_WIDE = "whsec_" + "b" * 48
LEGACY = "whsec_" + "c" * 48


class _Db:
    def __init__(self, course: Any) -> None:
        self.team = SimpleNamespace(id=uuid.uuid4(), course_id=course.id)
        self.course = course

    async def get(self, model: type, _key: Any) -> Any:
        return {Team: self.team, Course: self.course}.get(model)


def _course(legacy: str | None = None) -> SimpleNamespace:
    settings = SimpleNamespace(
        id=uuid.uuid4(),
        webhook_secret_hash=hash_webhook_secret(legacy) if legacy else None,
        webhook_secret_hash_previous=None,
        webhook_secret_previous_expires_at=None,
    )
    return SimpleNamespace(id=uuid.uuid4(), settings=settings)


def _imported_project() -> SimpleNamespace:
    return SimpleNamespace(
        team_id=uuid.uuid4(),
        webhook_secret_hash=hash_webhook_secret(OWN),
        webhook_secret_lookup=compute_webhook_lookup_key(OWN),
    )


@pytest.fixture
def configs(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The course's webhook configurations: the tokens they accept."""
    accepted: list[str] = []
    asked: list[str] = []

    async def authenticate(_db: Any, *, token: str, **_: Any) -> Any:
        asked.append(token)
        if token in accepted:
            return SimpleNamespace(config=SimpleNamespace(id=uuid.uuid4()), used_previous=False)
        return None

    async def stamp(*_: Any, **__: Any) -> None:
        return None

    monkeypatch.setattr(webhooks.webhook_configs, "authenticate", authenticate)
    monkeypatch.setattr(webhooks, "_stamp_last_used", stamp)
    accepted.append(COURSE_WIDE)
    return asked


DELIVERY = SimpleNamespace(project_gitlab_id=7, path_with_namespace="kurz/tim-01/projekt")


async def _auth(course: Any, project: Any, token: str) -> Any:
    return await webhooks._authenticate(_Db(course), token, project, DELIVERY)  # type: ignore[arg-type]


async def test_the_course_wide_secret_authenticates_an_imported_project(
    configs: list[str],
) -> None:
    course = _course()
    assert await _auth(course, _imported_project(), COURSE_WIDE) is course


async def test_the_projects_own_secret_is_tried_first(configs: list[str]) -> None:
    course = _course()
    assert await _auth(course, _imported_project(), OWN) is course
    assert configs == []


async def test_the_legacy_course_secret_authenticates_an_imported_project(
    configs: list[str],
) -> None:
    course = _course(legacy=LEGACY)
    assert await _auth(course, _imported_project(), LEGACY) is course


async def test_a_token_that_matches_nothing_is_refused(configs: list[str]) -> None:
    with pytest.raises(HTTPException) as refused:
        await _auth(_course(), _imported_project(), "whsec_" + "d" * 48)
    assert refused.value.status_code == 401


async def test_a_wrong_token_is_refused_with_a_legacy_secret_set(configs: list[str]) -> None:
    with pytest.raises(HTTPException) as refused:
        await _auth(_course(legacy=LEGACY), _imported_project(), "whsec_" + "d" * 48)
    assert refused.value.status_code == 401
