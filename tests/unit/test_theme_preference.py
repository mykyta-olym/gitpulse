from __future__ import annotations

from typing import Any

import pytest

from app.api.dashboard.auth import update_theme_preference


class _Request:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    async def json(self) -> Any:
        return self._payload


class _User:
    def __init__(self, preference: str = "system") -> None:
        self.theme_preference = preference


class _Db:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_theme_preference_is_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _User()
    db = _Db()

    async def _current_user(_auth: object, _db: object) -> _User:
        return user

    monkeypatch.setattr("app.dependencies.get_current_user", _current_user)

    response = await update_theme_preference(
        request=_Request({"preference": "dark"}),  # type: ignore[arg-type]
        _auth={"user": "teacher"},
        db=db,  # type: ignore[arg-type]
        _csrf=None,  # type: ignore[arg-type]
    )

    assert response.status_code == 204
    assert user.theme_preference == "dark"
    assert db.commits == 1


@pytest.mark.asyncio
async def test_theme_preference_rejects_unknown_mode() -> None:
    response = await update_theme_preference(
        request=_Request({"preference": "sepia"}),  # type: ignore[arg-type]
        _auth={"user": "teacher"},
        db=_Db(),  # type: ignore[arg-type]
        _csrf=None,  # type: ignore[arg-type]
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_theme_preference_does_not_commit_unchanged_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = _User("system")
    db = _Db()

    async def _current_user(_auth: object, _db: object) -> _User:
        return user

    monkeypatch.setattr("app.dependencies.get_current_user", _current_user)

    response = await update_theme_preference(
        request=_Request({"preference": "system"}),  # type: ignore[arg-type]
        _auth={"user": "teacher"},
        db=db,  # type: ignore[arg-type]
        _csrf=None,  # type: ignore[arg-type]
    )

    assert response.status_code == 204
    assert db.commits == 0
