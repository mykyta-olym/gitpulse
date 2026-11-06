# 1. Requirements Analysis

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


## 1.1 Assumptions & Decisions

| # | Assumption / Decision | Rationale |
|---|----------------------|-----------|
| A1 | GitLab webhooks are **at-least-once** | GitLab may retry on timeout. System must deduplicate by `X-Gitlab-Event-UUID` or computed hash. |
| A2 | One pilot course (ZSI, ~30 teams × 4-5 students ≈ 150 users) | Keeps scope manageable; same engine works for Základy DevOps later. |
| A3 | Teams of 4-5 are pre-registered by teacher via API | Auto-discovery from GitLab group membership is a post-pilot feature. |
| A4 | "Meaningful review" = MR note by a non-author with ≥ 30 words | Threshold is configurable per course via `CourseSettings`. |
| A5 | Traffic-light scoring: GREEN ≥ 80%, YELLOW ≥ 50%, RED < 50% | Simple, teacher-friendly; thresholds configurable. |
| A6 | PDF via WeasyPrint (not Playwright) | 60 MB vs 400 MB Docker delta; sufficient for table-heavy reports. |
| A7 | RQ over Celery | Already have Redis; RQ is simpler for 150-student scale; no extra broker. |
| A8 | GitLab OAuth + session-based dashboard auth | Single sign-on via GitLab; session managed with itsdangerous. |
| A9 | Single-VM deployment via Docker Compose | TUKE cloud VM: 8 CPU, 16 GB RAM, 250 GB disk - ample. |
| A10 | No LLM module in MVP | Default OFF per spec; add post-pilot after privacy review. |

## 1.2 Requirements Mapping

### ZSI Course Requirements -> System Features

| # | Course Requirement (ZSI week 12) | System Feature | Check ID | Acceptance Criteria |
|---|----------------------------------|----------------|----------|---------------------|
| 1 | Each member owns exactly 1 issue | Issue ownership tracking | R01 | `count(issues assigned to student) == 1` -> PASS |
| 2 | Each issue developed in a separate branch | Branch naming convention | R02 | `∀ MR: source_branch matches pattern` AND `≥ 1 MR authored` -> PASS |
| 3 | Each member creates 1 MR linked to their issue | MR-issue linking | R04 | `∃ MR: description or title references issue` -> PASS |
| 4 | MR has test changes | Test evidence | R03 | `∃ MR: diff includes test file changes` -> PASS |
| 5 | MR follows template | Template compliance | R05 | `∃ MR: description matches template pattern` -> PASS |
| 6 | Each MR reviewed by ≥ 2 members | Reviews received | R06 | `count(distinct reviewers on own MR) ≥ threshold` (partial scoring) |
| 7 | Each student performs ≥ 2 reviews on **different** MRs | Review duty | R07 | `count(meaningful reviews given) ≥ threshold` (partial scoring) |
| 8 | Author responds to review comments, references commits | Response quality | R08 | `response_rate == 1.0 AND has_commit_reference` (partial scoring) |
| 9 | Reviewers approve MR | Approvals received | R09 | `count(distinct approvers) ≥ threshold` (partial scoring) |
| 10 | Author/assignee merges to master | Merged by author | R10 | `∃ MR: merged AND merged_by is a team member` (passes for author or teammate; fails only for unknown user) -> PASS |
| 11 | Close MR and close issue | Closure state | R11 | `MR.state == merged AND its linked_issue_iid points to a closed issue` (falls back to any-closed-issue when MR has no link) -> PASS |
| 12 | CI pipeline passes | Pipeline health | R12 | `∃ pipeline: status == success AND has_test_job` -> PASS |
| 13 | Commits made locally, not via web editor | Commit quality | R13 | `web_editor_ratio ≤ threshold` -> PASS (default threshold 0.3) |

### Základy DevOps Requirements (future)

| DevOps Topic | Potential System Feature | Priority |
|-------------|-------------------------|----------|
| Issue tracking (week 8) | Same R01 issue ownership check | MVP (shared) |
| Unit testing (week 9) | R03 test evidence + R12 pipeline health | MVP (shared) |
| MR/review (weeks 10-11) | Full R01-R12 compliance engine | MVP |

## 1.3 MVP Scope vs. Nice-to-Have

### MVP (Pilot-Ready)

| Epic | User Stories | Status |
|------|-------------|--------|
| E1: Webhook Ingestion | US1.1: Receive GitLab events idempotently | Implemented |
| | US1.2: Store raw events with dedup key | Implemented |
| | US1.3: Enqueue for async processing | Implemented |
| E2: Enrichment | US2.1: Fetch full issue data from GitLab API | Implemented |
| | US2.2: Fetch MR + diff + approvals + notes | Implemented |
| | US2.3: Resolve student identities | Implemented |
| E3: Compliance Engine | US3.1: Compute 13 checks per student (R01-R13) | Implemented |
| | US3.2: Weighted scoring with traffic lights | Implemented |
| | US3.3: Communication indicators (non-scoring) | Implemented |
| E4: Dashboard | US4.1: Teacher login (GitLab OAuth) | Implemented |
| | US4.2: Course -> Teams -> Students drill-down | Implemented |
| | US4.3: R01-R13 check matrix per team | Implemented |
| | US4.4: Communication indicators per student | Implemented |
| E5: Export | US5.1: CSV export per team | Implemented |
| | US5.2: JSON export per team | Implemented |
| | US5.3: HTML report (self-contained) | Implemented |
| | US5.4: PDF report via WeasyPrint | Implemented |
| E6: Operations | US6.1: Structured JSON logging | Implemented |
| | US6.2: Prometheus metrics endpoint | Implemented |
| | US6.3: OpenTelemetry tracing (optional) | Implemented |
| | US6.4: Backup/restore scripts | Implemented |
| | US6.5: Security headers + least privilege | Implemented |

### Nice-to-Have (Post-Pilot) -> Now Implemented

| Feature | Status |
|---------|--------|
| GitLab OAuth for dashboard | Implemented (GitLab OAuth2 with PKCE) |
| Auto-discover teams from GitLab groups | Implemented (import from GitLab URL) |
| Historical trend charts (per-student score over time) | Implemented (timeline dashboard) |
| LLM review quality analysis (opt-in, privacy-aware) | Implemented (OpenAI/Gemini/Azure/Groq, PII redaction) |
| Moodle grade export integration | Not implemented |

## 1.4 Risks & Mitigations

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|------------|------------|
| R1 | **GitLab API rate limits** | Enrichment fails under burst | Medium | Exponential backoff (10s->30s->90s); batch enrichment in sweeps every 2h; cache responses |
| R2 | **Webhook delivery failures** | Missing events | Low | Periodic sweep job (every 15 min) re-processes unprocessed events; manual sync endpoint |
| R3 | **Low-quality review activity** (empty reviews, self-approval) | Inflated scores | Medium | Meaningful-review threshold, distinct reviewer/approver checks, and communication indicators surface anomalies |
| R4 | **Data privacy (GDPR)** | Legal risk | Medium | Store only GitLab usernames + public activity (no personal data beyond what's in GitLab); data retention policy (auto-purge after semester); teacher-only access |
| R5 | **Single-VM failure** | Downtime | Low | Docker restart policies; PostgreSQL WAL + daily backups; Redis AOF persistence |
| R6 | **Schema evolution** | Migration failures | Low | Alembic versioned migrations; tested in CI; backup before migrate |
| R7 | **Webhook token compromise** | Spoofed events | Low | Per-project webhook secrets; constant-time comparison; token rotation via API |
| R8 | **Large payloads** | Memory/DoS | Low | 1 MB payload limit enforced in webhook handler; Caddy rate limiting (60 req/min/IP) |
| R9 | **GitLab API changes** | Broken enrichment | Low | Permissive Pydantic parsing (`model_config = {"extra": "allow"}`); adapter pattern in GitLab client |
| R10 | **Scale beyond 150 students** | Slow queries | Low | Indexed queries; async DB; pool size configurable; horizontal worker scaling via `--scale worker=N` |

## 1.5 Prioritized Backlog

### Epics -> User Stories -> Tasks (estimated in ideal days)

```
E1: Webhook Ingestion [DONE - 5d]
  US1.1: Receive GitLab events ........................ 2d
    T1.1.1: POST /api/v1/webhooks/gitlab endpoint
    T1.1.2: X-Gitlab-Token verification
    T1.1.3: Payload size limit (1 MB)
    T1.1.4: Dedup by event UUID / computed hash
  US1.2: Store raw events ............................. 1d
    T1.2.1: WebhookEvent model + migration
    T1.2.2: EventRepository.create()
  US1.3: Enqueue for async processing ................. 2d
    T1.3.1: RQ queue setup (high/default/low)
    T1.3.2: enqueue_event_processing()
    T1.3.3: Fallback: event stored even if Redis is down

E2: Enrichment [DONE - 6d]
  US2.1: Enrich issues ................................ 2d
    T2.1.1: GitLab API client (httpx)
    T2.1.2: enrich_issue job
    T2.1.3: Upsert Issue model
  US2.2: Enrich merge requests ........................ 3d
    T2.2.1: Fetch MR + diff + approvals + notes
    T2.2.2: Compliance field extraction (branch, template, test files, issue links)
    T2.2.3: Upsert MR + MRNote + MRApproval models
  US2.3: Student identity resolution .................. 1d
    T2.3.1: Match GitLab user IDs to Student records
    T2.3.2: Handle unknown users gracefully

E3: Compliance Engine [DONE - 8d]
  US3.1: 12 compliance checks ......................... 5d
    T3.1.1-T3.1.12: One function per check (R01-R12)
  US3.2: Weighted scoring ............................. 2d
    T3.2.1: CourseSettings weight configuration
    T3.2.2: Traffic light thresholds
    T3.2.3: MetricSnapshot persistence
  US3.3: Communication indicators ..................... 1d
    T3.3.1: 6 non-scoring diagnostic metrics

E4: Dashboard [DONE - 5d]
  US4.1: Login ........................................ 1d
  US4.2: Course/team/student views .................... 2d
  US4.3: Check matrix with traffic lights ............. 1d
  US4.4: Communication indicators display ............. 1d

E5: Export [DONE - 4d]
  US5.1: CSV export ................................... 0.5d
  US5.2: JSON export .................................. 0.5d
  US5.3: HTML report .................................. 1.5d
  US5.4: PDF report (WeasyPrint) ...................... 1.5d

E6: Operations [DONE - 5d]
  US6.1: Structured logging ........................... 1d
  US6.2: Prometheus metrics ........................... 1d
  US6.3: OpenTelemetry tracing ........................ 1d
  US6.4: Backup/restore scripts ....................... 1d
  US6.5: Security hardening ........................... 1d

E7: Documentation & CI [IN PROGRESS - 3d]
  US7.1: Design documents (9 docs) .................... 2d
  US7.2: GitLab CI pipeline ........................... 0.5d
  US7.3: Pre-commit hooks ............................. 0.5d
--------------------------------------------------------
Total MVP: 36 ideal days
```
