"""What the application measures has to reach Prometheus, and add up there.

Measured on production on 2026-10-21, with the dashboard and the alerts looking
fine from the outside:

- six of the eighteen alert rules watched metrics that did not exist. The
  workers record them in a work-horse RQ forks per job, which exits with the
  values, and Prometheus scrapes only the API;
- the API runs as four uvicorn processes and a scrape reached one of them, so
  ``http_requests_total`` read 4195, 9956, 1487, 4196 on consecutive scrapes -
  5 808 counter resets in six hours, and every rate over it was noise;
- the connection pools could ask Postgres for 220 connections; it takes 100.
"""

from __future__ import annotations

import inspect
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

REPO = Path(__file__).resolve().parents[2]


class _FakeRedis:
    """Hashes, and a pipeline that applies its commands on execute()."""

    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, float]] = {}

    def pipeline(self, transaction: bool = True) -> _FakeRedis._Pipeline:
        return _FakeRedis._Pipeline(self)

    class _Pipeline:
        def __init__(self, redis: _FakeRedis) -> None:
            self._redis = redis
            self._ops: list[tuple[str, tuple[Any, ...]]] = []

        def hincrbyfloat(self, key: str, field: str, amount: float) -> None:
            self._ops.append(("hincrbyfloat", (key, field, amount)))

        def hgetall(self, key: str) -> None:
            self._ops.append(("hgetall", (key,)))

        def execute(self) -> list[Any]:
            out: list[Any] = []
            for op, args in self._ops:
                if op == "hincrbyfloat":
                    key, field, amount = args
                    h = self._redis.hashes.setdefault(key, {})
                    h[field] = h.get(field, 0.0) + amount
                    out.append(h[field])
                else:
                    stored = self._redis.hashes.get(args[0], {})
                    out.append({k.encode(): str(v).encode() for k, v in stored.items()})
            return out


@pytest.fixture
def redis(monkeypatch: pytest.MonkeyPatch) -> _FakeRedis:
    from app.observability import shared_metrics

    fake = _FakeRedis()
    monkeypatch.setattr(shared_metrics, "_redis", lambda: fake)
    return fake


def test_what_a_worker_counts_is_in_the_api_scrape(redis: _FakeRedis) -> None:
    from app.observability.metrics import (
        METRICS_COMPUTE_DURATION,
        WEBHOOK_PROCESSED,
        WEBHOOK_PROCESSING_DURATION,
        render_latest,
    )

    # As event_processor.py records them, in a process that is gone by the scrape.
    WEBHOOK_PROCESSED.labels(event_type="push", status="ok").inc()
    WEBHOOK_PROCESSED.labels(event_type="push", status="ok").inc()
    WEBHOOK_PROCESSED.labels(event_type="push", status="error").inc()
    WEBHOOK_PROCESSING_DURATION.labels(event_type="push").observe(0.3)
    WEBHOOK_PROCESSING_DURATION.labels(event_type="push").observe(4.0)
    METRICS_COMPUTE_DURATION.observe(2.0)

    text = render_latest().decode()

    assert 'webhook_events_processed_total{event_type="push",status="ok"} 2.0' in text
    assert 'webhook_events_processed_total{event_type="push",status="error"} 1.0' in text
    # Cumulative, as histogram_quantile reads them.
    assert 'webhook_processing_duration_seconds_bucket{event_type="push",le="0.25"} 0.0' in text
    assert 'webhook_processing_duration_seconds_bucket{event_type="push",le="0.5"} 1.0' in text
    assert 'webhook_processing_duration_seconds_bucket{event_type="push",le="5.0"} 2.0' in text
    assert 'webhook_processing_duration_seconds_bucket{event_type="push",le="+Inf"} 2.0' in text
    assert 'webhook_processing_duration_seconds_count{event_type="push"} 2.0' in text
    assert 'webhook_processing_duration_seconds_sum{event_type="push"} 4.3' in text
    assert 'metrics_compute_duration_seconds_bucket{le="2.5"} 1.0' in text


def test_rq_error_handler_exports_real_attempts_without_changing_retained_history(redis):
    from types import SimpleNamespace

    from app.observability.metrics import RQ_FAILED_JOBS, render_latest
    from app.workers.main import record_job_failure

    previous = RQ_FAILED_JOBS._value.get()
    try:
        RQ_FAILED_JOBS.set(86)
        job = SimpleNamespace(origin="default")
        assert record_job_failure(job, ValueError, ValueError("private payload"), None) is None
        record_job_failure(job, ValueError, ValueError("retry attempt"), None)
        record_job_failure(job, 1234, 9, object())  # RQ's unexpected work-horse death callback.
        text = render_latest().decode()
        assert 'rq_job_failures_total{queue_name="default"} 3.0' in text
        assert "rq_failed_jobs 86.0" in text
        assert "private payload" not in text
    finally:
        RQ_FAILED_JOBS.set(previous)


def test_a_metric_never_fails_the_job_that_records_it(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.observability import shared_metrics
    from app.observability.metrics import ENRICHMENT_TOTAL, render_latest

    def down() -> None:
        raise ConnectionError("redis is down")

    monkeypatch.setattr(shared_metrics, "_redis", down)
    ENRICHMENT_TOTAL.labels(entity_type="issue", status="ok").inc()  # does not raise
    text = render_latest()
    # The scrape still answers, with the API's own metrics.
    assert b"# HELP http_requests_total" in text
    assert b"enrichment_jobs_total{" not in text


def test_worker_entry_point_installs_both_rq_failure_callbacks(monkeypatch):
    from types import SimpleNamespace

    from app import redis_pool
    from app.workers import main

    created = {}

    def worker(queues, **kwargs):
        created.update(kwargs)
        assert queues == ["high", "default", "low"]
        return SimpleNamespace(work=lambda **kwargs: None)

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(
            log_level="info",
            log_format="json",
            otlp_endpoint="",
            redis_url="redis://unused",
            is_development=False,
        ),
    )
    monkeypatch.setenv("FLUSH_QUEUES_ON_START", "")
    monkeypatch.setattr(main, "setup_logging", lambda **kwargs: None)
    monkeypatch.setattr(main, "setup_tracing", lambda **kwargs: None)
    monkeypatch.setattr(main, "_connect_redis", lambda *args: object())
    monkeypatch.setattr(redis_pool, "init_redis_pool", lambda *args: None)
    monkeypatch.setattr(main, "Queue", lambda name, **kwargs: name)
    monkeypatch.setattr(main, "Worker", worker)
    monkeypatch.setattr(main, "SimpleWorker", worker)
    main.main()
    assert created["exception_handlers"] == [main.record_job_failure]
    assert created["work_horse_killed_handler"] is main.record_job_failure


def test_a_label_the_metric_does_not_take_is_a_programming_error(redis: _FakeRedis) -> None:
    from app.observability.metrics import WEBHOOK_PROCESSED

    with pytest.raises(ValueError, match="takes labels"):
        WEBHOOK_PROCESSED.labels(event_type="push").inc()


@pytest.mark.parametrize(
    ("metric_name", "alert_name", "labels"),
    [
        ("HTTP_REQUEST_DURATION", "HighHTTPLatency", {"method": "GET", "path": "/slow"}),
        ("WEBHOOK_PROCESSING_DURATION", "HighProcessingLatency", {"event_type": "push"}),
        ("GITLAB_API_DURATION", "GitLabAPILatencyHigh", {"endpoint": "projects"}),
    ],
)
def test_latency_buckets_can_represent_the_alert_threshold(
    redis: _FakeRedis, metric_name: str, alert_name: str, labels: dict[str, str]
) -> None:
    from prometheus_client.parser import text_string_to_metric_families

    from app.observability import metrics

    rules = yaml.safe_load((REPO / "monitoring/prometheus/alerts.yml").read_text())
    alert = next(r for group in rules["groups"] for r in group["rules"] if r["alert"] == alert_name)
    threshold = float(alert["expr"].rsplit(">", 1)[1])
    metric = getattr(metrics, metric_name)
    metric.labels(**labels).observe(30)
    family = next(
        f
        for f in text_string_to_metric_families(metrics.render_latest().decode())
        if f.name == metric._name
    )
    buckets = {float(s.labels["le"]): s.value for s in family.samples if s.name.endswith("_bucket")}
    finite = {bound: count for bound, count in buckets.items() if bound != float("inf")}
    # Prometheus clips a quantile in +Inf to the last finite bound. A bound
    # at or below the alert threshold makes that alert impossible to fire.
    assert max(finite) > threshold
    assert threshold in finite
    assert finite[30.0] >= 1


def _python(code: str, env: dict[str, str]) -> str:
    return subprocess.run(  # noqa: S603 - this interpreter on fixed code
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout


def test_the_counts_of_every_api_process_add_up(tmp_path: Path) -> None:
    """Four processes, one scrape: the answer is their sum, not one of them."""
    env = {
        **os.environ,
        "PROMETHEUS_MULTIPROC_DIR": str(tmp_path / "prometheus"),
        "PYTHONPATH": str(REPO / "src"),
    }
    record = (
        "from app.observability.metrics import HTTP_REQUESTS, RQ_QUEUE_DEPTH\n"
        "HTTP_REQUESTS.labels(method='GET', path='/dashboard', status='200').inc({n})\n"
        "RQ_QUEUE_DEPTH.labels(queue_name='default').set({n})\n"
    )
    for n in (3, 4):  # two processes, one after the other
        _python(record.format(n=n), env)

    text = _python(
        "import sys\nfrom app.observability.metrics import render_latest\n"
        "sys.stdout.write(render_latest().decode())",
        env,
    )

    assert 'http_requests_total{method="GET",path="/dashboard",status="200"} 7.0' in text
    # A gauge set from Redis at scrape time: the latest value, not a sum.
    assert 'rq_queue_depth{queue_name="default"} 4.0' in text
    if sys.platform.startswith("linux"):  # read from /proc
        assert "process_start_time_seconds" in text, "the API Uptime panel reads it"


def _sample(name: str, labels: dict[str, str]) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_a_request_is_labelled_by_the_route_it_matched(tmp_path: Path) -> None:
    from app.middleware.logging import RequestLoggingMiddleware

    (tmp_path / "core.bundle.8eb50949.js").write_text("x")
    app = FastAPI()

    @app.get("/probe-courses/{course_id}")
    async def course(course_id: str) -> dict[str, str]:
        return {}

    @app.get("/probe-stream")
    async def stream() -> StreamingResponse:
        async def events() -> Any:
            yield "data: hi\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    app.mount("/probe-static", StaticFiles(directory=tmp_path), name="probe-static")
    app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(app)

    def count(path: str, status: str = "200") -> float:
        return _sample("http_requests_total", {"method": "GET", "path": path, "status": status})

    def timed(path: str) -> float:
        return _sample("http_request_duration_seconds_count", {"method": "GET", "path": path})

    before = {p: count(p) for p in ("/probe-courses/{course_id}", "/probe-static")}
    unmatched = count("<unmatched>", "404")
    streams, streams_timed = count("/probe-stream"), timed("/probe-stream")

    client.get("/probe-courses/550e8400-e29b-41d4-a716-446655440000")
    client.get("/probe-courses/abc")
    client.get("/probe-static/core.bundle.8eb50949.js")
    client.get("/wp-login.php")
    client.get("/probe-stream")

    # The template, so an id, a release's hashed bundle or a scanner's guess
    # is never a series of its own.
    assert count("/probe-courses/{course_id}") == before["/probe-courses/{course_id}"] + 2
    assert count("/probe-static") == before["/probe-static"] + 1
    assert count("<unmatched>", "404") == unmatched + 1
    assert (
        _sample("http_requests_total", {"method": "GET", "path": "/wp-login.php", "status": "404"})
        == 0
    )
    # A stream is counted, but its open-tab hours are not a response time.
    assert count("/probe-stream") == streams + 1
    assert timed("/probe-stream") == streams_timed


def _compose() -> dict[str, Any]:
    return yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))


def _api_processes() -> int:
    dockerfile = (REPO / "Dockerfile").read_text(encoding="utf-8")
    found = re.search(r'"--workers",\s*"(\d+)"', dockerfile)
    assert found, "the Dockerfile no longer says how many API processes run"
    return int(found.group(1))


def test_the_connection_pools_fit_what_postgres_accepts() -> None:
    """The 101st connection is refused outright, not queued: a burst of pages
    then answers 500 where a smaller pool would have made it wait."""
    from app.config import Settings
    from app.db.session import init_engine

    compose = _compose()
    postgres = " ".join(str(part) for part in compose["services"]["postgres"].get("command", []))
    assert "max_connections" not in postgres, "update the budget below to the new limit"
    max_connections = 100  # Postgres' default
    reserve = 20  # a migration run, postgres-exporter, a psql, the superuser slots

    api = (
        Settings.model_fields["db_pool_size"].default
        + Settings.model_fields["db_max_overflow"].default
    )
    params = inspect.signature(init_engine).parameters
    worker = params["pool_size"].default + params["max_overflow"].default
    replicas = compose["services"]["worker"]["deploy"]["replicas"]

    total = _api_processes() * api + replicas * worker
    assert total <= max_connections - reserve, (
        f"the pools can ask for {total} connections; Postgres takes {max_connections}"
    )


def _megabytes(value: str) -> float:
    found = re.fullmatch(r"(\d+)\s*([a-zA-Z]+)", value.strip())
    assert found, f"not a size: {value}"
    number, unit = found.groups()
    return float(number) * {"mb": 1, "m": 1, "gb": 1024, "g": 1024}[unit.lower()]


def test_redis_evicts_before_the_kernel_kills_it() -> None:
    redis = _compose()["services"]["redis"]
    command = " ".join(redis["command"])
    maxmemory = re.search(r"--maxmemory (\S+)", command)
    assert maxmemory, "Redis has no maxmemory, so allkeys-lru never evicts"
    limit = redis["deploy"]["resources"]["limits"]["memory"]
    assert _megabytes(maxmemory.group(1)) < _megabytes(limit) * 0.9, (
        f"maxmemory {maxmemory.group(1)} is not under the container's {limit}"
    )


def test_jaeger_keeps_a_bounded_number_of_traces() -> None:
    """Unbounded, the in-memory store filled its 512M every day and a half and
    the kernel killed it - with every trace in it."""
    jaeger = _compose()["services"]["jaeger"]
    assert 0 < int(jaeger["environment"]["MEMORY_MAX_TRACES"]) <= 10000
    assert _megabytes(jaeger["environment"]["GOMEMLIMIT"].replace("MiB", "m")) < (
        _megabytes(jaeger["deploy"]["resources"]["limits"]["memory"]) * 0.9
    )


def test_the_api_adds_up_its_processes_metrics() -> None:
    api = _compose()["services"]["api"]
    directory = api["environment"]["PROMETHEUS_MULTIPROC_DIR"]
    # Emptied by every container start, so no dead process's file outlives it.
    assert any(directory.startswith(mount.split(":")[0]) for mount in api["tmpfs"])
