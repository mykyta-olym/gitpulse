# 8. Post-Pilot Improvements

> **Documentation Status (2026-02-09):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `ruff check src tests`, `ruff format --check src tests`, `mypy src/app`.


## 8.1 Evaluation Framework

After the pilot (week 13), evaluate along four axes:

| Axis | Method | Data Source |
|------|--------|-------------|
| **Accuracy** | Compare GitPulse scores with teacher's manual grading (10-team sample) | Manual grading spreadsheet vs GitPulse export |
| **Usability** | Teacher feedback survey (Likert 1-5) | Feedback Form #2 |
| **Reliability** | Uptime, event processing rate, error rate | Prometheus metrics, health logs |
| **Efficiency** | Time saved per team in grading | Teacher self-report |

## 8.2 Planned Improvements (Prioritized)

### Priority 1: High (Next Semester)

| # | Improvement | Effort | Trigger |
|---|-------------|--------|---------|
| I1 | **GitLab OAuth login** - replace password-based dashboard auth with GitLab OAuth2 + RBAC (admin/teacher/readonly) | 3d | Security hardening; multi-teacher support |
| I2 | **Auto-discover teams** from GitLab group membership - eliminate manual registration | 2d | Teacher setup friction |
| I3 | **Bulk CSV import** for teams/students - upload a spreadsheet instead of N API calls | 1d | 30 teams × manual API calls is tedious |
| I4 | **Recalibrate weights** based on pilot accuracy data - adjust R01-R12 weights to minimize disagreement with teacher | 1d | Accuracy analysis results |
| I5 | **Integration tests** with testcontainers - automated DB + Redis tests in CI | 3d | Confidence in refactors |

### Priority 2: Medium (Within Academic Year)

| # | Improvement | Effort | Trigger |
|---|-------------|--------|---------|
| I6 | **Historical trend charts** - per-student score over time (sparklines in dashboard) | 3d | Teacher wants to see progress trajectory |
| I7 | **Email/webhook alerts** - notify teacher when a team drops to RED | 2d | Proactive intervention |
| I8 | **Comparative team view** - side-by-side comparison of two teams | 2d | Teacher request |
| I9 | **LLM review quality analysis** - opt-in module to flag superficial reviews; privacy-aware; teacher-only output | 5d | Gaming detection; requires ethics review |
| I10 | **Základy DevOps integration** - add DevOps-specific checks (Dockerfile quality, CI config, Docker Compose) | 5d | Second course adoption |

### Priority 3: Low (Future)

| # | Improvement | Effort | Trigger |
|---|-------------|--------|---------|
| I11 | **Student self-service dashboard** - read-only view of own metrics (opt-in) | 3d | Student engagement |
| I12 | **Moodle grade export** - push final scores to Moodle gradebook via API | 2d | Administrative integration |
| I13 | **Arena integration** - lightweight hook to display status in Arena portal | 2d | If Arena API becomes available |
| I14 | **Git conflict simulator** - standalone tool for DevOps week 2-3 | 5d | DevOps course needs |
| I15 | **Docker build verifier** - validate student Dockerfiles against best practices | 5d | DevOps course needs |

## 8.3 What to Change in Tasks/Tools

Based on pilot data, potential task changes for students:

| If we observe... | Then change... |
|------------------|----------------|
| Most students pass all 12 checks easily | Raise thresholds (e.g. 3 reviews instead of 2); add new checks |
| R08 (response quality) has many false negatives | Improve commit reference detection regex; consider NLP |
| Students write one-word reviews to pass R07 | Increase meaningful review word threshold (20 -> 50 words) |
| Pipeline checks (R12) are too strict | Make test job name pattern configurable; accept more CI patterns |
| Communication indicators are not useful | Drop or redesign; consider different metrics |
| Teacher finds PDF reports too dense | Redesign layout; add executive summary section |

## 8.4 Technical Debt to Address

| Item | Current State | Target State |
|------|---------------|--------------|
| `teacher_password_hash` vs `dashboard_password_hash` config naming | Both exist (legacy) | Unify to single field |
| `_load_team_data` loads snapshots in a loop | N+1 query pattern | Single query with window function |
| Weight `weight_commit_references` exists but is unused | Dead weight in CourseSettings | Remove or repurpose in engine |
| CHECK_DEFS duplicated in dashboard.py and report_job.py | Two sources of truth | Extract to shared `compliance/check_defs.py` |
| No integration tests | Unit tests only | Add testcontainers-based integration suite |
| Coverage below CI threshold (`COVERAGE_THRESHOLD`, default 40%) | 23% (historical baseline before broader test expansion) | Keep CI threshold green and progressively raise target by semester |

