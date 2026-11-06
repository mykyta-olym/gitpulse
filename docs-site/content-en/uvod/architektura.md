---
title: "System architecture"
description: "Current technical architecture of GitPulse"
---
{{< details >}}
- For: Everyone
- Requires: Nothing
{{< /details >}}
> Verified against implementation on **2026-09-09**.

## Runtime architecture

```mermaid
flowchart LR
    subgraph Edge["Edge Layer"]
        Caddy["Caddy :80/:443"]
    end

    subgraph App["Application Layer"]
        API["FastAPI\n/api/v1 + /dashboard"]
        W["RQ Worker\nhigh / default / low"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL 16")]
        RD[("Redis 7")]
    end

    subgraph Ext["External"]
        GL["GitLab"]
    end

    subgraph Obs["Observability"]
        Prom["Prometheus"]
        Graf["Grafana"]
        J["Jaeger"]
    end

    GL -->|"Webhook + OAuth + API"| Caddy
    Caddy --> API
    API --> PG
    API --> RD
    RD --> W
    W --> PG
    W --> GL
    API --> Prom
    Prom --> Graf
    API -. "OTLP" .-> J
    W -. "OTLP" .-> J
```

## Components and responsibilities

| Component | Responsibility |
|---|---|
| `Caddy` | TLS termination and reverse proxy |
| `FastAPI` | REST API, dashboard routes, health/metrics endpoints |
| `PostgreSQL` | persistent data (courses, teams, events, metrics, support tickets, audit logs) |
| `Redis` | queue backend, idempotency locks, short-lived cache |
| `RQ Worker` | webhook processing, MR/issue enrichment, metric computation, compliance snapshots, auto-archive, LLM analysis; delayed jobs (such as email-delivery retries) are scheduled via `Queue.enqueue_in` and executed by the worker's built-in RQ scheduler |

## Async pipeline (webhook -> metrics)

```mermaid
sequenceDiagram
    participant GL as GitLab
    participant API as FastAPI
    participant DB as PostgreSQL
    participant RQ as Redis/RQ
    participant W as Worker

    GL->>API: POST /api/v1/webhooks/gitlab
    API->>API: verify X-Gitlab-Token
    API->>DB: store raw event
    API->>RQ: enqueue process_event (high)
    API-->>GL: 202 accepted

    RQ->>W: dequeue process_event
    W->>DB: upsert entities
    W->>RQ: enqueue enrichment/metrics (default)

    RQ->>W: dequeue compute_metrics
    W->>DB: save MetricSnapshot
```

## Authentication architecture

```mermaid
flowchart TB
    U["User"] -->|"/dashboard/login"| OAuth["GitLab OAuth"]
    OAuth -->|callback| Sess["gitpulse_session cookie"]
    Sess --> Dash["/dashboard/..."]

    APIClient["API client"] -->|"Authorization Bearer"| ApiAuth["/api/v1/..."]
    Sess -->|alternative| ApiAuth

    GitLabWH["GitLab webhook"] -->|"X-Gitlab-Token"| WH["/api/v1/webhooks/gitlab"]
```

Auth layers:

1. Dashboard: GitLab OAuth + signed session cookie.
2. API: Bearer token (`TEACHER_API_TOKEN`) or dashboard session.
3. Webhook endpoint: per-project secret (`X-Gitlab-Token`).

## Queues and scheduled jobs

| Queue | Purpose | Priority |
|---|---|---|
| `high` | webhook ingest processing | highest |
| `default` | enrichment, sync, metrics recompute | medium |
| `low` | compliance snapshots, auto-archive, LLM analysis | lowest |

The system runs **no periodic (cron) jobs**. Data refreshes come solely from
GitLab events (webhooks) and explicit actions in the UI. Maintenance
operations (pruning old events, archiving ended courses, re-analysis, etc.)
are exposed as manual actions under *System -> maintenance jobs* and an admin
runs them on demand. Delayed jobs (e.g. an email-delivery retry that backs off
and re-enqueues itself via `Queue.enqueue_in`) are executed by the worker's
built-in RQ scheduler.

## Deployment model

Production compose services:

- `postgres`
- `redis`
- `api`
- `worker`
- `caddy`

Optional `monitoring` profile adds:

- `prometheus`
- `grafana`
- `jaeger`

## Related pages

- [API reference](../api/index.md)
- [Monitoring](../operatori/monitoring.md)
- [Deployment](../operatori/nasadenie.md)
