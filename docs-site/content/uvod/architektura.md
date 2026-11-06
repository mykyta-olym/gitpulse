---
title: "Architektúra systému"
description: "Aktuálna technická architektúra GitPulse"
---
{{< details >}}
- Pre: Všetci
- Vyžaduje: Nič
{{< /details >}}
> Overené podľa implementácie dňa **2026-09-09**.

## Runtime architektúra

```mermaid
flowchart LR
    subgraph Edge["Edge vrstva"]
        Caddy["Caddy :80/:443"]
    end

    subgraph App["Aplikačná vrstva"]
        API["FastAPI\n/api/v1 + /dashboard"]
        W["RQ Worker\nhigh / default / low"]
    end

    subgraph Data["Dátová vrstva"]
        PG[("PostgreSQL 16")]
        RD[("Redis 7")]
    end

    subgraph Ext["Externé"]
        GL["GitLab"]
    end

    subgraph Obs["Pozorovateľnosť"]
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

## Komponenty a zodpovednosti

| Komponent | Zodpovednosť |
|---|---|
| `Caddy` | TLS terminácia, reverse proxy na API |
| `FastAPI` | REST API, dashboard routy, health/metrics endpointy |
| `PostgreSQL` | perzistentné dáta (kurzy, tímy, eventy, metriky, support tickety, audit logy) |
| `Redis` | queue backend, locky/idempotencia, krátkodobý cache |
| `RQ Worker` | spracovanie webhookov, enrichment MR/issues, výpočty metrík, snímky súladu, auto-archív, LLM analýza; odložené joby (napr. opakovanie doručenia e-mailu) si plánuje sám job cez `Queue.enqueue_in` a vykoná ich vstavaný RQ scheduler vo workeri |

## Asynchrónny pipeline (webhook -> metriky)

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

## Architektúra autentifikácie

```mermaid
flowchart TB
    U["Používateľ"] -->|"/dashboard/login"| OAuth["GitLab OAuth"]
    OAuth -->|callback| Sess["gitpulse_session cookie"]
    Sess --> Dash["/dashboard/..."]

    APIClient["API klient"] -->|"Authorization Bearer"| ApiAuth["/api/v1/..."]
    Sess -->|"alternatívne"| ApiAuth

    GitLabWH["GitLab webhook"] -->|"X-Gitlab-Token"| WH["/api/v1/webhooks/gitlab"]
```

Autentifikačné vrstvy:

1. Dashboard: GitLab OAuth + podpísaná session cookie.
2. API: Bearer token (`TEACHER_API_TOKEN`) alebo dashboard session.
3. Webhook endpoint: per-project secret (`X-Gitlab-Token`).

## Queue a plánované úlohy

| Queue | Účel | Priorita |
|---|---|---|
| `high` | webhook ingest processing | najvyššia |
| `default` | enrichment, sync, metrics recompute | stredná |
| `low` | snímky súladu, auto-archív, LLM analýza | najnižšia |

Systém **nepoužíva žiadne periodické (cron) joby**. Dáta sa obnovujú výhradne
udalosťami z GitLabu (webhooky) a explicitnými akciami v rozhraní. Údržbové
operácie (napr. čistenie starých eventov, archivácia ukončených kurzov,
re-analýza) sú dostupné ako ručné akcie v *System -> údržbové joby* a spúšťa
ich administrátor podľa potreby. Odložené joby (napr. opakovanie doručenia
e-mailu s exponenciálnym backoffom) si plánuje sám job cez `Queue.enqueue_in`
a vykoná ich vstavaný RQ scheduler vo workeri.

## Deployment model

Produkčný profil používa Docker Compose služby:

- `postgres`
- `redis`
- `api`
- `worker`
- `caddy`

Voliteľný profil `monitoring` pridáva:

- `prometheus`
- `grafana`
- `jaeger`

## Súvisiace stránky

- [API referencia](../api/index.md)
- [Monitoring](../operatori/monitoring.md)
- [Nasadenie](../operatori/nasadenie.md)
