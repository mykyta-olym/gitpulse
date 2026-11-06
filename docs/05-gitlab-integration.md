# 5. Deployment & GitLab Integration Guide

> **Documentation Status (2026-06-03):** Verified against current implementation.
>
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.

Complete guide for deploying the GitPulse and
integrating it with the TUKE departmental GitLab instance.

---

## 5.1 Deployment

### 5.1.1 Infrastructure Requirements

| Resource | Minimum | Recommended |
| ---------- | --------- | ------------- |
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 100 GB | 250 GB (SSD) |
| OS | Ubuntu 22.04+ / Debian 12+ | Ubuntu 24.04 LTS |
| Network | Ports 80, 443 open inbound | Static IP + DNS record |
| Docker | Docker Engine 24+ | Docker Engine 27+ |
| Docker Compose | v2.20+ | v2.30+ |

### 5.1.2 Initial Server Setup

```bash
# 1. Install Docker (if not present)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect

# 2. Install Docker Compose v2 (ships with Docker Engine 24+)
docker compose version
# Expected: Docker Compose version v2.x.y

# 3. Clone repository
git clone https://gitlab.kpi.tuke.sk/<group>/gitpulse.git /opt/gitpulse
cd /opt/gitpulse

# 4. Create environment file
cp .env.example .env
```

### 5.1.3 Configure Secrets

```bash
# Generate a cryptographic secret key (min 32 chars)
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Generate a teacher API bearer token
echo "TEACHER_API_TOKEN=$(openssl rand -hex 24)" >> .env

# Generate and hash a dashboard password
pip3 install bcrypt
python3 scripts/hash_password.py
# Enter desired password, copy the output line into .env

# Set a strong PostgreSQL password
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -hex 32)" >> .env

# Set the GitLab token (created in §5.2)
echo "GITLAB_API_TOKEN=glpat_placeholder_token" >> .env

# Set the public URL/hostnames for Caddy automatic HTTPS and secure cookies
echo "DOMAIN=gitpulse.kpi.fei.tuke.sk" >> .env
echo "APP_BASE_URL=https://gitpulse.kpi.fei.tuke.sk" >> .env
echo 'ALLOWED_HOSTS=["gitpulse.kpi.fei.tuke.sk"]' >> .env
```

### 5.1.4 DNS Configuration

Create an A record pointing to the VM's public IP:

```text
gitpulse.kpi.fei.tuke.sk.   300   IN   A   147.232.xx.xx
```

Caddy will automatically obtain and renew TLS certificates from Let's Encrypt
once DNS propagates (usually within 5 minutes).

### 5.1.5 Deploy

```bash
cd /opt/gitpulse

# Run database migrations
docker compose --profile migrate run --rm migrate

# Start all core services
docker compose up -d

# Verify
curl -s https://gitpulse.kpi.fei.tuke.sk/health | python3 -m json.tool
# Expected: {"status":"ok","version":"2026.6.5.post2",...}

curl -s https://gitpulse.kpi.fei.tuke.sk/health/ready
# Expected: {"status":"ready"}
```

### 5.1.6 Enable Monitoring (Optional)

```bash
# Start Prometheus + Jaeger alongside core services
docker compose --profile monitoring up -d

# Access (via SSH tunnel since ports are 127.0.0.1 only):
# Prometheus: ssh -L 9090:localhost:9090 user@server -> http://localhost:9090
# Jaeger UI:  ssh -L 16686:localhost:16686 user@server -> http://localhost:16686
```

### 5.1.7 Set Up Automated Backups

```bash
# Make backup script executable
chmod +x scripts/backup.sh scripts/restore.sh

# Test manual backup
./scripts/backup.sh

# Add daily cron job (02:00 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/gitpulse && ./scripts/backup.sh >> /var/log/gitpulse-backup.log 2>&1") | crontab -
```

### 5.1.8 Updating

```bash
cd /opt/gitpulse
git pull origin main
docker compose --profile migrate run --rm migrate
docker compose up -d --build
```

---

## 5.2 Create GitLab Tokens (Minimal Scopes)

### 5.2.1 Personal Access Token for API Enrichment

GitPulse uses the GitLab API to fetch full issue/MR/note/approval/pipeline data
that is not included in webhook payloads. A read-only token is sufficient.

| Step | Action |
| ------ | -------- |
| 1 | Navigate to: `https://gitlab.kpi.tuke.sk/-/user_settings/personal_access_tokens` |
| 2 | **Token name:** `gitpulse-enrichment-bot` |
| 3 | **Expiration date:** end of current semester (e.g. `2026-06-30`) |
| 4 | **Scopes:** `read_api` only |
| 5 | Click **Create personal access token** |
| 6 | Copy the token immediately (it will not be shown again) |

**Scope justification:**

| Scope | Purpose | Required |
| ------- | --------- | ---------- |
| `read_api` | GET requests for issues, MRs, notes, approvals, pipelines, diffs | **Yes** |
| `read_user` | Not needed (webhook payloads include user info) | No |
| `read_repository` | Not needed (diffs fetched via MR API, not repo API) | No |
| `api` | Full read+write access - **do NOT grant** | No |
| `write_repository` | The analytics never write to repos | No |

**Security best practice:** Create a dedicated GitLab user (e.g. `gitpulse-bot`)
that has **Guest** access to the relevant groups. This limits the blast
radius if the token is compromised.

### 5.2.2 The classroom assistant's bot token (per course, optional)

The classroom assistant (`app/services/assistant/`, behind
`FEATURE_CLASSROOM_ASSISTANT`) is the one part that writes to GitLab: it
comments, commits a conflicting edit, opens issues, approves and merges. It
never uses the token above. Each course connects its own bot token on the
course's **Assistant** tab:

| Setting | Value |
| ------- | ----- |
| Token type | Group Access Token in the course's group (GitLab creates a bot user) |
| Role | Maintainer (commits to the protected default branch, merges MRs) |
| Scope | `api` |
| Storage | `course_assistants.bot_token`, Fernet-encrypted like the OAuth tokens below |

The token is checked against GitLab (`GET /user`, `GET /personal_access_tokens/self`)
before it is stored, the read-only token above is refused, and the bot's client
(`BotGitLabClient`) is separate from `GitLabClient`: a 401 on the bot token never
marks the sync token unhealthy.

**Checking it against a real GitLab.** The unit and integration tests use a
GitLab kept in memory; `scripts/assistant_e2e.py` drives the assistant through
a real GitLab CE of the version the department runs (19.4.2): real webhooks, a
real `git merge` for the conflict exercise, GitLab's own merge, approval and
pipeline status. It needs Docker, the dev Postgres and Redis, and git.

```bash
docker compose -f docker-compose.gitlab-e2e.yml up -d   # GitLab on :8929, ~5 min
python scripts/assistant_e2e.py provision                # users, a course group, tokens
eval "$(python scripts/assistant_e2e.py env)"            # GitPulse's environment for it
docker compose -f docker-compose.dev.yml exec postgres createdb -U gitpulse gitpulse_e2e
python -m alembic upgrade head                           # a database of its own
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8020 &
python -m app.workers.main &
python scripts/assistant_e2e.py setup                    # import, webhook, connect the bot
python scripts/assistant_e2e.py run                      # every scenario, PASS/FAIL per step
python scripts/assistant_e2e.py accounts                 # logins, to try it by hand
```

`accounts` gives the teacher and the students GitLab passwords of their own
and prints them with the GitPulse dev login, so the same course can be worked
by hand: sign in to GitLab as a student and push, open a merge request or
comment, and watch the Assistant page as the teacher.

`provision` again makes a new course group, so the run repeats on the same
GitLab and database. The deliveries in `tests/fixtures/payloads/gitlab_19_4/`
were captured in such a run; the contract tests replay them.

### 5.2.3 OAuth Token Security

GitLab OAuth access and refresh tokens obtained during the login flow are
**encrypted at rest** using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256):

- The encryption key is derived from `SECRET_KEY` via **HKDF** with a static salt.
- Encrypted tokens are stored in the database as `enc:v1:<base64-ciphertext>`.
- The `decrypt_token()` function handles both encrypted and legacy plaintext tokens
  transparently, logging a warning for unencrypted values.
- See `src/app/security/token_encryption.py` for implementation details.

### 5.2.4 Teacher Detection

Teachers and admins are automatically identified based on:

1. **Username lists:** `GITLAB_ADMIN_USERNAMES` and `GITLAB_TEACHER_USERNAMES` env vars.
2. **Group membership:** Users belonging to groups listed in `GITLAB_TEACHER_GROUP_IDS` are assigned the `teacher` role.
3. **Course membership:** Users with a `CourseMembership` row (role `teacher` or `owner`) gain course-level access. A system-level `student` with any staff membership is elevated to `teacher` in the session.
4. **Team-level:** Team members flagged as `is_teacher=true` (migration 006) are excluded from compliance scoring aggregates.

### 5.2.2 Webhook Secret Token

Each GitLab project webhook uses a **per-project secret** generated by GitPulse
during registration. You don't need to generate it manually.

When you register a project, GitPulse returns:

- `webhook_secret` (plaintext, returned **once**)
- `webhook_url`
- `setup_instructions`

The secret is:

- Configured in GitLab webhook settings (`Secret token` field)
- Stored as a bcrypt hash in PostgreSQL (never in plaintext)
- Verified using constant-time comparison on every webhook delivery

---

## 5.3 Configure Webhooks

### 5.3.1 Project-Level Webhook

1. Navigate to the GitLab project:
   `Settings -> Webhooks`

2. Fill in the form:

   | Field | Value | Notes |
   | ------- | ------- | ------- |
   | **URL** | `https://gitpulse.kpi.fei.tuke.sk/api/v1/webhooks/gitlab` | HTTPS required |
   | **Secret token** | `<webhook-secret from §5.2.2>` | Must match GitPulse registration |
   | **Trigger: Push events** | Yes | Tracks commits referencing issues |
   | **Trigger: Issues events** | Yes | Tracks issue creation/assignment/closure |
   | **Trigger: Merge request events** | Yes | Core workflow tracking |
   | **Trigger: Note (comments) events** | Yes | Review communication tracking |
   | **Trigger: Pipeline events** | Yes | CI/CD health tracking |
   | **Trigger: Tag push events** | No | Not needed |
   | **Trigger: Wiki page events** | No | Not needed |
   | **Trigger: Releases events** | No | Not needed |
   | **Enable SSL verification** | Yes | Caddy provides valid Let's Encrypt certificate |

3. Click **Add webhook**

### 5.3.2 Group-Level Webhook (Not supported in current release)

GitPulse uses **per-project** secrets, so a single group-level webhook token
cannot authenticate all projects. Configure **project-level** webhooks
instead (one per project) using the per-project secret returned by GitPulse.

### 5.3.3 Register the Project in GitPulse

Before GitPulse can accept webhooks from a project, it must be registered:

```bash
# Set variables
TEACHER_TOKEN="your-teacher-api-token"
DTA_URL="https://gitpulse.kpi.fei.tuke.sk"
TEAM_ID="b2c3d4e5-f6a7-8901-bcde-f12345678901"  # From /api/v1/teams
GITLAB_PROJECT_ID=12345  # Find in GitLab: Settings -> General
GITLAB_PROJECT_PATH="zsi-2026/team-alpha-minesweeper"
GITLAB_PROJECT_NAME="Team Alpha Minesweeper"

# Register (GitPulse generates the webhook secret)
curl -X POST "$DTA_URL/api/v1/projects/$TEAM_ID/projects" \
  -H "Authorization: Bearer $TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gitlab_project_id": '"$GITLAB_PROJECT_ID"',
    "gitlab_project_path": "'"$GITLAB_PROJECT_PATH"'",
    "gitlab_project_name": "'"$GITLAB_PROJECT_NAME"'"
  }'
```

**Response (201 Created):**

```json
{
  "id": "c7a3b2d1-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
  "team_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "gitlab_project_id": 12345,
  "gitlab_project_path": "zsi-2026/team-alpha-minesweeper",
  "gitlab_project_name": "Team Alpha Minesweeper",
  "is_active": true,
  "last_synced_at": null,
  "created_at": "2026-02-15T10:00:00Z",
  "webhook_secret": "whsec_a3Bf9x...plaintext...Kz7",
  "webhook_url": "https://gitpulse.kpi.fei.tuke.sk/api/v1/webhooks/gitlab",
  "setup_instructions": "1. Go to GitLab project Settings -> Webhooks\n2. URL: https://gitpulse.kpi.fei.tuke.sk/api/v1/webhooks/gitlab\n3. Secret token: whsec_a3Bf9x...plaintext...Kz7\n4. Trigger: Push events, Issues events, Merge request events, Note events, Pipeline events\n5. Enable SSL verification\n6. Click 'Add webhook'"
}
```

Repeat for each project. For 30 teams, consider a shell loop:

```bash
# projects.csv: team_id,gitlab_project_id,gitlab_project_path,gitlab_project_name
# b2c3d4e5-f6a7-8901-bcde-f12345678901,12345,zsi-2026/team-alpha-minesweeper,Team Alpha Minesweeper
# b2c3d4e5-f6a7-8901-bcde-f12345678902,12346,zsi-2026/team-beta-minesweeper,Team Beta Minesweeper
# ...

while IFS=',' read -r team_id gitlab_project_id gitlab_project_path gitlab_project_name; do
  curl -s -X POST "$DTA_URL/api/v1/projects/$team_id/projects" \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"gitlab_project_id": '"$gitlab_project_id"', "gitlab_project_path": "'"$gitlab_project_path"'", "gitlab_project_name": "'"$gitlab_project_name"'"}'
  echo ""
done < projects.csv
```

---

## 5.4 Validate Delivery & Troubleshoot

### 5.4.1 Test Webhook Delivery

After adding the webhook in GitLab:

1. Click **Test** -> **Push events** in the webhook settings page
2. GitLab sends a test payload to GitPulse
3. Expected response:

   ```json
   {"status": "accepted", "event_id": "...", "message": "Event enqueued for processing"}
   ```

4. If you see `200 OK` with status `"duplicate"`, the test event was already
   received (GitLab sends the same test payload each time)

### 5.4.2 Check Webhook Delivery Log

In GitLab: `Settings -> Webhooks -> Edit -> Recent deliveries`

| Status | Meaning | Action |
| -------- | --------- | -------- |
| 202 | Accepted - event stored and enqueued | Normal |
| 200 | Duplicate - already received | Normal (retry) |
| 401 | Unauthorized | Secret token mismatch - compare secrets |
| 404 | Not found | Project not registered in GitPulse - run §5.3.3 |
| 413 | Payload too large | Payload > 1 MB - unusual, check GitLab config |
| 422 | Unprocessable | Missing `project.id` in payload - check event type |
| 500 | Internal server error | Check GitPulse logs: `docker compose logs api --tail=50` |
| Timeout | GitPulse unreachable | Check DNS, firewall, Caddy, container health |

### 5.4.3 Verify Processing

```bash
# Check API health
curl -s https://gitpulse.kpi.fei.tuke.sk/health | python3 -m json.tool

# Check recent webhook events in logs
docker compose logs api --tail=20 | grep webhook

# Check worker is processing
docker compose logs worker --tail=20

# Check queue depth (Prometheus metric)
curl -s https://gitpulse.kpi.fei.tuke.sk/metrics | grep rq_queue_depth
```

### 5.4.4 Common Issues

| Symptom | Cause | Fix |
| --------- | ------- | ----- |
| Events accepted but no metrics | Worker not running | `docker compose up -d worker` |
| Events accepted but enrichment fails | GitLab token expired/invalid | Regenerate token (§5.2.1), set in `.env`, restart |
| Webhook delivery times out | GitPulse is slow / overloaded | Check `docker compose logs api`; scale worker: `docker compose up -d --scale worker=2` |
| "Project not registered" on known project | Wrong `gitlab_id` | Check GitLab project ID in Settings -> General -> Project ID |
| SSL verification fails | Self-signed cert / no cert | Ensure Caddy is running and DNS points to the VM; use `DOMAIN=` correctly |
| Events arrive but student not matched | Student not registered | Register team members via the teams API (§5.6) |

---

## 5.5 Recommended MR Templates, Labels & Branch Naming Policy

These recommendations are for student teams. Configuring them in GitLab
ensures compliance with GitPulse's automated checks (R02, R04, R05).

### 5.5.1 Branch Naming Convention

GitPulse check **R02** validates branch naming. The default pattern is:

```text
<type>/<issue-number>-<short-description>
```

**Examples:**

```text
feature/42-add-game-timer
fix/17-fix-mine-counter
refactor/23-extract-board-class
```

**Accepted prefixes:** `feature/`, `fix/`, `bugfix/`, `hotfix/`, `refactor/`,
`docs/`, `test/`, `chore/`

**GitLab enforcement:** Add a push rule in the project:
`Settings -> Repository -> Push rules -> Branch name -> Allowed pattern`:

```text
(feature|fix|bugfix|hotfix|refactor|docs|test|chore)/\d+-.+
```

### 5.5.2 Merge Request Template

GitPulse check **R05** validates MR description against a template. Create a
default MR template in the repository:

**File:** `.gitlab/merge_request_templates/Default.md`

```markdown
## Summary

<!-- Describe what this MR does in 1-3 sentences -->

## Related Issue

Closes #<issue-number>

## Changes

- [ ] Describe change 1
- [ ] Describe change 2

## Tests

- [ ] Unit tests added/updated
- [ ] All tests pass locally (`pytest`)

## Checklist

- [ ] Code follows project conventions
- [ ] Self-review completed
- [ ] No unnecessary files committed
```

**Template compliance check (R05):** GitPulse verifies that the MR description
contains at minimum:

- A `## Summary` or `## Popis` section header
- A reference to an issue (`#123`, `Closes #123`, `Related to #123`)

### 5.5.3 Issue Labels

Recommended labels for student projects (create in GitLab ->
`Issues -> Labels -> New label`):

| Label | Color | Purpose |
| ------- | ------- | --------- |
| `task` | `#428BCA` (blue) | Standard assignment task |
| `bug` | `#D9534F` (red) | Bug fix |
| `enhancement` | `#5CB85C` (green) | Improvement |
| `review-needed` | `#F0AD4E` (yellow) | MR awaits review |
| `approved` | `#5CB85C` (green) | MR approved |

> Labels are not currently checked by GitPulse compliance engine but are useful
> for student workflow organization and may be used in future checks.

### 5.5.4 GitLab Project Settings Checklist

For each student team project, verify these settings:

| Setting | Path | Value |
| --------- | ------ | ------- |
| Merge method | Settings -> Merge requests | **Merge commit** (default) |
| Merge checks | Settings -> Merge requests | Pipelines must succeed |
| | | All discussions must be resolved |
| Approvals required | Settings -> Merge requests -> Approvals | **2 approvals** |
| Branch protection | Settings -> Repository -> Protected branches | `main`: Push=Maintainers, Merge=Developers+Maintainers |
| MR template | `.gitlab/merge_request_templates/Default.md` | Created per §5.5.2 |
| Push rules | Settings -> Repository -> Push rules | Branch pattern per §5.5.1 |

---

## 5.6 Register Course, Teams & Students

### 5.6.1 Create the Course

```bash
curl -X POST "$DTA_URL/api/v1/courses" \
  -H "Authorization: Bearer $TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ZSI",
    "name": "Základy softvérového inžinierstva",
    "academic_year": "2025/2026",
    "semester": 2
  }'
```

Save the returned `id` (e.g. `"course_id": "aaa-bbb-ccc"`).

### 5.6.2 Create Teams with Members

```bash
curl -X POST "$DTA_URL/api/v1/teams" \
  -H "Authorization: Bearer $TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Team Alpha",
    "course_id": "aaa-bbb-ccc",
    "gitlab_group_id": 678,
    "members": [
      {"gitlab_username": "xdoe01", "gitlab_user_id": 101, "full_name": "Alice Doe"},
      {"gitlab_username": "xsmith02", "gitlab_user_id": 102, "full_name": "Bob Smith"},
      {"gitlab_username": "xlee03", "gitlab_user_id": 103, "full_name": "Carol Lee"},
      {"gitlab_username": "xkim04", "gitlab_user_id": 104, "full_name": "Dave Kim"}
    ]
  }'
```

> **Finding `gitlab_user_id`:** Navigate to the user's GitLab profile.
> The user ID is in the URL or available via
> `GET /api/v4/users?username=xdoe01`.

### 5.6.3 Backfill Existing Data

If students have already been working before GitPulse was connected:

```bash
# Sync all issues and MRs for a project
curl -X POST "$DTA_URL/api/v1/sync/project/12345" \
  -H "Authorization: Bearer $TEACHER_TOKEN"

# Trigger metrics computation for a team
curl -X POST "$DTA_URL/api/v1/sync/metrics/<team-uuid>" \
  -H "Authorization: Bearer $TEACHER_TOKEN"
```

---

## 5.7 Pilot Semester Timeline

| Week | Phase | GitPulse Activity | Teacher Action |
| ------ | ------- | ------------- | ---------------- |
| **1** | Setup | Deploy VM, configure `.env` | Provision TUKE cloud VM |
| **2** | Setup | Test deployment, verify health | Set up DNS record |
| **3** | Onboard | Register course + projects + teams | Create GitLab groups, configure webhooks |
| **4-7** | Passive | Webhooks collecting data silently | Students work on tools assignments (Git, Docker, CI/CD) |
| **8** | Preview | Enable dashboard access | Teacher reviews dashboard, fills Feedback Form #1 |
| **9** | Tune | Adjust weights/thresholds if needed | Update `CourseSettings` based on feedback |
| **10** | Active | Full compliance tracking starts | Students begin MR/review/merge assignment |
| **11** | Active | Metrics computed continuously | Teacher monitors traffic lights in dashboard |
| **12** | Grade | Generate reports for all teams | Teacher uses reports for final assessment; compare with manual grading |
| **13** | Evaluate | Export data for analysis | Fill Feedback Form #2; analyze accuracy |

---

## 5.8 Validate End-to-End Flow

After completing setup, verify the entire pipeline works:

```bash
# 1. Health
curl -s "$DTA_URL/health" | python3 -m json.tool

# 2. Webhook (ask a student to push, or use GitLab test delivery)
# Check API logs:
docker compose logs api --tail=10 | grep webhook_accepted

# 3. Worker processing
docker compose logs worker --tail=10 | grep processed

# 4. Metrics
docker compose logs worker --tail=10 | grep compute_metrics

# 5. Dashboard
# Open https://gitpulse.kpi.fei.tuke.sk/dashboard/ -> login -> course -> team
# Verify student names appear and checks show data

# 6. Export
# Click CSV or JSON export button on team page
# Or via API:
curl -s "$DTA_URL/dashboard/teams/<team-uuid>/export/json" \
  --cookie "session=<your-session-cookie>" | python3 -m json.tool
```

If all 6 steps succeed, the system is operational.
