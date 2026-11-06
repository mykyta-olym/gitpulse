# Event Pipeline - Idempotency, Replay, DLQ, and Audit

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


## Overview

The event pipeline processes GitLab webhook events with three reliability layers:

1. **Triple idempotency** - deduplicates incoming webhooks at ingestion
2. **Dead-letter queue (DLQ)** - quarantines events that fail repeatedly
3. **Replay** - re-processes historical events by time range, project, or type
4. **Audit log** - immutable record of all processing and admin actions

All features are gated behind `FEATURE_EVENT_PIPELINE=true`.

---

## Architecture

```
GitLab -> POST /api/webhooks/gitlab
           |
           +- Layer 1: X-Gitlab-Delivery dedup
           +- Layer 2: X-Gitlab-Event-UUID dedup
           +- Layer 3: SHA-256 payload hash dedup
           |
           ▼
      webhook_events table (JSONB payload, immutable)
           |
           ▼
      RQ high queue -> process_event worker
           |
           +- Success -> mark processed, audit log
           +- Retry (< max) -> RQ retry with backoff
           +- Failure (>= max) -> move to DLQ, audit log
```

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `FEATURE_EVENT_PIPELINE` | `true` | Enable DLQ, replay, audit features |
| `DLQ_MAX_RETRIES` | `5` | Retries before moving to DLQ |
| `WORKER_MAX_RETRIES` | `5` | Sweep: max retries for re-enqueue |

## Database (Migration 001)

New columns on `webhook_events`:

| Column | Type | Purpose |
|---|---|---|
| `payload_hash` | `VARCHAR(64)` | SHA-256 of raw body |
| `gitlab_delivery_id` | `VARCHAR(100)` | X-Gitlab-Delivery header |
| `dead_letter_at` | `TIMESTAMPTZ` | When moved to DLQ (NULL = not in DLQ) |
| `dead_letter_reason` | `TEXT` | Why it was moved to DLQ |
| `replay_of_id` | `UUID FK` | Original event if this is a replay |
| `is_replayed` | `BOOLEAN` | True if this event has been replayed |

Indexes: `ix_we_payload_hash`, `ix_we_delivery_id`, partial indexes for DLQ and sweep.

---

## API Endpoints

All require teacher or admin role.

### Replay Events

```
POST /api/events/replay
```

Body:
```json
{
  "start": "2025-01-01T00:00:00Z",
  "end": "2025-01-02T00:00:00Z",
  "project_id": 42,
  "event_type": "push",
  "limit": 1000
}
```

Response:
```json
{
  "replayed": 3,
  "event_ids": ["uuid1", "uuid2", "uuid3"]
}
```

### List DLQ Events

```
GET /api/events/dlq?limit=100&event_type=push
```

### Resurrect from DLQ

```
POST /api/events/dlq/{event_id}/resurrect
```

Resets retry count, clears DLQ status, and re-enqueues for processing.

---

## Operational Runbook

### How to replay safely

1. **Identify the time range** of the incident (e.g., webhook processor was down 14:00-15:00 UTC)
2. **Check current DLQ** for any related events: `GET /api/events/dlq`
3. **Trigger replay** with a narrow scope:
   ```bash
   curl -X POST https://app/api/events/replay \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"start":"2025-01-15T14:00:00Z","end":"2025-01-15T15:00:00Z","limit":100}'
   ```
4. **Monitor** the RQ dashboard for job completion
5. **Verify** replay events appear in the audit log:
   ```sql
   SELECT * FROM audit_log WHERE action = 'event.replay' ORDER BY timestamp DESC LIMIT 5;
   ```

### DLQ management

**View DLQ events:**
```sql
SELECT id, event_type, gitlab_project_id, dead_letter_at, dead_letter_reason, retry_count
FROM webhook_events
WHERE dead_letter_at IS NOT NULL
ORDER BY dead_letter_at DESC;
```

**Resurrect via API:**
```bash
curl -X POST https://app/api/events/dlq/{event_id}/resurrect \
  -H "Authorization: Bearer $TOKEN"
```

**Bulk resurrect (SQL - use with caution):**
```sql
UPDATE webhook_events
SET dead_letter_at = NULL, dead_letter_reason = NULL,
    processed = false, processed_at = NULL, processing_error = NULL, retry_count = 0
WHERE dead_letter_at IS NOT NULL
  AND dead_letter_reason LIKE '%Max retries%';
```

### Audit log queries

```sql
-- Recent processing failures
SELECT * FROM audit_log WHERE action = 'event.failed' ORDER BY timestamp DESC LIMIT 20;

-- Replay history
SELECT * FROM audit_log WHERE action = 'event.replay' ORDER BY timestamp DESC;

-- DLQ resurrections
SELECT * FROM audit_log WHERE action = 'event.resurrect' ORDER BY timestamp DESC;
```

---

## Rollout

### Phase 1: Migration (zero-downtime)
```bash
alembic upgrade head  # adds nullable columns + indexes
```

### Phase 2: Enable feature
```bash
FEATURE_EVENT_PIPELINE=true
DLQ_MAX_RETRIES=5
```
Restart app and worker containers.

### Phase 3: Verify
- Send a test webhook, confirm payload_hash and delivery_id are stored
- Check audit_log for `event.processed` entries
- Confirm sweep excludes DLQ events

### Rollback
```bash
FEATURE_EVENT_PIPELINE=false
```
Restart. DLQ and audit features become no-ops. Triple idempotency (dedup) continues working as it's part of the webhook receiver logic regardless of the flag.

To fully revert the migration:
```bash
alembic downgrade -1
```
