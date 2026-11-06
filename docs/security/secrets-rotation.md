# Secrets Rotation Runbook

This document describes how to safely rotate every secret used by the
application in production.  All rotations are designed to be possible
without taking the public site offline (zero-downtime), with the
exception of `SECRET_KEY` rotation which invalidates active session
cookies.

> **Generate strong values** (32+ bytes hex):
>
> ```powershell
> python -c "import secrets; print(secrets.token_hex(32))"
> ```
> or
> ```bash
> openssl rand -hex 32
> ```

---

## Rotation triggers

Rotate immediately if any of the following happens:

- An operator with knowledge of the secrets leaves the team.
- A secret is accidentally committed to git, pasted into chat, or
  printed in logs that leave the host.
- A backup containing `.env` is suspected of having leaked.
- An unexpected access pattern is observed (auth failures, unfamiliar
  IPs in `audit_log`, GitLab API calls outside business hours).
- Periodically: every 90 days for `TEACHER_API_TOKEN` /
  `LLM_API_KEY` / `SMTP_PASSWORD`, every 180 days for the rest.

---

## Rotation order during an incident

If multiple secrets must be rotated together, do them in this order to
minimise the window of vulnerability:

1. `POSTGRES_PASSWORD` (rotate inside the DB first, then update env).
2. `REDIS_PASSWORD`.
3. `GITLAB_OAUTH_CLIENT_SECRET`.
4. `GITLAB_API_TOKEN`.
5. `TEACHER_API_TOKEN`.
6. `LLM_API_KEY`, `SMTP_PASSWORD`.
7. Per-course `webhook_secret` (use the dashboard rotate-webhook
   button - it does dual-secret bcrypt hashing automatically).
8. `SECRET_KEY` last (forces every user to log in again, so do this
   off-hours).

---

## SECRET_KEY

Used to sign session cookies (itsdangerous), CSRF tokens, and the
pre-login nonce.

**Effect of rotation:** all existing session cookies become invalid,
all users get logged out and have to re-authenticate.  Active CSRF
tokens are also invalidated, which means any in-progress form
submission will fail with a CSRF error and need to be retried.

```bash
NEW_SECRET=$(openssl rand -hex 32)
# Update .env
sed -i.bak "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_SECRET}/" /opt/gitpulse/.env
# Restart the API tier (worker / scheduler do not need restart for
# this - they don't sign cookies)
docker compose restart api
```

---

## TEACHER_API_TOKEN

Bearer token consumed by the teacher CLI / scripts and the public API
contract tests.

**Effect of rotation:** any external script using the old token will
get 401 until updated.

```bash
NEW_TOKEN=$(openssl rand -hex 32)
sed -i.bak "s/^TEACHER_API_TOKEN=.*/TEACHER_API_TOKEN=${NEW_TOKEN}/" /opt/gitpulse/.env
docker compose restart api worker scheduler
```

Notify all teacher-CLI users out-of-band (email / chat) and ask them
to update their local `.env`.

---

## GITLAB_API_TOKEN

Personal-access token used by the worker for project / member /
membership sync.

**Effect of rotation:** background sync stops working until the new
token is in place.  Webhook ingestion is **not** affected (webhooks
authenticate using per-course secrets, not the API token).

```bash
# 1. In GitLab -> User Settings -> Access Tokens -> revoke old
# 2. Generate new token with scopes: api, read_user, read_repository
# 3. Update env
sed -i.bak "s/^GITLAB_API_TOKEN=.*/GITLAB_API_TOKEN=${NEW_TOKEN}/" /opt/gitpulse/.env
docker compose restart api worker scheduler
```

---

## GITLAB_OAUTH_CLIENT_SECRET

Used for the dashboard OAuth login flow.

**Effect of rotation:** in-flight OAuth handshakes (within the 60 s
state-token window) will fail; users that are already logged in keep
their session.  Newly initiated logins require the new secret.

```bash
# 1. In GitLab -> Admin -> Applications -> your OAuth app -> "Renew
#    secret".  Copy the new value.
# 2. Update env
sed -i.bak "s/^GITLAB_OAUTH_CLIENT_SECRET=.*/GITLAB_OAUTH_CLIENT_SECRET=${NEW_SECRET}/" /opt/gitpulse/.env
docker compose restart api
```

---

## LLM_API_KEY

API key for OpenAI / Gemini / Groq / Azure OpenAI.

**Effect of rotation:** in-flight LLM analyses will fail with 401 on
the next call (RQ will retry per its retry policy).

```bash
# 1. Revoke the old key in the provider's dashboard.
# 2. Issue a new key.
sed -i.bak "s/^LLM_API_KEY=.*/LLM_API_KEY=${NEW_KEY}/" /opt/gitpulse/.env
docker compose restart api worker
```

---

## SMTP_PASSWORD

Outgoing-mail credential.

**Effect of rotation:** queued emails will start failing with 535
until the new password is in place.

```bash
sed -i.bak "s/^SMTP_PASSWORD=.*/SMTP_PASSWORD=${NEW_PW}/" /opt/gitpulse/.env
docker compose restart api worker
```

---

## REDIS_PASSWORD

Optional - only set if the Redis container is exposed beyond the
docker-compose `backend` network.

**Effect of rotation:** API / worker / scheduler must restart together
or they will fail to authenticate.  RQ jobs in flight are safe (RQ
reconnects on auth failure).

```bash
NEW_PW=$(openssl rand -hex 32)
sed -i.bak "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=${NEW_PW}/" /opt/gitpulse/.env
# Restart redis FIRST so the new password is enforced, then the
# clients pick up the matching env value.
docker compose up -d redis
docker compose restart api worker scheduler
```

---

## POSTGRES_PASSWORD

Master DB password for the application user.

**Effect of rotation:** the entire stack is offline until updated
(usually < 30 s).

```bash
NEW_PW=$(openssl rand -hex 32)
docker compose exec postgres psql -U postgres -c \
    "ALTER USER gitpulse WITH PASSWORD '${NEW_PW}';"
sed -i.bak "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${NEW_PW}/" /opt/gitpulse/.env
# Restart everything that opens DB connections
docker compose restart api worker scheduler
```

---

## Monitoring dashboards (Grafana / Prometheus / Jaeger / Alertmanager)

No shared secret: Caddy lets a request through only for a signed-in GitPulse
administrator (`forward_auth` to `/internal/monitoring-authz`). To cut
someone off, take away their admin role in GitPulse. Grafana's local `admin`
password (`GRAFANA_ADMIN_PASSWORD`, for 127.0.0.1:3000 on the host only) is
rotated with `grafana cli admin reset-admin-password` inside the container.

---

## Per-course GitLab webhook secret

Use the dashboard: **Course -> Settings -> Rotate webhook secret**.

The application supports zero-downtime rotation via dual-secret
bcrypt hashing:

1. The new secret is hashed into `webhook_secret_hash`.
2. The previous hash is preserved in `webhook_secret_hash_previous`
   for a configurable grace window (default 24 h, see
   `webhook_rotation_grace_hours`).
3. Incoming webhooks are accepted if they match either hash.
4. After the grace window elapses, the previous hash is cleared
   automatically by the scheduler sweep.

The old secret must be replaced inside GitLab before the grace
window elapses, otherwise webhooks will start being rejected with
401.

---

## Verification after rotation

After **any** rotation, verify the rotation succeeded:

```bash
# 1. Service health
curl -fsS https://<base-url>/healthz
# expected: {"status":"ready","database":"ready","redis":"ready"}

# 2. Login flow (manual smoke test)
#    - Open /dashboard/login
#    - Authenticate with OAuth
#    - Confirm landing on dashboard

# 3. Recent audit-log entries
docker compose exec postgres psql -U gitpulse -d gitpulse -c \
    "SELECT created_at, actor_user_login, action FROM audit_log
     ORDER BY created_at DESC LIMIT 20;"
```

Watch for an unexpected spike in 401 / 403 responses in Grafana
during the next hour.
