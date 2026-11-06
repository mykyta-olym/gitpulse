# API Specification

> **Documentation Status (2026-06-03):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.

This document describes the current API surface at a practical level. For exact request/response schemas and examples, use runtime OpenAPI from a running instance.

## 1. Canonical Contract Sources

1. Runtime OpenAPI: `GET /openapi.json`
2. Router implementations: `src/app/api/*.py`, `src/app/api/dashboard/` (14-module package)
3. DTO schemas: `src/app/schemas/*.py`
4. Unified errors: `src/app/api/contracts.py`, `src/app/api/exception_handlers.py`, `src/app/api/errors.py`

## 2. API Prefixes

| Area | Prefix | Auth |
|------|--------|------|
| Admin API | `/api/v1` | Bearer token (`TEACHER_API_TOKEN`) |
| Dashboard UI/API | `/dashboard` | Session cookie (GitLab OAuth) |
| Health/metrics | `/health`, `/metrics` | Internal/proxy-gated; public `/metrics` is blocked by Caddy |

Dashboard-internal JSON endpoints under `/dashboard/api/v1/...` are part of the server-rendered dashboard surface. They are not the public `/api/v1` API and keep the dashboard prefix intentionally to avoid compatibility conflicts.

## 3. Authentication Modes

1. Bearer token for `/api/v1/*` (except webhook-specific token flow).
2. Webhook secret (`X-Gitlab-Token`) for `POST /api/v1/webhooks/gitlab`.
3. OAuth-backed dashboard session for `/dashboard/*`.

### 3.1 Session Cookie Format

Dashboard sessions use a Redis-backed opaque cookie in production, with signed
legacy cookie validation kept for migration compatibility.

**Cookie name**: `__Host-gitpulse_session` (HTTPS) or `gitpulse_session` (HTTP dev). The `__Host-` prefix is browser-enforced to require `Secure`, `Path=/`, and no `Domain` attribute.

The cookie payload contains:

| Field | Type | Description |
|---|---|---|
| `user` | string | Username (login identifier) |
| `role` | string | `admin`, `teacher`, or `student` |
| `user_id` | string | Database user UUID or GitLab user ID |
| `gitlab_username` | string | GitLab username for OAuth sessions |
| `email` | string | User email address |
| `avatar_url` | string | GitLab profile picture URL (empty if unavailable) |
| `full_name` | string | Display name from GitLab (empty if unavailable) |
| `ts` | string | ISO 8601 timestamp of cookie creation |
| `bn` | string | Boot nonce - ties cookie to server process; invalidates on restart |
| `av` | string | `BUILD_HASH` - 12-char deploy fingerprint; sessions with a different hash are rejected after redeploy |
| `ua` | string | SHA-256(User-Agent)[:16] - fingerprint binding to detect session theft across browsers |

Max age: 30 days idle TTL (configurable via `SESSION_MAX_AGE_SECONDS`) with a 90-day absolute ceiling (`SESSION_ABSOLUTE_MAX_AGE_SECONDS`). `HttpOnly`, `Secure` (HTTPS), `SameSite=Lax`.

## 4. Error Contract

API endpoints use centralized error contract (`ErrorResponse`) and factory helpers (`raise_not_found`, `raise_conflict`, etc.).

Typical payload shape:

```json
{
  "error": "not_found",
  "detail": "Course not found",
  "status_code": 404,
  "path": "/api/v1/courses/123",
  "correlation_id": "...",
  "timestamp": "..."
}
```

## 5. Current Endpoint Inventory (Grouped)

> This section is generated from the live route table and pinned by
> `tests/unit/test_api_spec_inventory.py` - if a route is added, removed or
> renamed and this list is not updated, that test fails. Do not hand-edit the
> `/api/v1` lists below; regenerate them.

### Core system (outside `/api/v1`)

- `GET /health`, `GET /health/live`, `GET /health/ready`, `GET /health/gitlab`
- `GET /health/gitlab/status` - UI connectivity report, HTTP 200 with an `ok`,
  `error` or `unreachable` status. The monitoring probe `/health/gitlab` returns
  HTTP 503 for an outage; both share the same briefly cached GitLab check.
- `GET /metrics` (blocked at the edge by Caddy)
- `GET /robots.txt` - crawl rules; disallows `/api/`, `/dashboard/`, `/oauth/`,
  `/health/`, `/metrics` and the monitoring paths (admin session only)
- `GET /sitemap.xml` - public pages with hreflang alternates
- `GET /llms.txt` - AI-crawler context file
- `GET /google32f411f09f436ae2.html` - Search Console verification token
- `GET /privacy`, `GET /terms` - 301 redirects to the docs site
- `GET /favicon.ico`, `GET /sw.js`

### Course lifecycle and import

- `GET /api/v1/courses/`
- `POST /api/v1/courses/`
- `POST /api/v1/courses/check-import-duplicate`
- `POST /api/v1/courses/import/gitlab-group`
- `POST /api/v1/courses/import/gitlab-group/stream`
- `DELETE /api/v1/courses/{course_id}`
- `GET /api/v1/courses/{course_id}`
- `PUT /api/v1/courses/{course_id}`
- `POST /api/v1/courses/{course_id}/activate`
- `POST /api/v1/courses/{course_id}/archive`
- `POST /api/v1/courses/{course_id}/jobs/cancel`
- `DELETE /api/v1/courses/{course_id}/permanent`
- `POST /api/v1/courses/{course_id}/run-checks`
- `GET /api/v1/courses/{course_id}/run-checks-status`
- `GET /api/v1/courses/{course_id}/settings`
- `PUT /api/v1/courses/{course_id}/settings`
- `GET /api/v1/courses/{course_id}/stream`
- `POST /api/v1/courses/{course_id}/sync-all`
- `GET /api/v1/courses/{course_id}/sync-status`
- `GET /api/v1/courses/{course_id}/sync-stream`
- `POST /api/v1/courses/{course_id}/transfer`
- `GET /api/v1/courses/{course_id}/webhook-configs`
- `POST /api/v1/courses/{course_id}/webhook-configs`

### Sync, jobs, streaming

- `GET /api/v1/dashboard/stream`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/{job_id}/cancel`
- `GET /api/v1/jobs/{job_id}/stream`
- `GET /api/v1/support/tickets/{ticket_id}/stream`
- `GET /api/v1/sync/active`

### Webhooks, events, webhook configs

- `GET /api/v1/events/dlq`
- `POST /api/v1/events/dlq/{event_id}/resurrect`
- `GET /api/v1/events/recent`
- `POST /api/v1/events/replay`
- `POST /api/v1/events/delete`
- `POST /api/v1/events/purge`
- `GET /api/v1/events/{event_id}/payload`
- `DELETE /api/v1/webhook-configs/{config_id}`
- `GET /api/v1/webhook-configs/{config_id}`
- `PATCH /api/v1/webhook-configs/{config_id}`
- `POST /api/v1/webhook-configs/{config_id}/rotate`
- `POST /api/v1/webhooks/gitlab`

### LLM and GitLab tooling

- `POST /api/v1/gitlab/parse-url`
- `POST /api/v1/llm/mr/{project_id}/{mr_iid}`
- `GET /api/v1/llm/mr/{project_id}/{mr_iid}/history`

### Projects

- `GET /api/v1/projects/`
- `DELETE /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/gitlab/contributors`
- `GET /api/v1/projects/{project_id}/gitlab/labels`
- `GET /api/v1/projects/{project_id}/gitlab/milestones`
- `GET /api/v1/projects/{project_id}/gitlab/protected-branches`
- `GET /api/v1/projects/{project_id}/gitlab/releases`
- `GET /api/v1/projects/{project_id}/gitlab/statistics`
- `DELETE /api/v1/projects/{project_id}/permanent`
- `POST /api/v1/projects/{project_id}/reactivate`
- `POST /api/v1/projects/{project_id}/sync`
- `POST /api/v1/projects/{team_id}/projects`

### Students and users

- `GET /api/v1/students/`
- `POST /api/v1/students/`
- `GET /api/v1/students/{student_id}`
- `GET /api/v1/users/`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`

### Groups (teams)

- `POST /api/v1/teams/`
- `DELETE /api/v1/teams/{team_id}`
- `GET /api/v1/teams/{team_id}`
- `PUT /api/v1/teams/{team_id}`
- `GET /api/v1/teams/{team_id}/members`
- `DELETE /api/v1/teams/{team_id}/permanent`
- `POST /api/v1/teams/{team_id}/reactivate`
- `POST /api/v1/teams/{team_id}/run-checks`
- `GET /api/v1/teams/{team_id}/stream`
- `POST /api/v1/teams/{team_id}/sync`

### Compliance history

- `GET /api/v1/compliance/{course_id}/student/{student_id}`
- `GET /api/v1/compliance/{course_id}/trends`

### Observability

- `GET /api/v1/observability/status`

### Support tickets

- `PUT /api/v1/support/tickets/{ticket_id}`
- `POST /api/v1/support/tickets/delete`
- `POST /api/v1/support/tickets/purge`
- `GET /api/v1/support/tickets/{ticket_id}/comments`
- `POST /api/v1/support/tickets/{ticket_id}/comments`
- `POST /api/v1/support/upload`
- `GET /api/v1/support/{course_id}/responses`
- `GET /api/v1/support/{course_id}/stats`
- `POST /api/v1/support/{token}`


### Full course configuration (dashboard, JSON)

- `GET /dashboard/courses/{course_id}/settings/full-config` - export the complete
  course configuration. Returns course metadata, settings (including
  `enabled_checks`, `check_configs`), built-in check weights/configs, custom
  checks and weekly deadlines, under `$schema: "gitpulse/full-config/v2"`.
- `POST /dashboard/courses/{course_id}/settings/full-config` - import one.
  Form field `config_json` + `csrf_token`; every top-level section is optional;
  max 2 MB; **rejected with 409 on an archived course**.
- `GET /dashboard/courses/{course_id}/checks` - unified checks API (built-in
  R01-R13 + custom C01+) with one shape: `check_code`, `name`, `category`,
  `weight`, `is_active`, `check_config`.

## 6. Dashboard Routes

Dashboard routes are implemented as a modular package (`src/app/api/dashboard/`) with 16 modules:

| Module | Responsibility | Routes |
|--------|---------------|--------|
| `auth.py` | Login, OAuth, logout, language switch | 7 |
| `home.py` | Dashboard home orchestration, sidebar, search | 4 |
| `home_stats.py` | Role-specific dashboard stat-card SQL | - |
| `home_context.py` | Role-specific dashboard context and sidebar badges | - |
| `home_changelog.py` | Dashboard Latest changes entries and localization | - |
| `home_course_health.py` | Per-course RED-team health for course cards | - |
| `course_settings.py` | Course configuration | 6 |
| `course_checks.py` | Built-in + custom checks CRUD | 9 |
| `courses.py` | Course detail, activity, roster, lifecycle | - |
| `teams.py` | Team routes | 9 |
| `projects.py` | Project routes | 6 |
| `students.py` | Student detail | - |
| `admin.py` | Admin routes | 13 |
| `_helpers.py` | Shared helpers (templates, CSRF, role context) | - |
| `_access.py` | Access control helpers | - |
| `__init__.py` | Aggregates sub-routers | - |

**Worker cache helpers:** GitLab sync jobs keep dashboard page-cache
invalidation in `src/app/workers/sync_cache.py`, so full-team and per-project
sync can share the same project/team/course/student invalidation contract
without duplicating cache plumbing in `sync_job.py`.

**Support dashboard routes** (in `auth.py`):

| Route | Auth | Description |
|-------|------|-------------|
| `GET /dashboard/support` | DashboardAuth (any user) | Support form submission page (3-step flow) |
| `GET /dashboard/support/tickets` | TeacherAuth | Ticket list with filters and pagination |
| `GET /dashboard/support/ticket/{ticket_id}` | TeacherAuth | Individual ticket detail (GitHub-style) |

Routes include UI pages plus JSON endpoints under `/dashboard/*` for live updates (course/team/project detail, LLM job status, admin enrichment status, exports, and support flows).

### 6.1 Session Health Check

- `GET /dashboard/session-check` - Lightweight session validity check (no DB queries).
  - **200:** `{"status": "ok", "user": "<username>", "v": "<BUILD_HASH>"}` - session cookie is valid. The `v` field contains the current deployment fingerprint for client-side version detection.
  - **401:** `{"status": "expired"}` - session cookie is missing, expired, invalid, boot-nonce mismatch, or build-hash mismatch.
  - Used by the client-side health heartbeat (every ~60 s) to detect stale sessions and trigger auto-logout. Also used for client-side version detection - `core.js` compares the `v` field against the embedded `<meta name="app-version">` tag.

### 6.2 Global Search

- `GET /dashboard/search` - Role-aware search across users, courses, teams, and students.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | `""` | Search query (max 200 chars). Empty returns empty results. |
| `scope` | string | `all` | One of `all`, `pages`, `users`, `courses`, `students`. |

**Scope access rules:**

| Scope | Accessible by | Notes |
|-------|---------------|-------|
| `all` | All roles | Hybrid: searches all entity types the caller can access |
| `pages` | All roles | Client-side only; backend returns empty |
| `users` | Admin, Teacher | System user search (name, username, email) |
| `courses` | All roles | Courses + teams filtered to caller's accessible courses |
| `students` | All roles | Students within accessible courses (via team membership) |

**Response shape:**

```json
{
  "users": [
    { "id": "uuid", "username": "jdoe", "name": "John Doe", "email": "j@example.com",
      "role": "student", "avatar_url": "", "href": "/dashboard/admin/users" }
  ],
  "courses": [
    { "id": "uuid", "code": "ZSI", "name": "Základy softvérového inžinierstva",
      "year": "2025/2026", "semester": "winter", "active": true,
      "href": "/dashboard/courses/<id>" }
  ],
  "teams": [
    { "id": "uuid", "name": "Team Alpha", "course_id": "uuid",
      "course_name": "ZSI", "href": "/dashboard/teams/<id>" }
  ],
  "students": [
    { "id": "uuid", "username": "student1", "name": "Student Name",
      "team": "Team Alpha", "team_id": "uuid",
      "href": "/dashboard/students/<id>/team/<team_id>" }
  ]
}
```

**Frontend scope prefixes** (typed in the search input):

| Prefix | Scope | Example |
|--------|-------|---------|
| `>` | Pages | `>settings` |
| `@` | Users | `@john` (admin/teacher only) |
| `:` | Courses | `:ZSI` |
| `#` | Students | `#smith` |

The search palette UI (`search-palette.js`) is built from the shared components, as GitLab's is: the borderless `search_input`, a Filters dropdown in the field whose items type the prefix, and results as dropdown items under group headers with the shared avatar and `role_badge` colours. ↓ moves focus into the results, ↑ from the first one back to the field, Esc closes, "/" opens.

Use runtime OpenAPI for exact request/response models.

## 7. OpenAPI Export (Repeatable)

To inspect the live contract locally:

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

## 8. Notes on DTO and Validation Consistency

Current backend standard:

1. Route DTOs are defined in `src/app/schemas/*` (not inline in routers).
2. Route errors use shared factories in `src/app/api/errors.py`.
3. API errors are rendered via unified `ErrorResponse` contract.

This ensures consistent client behavior and easier maintenance.
