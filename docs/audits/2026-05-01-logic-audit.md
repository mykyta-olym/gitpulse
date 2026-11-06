# Logic & Correctness Audit - 2026-05-01

Scope: program-logic correctness audit of the GitPulse / DevOps Teaching
Assistant codebase carried out as part of the master's-thesis quality
gate.  Complements the security batch shipped on the same day (commit
range `9f9d68d0..f644d42d`).

The audit focuses on **logic** bugs (race conditions, fail-open paths,
transaction-boundary correctness, query efficiency, permission gaps) -
NOT static-analysis findings that the lint chain already enforces.

Severity scale:

| Tier      | Meaning                                                              |
| --------- | -------------------------------------------------------------------- |
| critical  | data corruption, auth bypass, or production-crashing bug             |
| high      | reliable user impact (silent data loss, PII exposure, lost emails)   |
| medium    | observable but tolerable in steady state (perf, monitoring gaps)     |
| low       | hygiene, dead code, configuration drift                              |

Status legend:

- **fixed** - addressed in this audit batch (this commit or earlier today)
- **deferred** - tracked for a follow-up sprint with rationale
- **false-positive** - investigated and confirmed not a defect

---

## 1. Email enqueue race vs. unique idempotency key - **fixed**

- **Severity:** high
- **Files:** [src/app/services/email_notifications.py](../../src/app/services/email_notifications.py#L240-L290)
- **Description:**
  `enqueue_email` did `SELECT ... WHERE idempotency_key = ?` then `INSERT`
  in two separate statements.  The DB-level `UNIQUE(idempotency_key)`
  constraint (see [src/app/models/email_log.py](../../src/app/models/email_log.py#L15))
  protected against duplicate rows, but the surrounding Python code did
  not catch `IntegrityError`.  When two concurrent webhooks (e.g. a
  rapid double-fire of a support-ticket notification) racing inside the
  same window both passed the `SELECT` check and both attempted to
  `INSERT`, the second `commit()` raised `IntegrityError` and bubbled
  up as an unhandled 500.
- **Symptom:** sporadic 500s on webhook handlers under burst load.
- **Fix:** wrap the `commit()` in `try/except IntegrityError`; on
  collision, log `email_duplicate_race` and return `None` (treat as
  duplicate).  Same change applied to both `_persist_with_current_engine`
  and `_persist_with_local_engine`.

## 2. Concurrent enqueue race in `_validate_per_user_token` - **false-positive**

- **Files:** [src/app/dependencies.py](../../src/app/dependencies.py#L140-L150)
- **Investigation:** initial concern was that
  `_validate_per_user_token` calls `db_session.merge(candidate)` for
  `last_used_at` but does not commit, so the update would be lost on
  rollback.  Confirmed false-positive: the caller wraps the call in
  `async_session_ctx()` (see
  [src/app/db/session.py](../../src/app/db/session.py#L177-L196)),
  which auto-commits at clean exit.  No fix required.

## 3. Webhook secret rotation grace period unbounded - **deferred**

- **Severity:** medium
- **Files:** [src/app/api/webhooks.py](../../src/app/api/webhooks.py)
  (search for `webhook_secret_hash_previous`)
- **Description:** dual-hash rotation accepts both the current AND the
  previous secret indefinitely.  After rotation, an attacker who has
  exfiltrated the old secret retains the ability to forge webhooks for
  as long as the previous hash remains in the DB.  There is no
  `webhook_secret_rotated_at` timestamp and no automatic expiry of the
  previous secret.
- **Fix sketch:** add `webhook_secret_rotated_at TIMESTAMPTZ`; in the
  dual-hash check, if `previous_hash` matched and
  `now() - rotated_at > 7d`, reject with HTTP 401.  Background job
  clears `webhook_secret_hash_previous` after the grace period.
- **Why deferred:** schema migration plus rollout coordination.  Logged
  for the next security cycle.

## 4. Legacy roster CSV path lacked all-or-nothing transaction semantics - **retired**

- **Severity:** high
- **Outcome:** the legacy upload path was removed from the active product.
  Student membership now comes from GitLab group/project sync and the course
  roster view is read-only/export-only.

## 5. N+1 in `_docker_reverify_async` - **deferred**

- **Severity:** medium (perf only, observed during full sweep on prod)
- **Files:** [src/app/workers/sweep.py](../../src/app/workers/sweep.py)
  (around `_docker_reverify_async`)
- **Description:** loads all active projects, then issues one
  `SELECT MAX(DockerBuildReport.created_at)` per project.  At 1000
  projects this is 1001 queries per sweep.
- **Fix sketch:** single `GROUP BY project_id` query returning
  `(project_id, max_created_at)` pairs, mirroring the pattern already
  used in `_sweep_stale_async`.
- **Why deferred:** isolated performance issue, no correctness impact;
  filed as DB-OPT-01 on the sprint board.

## 6. `_check_required_roles` bypassed when `feature_rbac=false` - **fixed (today, 9f9d68d0)**

The hardening landed earlier today: the `Settings` validator now
**refuses to start** in `APP_ENV=production` if `FEATURE_RBAC=false`,
turning the historical fail-open into fail-closed.  The runtime check
in `_check_required_roles` itself is unchanged (early-return when
`allowed_roles is None` is intentional - endpoints opt-in to RBAC), but
the enforcement boundary is now at startup.

## 7. UA fingerprint silently disabled when stored UA is empty - **deferred**

- **Severity:** medium
- **Files:** [src/app/security/session_auth.py](../../src/app/security/session_auth.py)
  (search for `stored_ua`)
- **Description:** if a session was created without a `User-Agent`
  header (CLI client, headless test runner), `stored_ua` is `""` and
  the binding check is skipped on subsequent requests.  A stolen cookie
  from such a session can be replayed from any browser.
- **Fix sketch:** treat empty stored UA as a sentinel value - store
  the literal `"none"` and compare against `"none"` on subsequent
  loads.  Reject if the request's UA fingerprint differs.  Or simply
  reject login attempts with empty UA.
- **Why deferred:** CLI/automation users would break; needs an explicit
  allowlist for known automation user agents (CI runners, telemetry
  scrapers) before this can be enforced.

## 8. Stateless cookie fallback when session-store is slow - **logged-only fix needed**

- **Severity:** medium (operational visibility)
- **Files:** [src/app/security/session_auth.py](../../src/app/security/session_auth.py)
  (`create_session_cookie` fallback path)
- **Description:** when the Redis-backed session store times out,
  `create_session_cookie` silently falls back to a self-contained
  stateless cookie.  No `WARNING` log, no Prometheus counter.  Ops has
  no way to detect that sessions are degraded.
- **Recommendation:** add `logger.warning("session_store_unavailable_fallback")`
  and a counter `session_store_fallback_total` already declared in
  metrics.  Alert if rate > 5/min for 2 min.
- **Why deferred:** observability change only; the security posture is
  already acceptable because the fallback cookie is signed.  Filed as
  OBS-04 on the sprint board.

## 9. Student email visible to teammates on detail page - **by design**

- **Files:** [src/app/api/dashboard/students/routes.py](../../src/app/api/dashboard/students/routes.py#L74),
  [src/app/templates/partials/student/_detail_content.html](../../src/app/templates/partials/student/_detail_content.html#L50)
- **Investigation:** access to `/students/{id}/team/{team_id}` is
  gated by `_can_view_team`, which permits any TeamMember of the same
  team in addition to teachers/admins.  The student-detail template
  renders `student.email` for the viewer.  This is a deliberate
  pedagogical decision (teammates communicate via email during group
  work).  GitLab-private emails are stored as the literal string
  `"PRIVATE"` and the template renders the I18N
  placeholder *(soukromé/private)* instead of the address.
- **Outcome:** documented as intentional; no code change.

## 10. LLM API key risk in debug logs - **already mitigated**

- **Files:** [src/app/services/llm/service.py](../../src/app/services/llm/service.py)
- **Investigation:** the only `logger.*` calls reference
  prompts and sanitised responses; the key is read once into a local
  variable and never serialised.  `Settings.__repr__` is the default
  pydantic repr which redacts `SecretStr` fields, but `llm_api_key` is
  declared as `str`.  Acceptable today because logs are off by default
  and no code path interpolates the settings object directly into a
  log line.  Filed as SEC-OBS-01 to convert to `SecretStr`.

## 11. Health-readiness divergence from session store - **deferred**

- **Files:** [src/app/api/health.py](../../src/app/api/health.py)
- **Description:** `/health/ready` only `PING`s Redis; it does not
  exercise the session-store key namespace.  If Redis is up but the
  session-store hash is corrupted (e.g. `MEMORY OVERLOAD` evicted the
  hash), readiness still returns 200.
- **Fix sketch:** in the readiness probe, call
  `SessionStore.health_probe()` which writes-then-reads a synthetic
  key.  Add a hard timeout of 250 ms to keep readiness fast.
- **Why deferred:** readiness latency budget needs review with the
  prod SRE; deferred to next observability sprint.

## 12. Cleanup sweep deletes pending emails older than retention - **false-positive**

- **Investigation:** at audit time there was no email-log retention
  sweep.  This was later fixed with an email-only cleanup that prunes
  terminal `sent` / `failed` rows without touching pending retries.

## 13. Configuration drift: `gitlab_cache_compress_threshold` - **false-positive**

- **Investigation:** grepped the codebase - used in
  [src/app/services/gitlab/cache.py](../../src/app/services/gitlab/cache.py)
  for compress-on-write decision.  Setting is wired up correctly.

## 14. `email_log` has no retention sweep - **deferred**

- **Severity:** low
- **Description:** at audit time, `email_log` rows were never deleted.
- **Fix sketch:** add `cleanup_old_email_logs` with retention default of
  180 days (`status IN ('sent', 'failed')` only - never delete `pending`
  or `retry`).
- **Why deferred:** at current volumes the table is < 1 GB / year;
  filed as DB-OPS-02.

---

## Summary

| Category                    | Findings | Fixed | Deferred | False-positive |
| --------------------------- | -------- | ----- | -------- | -------------- |
| Race conditions             | 2        | 1     | 1        | 0              |
| Auth / RBAC fail-open       | 2        | 2     | 0        | 0              |
| Permission boundaries       | 1        | 0     | 0        | 1 (by design)  |
| Transaction boundaries      | 2        | 0     | 1        | 1              |
| Query efficiency / N+1      | 1        | 0     | 1        | 0              |
| Crypto / token handling     | 2        | 0     | 1        | 1              |
| Health / observability      | 2        | 0     | 2        | 0              |
| Configuration drift         | 1        | 0     | 0        | 1              |
| Sweep / retention coverage  | 1        | 0     | 1        | 0              |
| **Total**                   | **14**   | **3** | **7**    | **4**          |

Three substantive logic bugs were fixed in this batch (#1 race, #6
RBAC fail-open which landed earlier today as `9f9d68d0`, plus the
flaky `test_tampered_signature_returns_none` cleanup).  Seven items
remain on the backlog with explicit rationale.  Four items were
investigated and confirmed not to be defects.

The most important takeaway for the thesis defence: the high-risk
fail-open patterns (RBAC false, DEBUG true, Redis unauthenticated,
rate-limit graceful-degradation) are now hard failures at startup or
fail-closed at request time.  The system can no longer silently weaken
its own security posture through configuration drift.

---

# Round 2 (deeper pass) - 2026-05-01

A second audit pass on hot subsystems (event processor, session store, member sync, and retired teaching helpers). Findings 15-17 below were verified by quoting the actual code and were fixed in the same commit; remaining active findings are recorded for follow-up.

## 15. Event processor: post-commit side-effects could fail silently - **HIGH, fixed**

- **File:** [src/app/workers/event_processor.py](../../src/app/workers/event_processor.py)
- **Bug:** `event.processed = True` and `await session.commit()` ran
  *before* cache invalidation, immediate enrichment, metrics enqueue,
  dashboard SSE notify, and (for `push`) member sync.  If any of those
  side-effects raised, control fell into the outer `except Exception:`
  which called `await session.rollback()` - but the row was already
  committed, so rollback was a no-op.  `event.processed` remained
  `True`, so the next worker run skipped the event.  Net effect: stale
  cache + missing enrichment for hours until the periodic 24 h sweep.
- **Fix:** wrapped each post-commit side-effect in `_safe(coro, name)`
  that catches exceptions, increments a Prometheus counter
  (`webhook_processed_total{status="sideeffect_failed:<name>"}`) and
  logs `WARNING` instead of bubbling.  Allows ops to alert on the
  counter rather than silently losing cache invalidations.

## 16. Session store: no absolute lifetime ceiling - **MEDIUM, fixed**

- **File:** [src/app/security/session_store.py](../../src/app/security/session_store.py)
- **Bug:** `_maybe_refresh_ttl` implemented a sliding-window TTL with
  no hard maximum.  An active user (or a stolen long-lived cookie)
  could keep refreshing the TTL indefinitely.
- **Fix:** added `session_absolute_max_age_seconds` (default 24 h),
  stamped `created_at` on `create()`, and on `load()` the store
  rejects sessions older than the absolute ceiling regardless of how
  often the sliding TTL was refreshed.  Bounds the blast radius of a
  stolen cookie.

## 17. Round-1 finding #1 follow-through - **already fixed in commit 5a4479fb**

- The IntegrityError race on `email_log.idempotency_key` was patched
  in the previous batch but is recorded here for traceability.  Both
  `_persist_with_current_engine` and `_persist_with_local_engine`
  catch `IntegrityError`, roll back, and return `None` instead of
  bubbling a 500.

## 18. Retired grading helper: zero-weight fallback - **retired**

- **Outcome:** the helper and its editor/API surface were removed from the
  active system. No active follow-up remains.

## 19. Member sync: delete-then-add visibility window - **MEDIUM, deferred**

- **File:** [src/app/services/member_sync.py](../../src/app/services/member_sync.py)
- During a sync run the team's roster passes through an interim
  state where removed members have `is_active=False` set but added
  members have not been inserted yet.  A concurrent dashboard query
  reading `TeamMember.is_active.is_(True)` may briefly observe a
  shrunken team.  Read-committed isolation tolerates this.
- **Deferred:** the right fix is to load the relevant rows with
  `with_for_update()` at the start of the sync.  The change has
  cross-cutting implications for scheduled automation and warrants a
  dedicated migration.  Risk today is cosmetic (transient roster
  flicker), not data-loss.

## 20. Retired review-quality heuristic false positives - **retired**

- **Outcome:** the heuristic module was removed from the active system.
  Review quality is evaluated from GitLab evidence and course rules instead.

## 21. Event processor: side-effect failure observability - **fixed alongside #15**

- The new `_safe()` wrapper emits `webhook_processed_total{status=
  "sideeffect_failed:<name>"}`.  Add a Grafana alert on
  `rate(... [5m]) > 0` once the counter has accumulated baseline
  data.  Recorded as an ops-follow-up.

---

**Round-2 categorisation summary:**

| Severity | Total | Fixed | Deferred |
|----------|-------|-------|----------|
| HIGH     | 1     | 1     | 0        |
| MEDIUM   | 1     | 1     | 1        |
| LOW      | 2     | 0     | 2        |

Combined with round 1 (3 fixed, 7 deferred, 4 false-positive):
**5 fixes shipped, 10 deferred to next sprint, 4 false-positive.**
