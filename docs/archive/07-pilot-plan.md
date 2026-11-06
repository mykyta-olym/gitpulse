# 7. Pilot Execution Plan

> **Documentation Status (2026-02-09):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `ruff check src tests`, `ruff format --check src tests`, `mypy src/app`.


## 7.1 Timeline

| Week | Activity | Deliverable |
|------|----------|-------------|
| **Week 1-2** | Deploy GitPulse on TUKE cloud VM | Running instance with HTTPS |
| **Week 3** | Register pilot course + teams + projects | GitLab webhooks active |
| **Weeks 3-9** | Passive data collection (webhooks ingested, enriched) | Growing DB of events |
| **Week 8** | Teacher preview: show dashboard to teacher | Feedback form #1 |
| **Week 10-11** | Active evaluation: students do MR/review assignment | Real compliance data flowing |
| **Week 12** | Teacher uses GitPulse for grading assessment | Final compliance reports |
| **Week 13** | Collect feedback, analyze results | Feedback form #2 + analysis |

## 7.2 Deployment Steps

### Before Week 3

```bash
# 1. Provision VM (TUKE cloud)
#    8 CPU, 16 GB RAM, 250 GB disk, Ubuntu 22.04+
#    Open ports: 80, 443

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 3. Clone and configure
git clone <repo-url> /opt/gitpulse
cd /opt/gitpulse
cp .env.example .env
# Fill in all values (see README)

# 4. Set up DNS
#    Point gitpulse.kpi.fei.tuke.sk -> VM IP (A record)

# 5. Deploy
docker compose --profile migrate run --rm migrate
docker compose up -d

# 6. Verify
curl https://gitpulse.kpi.fei.tuke.sk/health
curl https://gitpulse.kpi.fei.tuke.sk/health/ready

# 7. Set up backup cron
echo "0 2 * * * cd /opt/gitpulse && ./scripts/backup.sh >> /var/log/GitPulse-backup.log 2>&1" | crontab -

# 8. Register pilot course + teams (see docs/05-gitlab-integration.md)
```

## 7.3 Pilot Scope

| Parameter | Value |
|-----------|-------|
| Course | ZSI (Základy softvérového inžinierstva) |
| Semester | Summer 2025/2026 |
| Teams | ~30 teams × 4-5 students |
| Students | ~120-150 |
| Projects | ~30 GitLab projects |
| Duration | Weeks 3-13 (11 weeks) |
| Evaluation window | Weeks 10-12 (MR/review assignment) |

## 7.4 Success Criteria

### Quantitative

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Uptime** | ≥ 99% during weeks 10-12 | Health check logs / uptime monitor |
| **Webhook processing** | ≥ 95% events processed within 5 min | `webhook_events_processed_total` / `webhook_events_received_total` |
| **Metrics accuracy** | ≥ 90% agreement with manual grading | Sample 10 teams, compare GitPulse scores with teacher's manual assessment |
| **Report generation** | 100% teams exportable | All teams produce HTML/PDF/CSV without errors |
| **No data loss** | 0 lost events | Compare webhook count (GitLab delivery log) vs stored events |

### Qualitative

| Criterion | Assessment Method |
|-----------|-------------------|
| Teacher finds dashboard useful | Post-pilot survey (Likert 1-5) |
| Reports reduce grading time | Teacher self-report (hours before vs after) |
| Traffic lights match teacher's intuition | Teacher reviews 10 teams, rates agreement |
| System is easy to set up | Teacher rates setup experience |
| Students cannot game the system | Review communication indicators for anomalies |

## 7.5 Feedback Collection

### Feedback Form #1 (Week 8 - Preview)

1. Is the dashboard layout clear and intuitive? (1-5)
2. Are the 12 compliance checks aligned with your expectations? (1-5)
3. Which information is missing?
4. Which information is unnecessary?
5. Would you use traffic-light status in actual grading? (Yes/No/Maybe)

### Feedback Form #2 (Week 13 - Post-Pilot)

1. Did GitPulse save you time in grading? (Yes/Partially/No)
2. Estimated hours saved per team? (0/0.5/1/2+)
3. Were there false positives (GitPulse flagged OK work as FAIL)? How many?
4. Were there false negatives (GitPulse missed bad work)? How many?
5. Would you use GitPulse again next semester? (1-5)
6. What feature would you add first?
7. Any bugs or issues encountered?

## 7.6 Risk Mitigation During Pilot

| Risk | Mitigation |
|------|------------|
| VM goes down during week 10-12 | Daily backups; 5-min recovery via restore script; teacher has CSV fallback |
| GitLab webhook misconfigured | Test webhook on each project at registration; monitor `webhook_events_received_total` |
| Students complain about "surveillance" | Communicate clearly: tool helps teacher, not automated grading; student data is only activity already visible in GitLab |
| Metrics disagree with teacher | GitPulse is advisory; teacher makes final decision; log disagreements for calibration |

## 7.7 Monitoring During Pilot

```bash
# Daily checks (automated via cron or manual)
curl -s https://gitpulse.kpi.fei.tuke.sk/health | jq .

# Weekly review
# - Check Prometheus: http://localhost:9090 (SSH tunnel)
# - Review failed jobs: rq_failed_jobs_total
# - Check queue depth: rq_queue_depth{queue_name="high"}
# - Review backup logs
```

