"""Unit tests for the SEC-03 ``/csp/report`` violation receiver."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
import structlog
from fastapi import FastAPI
from starlette.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from app.api.csp_report import csp_report_router

    app = FastAPI()
    app.include_router(csp_report_router)
    return TestClient(app)


@pytest.fixture
def captured_logs() -> list[dict[str, Any]]:
    """Capture structlog events into a list - mirrors structlog test-helpers."""
    events: list[dict[str, Any]] = []

    def _capture(logger: object, name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        events.append({"level": name, **event_dict})
        return event_dict

    structlog.configure(
        processors=[_capture, structlog.dev.ConsoleRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        cache_logger_on_first_use=False,
    )
    yield events
    # Reset structlog so other tests are not affected by our processor stack.
    structlog.reset_defaults()


def test_legacy_csp_report_logs_violation(
    client: TestClient, captured_logs: list[dict[str, Any]]
) -> None:
    payload = {
        "csp-report": {
            "document-uri": "https://app.example/dashboard/courses",
            "violated-directive": "script-src",
            "blocked-uri": "inline",
            "source-file": "https://app.example/dashboard/courses",
            "line-number": 42,
            "disposition": "report",
        }
    }
    resp = client.post(
        "/csp/report",
        content=json.dumps(payload),
        headers={"content-type": "application/csp-report"},
    )
    assert resp.status_code == 204
    assert any(e.get("event") == "csp_violation" for e in captured_logs)
    violation = next(e for e in captured_logs if e.get("event") == "csp_violation")
    assert violation.get("violated_directive") == "script-src"
    assert violation.get("blocked_uri") == "inline"


def test_modern_reports_json_array(client: TestClient, captured_logs: list[dict[str, Any]]) -> None:
    payload = [
        {
            "type": "csp-violation",
            "body": {
                "documentURL": "https://app.example/login",
                "effectiveDirective": "script-src-elem",
                "blockedURL": "eval",
                "sourceFile": "https://app.example/static/app.js",
                "lineNumber": 7,
                "disposition": "report",
            },
        }
    ]
    resp = client.post(
        "/csp/report",
        content=json.dumps(payload),
        headers={"content-type": "application/reports+json"},
    )
    assert resp.status_code == 204
    violation = next(e for e in captured_logs if e.get("event") == "csp_violation")
    assert violation.get("violated_directive") == "script-src-elem"
    assert violation.get("blocked_uri") == "eval"


def test_malformed_json_returns_204(client: TestClient) -> None:
    resp = client.post(
        "/csp/report",
        content="not json at all",
        headers={"content-type": "application/csp-report"},
    )
    assert resp.status_code == 204


def test_oversized_body_dropped(client: TestClient) -> None:
    huge = "A" * (32 * 1024)
    resp = client.post(
        "/csp/report",
        content=huge,
        headers={"content-type": "application/csp-report"},
    )
    assert resp.status_code == 204


def test_dedup_suppresses_immediate_repeats(
    client: TestClient, captured_logs: list[dict[str, Any]]
) -> None:
    """Repeated identical violations within the dedupe window log only once."""
    # Reset the in-process dedupe cache so the test is hermetic.
    from app.api import csp_report as module

    with patch.object(module, "_dedupe", module._DedupeCache(64, 60.0)):
        payload = {
            "csp-report": {
                "document-uri": "https://app.example/x",
                "violated-directive": "img-src",
                "blocked-uri": "https://evil.example/pixel.gif",
                "source-file": "https://app.example/x",
                "line-number": 1,
            }
        }
        for _ in range(5):
            resp = client.post(
                "/csp/report",
                content=json.dumps(payload),
                headers={"content-type": "application/csp-report"},
            )
            assert resp.status_code == 204

    violations = [e for e in captured_logs if e.get("event") == "csp_violation"]
    assert len(violations) == 1, f"Expected exactly one logged violation, got {len(violations)}"


def test_empty_body_returns_204(client: TestClient) -> None:
    resp = client.post("/csp/report", content="")
    assert resp.status_code == 204
