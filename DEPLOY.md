# Deployment Guide - GitPulse on Ubuntu 24.04 VM

Target machine: `svra-ubuntu-server-0261` / `147.232.205.227`  
Public URL: `https://gitpulse.kpi.fei.tuke.sk`  
OS: Ubuntu 24.04 LTS, 4 CPU, 8 GB RAM, 250 GB disk

---

## 1. SSH to the VM

```bash
ssh mo562nu@147.232.205.227
```

## 2. Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install prerequisites
sudo apt install -y ca-certificates curl gnupg git

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repo
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow current user to run Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

## 3. Clone the repository

```bash
cd ~
git clone https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/workspace/workspace.git gitpulse
cd gitpulse
```

## 4. Configure production environment

The `.env.production` file is already prepared in the repo.  
Copy it and review:

```bash
# The file should already exist. If not, create from the template:
# cp .env.production.example .env.production

# Verify it exists
cat .env.production | head -20
```

**IMPORTANT**: Before deploying, update the OAuth redirect URI in GitLab:
1. Go to https://gitlab.example.com -> **Admin Area** -> **Applications** (or your user OAuth app)
2. Edit the GitPulse OAuth application
3. Change the **Redirect URI** to:  
   `https://gitpulse.kpi.fei.tuke.sk/dashboard/oauth/callback`
4. Save

## 5. Open firewall ports

```bash
# Allow HTTP and HTTPS (Caddy handles TLS automatically)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow ssh
sudo ufw enable
```

## 6. First deployment

```bash
cd ~/gitpulse

# Build images (takes a few minutes on first run)
docker compose --env-file .env.production build

# Start all services
docker compose --env-file .env.production up -d

# Wait for PostgreSQL to be healthy
sleep 10

# Run database migrations
docker compose --env-file .env.production run --rm migrate

# Import course configurations (ZSI + DevOps fixtures)
docker compose --env-file .env.production exec api python -m scripts.import_course_configs

# Check health
curl -s http://localhost:8000/health | python3 -m json.tool
```

If you have PowerShell installed on the VM (optional):
```powershell
.\deploy-production.ps1 -Build -Migrate -ImportConfigs
```

## 7. Verify deployment

```bash
# Check all containers are running
docker compose --env-file .env.production ps

# Expected services: api, worker, gitpulse-docs, postgres, redis, caddy
# All should show "Up" or "healthy"

# Check health endpoint
curl -s https://gitpulse.kpi.fei.tuke.sk/health | python3 -m json.tool

# Check logs for errors
docker compose --env-file .env.production logs --tail=50 api
```

Open in browser: `https://gitpulse.kpi.fei.tuke.sk/dashboard/`

### Monitoring access

`/grafana/`, `/prometheus/`, `/jaeger/` and `/alertmanager/` open for a
GitPulse **administrator** who is signed in to GitPulse - there is no password
of their own. Caddy asks the application before every request there
(`forward_auth` to `/internal/monitoring-authz`, see
`src/app/api/monitoring_authz.py`): an admin session is served, a missing one
is sent to sign in and back, any other role gets 403. Grafana signs the same
login in through its auth proxy (`GF_AUTH_PROXY_*` in `docker-compose.yml`) and
makes it an Admin of the main org on the first visit.

The gate fails closed: while the application is down the tools are closed too.
On the host they stay reachable without it, e.g. over an SSH tunnel:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 -L 16686:127.0.0.1:16686 root@<host>
# Grafana http://localhost:3000/grafana/ (local `admin`, GRAFANA_ADMIN_PASSWORD),
# Prometheus http://localhost:9090/, Jaeger http://localhost:16686/jaeger/
```

## 8. Start with monitoring (optional)

```bash
docker compose --env-file .env.production --profile monitoring up -d
```

This adds:
- **Grafana**: http://localhost:3000 (admin/admin, via SSH tunnel)
- **Prometheus**: http://localhost:9090 (via SSH tunnel)
- **Jaeger**: http://localhost:16686 (via SSH tunnel)

Note: monitoring ports are bound to `127.0.0.1` - access via SSH tunnel if needed:
```bash
ssh -L 3000:localhost:3000 -L 9090:localhost:9090 -L 16686:localhost:16686 mo562nu@147.232.205.227
```

---

## Routine Operations

### View logs
```bash
docker compose --env-file .env.production logs -f           # All services
docker compose --env-file .env.production logs -f api       # API only
docker compose --env-file .env.production logs -f worker    # Workers only
```

### Restart a service
```bash
docker compose --env-file .env.production restart api
```

The image contains Python bytecode and a Jinja bytecode cache, built from the
same template sources and filters the API uses. The Jinja cache lives at
`/app/template-cache`, outside the host-mounted templates directory, and is
readable by the `app` user on the read-only filesystem. Missing or changed
templates fall back to normal compilation without runtime writes.

Gunicorn preloads the application once before forking four Uvicorn workers.
This avoids four simultaneous imports of the same routers and models. Database
and Redis pools are created in each worker's ASGI lifespan, after the fork.
Each worker loads its templates and prepares the ORM before completing
startup and accepting requests. The database warm-up has a five-second limit;
if the database is unavailable, `/health/ready` still reports it as not ready.
The `process_warmed` log precedes Uvicorn's startup-complete message.

Caddy checks `/health/live` every second and resumes forwarding as soon as the
API is ready. Its retry window covers a normal cold boot. Measure that window
from the restart itself: querying only after `/health/ready` succeeds misses
startup delay and the proxy's recovery interval.

### Update and redeploy
```bash
cd ~/gitpulse
git pull
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d
docker compose --env-file .env.production run --rm migrate
```

### Local redeploy helper

`redeploy.py` runs the production pull, rebuild, migration and health-check
sequence over OpenSSH. Keep SSH credentials out of the repository and use a
deploy key or SSH agent:

```bash
export DEPLOY_HOST=147.232.205.227
export DEPLOY_USER=root
export DEPLOY_SSH_KEY_FILENAME="$HOME/.ssh/gitpulse_deploy"
git push origin main
python redeploy.py
```

Commit and push the release before running the helper. It requires a clean
tracked production checkout and a fast-forward pull matching the local commit;
it never stashes production changes. Every remote command runs in Bash with
failure and pipeline checks enabled.

The helper builds documentation before replacing its container, drains workers,
and runs and verifies migrations in the newly built image before replacing the
serving API. It checks the running commit and application version, then waits
for a successful readiness response with bounded retries. A failed step stops
the release. Routine builds reuse dependency layers keyed by `requirements.lock`;
use `python redeploy.py --no-cache` only when a complete rebuild is needed.

Supported variables:

| Variable | Default | Notes |
| --- | --- | --- |
| `DEPLOY_HOST` | `147.232.205.227` | Production SSH host. |
| `DEPLOY_SSH_PORT` | `22` | SSH port. |
| `DEPLOY_USER` | `root` | SSH user. |
| `DEPLOY_APP_PATH` | `/root/devops-teaching-assistant` | App path on the host. |
| `DEPLOY_SSH_KEY_FILENAME` | unset | Preferred authentication method. |
| `DEPLOY_SSH_STRICT_HOST_KEY` | `true` | Rejects unknown host keys by default. |

`DEPLOY_SSH_PASSWORD` is intentionally unsupported. Do not pass production SSH
passwords to process environments; create a restricted deploy key instead.

With strict host-key checking, add the production host to `known_hosts` before
the first run:

```bash
ssh-keyscan -H "$DEPLOY_HOST" >> ~/.ssh/known_hosts
```

### Stop all services
```bash
docker compose --env-file .env.production down
```

### Database backup
```bash
docker compose --env-file .env.production exec postgres pg_dump -U gitpulse gitpulse > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database restore
```bash
cat backup_YYYYMMDD_HHMMSS.sql | docker compose --env-file .env.production exec -T postgres psql -U gitpulse gitpulse
```

### Automated nightly backups (recommended)

`scripts/backup.sh` performs `pg_dump` + 14-day retention.  Schedule it
via `cron` on the host:

```cron
# /etc/cron.d/gitpulse-backup
# Run nightly at 03:15 UTC, log to /var/log/gitpulse-backup.log
15 3 * * *  root  /opt/gitpulse/scripts/backup.sh /var/backups/gitpulse >> /var/log/gitpulse-backup.log 2>&1
```

After installing, verify with:
```bash
sudo systemctl status cron
sudo run-parts --test /etc/cron.d
ls -lh /var/backups/gitpulse | tail
```

Restore from the latest dump:
```bash
zcat /var/backups/gitpulse/$(ls -t /var/backups/gitpulse | head -1) \
  | docker compose --env-file .env.production exec -T postgres psql -U gitpulse gitpulse
```

---

## Database connection pool sizing

The total number of Postgres connections an API replica can open is:

```
max_connections_per_replica = (DB_POOL_SIZE + DB_MAX_OVERFLOW) × UVICORN_WORKERS
```

Multiply by the number of API containers and add the worker pool to get
the cluster total:

```
cluster_total = api_replicas × (DB_POOL_SIZE + DB_MAX_OVERFLOW) × UVICORN_WORKERS
              + worker_replicas × (worker pool_size + max_overflow)
```

### Defaults
| Setting                                   | Default | Where                                   |
|-------------------------------------------|---------|-----------------------------------------|
| `DB_POOL_SIZE` + `DB_MAX_OVERFLOW`        | 12 + 4  | `src/app/config.py`, per API process    |
| `UVICORN_WORKERS`                         | 4       | `--workers` in the `Dockerfile`         |
| `api` replicas                            | 1       | `docker-compose.yml`                    |
| worker pool (one job at a time)           | 2 + 2   | `init_engine()` in `src/app/db/session.py` |
| `worker` replicas                         | 4       | `docker-compose.yml`                    |

That is **`(12+4)*4 + 4*(2+2) = 80`** of Postgres' default
`max_connections = 100`, leaving 20 for a migration run, postgres-exporter
and a `psql`. The earlier defaults (25 + 15 everywhere) promised 320, and the
101st connection is refused outright rather than queued in the pool.
`tests/unit/test_metrics_reach_prometheus.py` fails when a change breaks the
budget.

To give the API more, raise Postgres' limit first - in the postgres service,
`command: ["postgres", "-c", "max_connections=200"]`, within its 512M memory
limit - and the budget in that test with it.

Always verify with:
```bash
docker compose exec postgres psql -U gitpulse -c "SHOW max_connections;"
docker compose exec postgres psql -U gitpulse -c \
  "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

---

## Monitoring credentials

There is nothing to rotate for the monitoring paths: they open for a
GitPulse administrator's session (see "Monitoring access" above). Revoking
someone's admin role in GitPulse closes them for that person. The one local
credential left is Grafana's own `admin` (`GRAFANA_ADMIN_PASSWORD`), used only
at 127.0.0.1:3000 on the host; change it with
`docker compose --env-file .env.production exec grafana grafana cli admin reset-admin-password '<new>'`.

---

## TLS/HTTPS Notes

The application is accessible via `https://gitpulse.kpi.fei.tuke.sk`.  
TLS termination is handled by the TUKE university reverse proxy.  
Caddy runs in HTTP mode behind the proxy and accepts requests for the domain.

The DNS wildcard `*.svra-ubuntu-server-0261.virtual.cloud.tuke.sk` is also available,
but the primary domain `gitpulse.kpi.fei.tuke.sk` is used for OAuth callbacks and all public access.

---

## Architecture (Docker Compose)

```
                    +------------+
Internet ---- HTTPS --->| TUKE Proxy | (TLS termination)
                    +-----+------+
                          | HTTP
                    +-----▼------+
              80/443 --->|   Caddy   | (reverse proxy, headers)
                    +-----+------+
                          |
                    +-----▼------+
                    |    API     | (FastAPI, 4 workers)
                    +-----+------+
                    +-----+------+
              +-----+   Redis    +-----+
              |     +------------+     |
         +----▼-----+          +------▼---+
         | Workers  |          |Scheduler |
         |  (x4)    |          +----------+
         +----+-----+
              |
         +----▼------+
         |PostgreSQL |
         +-----------+
```
