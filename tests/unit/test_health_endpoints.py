"""Tests for health endpoints module."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("upstream", "status"),
    [
        ("ok", 200),
        ("ok", 302),
        ("error", 401),
        ("error", 403),
        ("error", 404),
        ("error", 429),
        ("error", 503),
        ("unreachable", 0),
    ],
)
async def test_gitlab_status_reports_outages_without_changing_the_monitoring_probe(
    monkeypatch, upstream: str, status: int
) -> None:
    import json
    from types import SimpleNamespace

    import httpx

    from app.api import health

    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if upstream == "unreachable":
            raise httpx.ConnectTimeout("GitLab is unavailable", request=request)
        return httpx.Response(status, text="GitLab sign-in page")

    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs)
    )
    monkeypatch.setattr(
        health, "get_settings", lambda: SimpleNamespace(gitlab_url="https://git.example.edu")
    )
    monkeypatch.setattr(health, "_recent_gitlab_health", health._Recent(15))

    report = await health.gitlab_status()
    probe = await health.gitlab_health()
    assert report.status_code == 200
    assert probe.status_code == (200 if upstream == "ok" else 503)
    assert report.body == probe.body
    assert json.loads(report.body)["status"] == upstream
    assert len(requests) == 1, "the UI report and monitoring probe share their cached check"
    assert requests[0].url == "https://git.example.edu/users/sign_in"
    assert "PRIVATE-TOKEN" not in requests[0].headers


@pytest.mark.parametrize("probe", ["health", "readiness"])
@pytest.mark.parametrize("blocked_at", ["connect", "query"])
async def test_database_probe_timeout_includes_waiting_for_a_connection(
    monkeypatch, probe: str, blocked_at: str
) -> None:
    import asyncio
    import json

    from app.api import health

    cancelled = asyncio.Event()

    async def block() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    class Connection:
        async def __aenter__(self):
            if blocked_at == "connect":
                await block()
            return self

        async def __aexit__(self, *args):
            pass

        async def execute(self, statement):
            await block()

    class Redis:
        @classmethod
        def from_url(cls, *args, **kwargs):
            return cls()

        async def ping(self):
            return True

        async def aclose(self):
            pass

    monkeypatch.setattr(health, "_COMPONENT_TIMEOUT", 0.01)
    monkeypatch.setattr(health, "get_engine", lambda: SimpleNamespace(connect=Connection))
    if probe == "health":
        result = await asyncio.wait_for(health._check_database(), 1)
        assert result.status == "error"
        assert "timed out" in result.error
    else:
        monkeypatch.setattr(
            health,
            "get_settings",
            lambda: SimpleNamespace(redis_url="redis://unused", feature_redis_sessions=False),
        )
        monkeypatch.setattr("redis.asyncio.Redis", Redis)
        result = await asyncio.wait_for(health.readiness(), 1)
        assert result.status_code == 503
        assert json.loads(result.body)["components"] == {
            "database": "not_ready",
            "redis": "ready",
        }
    assert cancelled.is_set()


class TestHealthSchemas:
    """Tests for health endpoint schemas."""

    def test_component_health_schema_exists(self) -> None:
        from app.schemas.health import ComponentHealth

        assert ComponentHealth is not None

    def test_component_health_ok_status(self) -> None:
        from app.schemas.health import ComponentHealth

        health = ComponentHealth(status="ok", latency_ms=1.5)
        assert health.status == "ok"
        assert health.latency_ms == 1.5
        assert health.error is None

    def test_component_health_error_status(self) -> None:
        from app.schemas.health import ComponentHealth

        health = ComponentHealth(status="error", error="Connection refused")
        assert health.status == "error"
        assert health.error == "Connection refused"

    def test_health_response_schema_exists(self) -> None:
        from app.schemas.health import HealthResponse

        assert HealthResponse is not None

    def test_health_response_model(self) -> None:
        from datetime import UTC, datetime

        from app.schemas.health import ComponentHealth, HealthResponse

        response = HealthResponse(
            status="ok",
            version="1.0.0",
            uptime_seconds=3600.5,
            components={
                "database": ComponentHealth(status="ok", latency_ms=2.0),
            },
            timestamp=datetime.now(UTC),
        )

        assert response.status == "ok"
        assert response.version == "1.0.0"
        assert response.uptime_seconds == 3600.5
        assert "database" in response.components


class TestHealthRouterExists:
    """Tests for health router existence."""

    def test_health_router_module_importable(self) -> None:
        # The health module may require DB connection on import
        # Just test that the module exists
        import importlib.util

        spec = importlib.util.find_spec("app.api.health")
        assert spec is not None


class TestAppInfo:
    """Tests for APP_INFO metric."""

    def test_app_info_metric_set(self) -> None:
        from app.observability.metrics import APP_INFO

        # APP_INFO should be set with version and service info
        assert APP_INFO is not None


class TestAppVersionDetection:
    def test_app_version_falls_back_to_pyproject(
        self,
        monkeypatch,
        tmp_path,
    ) -> None:
        from importlib.metadata import PackageNotFoundError

        from app import config

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[project]\nname = "gitpulse"\nversion = "2026.5.16.post1"\n',
            encoding="utf-8",
        )

        def _missing_package(_: str) -> str:
            raise PackageNotFoundError

        monkeypatch.setattr(config, "_pkg_version", _missing_package)
        monkeypatch.setattr(config, "_PYPROJECT_PATH", pyproject)

        assert config._detect_app_version() == "2026.5.16.post1"


class TestGitLabHealthEndpoint:
    @pytest.mark.asyncio
    async def test_gitlab_health_does_not_forward_private_token(self) -> None:
        from app.api import health

        captured: dict[str, object] = {}

        class _Response:
            status_code = 200

            def json(self) -> dict[str, str]:
                return {"version": "17.0.0"}

        class _Client:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            async def __aenter__(self) -> "_Client":
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

            async def get(self, url: str, **kwargs: object) -> _Response:
                captured["url"] = url
                captured["kwargs"] = kwargs
                return _Response()

        settings = SimpleNamespace(
            gitlab_url="https://git.example.edu",
            gitlab_api_token="should-not-be-forwarded",
        )
        with (
            patch("app.api.health.get_settings", return_value=settings),
            patch("httpx.AsyncClient", _Client),
        ):
            response = await health.gitlab_health()

        assert response.status_code == 200
        assert captured["url"] == "https://git.example.edu/users/sign_in"
        kwargs = captured["kwargs"]
        assert isinstance(kwargs, dict)
        assert "headers" not in kwargs


@pytest.mark.asyncio
async def test_database_probe_clamps_negative_pool_overflow(monkeypatch) -> None:
    from app.api import health

    class _Conn:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def execute(self, _stmt):
            return SimpleNamespace(close=lambda: None)

    pool = SimpleNamespace(
        size=lambda: 12,
        checkedin=lambda: 2,
        checkedout=lambda: 0,
        overflow=lambda: -10,
    )
    monkeypatch.setattr(health, "get_engine", lambda: SimpleNamespace(connect=_Conn, pool=pool))
    comp = await health._check_database()
    assert comp.status == "ok"
    assert comp.details["pool_overflow"] == 0


@pytest.mark.asyncio
async def test_redis_probe_fetches_info_once_and_populates_clients(monkeypatch) -> None:
    from app.api import health

    info_calls: list[tuple[object, ...]] = []

    class _Redis:
        @classmethod
        def from_url(cls, *args, **kwargs):
            return cls()

        async def ping(self):
            return True

        async def info(self, *args):
            info_calls.append(args)
            return {
                "redis_version": "7.4.8",
                "connected_clients": 9,
                "used_memory_human": "10.47M",
            }

        async def aclose(self):
            return None

    monkeypatch.setattr(health, "get_settings", lambda: SimpleNamespace(redis_url="redis://test"))
    monkeypatch.setattr("redis.asyncio.Redis", _Redis)
    comp = await health._check_redis()
    assert comp.status == "ok"
    assert info_calls == [()]
    assert comp.details == {
        "redis_version": "7.4.8",
        "connected_clients": 9,
        "used_memory_human": "10.47M",
    }


@pytest.mark.asyncio
async def test_get_health_report_singleflight_and_admin_system_health_header(monkeypatch) -> None:
    import asyncio
    from datetime import UTC, datetime

    import httpx
    from fastapi import FastAPI

    from app.api import health
    from app.api.dashboard.admin.system import router as system_router
    from app.dependencies import AdminAuth
    from app.schemas.health import ComponentHealth, HealthResponse

    calls = 0

    async def fake_probe() -> ComponentHealth:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return ComponentHealth(
            status="ok",
            latency_ms=1.2,
            details={"pool_size": 5, "pool_idle": 5, "pool_overflow": 0},
        )

    monkeypatch.setattr(health, "_recent_health", health._Recent(15))
    monkeypatch.setattr(health, "_check_database", fake_probe)
    monkeypatch.setattr(
        health,
        "_check_redis",
        lambda: asyncio.sleep(0, ComponentHealth(status="ok", latency_ms=0.8)),
    )
    monkeypatch.setattr(
        health,
        "_check_gitlab",
        lambda: asyncio.sleep(0, ComponentHealth(status="ok", latency_ms=5.0)),
    )
    monkeypatch.setattr(
        health,
        "get_settings",
        lambda: SimpleNamespace(
            app_version="2026.10.30",
            app_env=SimpleNamespace(value="production"),
            feature_redis_sessions=False,
            smtp_host="",
        ),
    )

    reports = await asyncio.gather(*(health.get_health_report(force=False) for _ in range(8)))
    assert calls == 1
    assert all(r.status == "ok" for r in reports)

    await health.get_health_report(force=True)
    assert calls == 2

    degraded_report = HealthResponse(
        status="degraded",
        version="2026.10.30",
        uptime_seconds=125.0,
        components={"gitlab": ComponentHealth(status="error", error="Upstream timeout")},
        timestamp=datetime.now(UTC),
    )
    monkeypatch.setattr(
        "app.api.dashboard.admin.system.get_health_report",
        lambda force=False: asyncio.sleep(0, degraded_report),
    )
    app = FastAPI()
    app.include_router(system_router)
    app.dependency_overrides[AdminAuth.__metadata__[0].dependency] = lambda: {"role": "admin"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        res = await client.get("/api/v1/admin/system/health?fresh=1&lang=en")
    assert res.status_code == 200
    assert res.headers["x-health-status"] == "degraded"
    assert "0 / 1" in res.text
    assert "Some components are degraded" in res.text
    assert "Upstream timeout" in res.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("core_status", "external_status", "expected"),
    [
        ("ok", "ok", "ok"),
        ("ok", "degraded", "degraded"),
        ("ok", "error", "degraded"),
        ("down", "ok", "down"),
    ],
)
async def test_health_card_summarizes_external_checks_without_changing_readiness(
    monkeypatch, core_status, external_status, expected
) -> None:
    import asyncio
    from datetime import UTC, datetime

    import httpx
    from fastapi import FastAPI

    from app.api.dashboard.admin.system import router
    from app.dependencies import AdminAuth
    from app.schemas.health import ComponentHealth, HealthResponse

    report = HealthResponse(
        status=core_status,
        version="2026.11.1",
        uptime_seconds=5,
        components={"gitlab": ComponentHealth(status=external_status)},
        timestamp=datetime.now(UTC),
    )
    reads = []

    async def read(*, force=False):
        reads.append(force)
        return await asyncio.sleep(0, report)

    monkeypatch.setattr("app.api.dashboard.admin.system.get_health_report", read)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[AdminAuth.__metadata__[0].dependency] = lambda: {"role": "admin"}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/admin/system/health?fresh=1&lang=en")
    assert response.status_code == 200
    assert response.headers["x-health-status"] == expected
    assert reads == [True]
    assert report.status == core_status
    if expected == "degraded":
        assert "Some components are degraded" in response.text
        assert "All systems operational" not in response.text
