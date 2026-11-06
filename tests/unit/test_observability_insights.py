"""Monitoring reads have a deadline, a cache and role-safe projections."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.api.observability import router
from app.dependencies import get_current_user
from app.observability import insights


@pytest.fixture(autouse=True)
def monitoring(monkeypatch):
    settings = SimpleNamespace(prometheus_url="http://prometheus:9090")
    monkeypatch.setattr(insights, "get_settings", lambda: settings)
    monkeypatch.setattr(insights, "_cache", None)
    monkeypatch.setattr(insights, "_cache_base", "")
    monkeypatch.setattr(insights, "_lock", asyncio.Lock())
    return settings


@pytest.mark.asyncio
async def test_disabled_monitoring_does_not_contact_any_service(monitoring, monkeypatch):
    monitoring.prometheus_url = ""
    read = AsyncMock()
    monkeypatch.setattr(insights, "_read", read)
    snap = await insights.snapshot()
    assert not snap.configured
    assert not snap.reachable
    read.assert_not_awaited()


@pytest.mark.asyncio
async def test_concurrent_readers_share_one_cached_snapshot(monitoring, monkeypatch):
    read = AsyncMock(return_value=insights.Snapshot(True, True, {"workers": 4}))
    monkeypatch.setattr(insights, "_read", read)
    results = await asyncio.gather(*(insights.snapshot() for _ in range(20)))
    assert all(s is results[0] for s in results)
    read.assert_awaited_once()
    monitoring.prometheus_url = "http://other-prometheus:9090"
    await insights.snapshot()
    assert read.await_count == 2


@pytest.mark.parametrize(
    "error", [ValueError("bad data"), httpx.ConnectError("offline"), TimeoutError()]
)
@pytest.mark.asyncio
async def test_failure_is_cached_as_unknown_not_all_clear(monkeypatch, error):
    read = AsyncMock(side_effect=error)
    monkeypatch.setattr(insights, "_read", read)
    first = await insights.snapshot()
    second = await insights.snapshot()
    assert first is second
    assert first.configured
    assert not first.reachable
    read.assert_awaited_once()


@pytest.mark.asyncio
async def test_real_http_contract_and_non_finite_values(monkeypatch):
    client_class = httpx.AsyncClient
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/alerts"):
            data = {
                "alerts": [
                    {
                        "labels": {"alertname": "WorkerDown", "severity": "critical"},
                        "state": "firing",
                        "annotations": {"summary": "Worker host internal"},
                    }
                ]
            }
        else:
            data = {"resultType": "vector", "result": [{"value": [1, "NaN"]}]}
        return httpx.Response(200, json={"status": "success", "data": data})

    monkeypatch.setattr(
        insights.httpx,
        "AsyncClient",
        lambda **kw: client_class(**kw, transport=httpx.MockTransport(handle)),
    )
    snap = await insights.snapshot()
    assert snap.reachable
    assert all(v is None for v in snap.values.values())
    assert snap.firing == {"WorkerDown"}
    assert len(requests) == len(insights.SERIES) + 1
    assert all(r.url.host == "prometheus" for r in requests)


@pytest.mark.asyncio
async def test_a_hanging_monitoring_read_has_one_total_deadline(monkeypatch):
    client_class = httpx.AsyncClient

    async def handle(request):
        await asyncio.Event().wait()

    monkeypatch.setattr(insights, "TIMEOUT_S", 0.03)
    monkeypatch.setattr(
        insights.httpx,
        "AsyncClient",
        lambda **kw: client_class(**kw, transport=httpx.MockTransport(handle)),
    )
    snap = await asyncio.wait_for(insights.snapshot(), timeout=0.5)
    assert not snap.reachable


@pytest.mark.parametrize(
    "body", [{}, [], {"status": "error", "data": {}}, {"status": "success", "data": None}]
)
def test_invalid_prometheus_envelopes_are_not_success(body):
    response = httpx.Response(200, json=body, request=httpx.Request("GET", "http://prometheus"))
    with pytest.raises(ValueError, match="Invalid Prometheus response"):
        insights._data(response)


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (None, "s", "-"),
        (0.3, "s", "300 ms"),
        (1.6, "s", "1.6 s"),
        (2, "pct", "2.0 %"),
        (0.1, "rate", "0.10"),
        (4, "count", "4"),
    ],
)
def test_units(value, unit, expected):
    assert insights.format_value(value, unit) == expected


def test_internal_alerts_surface_to_admins_without_leaking_to_other_roles():
    snap = insights.Snapshot(True, True, {}, [{"name": "PrometheusTargetDown", "state": "firing"}])
    assert insights.notices_for(snap, "student") == []
    assert insights.notices_for(snap, "teacher") == []
    assert insights.notices_for(snap, "admin")[0]["key"] == "infrastructure"


def test_retained_history_and_new_errors_have_distinct_grafana_queries():
    import json
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[2]
    panels = {
        panel["id"]: panel
        for panel in json.loads(
            (root / "monitoring/grafana/dashboards/gitpulse.json").read_text(encoding="utf-8")
        )["panels"]
    }
    for series in insights.SERIES:
        if series.key in {"failed_jobs", "job_errors"}:
            assert series.query == panels[series.panel]["targets"][0]["expr"]
    rules = yaml.safe_load((root / "monitoring/prometheus/alerts.yml").read_text(encoding="utf-8"))
    failure_rule = next(
        rule
        for group in rules["groups"]
        for rule in group["rules"]
        if rule.get("alert") == "RQFailedJobsHigh"
    )
    assert failure_rule["expr"] == "sum(increase(rq_job_failures_total[1h])) > 5"
    assert "rq_failed_jobs" not in failure_rule["expr"]


@pytest.mark.asyncio
async def test_status_api_projects_only_notices_for_the_reader(monkeypatch):
    snap = insights.Snapshot(
        True,
        True,
        {"workers": 4},
        [
            {"name": "WorkerDown", "state": "firing", "summary": "secret internal hostname"},
            {"name": "GitLabAPILatencyHigh", "state": "firing"},
            {"name": "HighHTTPErrorRate", "state": "pending"},
        ],
    )
    monkeypatch.setattr(insights, "snapshot", AsyncMock(return_value=snap))
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    for role in ("student", "teacher", "admin"):
        app.dependency_overrides[get_current_user] = lambda role=role: SimpleNamespace(role=role)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/observability/status")
        assert response.status_code == 200
        body = response.json()
        assert body["state"] == "degraded"
        keys = {n["key"] for n in body["notices"]}
        assert keys == ({"delay"} if role == "student" else {"delay", "gitlab"})
        assert "secret" not in response.text
        assert "workers" not in response.text


@pytest.mark.asyncio
async def test_unknown_status_is_explicit(monkeypatch):
    monkeypatch.setattr(
        insights, "snapshot", AsyncMock(return_value=insights.Snapshot(True, False))
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(role="student")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/observability/status")).json() == {
            "state": "unknown",
            "notices": [],
        }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "target"),
    [("admin", "/dashboard/admin/system"), ("teacher", "/dashboard/"), ("student", "/dashboard/")],
)
async def test_old_status_bookmark_redirects_without_loading_monitoring(monkeypatch, role, target):
    from app.api.dashboard.home.routes import router as home_router
    from app.dependencies import require_dashboard_auth

    read = AsyncMock()
    monkeypatch.setattr(insights, "snapshot", read)
    app = FastAPI()
    app.include_router(home_router)
    app.dependency_overrides[require_dashboard_auth] = lambda: {"role": role, "user": "test"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/status")
    assert response.status_code == 303
    assert response.headers["location"] == target
    assert response.headers["cache-control"] == "no-store"
    read.assert_not_awaited()


def test_monitoring_partial_uses_one_compact_summary_without_duplicate_tables():
    from app.main import templates

    snap = insights.Snapshot(
        True,
        True,
        {"workers": 4},
        [
            {
                "name": "WorkerDown",
                "state": "firing",
                "severity": "critical",
                "summary": "internal-host",
            }
        ],
    )
    html = templates.env.get_template("partials/admin/_system_monitoring.html").render(
        monitoring=snap, series=insights.series_rows(snap), monitoring_enabled=True, t=lambda s: s
    )
    assert "internal-host" in html
    assert "<table" not in html
    assert 'href="/grafana/' in html
    assert "Active workers" not in html
    assert "Retained failed jobs" not in html


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("configured", "reachable", "status"),
    [(True, False, 503), (True, True, 200), (False, False, 200)],
)
async def test_monitoring_refresh_does_not_report_an_outage_as_success(
    monkeypatch, configured, reachable, status
):
    from app.api.dashboard.admin.system import router as system_router
    from app.dependencies import AdminAuth

    monkeypatch.setattr(
        insights, "snapshot", AsyncMock(return_value=insights.Snapshot(configured, reachable))
    )
    app = FastAPI()
    app.include_router(system_router)
    app.dependency_overrides[AdminAuth.__metadata__[0].dependency] = lambda: {"role": "admin"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/admin/system/monitoring?lang=en")
    assert response.status_code == status
    assert ("Monitoring is unavailable" in response.text) == (configured and not reachable)


@pytest.mark.asyncio
async def test_snapshot_force_bypasses_cache_and_admin_notice_carries_action(monkeypatch):
    calls = 0

    async def fake_read(_base: str) -> insights.Snapshot:
        nonlocal calls
        calls += 1
        return insights.Snapshot(
            True,
            True,
            {"http_rate": float(calls)},
            [{"name": "PrometheusTargetDown", "state": "firing"}],
        )

    monkeypatch.setattr(insights, "_read", fake_read)
    first = await insights.snapshot()
    cached = await insights.snapshot()
    forced = await insights.snapshot(force=True)
    assert first is cached
    assert forced is not first
    assert calls == 2

    admin_notices = insights.notices_for(forced, "admin")
    assert admin_notices == [
        {
            "key": "infrastructure",
            "text": "Monitoring reports an infrastructure issue.",
            "action_href": "/dashboard/admin/system",
            "action_label": "Open System",
        }
    ]
