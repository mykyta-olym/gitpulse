"""A list endpoint refuses a limit it cannot execute.

`/api/v1/events/recent`, `/api/v1/events/dlq` and the operations log
accepted `limit=-5`, passed it into `LIMIT` and answered 500 with an asyncpg
"LIMIT must not be negative". A caller's bad number is a 422 (or is clamped
where the endpoint parses by hand), never a server error.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import events
from app.api.dashboard.admin import system
from app.dependencies import AdminAuth, DbSession, SettingsDep, TeacherAuth


def _override(app: FastAPI, annotated: Any, value: Any) -> None:
    app.dependency_overrides[annotated.__metadata__[0].dependency] = lambda: value


class _Settings:
    feature_event_pipeline = True


def _events_client() -> TestClient:
    app = FastAPI()
    app.include_router(events.router, prefix="/api/v1/events")
    _override(app, DbSession, object())
    _override(app, SettingsDep, _Settings())
    _override(app, TeacherAuth, {"role": "teacher"})
    return TestClient(app)


@pytest.mark.parametrize("path", ["/api/v1/events/recent", "/api/v1/events/dlq"])
@pytest.mark.parametrize("limit", ["-5", "0"])
def test_a_negative_or_zero_limit_is_a_422(path: str, limit: str) -> None:
    resp = _events_client().get(path, params={"limit": limit})
    assert resp.status_code == 422, resp.text


def test_the_operations_log_clamps_what_it_parses_by_hand(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[int, int]] = []

    async def fake_payload(
        db: Any, status: Any, kind: Any, limit: int, offset: int, **kwargs: Any
    ) -> dict[str, Any]:
        seen.append((limit, offset))
        return {
            "jobs": [],
            "job_types": [],
            "total": 0,
            "failure_history": {"available": True, "total": 0},
        }

    monkeypatch.setattr(system, "build_jobs_payload", fake_payload)
    monkeypatch.setattr(system.job_diagnostics, "snapshot", AsyncMock())
    app = FastAPI()
    app.include_router(system.router)
    _override(app, DbSession, object())
    _override(app, AdminAuth, {"role": "admin"})
    client = TestClient(app)

    assert (
        client.get("/api/v1/admin/system/jobs", params={"limit": "-5", "offset": "-3"}).status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/admin/system/jobs", params={"limit": "abc", "offset": "abc"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/admin/system/jobs", params={"limit": "9999"}).status_code == 200
    assert seen == [(1, 0), (100, 0), (500, 0)]
