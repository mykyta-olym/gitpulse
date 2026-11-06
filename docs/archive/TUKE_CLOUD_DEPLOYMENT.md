# Deployment Guide: TUKE Cloud (SIVVP)

## Prerequisites

From your TUKE Cloud catalog, request **Ubuntu 24.04 Server (SIVVP)** VM with:

- **RAM**: minimum 4 GB (recommended 8 GB for monitoring stack)
- **Disk**: 40 GB+ (Docker images + PostgreSQL data + logs)
- **CPU**: 2+ vCPU
- **Network**: open ports 80 (HTTP) and 443 (HTTPS)

> The Ubuntu Server blueprint is ideal - no desktop overhead, maximum resources for Docker.

---

## Step 1: Request and Configure VM

1. In TUKE Cloud catalog, click **ЗАПРОС** on "Ubuntu 24.04 server (SIVVP)"
2. Fill in the request form (VM name, e.g. `gitpulse-prod`)
3. Wait for provisioning (typically 15-60 min)
4. Connect via SSH: `ssh your-username@<vm-ip>`

---

## Step 2: Install Docker on Ubuntu 24.04

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (official method)
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (logout/login after)
sudo usermod -aG docker $USER

# Install Git
sudo apt install -y git
```

Log out and back in for the docker group to take effect.

---

## Step 3: Clone Repository

```bash
git clone https://github.com/mykyta-olym/gitpulse.git
cd gitpulse
```

---

## Step 4: Configure GitLab OAuth Application

Before deploying, create an OAuth application in your TUKE GitLab:

1. Go to `https://gitlab.example.com` -> top-right profile -> **Preferences** -> **Applications**
   (or ask a GitLab admin to create a group-level application)
2. Create new application:
   - **Name**: `GitPulse`
   - **Redirect URI**: `https://<YOUR-DOMAIN>/dashboard/oauth/callback`
   - **Scopes**: `read_user`, `read_api`, `openid`
   - **Confidential**: Yes
3. Save the **Application ID** and **Secret**

---

## Step 5: Configure Environment

```bash
# Copy template
cp .env.production.example .env.production

# Generate secrets
echo "Generating secrets..."
POSTGRES_PW=$(openssl rand -hex 16)
SECRET=$(openssl rand -hex 32)
API_TOKEN=$(openssl rand -hex 24)

echo "POSTGRES_PASSWORD=$POSTGRES_PW"
echo "SECRET_KEY=$SECRET"
echo "TEACHER_API_TOKEN=$API_TOKEN"
```

Edit `.env.production` with the generated values:

```bash
nano .env.production
```

**Critical settings to fill in:**

| Variable | Value |
| ---------- | ------- |
| `DOMAIN` | Your VM's domain or IP (e.g. `gitpulse.kpi.fei.tuke.sk`) |
| `POSTGRES_PASSWORD` | Generated hex string |
| `SECRET_KEY` | Generated hex string (min 16 chars) |
| `TEACHER_API_TOKEN` | Generated hex string |
| `GITLAB_URL` | `https://gitlab.example.com` |
| `GITLAB_API_TOKEN` | Personal Access Token with `api` scope |
| `GITLAB_OAUTH_CLIENT_ID` | From Step 4 |
| `GITLAB_OAUTH_CLIENT_SECRET` | From Step 4 |
| `GITLAB_ADMIN_USERNAMES` | `["your-gitlab-username"]` |

---

## Step 6: Deploy

```bash
# First deployment - build images and run migrations
./deploy-production.ps1 -Build -Migrate

# OR if PowerShell is not installed (use Docker Compose directly):
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d
docker compose --env-file .env.production run --rm migrate
```

### Without PowerShell (pure bash)

```bash
# Build
docker compose --env-file .env.production build

# Start all services
docker compose --env-file .env.production up -d

# Run database migrations
docker compose --env-file .env.production exec api python -m alembic upgrade head

# Check health
curl http://localhost:8000/health
```

---

## Step 7: Verify Deployment

```bash
# Check all containers are running
docker compose --env-file .env.production ps

# Expected: postgres, redis, api, worker, scheduler, caddy - all "Up (healthy)"

# Check health endpoint
curl -s http://localhost:8000/health | python3 -m json.tool

# Check logs
docker compose --env-file .env.production logs api --tail=50
```

Open in browser: `https://<YOUR-DOMAIN>/dashboard/`

---

## Step 8: DNS Configuration

If your VM has a public IP, configure DNS:

1. Request from TUKE network admin: A record `gitpulse.kpi.fei.tuke.sk -> <VM-IP>`
2. Caddy will automatically obtain Let's Encrypt certificate
3. Both HTTP->HTTPS redirect and HSTS are automatic

**If no DNS available** (IP only):

Edit `Caddyfile` to use IP:

```text
:80 {
    reverse_proxy api:8000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

---

## Step 9: Start Monitoring (Optional)

```bash
docker compose --env-file .env.production --profile monitoring up -d

# Access (SSH tunnel from your machine):
# ssh -L 3000:localhost:3000 -L 9090:localhost:9090 -L 16686:localhost:16686 user@<vm-ip>

# Grafana:    http://localhost:3000  (admin/admin)
# Prometheus: http://localhost:9090
# Jaeger:     http://localhost:16686
```

---

## Architecture on VM

```text
Internet -> :80/:443 -> [Caddy] -> :8000 -> [FastAPI API]
                                            +-- [PostgreSQL 16] (data network)
                                            +-- [Redis 7] (backend network)
                                            +-- [RQ Worker] (background jobs)
                                            +-- [RQ Scheduler] (periodic tasks)

Optional monitoring:
  [Prometheus] -> scrapes /metrics -> [Grafana dashboards]
  [Jaeger] <- OTLP traces from API
```

---

## Daily Operations

| Task | Command |
| ------ | --------- |
| View logs | `docker compose --env-file .env.production logs -f api` |
| Restart API | `docker compose --env-file .env.production restart api` |
| Restart all | `docker compose --env-file .env.production restart` |
| Stop everything | `docker compose --env-file .env.production down` |
| Update deployment | `git pull && docker compose --env-file .env.production build && docker compose --env-file .env.production up -d` |
| Run new migrations | `docker compose --env-file .env.production exec api python -m alembic upgrade head` |
| Backup database | `docker compose --env-file .env.production exec postgres pg_dump -U gitpulse gitpulse > backup_$(date +%Y%m%d).sql` |
| Restore database | `cat backup.sql \| docker compose --env-file .env.production exec -T postgres psql -U gitpulse gitpulse` |

---

## Firewall Rules

| Port | Service | Access |
| ------ | --------- | -------- |
| 22 | SSH | TUKE network only |
| 80 | HTTP (-> HTTPS redirect) | Public |
| 443 | HTTPS | Public |
| 5433 | PostgreSQL | localhost only (127.0.0.1) |
| 6379 | Redis | localhost only (127.0.0.1) |
| 3000 | Grafana | localhost only (SSH tunnel) |
| 9090 | Prometheus | localhost only (SSH tunnel) |
| 16686 | Jaeger | localhost only (SSH tunnel) |

```bash
# Ubuntu firewall setup
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Troubleshooting

| Problem | Solution |
| --------- | ---------- |
| Caddy can't get certificate | Check DNS, ensure ports 80/443 open, check `docker logs <caddy-container>` |
| API won't start | `docker compose --env-file .env.production logs api` - check DB connection |
| OAuth callback fails | Verify redirect URI matches exactly, check `GITLAB_OAUTH_CLIENT_ID` |
| 502 Bad Gateway | API container not ready yet - wait 30s or check health |
| Database migration fails | Check `DATABASE_URL` in .env.production, ensure postgres is healthy |
| Workers not processing | `docker compose --env-file .env.production logs worker` - check Redis connection |
