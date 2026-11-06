"""The monitoring tools open for a GitPulse administrator's session, nobody else.

Grafana, Prometheus, Jaeger and Alertmanager used to share one Basic Auth
password, which had ended up in the operator documentation. Caddy now asks
/internal/monitoring-authz before each request to them (Caddyfile,
forward_auth), as it does for /docs/. These pin the decision, its failure mode
(closed, unlike the documentation) and the wiring that makes it the only way in.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from app.api import monitoring_authz

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client() -> TestClient:
    from app.config import get_settings
    from app.main import create_app

    hosts = get_settings().allowed_hosts
    host = next((h for h in hosts if "*" not in h), None) if hosts else "testserver"
    return TestClient(create_app(), base_url=f"http://{host or 'testserver'}")


def _as(monkeypatch: pytest.MonkeyPatch, session: dict[str, Any] | None) -> None:
    monkeypatch.setattr(monitoring_authz, "get_current_session", lambda *a, **k: session)


def _ask(client: TestClient, service: str, uri: str) -> Any:
    return client.get(
        f"/internal/monitoring-authz?service={service}",
        headers={"X-Forwarded-Uri": uri},
        follow_redirects=False,
    )


ADMIN = {"user": "mykyta.olym", "role": "admin", "email": "admin@example.test"}


def test_an_administrator_is_let_in(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _as(monkeypatch, ADMIN)
    for service in monitoring_authz.SERVICES:
        r = _ask(client, service, "/")
        assert r.status_code == 204, service


def test_grafana_is_told_who_signed_in(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _as(monkeypatch, ADMIN)
    r = _ask(client, "grafana", "/grafana/d/gitpulse-overview")
    assert r.headers[monitoring_authz.GRAFANA_USER_HEADER] == "mykyta.olym"
    assert r.headers[monitoring_authz.GRAFANA_EMAIL_HEADER] == "admin@example.test"
    # The other tools have no user of their own to name.
    assert monitoring_authz.GRAFANA_USER_HEADER not in _ask(client, "prometheus", "/").headers


@pytest.mark.parametrize("role", ["teacher", "student", ""])
def test_any_other_role_is_refused(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, role: str
) -> None:
    _as(monkeypatch, {"user": "someone", "role": role})
    r = _ask(client, "grafana", "/grafana/")
    assert r.status_code == 403
    assert monitoring_authz.GRAFANA_USER_HEADER not in r.headers
    assert "administr" in r.text


@pytest.mark.parametrize(
    ("service", "forwarded", "back_to"),
    [
        # handle_path strips the prefix before Caddy forwards the URI ...
        ("prometheus", "/graph?g0.expr=up", "/prometheus/graph?g0.expr=up"),
        ("alertmanager", "/", "/alertmanager/"),
        # ... handle does not.
        ("grafana", "/grafana/d/gitpulse-overview", "/grafana/d/gitpulse-overview"),
        ("jaeger", "/jaeger/search", "/jaeger/search"),
    ],
)
def test_no_session_signs_in_and_comes_back(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    service: str,
    forwarded: str,
    back_to: str,
) -> None:
    _as(monkeypatch, None)
    r = _ask(client, service, forwarded)
    assert r.status_code == 302
    location = r.headers["location"]
    assert location.startswith("/dashboard/login?next=")
    assert back_to in location.replace("%3D", "=")
    assert "signin=1" in location


def test_a_second_refusal_explains_instead_of_looping(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _as(monkeypatch, None)
    r = _ask(client, "grafana", "/grafana/?signin=1")
    assert r.status_code == 401
    assert "/dashboard/login" in r.text


def test_it_fails_closed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """The documentation gate lets a reader through when it cannot read the
    session; the monitoring tools are the system's insides and must not."""

    def broken(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("redis is down")

    monkeypatch.setattr(monitoring_authz, "get_current_session", broken)
    for service in monitoring_authz.SERVICES:
        assert _ask(client, service, "/").status_code == 503, service


def test_an_unknown_service_is_refused(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _as(monkeypatch, ADMIN)
    assert _ask(client, "postgres", "/").status_code == 403


def _caddy_block(caddy: str, opener: str) -> str:
    block = caddy[caddy.index(opener) :]
    return block[: block.index("\n    }\n")]


@pytest.mark.parametrize(
    ("service", "opener", "upstream"),
    [
        ("grafana", "handle /grafana/* {", "grafana:3000"),
        ("prometheus", "handle_path /prometheus/* {", "prometheus:9090"),
        ("jaeger", "handle /jaeger/* {", "jaeger:16686"),
        ("alertmanager", "handle_path /alertmanager/* {", "alertmanager:9093"),
    ],
)
def test_caddy_asks_the_gate_before_every_tool(service: str, opener: str, upstream: str) -> None:
    caddy = (REPO / "Caddyfile").read_text(encoding="utf-8")
    block = _caddy_block(caddy, opener)
    assert f"uri /internal/monitoring-authz?service={service}" in block
    assert block.index("forward_auth api:8000") < block.index(f"reverse_proxy {upstream}")
    assert "basic_auth" not in caddy, "the shared password is gone, not kept beside the gate"


def test_grafana_trusts_only_the_header_caddy_sets() -> None:
    caddy = (REPO / "Caddyfile").read_text(encoding="utf-8")
    block = _caddy_block(caddy, "handle /grafana/* {")
    copied = re.search(r"^\s*copy_headers (.+)$", block, re.MULTILINE)
    assert copied, "Caddy must set the login from the gate's answer"
    assert monitoring_authz.GRAFANA_USER_HEADER in copied.group(1).split()
    grafana = yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))["services"][
        "grafana"
    ]["environment"]
    assert grafana["GF_AUTH_PROXY_ENABLED"] == "true"
    assert grafana["GF_AUTH_PROXY_HEADER_NAME"] == monitoring_authz.GRAFANA_USER_HEADER


def test_the_gate_does_not_spend_the_reader_s_rate_limit() -> None:
    from app.middleware.rate_limit import _is_exempt_path

    assert _is_exempt_path("/internal/monitoring-authz")
