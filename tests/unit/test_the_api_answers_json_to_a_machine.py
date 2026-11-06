"""A JSON API error stays JSON, whatever the caller says it accepts.

The error boundary rewrote every 4xx from a POST without `Accept: application/json`
into an HTML error page - the rule meant for a browser's plain form submit.
GitLab's webhook deliveries send no Accept header, so the 422 the receiver
describes ("Payload is not a GitLab webhook (bad or missing: project.id)")
reached GitLab's delivery log as a `<!DOCTYPE html>` document, and the same
happened to every script talking to `/api/v1` with curl.

A `project: null` payload was a separate 500 (`{}.get` on None after the
schema had admitted the null) - GitLab retries a 5xx for 24 hours.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api import webhooks
from app.dependencies import DbSession
from app.middleware.error_boundary import ErrorBoundaryMiddleware, _wants_html


def _app() -> TestClient:
    app = FastAPI()

    @app.post("/api/v1/webhooks/gitlab")
    async def receiver() -> JSONResponse:
        return JSONResponse({"detail": "bad or missing: project.id"}, status_code=422)

    @app.post("/dashboard/courses/x/settings")
    async def form() -> JSONResponse:
        return JSONResponse({"detail": "nope"}, status_code=422)

    app.add_middleware(ErrorBoundaryMiddleware)
    return TestClient(app)


def test_a_webhook_rejection_reaches_gitlab_as_json() -> None:
    resp = _app().post("/api/v1/webhooks/gitlab", json=[], headers={})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/json")
    assert resp.json()["detail"] == "bad or missing: project.id"


def test_a_plain_form_post_still_gets_the_page() -> None:
    resp = _app().post("/dashboard/courses/x/settings", data={"a": "b"}, headers={"Accept": ""})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("text/html")


def test_the_rule_itself() -> None:
    def req(path: str, method: str = "POST", accept: str | None = None) -> Request:
        headers = [(b"accept", accept.encode())] if accept is not None else []
        return Request(
            {
                "type": "http",
                "method": method,
                "path": path,
                "headers": headers,
                "query_string": b"",
            }
        )

    assert _wants_html(req("/api/v1/courses/")) is False
    assert _wants_html(req("/api/v1/courses/", accept="text/html")) is False
    assert _wants_html(req("/dashboard/x")) is True
    assert _wants_html(req("/dashboard/x", accept="application/json")) is False


def test_a_null_project_is_a_422_not_a_crash() -> None:
    app = FastAPI()
    app.include_router(webhooks.router, prefix="/api/v1/webhooks")
    app.dependency_overrides[DbSession.__metadata__[0].dependency] = lambda: object()
    app.add_middleware(ErrorBoundaryMiddleware)
    resp = TestClient(app).post(
        "/api/v1/webhooks/gitlab",
        json={"object_kind": "push", "project": None},
        headers={"X-Gitlab-Token": "x"},
    )
    assert resp.status_code == 422
    assert "project.id" in resp.json()["detail"]
