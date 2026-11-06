# 13 - Observability

> **Documentation Status (2026-10-30):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


## In-app service status and monitoring

Set `PROMETHEUS_URL=http://prometheus:9090` to connect the application to the
Prometheus stack. An empty value disables the Prometheus poll while keeping
basic health probes active. This is a deployment setting, separate from
teacher-controlled course checks, LLM analysis and the classroom assistant.

`/dashboard/admin/system` renders both `#systemHealth` (`partials/admin/_system_health.html`,
refreshed via `GET /dashboard/api/v1/admin/system/health`) and `#systemMonitoring`
(`partials/admin/_system_monitoring.html`, refreshed via
`GET /dashboard/api/v1/admin/system/monitoring`) on the initial server frame for
administrators. It surfaces component probes, metric summaries, firing and
pending alerts, and links to the protected `/grafana/`, `/prometheus/`,
`/jaeger/` and `/alertmanager/` routes (admin-only).

The shared health monitor (`health-monitor.js`) polls `/api/v1/observability/status`
alongside the GitLab connectivity check while the page is visible. When an alert
affects the signed-in reader's role, `#serviceNoticeBanner` renders a role-safe
`.gp-top-banner` notice at the top of the page (with a direct `Open System`
action link for administrators, and suppressed on `/dashboard/admin/system`
where `#systemMonitoring` is already visible). Students and teachers receive
only allowlisted service-impact notices, never worker details or logs. The
offline, backend, and GitLab connectivity banners retain their independent
meaning; a monitoring failure cannot report a GitLab outage or recovery.

Prometheus results are cached for 20 seconds per API process with a single
in-flight read. All concurrent HTTP queries share a 1.5-second deadline. Missing,
invalid or unavailable monitoring is shown as unknown, with no synthetic zeroes.
Aggregate rates/latencies link to the detailed Grafana series; no user clicks,
page visits or estimated teacher time savings are collected.

Reference: [Prometheus HTTP API](https://prometheus.io/docs/prometheus/latest/querying/api/).

Duration histogram finite bounds must extend above each alert threshold:
Prometheus clips a quantile in `+Inf` to the highest finite bound. HTTP,
webhook and GitLab API durations now extend to 60 seconds, including the
5/10/15-second alert boundaries. See [histogram_quantile](https://prometheus.io/docs/prometheus/latest/querying/functions/#histogram_quantile).

When upgrading shared histogram bounds, reset only the affected operational
hashes after every API/worker writer has upgraded:
`gitpulse:metrics:webhook_processing_duration_seconds` and
`gitpulse:metrics:gitlab_api_duration_seconds`. Keep the other counters and
application data. Prometheus retains its historical series and handles the
counter reset; latency rates need fresh observations in the query window.

## Architecture

```
+----------+    /metrics     +------------+    scrape    +------------+
|   API    |<----------------| Prometheus |<-------------|  Grafana   |
|  :8000   |                 |   :9090    |              |   :3000    |
+----+-----+                 +------------+              +------------+
     | OTLP gRPC (:4317)
     v
+----------+
|  Jaeger  |  <- distributed traces
|  :16686  |
+----------+
```

All three pillars-**metrics**, **traces**, **logs**-share a `correlation_id` (per-request UUID) for cross-referencing.

## Middleware Stack (Request Pipeline)

All HTTP requests pass through a middleware chain (last added = first executed):

| # | Middleware | Module | Purpose |
|---|-----------|--------|---------|
| 1 | `RequestLoggingMiddleware` | `middleware/logging.py` | Structured JSON logs with timing, method, path, status |
| 2 | `SecurityHeadersMiddleware` | `middleware/security.py` | CSP, HSTS, `X-App-Version`, `X-Frame-Options`, cache control |
| 3 | `RateLimitMiddleware` | `middleware/rate_limit.py` | Per-IP sliding window (10-60 req/min by endpoint) |
| 4 | `StaticCacheMiddleware` | `middleware/performance.py` | Immutable one-year cache for `/static/*?v=<hex-hash>`; short cache for unversioned/manual `/static/*` |
| 5 | `CorrelationIdMiddleware` | `middleware/correlation.py` | Generates/propagates `X-Correlation-ID` UUID per request |
| 6 | `LocaleMiddleware` | `middleware/locale.py` | Resolves locale, sets `Content-Language`, persists `gp_lang` cookie |
| 7 | `GZipMiddleware` | Starlette built-in | Response compression (min 500 bytes) |
| 8 | `ErrorBoundaryMiddleware` | `middleware/error_boundary.py` | Catches unhandled exceptions -> JSON 500 or HTML error page |
| 9 | `CORSMiddleware` | FastAPI built-in | Cross-origin resource sharing |
| 10 | `TrustedHostMiddleware` | FastAPI built-in | Rejects unexpected `Host` headers |
| 11 | `ProxyHeadersMiddleware` | Uvicorn | Trusts `X-Forwarded-For`/`X-Forwarded-Proto` from Caddy |

## Response Headers

Every HTTP response includes these security and observability headers:

| Header | Value | Source |
|--------|-------|--------|
| `X-Correlation-ID` | UUID v4 | `CorrelationIdMiddleware` |
| `X-App-Version` | 12-char `BUILD_HASH` | `SecurityHeadersMiddleware` |
| `X-Content-Type-Options` | `nosniff` | `SecurityHeadersMiddleware` |
| `X-Frame-Options` | `DENY` | `SecurityHeadersMiddleware` |
| `Content-Security-Policy` | Dynamic (see section 12) | `SecurityHeadersMiddleware` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | `SecurityHeadersMiddleware` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | `SecurityHeadersMiddleware` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | `SecurityHeadersMiddleware` |
| `Content-Language` | `sk` or `en` | `LocaleMiddleware` |
| `Cache-Control` | `no-store, no-cache, must-revalidate, private` | On `/dashboard/*` paths |
| `Cache-Control` | `public, max-age=31536000, immutable` | On versioned `/static/*?v=<hex-hash>` assets |
| `Cache-Control` | `public, max-age=300` | On direct unversioned or invalid-version `/static/*` assets |
| `Clear-Site-Data` | `"cache", "storage"` | On `GET /dashboard/logout` only |

The Service Worker follows the same ownership rule: static assets are cached
cache-first, but `/dashboard` navigations are bypassed and any response marked
`no-store` or `private` is not written to the browser Cache API.

The standalone browser 429 page emitted by `RateLimitMiddleware` cannot use the
Jinja `static_url()` helper because it is generated before template rendering;
it therefore appends the deploy `BUILD_HASH` as the static asset `?v=` token for
its favicon, stylesheet, and illustration.

## Enabling

```bash
docker compose --profile monitoring up -d
```

This starts Prometheus (`:9090`), Jaeger (`:16686`), and Grafana (`:3000`).

## Metrics (Prometheus)

Exposed at `GET /metrics` by the API server.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `webhook_events_received_total` | Counter | - | Webhooks received |
| `webhook_events_processed_total` | Counter | `status` | Webhooks processed (ok/error) |
| `webhook_processing_duration_seconds` | Histogram | - | End-to-end processing time |
| `gitlab_api_requests_total` | Counter | `endpoint`, `status` | GitLab API calls |
| `gitlab_api_duration_seconds` | Histogram | `endpoint` | GitLab API latency |
| `metrics_compute_total` | Counter | `status` | Compliance metric computations |
| `metrics_compute_duration_seconds` | Histogram | - | Compliance compute time |
| `http_requests_total` | Counter | `method`, `status`, `path` | HTTP requests |
| `rq_queue_depth` | Gauge | `queue` | Jobs waiting per queue |
| `rq_workers_active` | Gauge | - | Active RQ workers |
| `db_pool_size` | Gauge | - | SQLAlchemy pool size |
| `db_pool_checked_out` | Gauge | - | Connections in use |
| `session_store_fallback_total` | Counter | `reason` | Redis session-store create fallbacks to signed stateless cookies |
| `page_cache_hits_total` | Counter | `kind` | HTMX page-fragment cache hits (per template kind) |
| `page_cache_misses_total` | Counter | `kind` | HTMX page-fragment cache misses (per template kind) |
| `page_cache_invalidations_total` | Counter | `kind` | HTMX page-fragment cache keys evicted by writes / cascades |

## Traces (OpenTelemetry -> Jaeger)

Auto-instrumented: FastAPI, SQLAlchemy, httpx, Redis.

Manual spans added for worker jobs:
- `process_event` - webhook event processing (attributes: `event_id`, `object_kind`, `project_id`, `correlation_id`)
- `compute_metrics` - compliance metric recomputation (`team_id`)
- `sweep_unprocessed` - sweep stale events

Set `OTLP_ENDPOINT=http://jaeger:4317` to enable trace export.

## Logs (structlog -> JSON)

Every log line is a JSON object:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "logger": "app.workers.event_processor",
  "event": "Event processed",
  "service": "gitpulse",
  "correlation_id": "abc-123",
  "trace_id": "0af7651916cd43dd...",
  "span_id": "b7ad6b7169203331"
}
```

**Secret redaction**: Values for keys matching `password`, `token`, `secret`, `api_key`, `authorization`, `gitlab_token`, etc. are replaced with `***REDACTED***`.

Configure via env:
- `LOG_LEVEL` - `debug` | `info` | `warning` | `error`
- `LOG_FORMAT` - `json` (production) | `console` (development, coloured)

## Grafana Dashboard

Access at `http://localhost:3000` (default credentials: `admin` / value of `GRAFANA_ADMIN_PASSWORD` or `admin`).

The provisioned dashboard **GitPulse** includes:
1. Webhook rate (received vs processed per minute)
2. Processing latency (p50/p95/p99)
3. RQ queue depth by queue
4. Job success/failure rate
5. DB pool utilization (gauge)
6. HTTP request rate by status
7. GitLab API latency (p50/p95)
8. Report generation time (p95)
9. Active workers (stat)
10. Metrics compute duration (p95)

## Alert Rules

Defined in `monitoring/prometheus/alerts.yml`, loaded by Prometheus.

| Alert | Condition | Severity |
|-------|-----------|----------|
| QueueStuck | `rq_queue_depth > 50` for 5m | warning |
| HighFailureRate | error rate > 0.1/s for 5m | critical |
| ApiDown | target down for 1m | critical |
| HighProcessingLatency | p95 > 10s for 5m | warning |
| WorkerDown | 0 active workers for 2m | critical |
| DBPoolExhausted | checked_out >= pool_size for 5m | warning |
| HighHTTPErrorRate | 5xx rate > 5% for 5m | warning |

## Troubleshooting

**No metrics at `/metrics`**
- Ensure the API is running and healthy: `curl http://localhost:8000/health/live`

**No traces in Jaeger**
- Verify `OTLP_ENDPOINT` is set and Jaeger is reachable on port 4317

**Grafana shows "No data"**
- Check Prometheus targets at `http://localhost:9090/targets` - the `gitpulse-api` job should be UP
- Verify the Prometheus datasource in Grafana points to `http://prometheus:9090`

**Alert not firing**
- Check `http://localhost:9090/alerts` for rule evaluation status
- Verify `rule_files` in `prometheus.yml` points to `/etc/prometheus/alerts.yml`

## Client-Side Health Resilience

The frontend includes a **health monitor** (`health-monitor.js`) that polls
`GET /health` every 30 s when healthy (10 s degraded, 3 s down). When the backend becomes unreachable (3 consecutive
failures with 5 s timeout each), it dispatches a `gp-health-change` CustomEvent
with `detail.current === 'down'`.

### SSE & Polling Pause/Resume

Every page-level SSE stream and polling loop listens for `gp-health-change` and
reacts as follows:

| Phase | Action |
|-------|--------|
| **Health -> down** | All `EventSource` instances are `.close()`'d, all `setInterval` polls are cleared, guard flag set |
| **Health -> ok** | Error counters reset, SSE reconnected, polling restarted (if SSE unavailable) |

This prevents the browser from flooding the console with `ERR_CONNECTION_REFUSED`
errors during backend downtime and eliminates unnecessary network traffic.

**Files with health-aware SSE/polling:**

| Module | SSE Variable | Polling |
|--------|-------------|--------|
| `sidebar.js` | `_badgeSSE` | `_badgePollTimer` |
| `_parts/global-job-bar/*` | per-job `sseSource` | per-job `pollTimerId` |
| `sse-stream.js` | `source` (job streams) | manual `setTimeout` chain |
| `pages/team-detail.js` | `_teamSSE` | `_autoRefreshTimer` |
| `pages/dashboard.js` | `_dashSSE` | `_dashPollTimer` |
| `pages/project-detail.js` | `_projSSE` | `_projPollTimer` |
| `pages/course-detail.js` | `_sseSource` + `_courseSSE` | `_courseAutoRefresh` |
| `pages/course-settings.js` | `_settingsSSE` | - |
| `pages/course-activity.js` | `_sse` | `_pollTimer` |
| `pages/course-analytics.js` | `_sseSource` | `_pollTimer` |
| `pages/student-detail.js` | `_sdSSE` | - |
| `pages/admin-events.js` | `_dlqSSE` | - |

### Global Job Bar Behaviour

When health goes down, `_parts/global-job-bar/20-listeners-api.js` additionally:
- Adds CSS class `gjb-health-down` (amber progress bar, paused spinner)
- Appends " - connection lost" to each running job's message
- Stops all job pollers

On recovery: original messages are restored, pollers restart, CSS class removed.

### Health Monitor Public API

```javascript
GP.health.getState()   // { status: 'ok'|'degraded'|'down', ... }
GP.health.check()      // Force an immediate health check
GP.health.isDown       // Boolean - true when status === 'down'
```

The `isDown` getter is also checked within `sse-stream.js` `onerror` handlers to
avoid automatic SSE reconnection when the backend is known to be unreachable.

## Rollback

To disable monitoring services:

```bash
docker compose --profile monitoring down
```

Code changes (metric instrumentation, OTel spans, secret redaction) are passive - they emit data but don't affect application behaviour. Reverting the code changes simply stops metric emission.
