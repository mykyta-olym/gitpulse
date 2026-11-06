"""What the monitoring stack knows about GitPulse, for GitPulse's own pages.

Grafana, Prometheus, Jaeger and Alertmanager are admin tools behind Caddy
(api/monitoring_authz.py). This module reads Prometheus's HTTP API from inside
the stack (``PROMETHEUS_URL``) so the app can show the same numbers to the
people they matter to:

* the System page for admins: the key series of the Grafana dashboard, each linking to
  its panel, and every alert that is firing or pending;
* every page, every role: a shared service notice while an
  alert that affects the reader is firing (core health-monitor.js polls
  ``/api/v1/observability/status``).

The queries summarise the dashboard's metrics (monitoring/grafana/dashboards/
gitpulse.json); aggregate values link to their detailed series. Results are
cached for a few seconds per process: the status poll runs on every open page.
A Prometheus that is not configured or does not answer is reported as such,
never as "all clear".
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)

#: Grafana dashboard the series come from (its `uid`).
GRAFANA_DASHBOARD = "gitpulse-overview"
#: How long one answer from Prometheus is reused, per process.
CACHE_TTL_S = 20.0
#: An unreachable Prometheus must not hold a page render up.
TIMEOUT_S = 1.5


@dataclass(frozen=True)
class Series:
    """One number the pages show: a PromQL query and the Grafana panel it is from."""

    key: str
    label: str
    query: str
    unit: str  # "s" | "pct" | "rate" | "count"
    panel: int
    icon: str


#: In the order the System page lists them.
SERIES: tuple[Series, ...] = (
    Series(
        "http_rps",
        "Requests / s",
        "sum(rate(http_requests_total[5m]))",
        "rate",
        12,
        "activity",
    ),
    Series(
        "http_5xx",
        "Server errors",
        '100 * sum(rate(http_requests_total{status=~"5.."}[5m]))'
        " / clamp_min(sum(rate(http_requests_total[5m])), 1e-9)",
        "pct",
        12,
        "alert-circle",
    ),
    Series(
        "http_p95",
        "Response time p95",
        "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
        "s",
        13,
        "clock",
    ),
    Series(
        "webhooks",
        "Webhooks / min",
        "60 * sum(rate(webhook_events_received_total[5m]))",
        "rate",
        7,
        "zap",
    ),
    Series(
        "webhook_p95",
        "Webhook processing p95",
        "histogram_quantile(0.95, sum by (le)"
        " (rate(webhook_processing_duration_seconds_bucket[5m])))",
        "s",
        8,
        "clock",
    ),
    Series(
        "job_errors",
        "Job execution errors (1h)",
        "sum(increase(rq_job_failures_total[1h]))",
        "count",
        24,
        "alert-triangle",
    ),
    Series(
        "gitlab_p95",
        "GitLab API p95",
        "histogram_quantile(0.95, sum by (le) (rate(gitlab_api_duration_seconds_bucket[5m])))",
        "s",
        21,
        "gitlab",
    ),
)

#: What a reader is told while one of these alerts fires, and which roles are
#: told. A notice names what the reader will notice, not the alert.
NOTICES: tuple[tuple[str, frozenset[str], frozenset[str], str], ...] = (
    (
        "slow",
        frozenset(
            {
                "ApiDown",
                "HighHTTPLatency",
                "HighHTTPErrorRate",
                "DBPoolExhausted",
                "HighDBPoolOverflow",
            }
        ),
        frozenset({"student", "teacher", "admin"}),
        "GitPulse is responding slowly right now.",
    ),
    (
        "delay",
        frozenset(
            {
                "NoWebhooksReceived",
                "HighProcessingLatency",
                "HighFailureRate",
                "QueueStuck",
                "WorkerDown",
                "RQFailedJobsHigh",
                "MetricsComputeFailureRate",
                "EnrichmentFailureRate",
            }
        ),
        frozenset({"student", "teacher", "admin"}),
        "New GitLab activity is reaching GitPulse with a delay.",
    ),
    (
        "gitlab",
        frozenset({"GitLabAPILatencyHigh"}),
        frozenset({"teacher", "admin"}),
        "GitLab is answering slowly, so syncs take longer than usual.",
    ),
)


@dataclass
class Snapshot:
    """One read of Prometheus: the series' values and the active alerts."""

    configured: bool
    reachable: bool
    values: dict[str, float | None] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    taken_at: float = field(default_factory=time.monotonic)
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def firing(self) -> set[str]:
        return {a["name"] for a in self.alerts if a["state"] == "firing"}


_cache: Snapshot | None = None
_cache_base = ""
_lock = asyncio.Lock()


def format_value(value: float | None, unit: str) -> str:
    """The way every page writes a series' value."""
    if value is None:
        return "-"
    if unit == "s":
        return f"{value * 1000:.0f} ms" if value < 1 else f"{value:.1f} s"
    if unit == "pct":
        return f"{value:.1f} %"
    if unit == "rate":
        return f"{value:.1f}" if value >= 1 or value == 0 else f"{value:.2f}"
    return str(round(value))


def _number(result: list[dict[str, Any]]) -> float | None:
    """The scalar of an instant-vector answer; NaN (no data) reads as none."""
    if not result:
        return None
    try:
        value = float(result[0]["value"][1])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return None if math.isnan(value) or math.isinf(value) else value


def _data(resp: httpx.Response) -> dict[str, Any]:
    resp.raise_for_status()
    body = resp.json()
    if (
        not isinstance(body, dict)
        or body.get("status") != "success"
        or not isinstance(body.get("data"), dict)
    ):
        raise ValueError("Invalid Prometheus response")
    data: dict[str, Any] = body["data"]
    return data


async def _read(base: str) -> Snapshot:
    # One deadline includes connection setup, all queries and response parsing.
    # Monitoring must not turn a cold page render into a long wait.
    async with asyncio.timeout(TIMEOUT_S):
        async with httpx.AsyncClient(
            base_url=base.rstrip("/") + "/", timeout=TIMEOUT_S, trust_env=False
        ) as client:

            async def one(series: Series) -> tuple[str, float | None]:
                data = _data(await client.get("api/v1/query", params={"query": series.query}))
                if data.get("resultType") != "vector" or not isinstance(data.get("result"), list):
                    raise ValueError("Invalid instant vector")
                return series.key, _number(data["result"])

            async def active_alerts() -> list[dict[str, Any]]:
                data = _data(await client.get("api/v1/alerts"))
                found = data.get("alerts")
                if not isinstance(found, list) or any(not isinstance(a, dict) for a in found):
                    raise ValueError("Invalid alerts response")
                return found

            pairs, raw_alerts = await asyncio.gather(
                asyncio.gather(*(one(s) for s in SERIES)), active_alerts()
            )
    alerts = []
    for a in raw_alerts:
        labels, annotations = a.get("labels"), a.get("annotations")
        if (
            not isinstance(labels, dict)
            or not isinstance(annotations, dict)
            or a.get("state") not in {"pending", "firing"}
        ):
            raise ValueError("Invalid alert")
        alerts.append(
            {
                "name": str(labels.get("alertname", "?")),
                "severity": str(labels.get("severity", "warning")),
                "state": a["state"],
                "summary": str(annotations.get("summary", "")),
            }
        )
    alerts.sort(key=lambda a: (a["state"] != "firing", a["severity"] != "critical", a["name"]))
    return Snapshot(True, True, dict(pairs), alerts)


async def snapshot(*, force: bool = False) -> Snapshot:
    """Read only the existing monitoring stack; share a bounded result per process."""
    global _cache, _cache_base
    base = get_settings().prometheus_url
    if not base:
        return Snapshot(configured=False, reachable=False)
    async with _lock:
        if (
            not force
            and _cache is not None
            and _cache_base == base
            and time.monotonic() - _cache.taken_at < CACHE_TTL_S
        ):
            return _cache
        try:
            _cache = await _read(base)
        except (httpx.HTTPError, httpx.InvalidURL, ValueError, TimeoutError) as exc:
            logger.info("observability_prometheus_unreachable", error=str(exc)[:200])
            _cache = Snapshot(configured=True, reachable=False)
        _cache_base = base
        return _cache


def notices_for(snap: Snapshot, role: str) -> list[dict[str, str]]:
    """The notices a reader in `role` is shown while their alerts fire."""
    firing = snap.firing
    notices: list[dict[str, str]] = [
        {"key": key, "text": text}
        for key, alerts, roles, text in NOTICES
        if role in roles and firing & alerts
    ]
    known = frozenset().union(*(alerts for _, alerts, _, _ in NOTICES))
    if role == "admin" and firing - known:
        notices.append(
            {
                "key": "infrastructure",
                "text": "Monitoring reports an infrastructure issue.",
            }
        )
    if role == "admin":
        for item in notices:
            item["action_href"] = "/dashboard/admin/system"
            item["action_label"] = "Open System"
    return notices


def _series_state(key: str, raw: float | None) -> str:
    """Map a raw metric value to a stat_card semantic state."""
    if raw is None:
        return "empty"
    if key in ("http_5xx", "job_errors") and round(raw, 4) > 0:
        return "danger"
    return ""


def series_rows(snap: Snapshot, keys: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    """The series for a template: label, formatted value, icon, state and Grafana panel."""
    rows: list[dict[str, Any]] = []
    for s in SERIES:
        if keys is not None and s.key not in keys:
            continue
        raw = snap.values.get(s.key)
        rows.append(
            {
                "key": s.key,
                "label": s.label,
                "value": format_value(raw, s.unit),
                "icon": s.icon,
                "state": _series_state(s.key, raw),
                "panel": s.panel,
                "href": f"/grafana/d/{GRAFANA_DASHBOARD}?viewPanel={s.panel}",
            }
        )
    return rows
