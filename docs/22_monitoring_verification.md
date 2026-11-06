# 22 - Monitoring Verification Guide

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (observability):** `monitoring/*`, `src/app/observability/*`, `src/app/api/health.py`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.

Production-readiness checklist for the observability stack (Prometheus + Grafana + Jaeger).

## 1. Starting the Monitoring Stack

```bash
docker compose --profile monitoring up -d
```

This starts three services alongside the core stack:

| Service    | Port   | URL                       |
|------------|--------|---------------------------|
| Prometheus | 9090   | http://localhost:9090      |
| Grafana    | 3000   | http://localhost:3000      |
| Jaeger     | 16686  | http://localhost:16686     |

All ports are bound to `127.0.0.1` - use SSH tunneling for remote servers:

```bash
ssh -L 9090:localhost:9090 -L 3000:localhost:3000 -L 16686:localhost:16686 user@server
```

## 2. Prometheus Verification

### 2.1 Targets

Open **Status -> Targets** (`http://localhost:9090/targets`).

- [ ] `gitpulse-api` target shows **UP** with last scrape < 30s ago
- [ ] Endpoint is `api:8000/metrics`

### 2.2 Key Metrics

Run these queries in the **Graph** tab (`http://localhost:9090/graph`):

| Query | Expected |
|-------|----------|
| `up{job="gitpulse-api"}` | `1` |
| `webhook_events_received_total` | Counter ≥ 0 |
| `webhook_events_processed_total` | Counter with `status` label |
| `rq_queue_depth` | Gauge per queue |
| `rq_workers_active` | Gauge ≥ 1 |
| `http_requests_total` | Counter with `method`, `status`, `path` |
| `db_pool_size` | Pool size (default 20) |
| `db_pool_checked_out` | Active connections |

### 2.3 Alerts

Open **Status -> Rules** (`http://localhost:9090/rules`).

- [ ] `QueueStuck` - fires when `rq_queue_depth > 50` for 5m
- [ ] `HighFailureRate` - fires when error rate > 0.1/s for 3m
- [ ] `ApiDown` - fires when API target is down for 1m
- [ ] `HighProcessingLatency` - fires when p95 > 10s for 5m
- [ ] `WorkerDown` - fires when `rq_workers_active == 0` for 2m
- [ ] `DBPoolExhausted` - fires when pool usage > 90% for 3m

Trigger a test: stop the worker container and wait 2m - `WorkerDown` should fire.

## 3. Grafana Verification

### 3.1 Login

Open `http://localhost:3000`. Default credentials: `admin` / value of `GRAFANA_ADMIN_PASSWORD` env var (default: `admin`).

**Change the admin password on first login for production.**

### 3.2 Data Source

Open **Connections -> Data sources**.

- [ ] `Prometheus` data source exists
- [ ] URL points to `http://prometheus:9090`
- [ ] **Test** button returns "Data source is working"

### 3.3 Dashboard Panels

Open **Dashboards -> GitPulse**.

The pre-provisioned dashboard (`monitoring/grafana/dashboards/gitpulse.json`) includes:

| Panel | Type | Verifies |
|-------|------|----------|
| Webhook Rate | Time series | `webhook_events_received_total`, `webhook_events_processed_total` |
| Processing Latency | Time series | p50/p95/p99 of `webhook_processing_duration_seconds` |
| RQ Queue Depth | Time series | `rq_queue_depth` per queue |
| Active Workers | Stat | `rq_workers_active` |
| HTTP Requests | Time series | `http_requests_total` by status code |
| DB Pool Usage | Gauge | `db_pool_checked_out / db_pool_size` |

- [ ] All panels show data (not "No data")
- [ ] After triggering a sync or webhook, the Webhook Rate panel updates within 30s

### 3.4 Generating Test Traffic

To populate the dashboard with data:

```bash
# Trigger a course sync (generates webhooks + worker activity)
curl -X POST http://localhost:8000/api/v1/courses/{course_id}/sync \
  -H "Cookie: session=..."

# Or run the load test script
python scripts/load_test_scale.py --courses 1 --teams 5
```

## 4. Jaeger Verification

### 4.1 Traces

Open `http://localhost:16686`.

- [ ] Service dropdown shows `gitpulse`
- [ ] Select the service and click **Find Traces**
- [ ] Traces appear with spans for HTTP requests, DB queries, GitLab API calls

### 4.2 Correlation

Each trace carries a `correlation_id` that matches the API logs. To verify:

1. Find a trace in Jaeger - note the `correlation_id` tag
2. Search the API logs: `docker compose logs api | grep <correlation_id>`
3. The log entries should match the trace spans

## 5. Health Endpoint & Client-Side Resilience

The API exposes `GET /health` for uptime monitoring.

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

- [ ] Returns `200` with `status: "ok"`
- [ ] Includes component statuses (database, redis, worker)
- [ ] Response time < 1s under normal load

### Frontend Health Monitor

The client-side health monitor (`health-monitor.js`) polls `/health` every ~10 s
and dispatches a `gp-health-change` event on status transitions.

**Thresholds:**
- `FAIL_THRESHOLD`: 3 consecutive failures -> status `down`
- `CHECK_TIMEOUT_MS`: 5000 ms per check

**Verification steps:**

1. Stop the API container: `docker compose stop api`
2. Wait ~30 s - the frontend should show the **"System unreachable"** banner
3. [ ] All SSE `EventSource` connections are closed (no `ERR_CONNECTION_REFUSED` in console)
4. [ ] All polling intervals are paused
5. [ ] Global job bar shows amber progress bars with "- connection lost" suffix
6. Restart the API: `docker compose start api`
7. [ ] SSE connections re-establish automatically
8. [ ] Polling resumes
9. [ ] Global job bar restores original messages and blue progress colour
10. [ ] Banner disappears

## 6. Production Checklist

- [ ] `GRAFANA_ADMIN_PASSWORD` set to a strong value in `.env`
- [ ] Monitoring ports not exposed to the public internet (bound to `127.0.0.1`)
- [ ] Prometheus retention set appropriately (`--storage.tsdb.retention.time=30d`)
- [ ] Grafana `GF_USERS_ALLOW_SIGN_UP=false`
- [ ] Alert rules reviewed and thresholds adjusted for expected load
- [ ] SSH tunnel or VPN configured for remote dashboard access
- [ ] Dashboard tested with representative traffic
