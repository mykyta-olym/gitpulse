# Rollout & Rollback Plan

> **Documentation Status (2026-06-05):** Current operational rollout plan for GitPulse.
> Active Alembic head: `049`.

## Scope

This rollout removes the last inactive/retired schema and code paths while keeping the active GitLab-driven workflow:

- GitLab OAuth/session auth
- course import from GitLab groups
- webhook and manual sync processing
- R01-R13 and custom compliance checks
- activity/analytics dashboards
- support forms, compliance history and service monitoring
- optional LLM suggestions

Retired and removed:

- legacy roster upload flow
- retired scheduled fallbacks and scheduler master switch
- retired PDF/report API flow
- retired grading and heuristic subsystems with their global gates

## Pre-Deployment Checklist

```bash
git pull origin main
python scripts/build_bundle.py --check
python scripts/check_static_artifacts.py
ruff check src tests scripts
ruff format --check src tests scripts
mypy src/app
pytest -q
```

Back up production before applying migrations:

```bash
docker compose exec postgres pg_dump -U gitpulse gitpulse > backup_$(date +%Y%m%d).sql
```

## Feature Flags

Required/default active platform flags remain in `src/app/config.py`.

Optional disabled-by-default teaching tools that may remain configured but off:

| Flag | Purpose |
|---|---|
| `FEATURE_LLM_SUGGESTIONS` | Optional LLM MR analysis and suggestions |

Removed global switches for retired scheduler fallbacks, legacy upload/report
flows, grading helpers, behaviour heuristics, manual intervention panels, and
global auto-sync gates must not be reintroduced in deployment env files.

## Deployment Steps

```bash
docker compose build api worker
docker compose run --rm migrate
docker compose up -d --no-deps api worker scheduler
```

Verify:

```bash
docker compose exec api alembic current
curl -f http://localhost:8000/health/live
curl -f http://localhost:8000/health/ready
```

Expected database cleanup at head `049`:

- the legacy snapshot column is absent;
- the two retired history/report tables are absent.

## Post-Deployment Smoke Test

1. Login via GitLab OAuth.
2. Open dashboard and confirm courses render server-side.
3. Start a course sync.
4. Navigate dashboard -> course -> projects -> team -> analytics while sync is running.
5. Confirm queued/running/finishing/done job states are stable and not duplicated.
6. Confirm synced teams/projects/activity refresh without hard browser cache clears.
7. Open System Health and run `Check Now`.
8. Open Admin scheduled jobs and confirm only active scheduler jobs are listed.

## Rollback

Application rollback:

```bash
git checkout <previous-good-sha>
docker compose build api worker
docker compose up -d --no-deps api worker scheduler
```

Database rollback for `048`/`049` is intentionally not supported because those migrations drop removed feature schema. Restore from backup if the old code must run against the old schema:

```bash
docker compose exec -T postgres psql -U gitpulse gitpulse < backup_YYYYMMDD.sql
```

## Monitoring

```bash
docker compose logs --since 30m api
docker compose logs --since 30m worker
docker compose logs --since 30m scheduler
curl http://localhost:8000/metrics
```

Watch for:

- failed migration at startup
- repeated job terminal toasts
- stale course/team/project cards after sync
- Redis/session-store health failures
- webhook replay or DLQ growth
