# Security Architecture

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


Multi-layered defense-in-depth for university VM deployment.

## Authentication Overview

### Three Authentication Mechanisms

| Mechanism | Header / Cookie | Used By | How to Obtain |
|-----------|-----------------|---------|---------------|
| **GitLab OAuth** | `session=<signed>` cookie | Dashboard (`/dashboard/*`) | Click "Login with GitLab" |
| **Bearer Token** | `Authorization: Bearer <token>` | API (`/api/v1/*`) | `TEACHER_API_TOKEN` env var |
| **Webhook Token** | `X-Gitlab-Token: <secret>` | Webhooks (`/api/v1/webhooks/gitlab`) | Generated per-project |
| **None** | - | Health, metrics | Public endpoints |

### GitLab OAuth Flow

```
1. User clicks "Login with GitLab"
2. Redirect to GitLab: /oauth/authorize?client_id=...&redirect_uri=...&scope=read_user
3. User authenticates with GitLab
4. GitLab redirects to: /dashboard/oauth/callback?code=...
5. Backend exchanges code for access token
6. Backend fetches user profile + groups
7. Access token encrypted via Fernet and stored in DB
8. Role determined (admin/teacher/student)
9. Session cookie set: signed payload or Redis-backed opaque sid with bn, av, ua claims
   (HttpOnly, Secure, SameSite=Lax, __Host- prefix, 30 d idle / 90 d absolute TTL)
```

### Role Assignment Priority

1. **Admin** - Username in `GITLAB_ADMIN_USERNAMES`
2. **Teacher** - Username in `GITLAB_TEACHER_USERNAMES` OR member of groups in `GITLAB_TEACHER_GROUP_IDS`
3. **Student** - Any authenticated GitLab user

### API Auth Levels

| Dependency | Access Level | Used By |
|------------|--------------|---------|
| `ApiAuth` | Any valid Bearer OR session | Read endpoints |
| `ApiTeacherAuth` | Bearer OR session with teacher/admin | Write endpoints |
| `ApiAdminAuth` | Bearer OR session with admin | User management |

## Threat Model (STRIDE)

### Spoofing (Identity)

| Threat | Mitigation | Residual Risk |
|--------|------------|---------------|
| Unauthorized dashboard access | GitLab OAuth, signed session cookies, RBAC | GitLab account compromise |
| Forged webhook events | Per-project webhook secret (bcrypt) | Secret leak; rotate via runbook |
| API token theft | Bearer token via `hmac.compare_digest()` | Token in env; restrict access |
| Session hijacking | HttpOnly, Secure, SameSite=Lax, `__Host-` prefix (HTTPS), UA fingerprint binding | XSS (mitigated by CSP) |

### Tampering

| Threat | Mitigation | Residual Risk |
|--------|------------|---------------|
| CSRF on dashboard forms | HMAC-SHA256 CSRF tokens + SameSite=Lax | Requires feature flag enabled |
| Webhook payload modification | SHA-256 hash stored immutably | None significant |
| Session cookie tampering | itsdangerous URLSafeTimedSerializer | Secret key compromise |

### Repudiation

| Threat | Mitigation |
|--------|------------|
| Denied admin actions | Audit log (`FEATURE_EVENT_PIPELINE`), structured JSON logging |
| Untracked changes | Settings, webhook configuration, and sync actions are audit logged |

### Information Disclosure

| Threat | Mitigation |
|--------|------------|
| Student data exposure | TLS (Caddy automatic HTTPS), HSTS, HttpOnly cookies |
| GitLab token leak | Env vars only, `.env` in `.gitignore`, Fernet encryption at rest |
| API docs in production | OpenAPI disabled when `APP_ENV != development` |
| LLM data leakage | PII redaction before sending to LLM provider |
| Private data indexed by search engines or scraped by AI bots | **Search Indexation Controls**: `X-Robots-Tag: noindex, nofollow, noarchive` enforced via `SecurityHeadersMiddleware` for `/dashboard/*` (except login) and all `/api/*` endpoints. A dynamic `/robots.txt` explicitly disallows private paths, `/sitemap.xml` lists only public pages, and `/llms.txt` sets strict boundaries for AI agents. |

### Denial of Service

| Threat | Mitigation |
|--------|------------|
| Brute-force login | App rate limiting: 10 req/min per IP |
| Webhook flooding | Caddy: 60 req/min; app: 10 req/min |
| Resource exhaustion | Docker memory limits (256-512MB); 1MB payload limit |
| Queue flooding | Backpressure controls (`FEATURE_BACKPRESSURE`) |

### Elevation of Privilege

| Threat | Mitigation |
|--------|------------|
| Student -> admin | RBAC role checks via `require_role()` |
| Container escape | Read-only filesystem; non-root user |
| Network lateral movement | Docker network isolation |

## Security Controls by Layer

### Network (Docker Compose)

- **3-tier network isolation**: `frontend`, `backend`, `data`
- All ports bound to `127.0.0.1` except Caddy 80/443
- `/metrics` blocked from public by Caddy
- PostgreSQL on internal-only network
- Redis requires `REDIS_PASSWORD` in production and the app refuses
  passwordless `REDIS_URL` when `APP_ENV=production`

### Reverse Proxy (Caddy)

- Automatic TLS via Caddy for real domains and localhost. If TLS is terminated
  by an upstream proxy, operators must set `CADDY_SITE_ADDRESS=http://...`
  while keeping `APP_BASE_URL=https://...`.
- Security headers (CSP, HSTS, X-Frame-Options)
- Public `/metrics` blocked at the proxy; Prometheus scrapes the internal API
- `Server` header removed
- Request size limits

### Application (FastAPI)

```python
# Security headers on all responses (SecurityHeadersMiddleware)
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-<per-request>' 'strict-dynamic'; style-src 'self' 'unsafe-inline' <style-origins>; img-src 'self' data: <img-origins> <gitlab-origin>; font-src 'self' <font-origins>; connect-src 'self' <gitlab-origin>; frame-ancestors 'none'; base-uri 'self'; form-action 'self' <gitlab-origin>
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
X-App-Version: <BUILD_HASH>   # 12-char deploy fingerprint for client version detection
Cache-Control: no-store, no-cache, must-revalidate, private  # on /dashboard/* paths
X-Robots-Tag: noindex, nofollow, noarchive  # on all authenticated routes, APIs, webhook, and health endpoints
```

CSP is **dynamically constructed** at startup from the configured `GITLAB_URL`
origin and CDN constants in `app.utils.constants`. The GitLab origin is injected
into `img-src`, `connect-src`, and `form-action` directives so that OAuth
redirects and avatar images work without CSP violations.

#### Script CSP enforcement

All authentication and dashboard pages use `@alpinejs/csp` 3.17.5. There is
one script policy, enforced on every response:

```
script-src 'self' 'nonce-<per-request-value>' 'strict-dynamic';
report-uri /csp/report; report-to csp-endpoint
```

`SecurityHeadersMiddleware` generates the nonce and exposes it to Jinja as
`csp_nonce`. External scripts and JSON data islands carry that nonce. The
page cache substitutes a fresh nonce when serving cached HTML. Scripts cannot
use `eval`, `Function` or inline event handlers.

`Reporting-Endpoints: csp-endpoint="/csp/report"` directs browser violations to
the structured, deduplicated CSP report handler. Styles currently allow inline
values for dynamic layout and progress properties.

`scripts/vendor_alpine_csp.py` verifies both the upstream and installed SHA-256
for Alpine and its matching collapse plugin. Its documented local patch skips
the deprecated `window.fence` getter during Alpine's global-value collection;
the application does not use that advertising API.

Shared components and page factories register through `Alpine.data` and
`Alpine.magic`; delegated `data-action` handlers cover ordinary buttons.

### Token Encryption at Rest

GitLab OAuth access tokens are encrypted before storage using **Fernet**
(AES-128-CBC + HMAC-SHA256) via the `token_encryption` module:

- Fernet key is derived from `SECRET_KEY` using **HKDF** (HMAC-based Key Derivation)
  with a static salt (`dta-token-encryption-v1`) and info context (`gitlab-oauth-tokens`).
- Encrypted tokens are stored with the prefix `enc:v1:<base64-ciphertext>`.
- Encryption is **idempotent** - already-encrypted values pass through unchanged.
- Legacy plaintext tokens are transparently decrypted with a warning log for migration.

### Data

- bcrypt password hashing
- Webhook secrets stored as bcrypt hashes plus deterministic HMAC lookup columns for indexed authentication
- Rotated previous webhook secrets are accepted only until `webhook_secret_previous_expires_at`; the cleanup sweep clears expired previous hashes/lookups
- Secrets via environment variables only
- `redeploy.py` uses OpenSSH with deploy keys or the SSH agent; production SSH passwords are intentionally unsupported and unknown host keys are rejected by default
- GitLab OAuth tokens encrypted at rest (Fernet - see Token Encryption above)
- PII redaction before LLM calls

## Session Hardening

The default session cookie is a signed `itsdangerous` payload. When
`FEATURE_REDIS_SESSIONS=true`, the cookie carries a signed opaque sid and Redis
stores the server-side payload. Both modes share the same multi-layer
invalidation controls:

### Cookie attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| Name | `__Host-gitpulse_session` (HTTPS) / `gitpulse_session` (HTTP) | `__Host-` prefix enforces Secure + Path=/ + no Domain |
| HttpOnly | `true` | Prevents JS access |
| Secure | `true` (HTTPS) | Cookie only sent over TLS |
| SameSite | `Lax` | CSRF protection while allowing top-level navigations |
| Max-Age | 2 592 000 s (30 days idle) | Configurable via `SESSION_MAX_AGE_SECONDS` |
| Path | `/` | Required by `__Host-` prefix |

### Session payload claims

| Claim | Value | Purpose |
|-------|-------|---------|
| `user` | GitLab username | Identity |
| `role` | `admin` / `teacher` / `student` | Authorization |
| `bn` | 16-char hex boot nonce | Rejects sessions from a previous server process |
| `av` | 12-char `BUILD_HASH` | Rejects sessions from a different deployment |
| `ua` | SHA-256(User-Agent)[:16] | Detects session cookie theft across browsers |
| `ts` | ISO 8601 timestamp | Session creation time |

### Invalidation layers

1. **Idle max-age** - signed cookies and Redis session records expire after 30 days without activity.
2. **Boot nonce (`bn`)** - Each worker process generates a secret nonce at startup;
   server restart invalidates all sessions (unless `PERSISTENT_SESSIONS=true`).
3. **Build hash (`av`)** - Sessions embed the deploy fingerprint; a redeploy
   creates a new `BUILD_HASH`, rejecting all old sessions as defence-in-depth.
4. **UA fingerprint (`ua`)** - SHA-256 hash of the User-Agent string; a cookie
   presented from a different browser is rejected.
5. **Absolute TTL** - `SESSION_ABSOLUTE_MAX_AGE_SECONDS` defaults to 90 days and rejects sessions older than that regardless of refresh activity.
6. **Signature** - HMAC signature via `itsdangerous`; tampered cookies are rejected.

### Logout behaviour

`GET /dashboard/logout` performs a clean logout:

1. Deletes the session cookie (both `__Host-` prefixed and unprefixed names for
   transitional compatibility).
2. Sends `Clear-Site-Data: "cache", "storage"` header - instructs the browser to
   purge all cached pages and local/sessionStorage (Chrome 77+, Firefox 94+, Edge 79+).
3. The Service Worker deliberately bypasses `/dashboard` navigations and refuses
   to store responses marked `no-store` or `private`, so authenticated HTML is
   not retained in the browser Cache API.

## Client-Side Version Detection

The application implements automatic detection of stale client pages after deployment:

1. **`<meta name="app-version">`** tag in `base.html` contains the current `BUILD_HASH`.
2. **`X-App-Version`** response header is set on every HTTP response by `SecurityHeadersMiddleware`.
3. **`core.js` version check** (`_checkVersionHeader()`) - runs after every
   `apiCall()`, htmx `afterRequest` event, and `/dashboard/session-check` poll.
   Compares the header value against the embedded `<meta>` tag.
4. On **mismatch** -> shows a toast "A new version is available" and auto-reloads
   the page after 3 seconds for a seamless UX during rolling deploys.
5. **Session-check endpoint** returns `{"status":"ok","user":"...","v":"<BUILD_HASH>"}`
   - the `v` field enables version detection even for cached pages that don't
   make API calls.

### Container

- Read-only filesystem (API container)
- Memory limits on all containers
- `tmpfs` for writable `/tmp`
- Non-root user in containers

## Feature Flags

| Flag | Default | Controls |
|------|---------|----------|
| `FEATURE_SECURITY_HARDENING` | `true` | CSRF + app-level rate limiting |
| `FEATURE_RBAC` | `true` | Role-based access control |
| `FEATURE_EVENT_PIPELINE` | `true` | DLQ, replay, audit log |

## Deployment Checklist

### Pre-Deployment

- [ ] Generate SECRET_KEY: `openssl rand -hex 32`
- [ ] Generate TEACHER_API_TOKEN: `openssl rand -hex 24`
- [ ] Create GitLab OAuth application
- [ ] Set `GITLAB_OAUTH_CLIENT_ID` and `GITLAB_OAUTH_CLIENT_SECRET`
- [ ] Set `GITLAB_ADMIN_USERNAMES` and `GITLAB_TEACHER_USERNAMES`
- [ ] Set `ALLOWED_HOSTS` to actual domain
- [ ] Verify `.env` is in `.gitignore`

### Post-Deployment

- [ ] Verify HTTPS works (Caddy auto-certificate)
- [ ] Test GitLab OAuth login flow
- [ ] Test RBAC role assignment
- [ ] Verify `/metrics` is not publicly accessible
- [ ] Test webhook token verification
- [ ] Run security scan: `python scripts/security_scan.py`

## Secret Rotation Runbook

### Rotate TEACHER_API_TOKEN

```bash
# 1. Generate new token
NEW_TOKEN=$(openssl rand -hex 24)

# 2. Update .env
sed -i "s/TEACHER_API_TOKEN=.*/TEACHER_API_TOKEN=$NEW_TOKEN/" .env

# 3. Restart API
docker compose up -d api

# 4. Update any external integrations using the token
```

### Rotate Webhook Secret (per project)

Per-project webhook secrets are generated on import and verified by the
delivery path; rotation is no longer exposed via UI/API. Use **Settings ->
Webhook Configurations** to manage scope-based (course/group/sub-group)
webhook secrets, which support 24h grace-window rotation through the
dashboard.

### Rotate GitLab OAuth Credentials

```bash
# 1. Create new OAuth app in GitLab
# 2. Update .env with new credentials
# 3. Restart API
docker compose up -d api
# 4. Delete old OAuth app in GitLab
```

## Incident Response

### Suspected Token Leak

1. Immediately rotate the leaked token
2. Check audit logs for unauthorized access
3. Review recent API calls with the token
4. Notify affected users if necessary

### Suspicious Activity

1. Check structured logs for anomalies
2. Review rate limit events
3. Check circuit breaker status
4. Block suspicious IPs at Caddy level if needed

### Data Breach

1. Disable affected accounts
2. Rotate all secrets
3. Review audit logs
4. Notify data protection officer
5. Document incident timeline

## Security Testing

### Automated Tests

```bash
# Run security-focused tests
pytest tests/unit/test_security.py -v

# Run RBAC tests
pytest tests/unit/test_rbac.py -v

# Run GitLab OAuth tests
pytest tests/unit/test_gitlab_oauth.py -v
```

### Manual Testing

```bash
# Test CSRF protection
curl -X POST http://localhost:8000/dashboard/settings \
  -H "Cookie: session=..." \
  -d "setting=value"
# Should fail without CSRF token

# Test rate limiting
for i in {1..20}; do curl http://localhost:8000/dashboard/login; done
# Should get 429 after 10 requests

# Test auth bypass
curl http://localhost:8000/api/v1/courses
# Should get 401 Unauthorized
```

## Compliance

### GDPR Considerations

- Student data stored only with consent (via GitLab OAuth)
- PII redacted before LLM processing
- Data retention policies enforced
- Audit logging for accountability
- Right to deletion available via admin API

### University IT Policy

- All traffic encrypted (TLS)
- Authentication via institutional GitLab
- No passwords stored (OAuth only)
- Secrets in environment variables (not code)
- Container isolation for security


## Roadmap: deferred performance & defence-in-depth items

### ARCH-01 / ARCH-07: worker DB engine and asyncio loop reuse

Every RQ job currently calls `init_engine` then `dispose_engine` and wraps`the body in `asyncio.run(...)`.  This creates a new SQLAlchemy engine`+ connection pool and a new asyncio event loop per job, which:

- Burns 50-200 ms per job on engine init / pool creation`- Closes asyncpg connections immediately after every job, preventing pool reuse`- Re-creates httpx clients (no keep-alive across jobs)

**Plan:** introduce `app.workers.runner` with a long-lived asyncio loop
started in `workers/main.py`.  Jobs become `loop.run_until_complete(coro)`.`Engine init happens once during worker startup; `dispose_engine` runs on`SIGTERM only.  Httpx `AsyncClient` is also moved to the runner scope.`Risk: incompatible with `rq.Worker` fork mode on POSIX - sticking with`SimpleWorker (already used on Windows) for cross-platform consistency.

**Effort:** ~1 day refactor + thorough load test.  Tracked SEC/ARCH backlog.

### SEC-03 CSP unsafe-eval removal

Completed for `script-src`; the enforced policy now uses nonce + `strict-dynamic`.
Remaining CSP hardening is limited to deferred `style-src` cleanup.

### #6 server-side session store (Implemented)

Authenticated session cookies historically carried the full signed
payload (stateless `itsdangerous`).  A Redis-backed store now provides:

- **instant revocation** - `RedisSessionStore.revoke()` deletes the
  server-side record so a stolen cookie cannot be replayed before its
  cookie-level expiry;
- **force-logout-everywhere** - `revoke_all_for_user(user_id)` walks the
  per-user secondary index `session:user:<uid>` and deletes every active
  session in one round-trip;
- **smaller cookies** - the cookie now carries only an HMAC-signed 24 B
  opaque sid (~80 chars on the wire) instead of the ~400 char stateless
  payload;
- **no migration break** - when the store is enabled the loader still
  accepts legacy stateless cookies during the rollout window so users
  do not get logged out at deploy time.

**Implementation:** `src/app/security/session_store.py` defines
`RedisSessionStore` with a narrow `_RedisLike` Protocol so tests can
inject an in-memory fake.  Cookies are signed with `URLSafeSerializer`
keyed by `Settings.secret_key` so a tampered sid is rejected before any
Redis round-trip (constant-time signature check).  TTL is refreshed on
a sliding window controlled by `SESSION_REDIS_IDLE_REFRESH_SECONDS`
(default 300) to avoid an `EXPIRE` per request.

**Failure mode:** if Redis is unreachable the store fails *closed* on
read (`load -> None` => "not authenticated") and *gracefully* on write
(`create_session_cookie` falls back to the legacy stateless cookie path
so logins still succeed during a transient outage). Each fallback increments
`session_store_fallback_total{reason=...}` and emits an alertable warning log.
Readiness performs a short write/read/delete probe for the session store only
when `FEATURE_REDIS_SESSIONS=true`.

**Operator rollout:**

1. Deploy with `FEATURE_REDIS_SESSIONS=true` and a password-protected Redis URL.
   Production startup refuses `FEATURE_REDIS_SESSIONS=false`.
2. Existing browsers keep working - legacy cookies still validate; new logins
   write to Redis.
3. After 30 days (longer than `SESSION_MAX_AGE_SECONDS`) every active
   session is server-side.  At this point you may rotate `SECRET_KEY`
   to invalidate any leaked legacy cookies - Redis-backed sids stay
   valid because they live in the store, not the cookie.

**Settings:**

| Setting | Default | Purpose |
|---|---|---|
| `FEATURE_REDIS_SESSIONS` | `true` | Master switch; required in production. |
| `SESSION_REDIS_KEY_PREFIX` | `session:` | Redis namespace. |
| `SESSION_REDIS_IDLE_REFRESH_SECONDS` | `300` | Sliding-TTL refresh cadence. |
| `SESSION_MAX_AGE_SECONDS` | `2592000` | Idle TTL for cookie and Redis session records. |
| `SESSION_ABSOLUTE_MAX_AGE_SECONDS` | `7776000` | Hard ceiling on a single session lifetime. |

### #29 Caddy internal TLS

Caddy <-> upstream containers currently speak HTTP on the internal docker`network.  Issuing internal CA certs (`tls internal`) raises bar against`container-network sniffing.  Effort: 0.5 day; defer until production`threat model demands it.

### #30 PostgreSQL `sslmode=require`

DB driver currently does not enforce TLS to PostgreSQL.  Generate a server`cert via `openssl`, mount into `postgres` container, append `?sslmode=require`
to DATABASE_URL.  Defer until #29 (Caddy internal TLS) - same threat model.
