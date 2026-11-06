# Test GitLab Repository - Verification Guide

## Repository Details

| Field | Value |
|-------|-------|
| **URL** | `https://github.com/mykyta-olym/test-diplomova` |
| **GitLab Project ID** | `79110` |
| **Primary User** | `mykyta.olym` (ID: 0001) |
| **Bot Reviewer 1** | `project_79110_bot_...` (ID: 14260) |
| **Bot Reviewer 2** | `project_79110_bot_...` (ID: 14261) |

---

## Compliance Rules (R01-R12) Status

| Rule | Name | Expected | Notes |
|------|------|----------|-------|
| **R01** | Issue Tracking | PASS | 6 issues (#1-#6), all closed, all assigned to `mykyta.olym` |
| **R02** | Issue-MR Link | PASS | All MR descriptions contain `Closes #N` |
| **R03** | Branching | PASS | Branches follow `issue-N-description` convention |
| **R04** | MR Workflow | PASS | 5 MRs merged (!2-!6), 1 closed (!1) |
| **R05** | Review Given | N/A | Single-student repo - no peer MRs to review |
| **R06** | Review Received | PASS | 2 distinct reviewers (bot IDs 14260, 14261) per MR, meets `min_reviews_per_mr=2` |
| **R07** | Meaningful Review | N/A | Requires reviews on *others'* MRs - single-student limitation |
| **R08** | Author Response | PASS | Author responded with commit SHA references on all MRs |
| **R09** | Approval | PASS | All MRs approved by `mykyta.olym` |
| **R10** | Merged by Author | PASS | All merged MRs have `merged_by_id == author_id` |
| **R11** | MR + Issue Closed | PASS | Merged MRs + closed issues exist |
| **R12** | Pipeline Green | PASS | Pipeline #511398 `success` with `test` job in `test` stage |

### R05/R07 Note
These rules check if the student reviewed OTHER students' MRs. In our single-student test
scenario there are no peer MRs, so these will show as not passed. This is expected and
demonstrates the system correctly distinguishes individual vs team compliance.

---

## Docker Verification

### Dockerfile Quality
The Dockerfile includes all best practices that the Docker linter checks:
- Multi-stage build (`FROM python:3.12-slim AS builder`)
- Non-root user (`USER appuser`)
- Health check (`HEALTHCHECK --interval=30s ...`)
- Port exposed (`EXPOSE 5000`)
- No `:latest` tag (uses `python:3.12-slim`)
- No `ADD` (uses `COPY` only)
- No `curl | bash` patterns
- `.dockerignore` present

### Docker Lint Rules (DL001-DL011)
| Rule | Check | Our Dockerfile |
|------|-------|---------------|
| DL001 | Missing `FROM` | Has FROM |
| DL002 | Using `:latest` tag | Uses `:3.12-slim` |
| DL003 | Not pinned to digest | Warning only |
| DL004 | Multi-stage build | Has multi-stage |
| DL005 | No cache cleanup after apt-get | No apt-get used |
| DL007 | No `USER` instruction | Has USER |
| DL008 | No `HEALTHCHECK` | Has HEALTHCHECK |
| DL010 | `curl \| bash` pattern | Not used |
| DL011 | `ADD` when `COPY` suffices | Uses COPY |

---

## Pipeline Verification

### Current Pipeline State
| Pipeline | Status | Branch | Test Job |
|----------|--------|--------|----------|
| #511398 | **success** | main | test (success) |
| #510350 | **success** | main | test (success) |
| #511397 | failed | main | (test fixed but build also ran) |

### CI/CD Configuration (`.gitlab-ci.yml`)
4 stages: `lint` -> `test` -> `build` -> `deploy`

- **lint**: `ruff check app/ tests/` - passes after import fix
- **test**: `pytest tests/ -v --cov=app` - passes, 1546 tests
- **build**: `docker build` (main only) - passes
- **deploy**: Manual trigger (main only)

### What GitPulse Verifies
R12 checks:
1. At least one pipeline with `status == "success"`
2. That pipeline has a job where "test" appears in the job name or stage

Both conditions are met by pipeline #511398.

---

## Gaming Detection

### Expected Flags
| Detector | Will Trigger? | Why |
|----------|--------------|-----|
| **COMMIT_SPAM** | No | Only 6 MRs, threshold is ≥10 |
| **COMMIT_SPAM_BURST** | No | Max 3 MRs within 10-min window, threshold is ≥5 |
| **LOW_EFFORT_REVIEW** | No | No reviews on others' MRs (single-student) |
| **REVIEW_RING** | No | Team-level check, single student |

Gaming detection correctly produces no false positives for this test scenario.

---

## How to Test End-to-End (JSON Import Flow)

The recommended way to set up courses is via **JSON configuration import**. This
ensures reproducible, version-controlled course setup. Two pre-built course
configs are available:

| Config File | Course | Purpose |
|-------------|--------|---------|
| `docs/fixtures/zsi-course-config.json` | ZSI | Základy softvérového inžinierstva |
| `docs/fixtures/devops-course-config.json` | DEVOPS | Základy DevOps |

### Step 1: Start the GitPulse Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
``

### Step 2: Create the Course

1. Log in as **teacher** at `http://localhost:8000/dashboard`
2. Navigate to **Courses** -> **Create Course**
3. Fill in the basic fields (code, name, academic year, semester)
4. The created course will have default settings

### Step 3: Import Full Course Configuration via JSON

1. On the **Dashboard**, click **Import JSON** button
2. Upload one of the JSON config files:
   - For ZSI: `docs/fixtures/zsi-course-config.json`
   - For DevOps: `docs/fixtures/devops-course-config.json`
3. Preview shows course info, sections, weight sum, and warnings
4. Click **Create & Apply Configuration** - course is created and all sections applied
5. You are redirected to the new course page

Alternatively, apply to an existing course via **Course -> Settings -> Full Course Configuration -> Import**.

6. The import applies **all sections** at once:
   - Course metadata (code, name, description, teachers)
   - Settings (branch patterns, deadlines, thresholds, GitLab group path)
   - Built-in checks R01-12 (weights, configs, enabled state)
   - Custom checks C01+ (evaluation rules, weights)
   - Weekly deadlines (progressive check expectations per week)
   - Gaming detection (thresholds, patterns)
   - Rubric (categories, criteria, week-based weight overrides)
6. Review the import result - it shows applied sections and any warnings

### Step 3a: Alternative - Import Checks Only

If you only need to update check configurations (not full course settings):

1. In the course -> **Checks** tab
2. Click **Import Check Configuration**
3. Upload a JSON file with `$schema: gitpulse/check-config/v1`
4. This updates only built-in check weights + custom checks

### Step 4: Verify Imported Configuration

After import, verify the configuration was applied correctly:

| Check | What to verify |
|-------|----------------|
| **Course Info** | Code, name, description, teachers match JSON |
| **Settings** | Branch pattern, deadlines, thresholds, GitLab group path |
| **Built-in checks** | Each R01-R12 has correct weight, config, enabled state |
| **Custom checks** | C01+ created with proper evaluation rules |
| **Weekly deadlines** | 12 weeks with progressive check expectations |
| **Gaming detection** | Thresholds and patterns populated |
| **Rubric** | Categories with criteria, week weight overrides |
| **Weight sum** | Total weight ≈ 1.00 (import warns if not) |

### Step 5: Add the Test Project

1. Navigate to the imported course -> **Add Project**
2. Enter GitLab URL: `https://github.com/mykyta-olym/test-diplomova`
3. Enter the GitLab API token
4. The project is imported with settings from the JSON config

### Step 6: Run Sync

1. In the GitPulse dashboard, open the imported project
2. Click **"Sync"** to fetch all data from GitLab
3. This will import: issues, MRs, notes, pipelines, jobs, commits, approvals

### Step 7: Docker Verification

1. After sync, click **"Analyze Dockerfile"** button on the project page
2. This fetches the Dockerfile via GitLab API and runs the linter locally
3. View results in the Docker Verification section

### Step 8: View Compliance Results

After sync completes, `compute_team_metrics()` runs automatically, which:
- Evaluates all R01-R12 rules per student
- Runs custom check evaluation (C01+)
- Runs gaming detection
- Stores compliance snapshots
- Calculates rubric scores per category

Navigate to the team/student detail page to see compliance scores.

### Step 9: Verify Weekly Deadline Progress

1. Navigate to the course dashboard
2. Check the **Weekly Progress** chart - it should show progressive check completion
3. Compare expected checks per week (from JSON config) against actual student results
4. The traffic-light system (green/yellow/red) uses the thresholds from the config

### Step 10: Export and Re-import (Round-trip Test)

1. In the course settings, click **Export Full Configuration**
2. Download the exported JSON
3. Create a **new course** and import the exported JSON
4. Verify all settings match the original - this confirms export/import symmetry

### Step 11: Webhook Setup (Optional, for Real-Time Updates)

To enable real-time webhook processing:
1. In GitPulse, generate a webhook secret for the project
2. In GitLab -> Settings -> Webhooks:
   - URL: `https://<DTA_HOST>/api/v1/webhooks/gitlab`
   - Secret Token: (the generated secret)
   - Triggers: Push, Merge Request, Note, Issues, Pipeline
3. New events will be processed in real-time

---

## Course Configuration Details

### ZSI (Základy softvérového inžinierstva)

**Grading Structure**: 20 pts exercises (min 11 for credit) + 80 pts exam (min 41)

| Component | Points | Week Due | GitPulse Mapping |
|-----------|--------|----------|-------------|
| Zadanie 1: Analýza požiadaviek + konceptuálny návrh | 9 | 7 | R01, R02, R04, R05, R06, R07, R09 |
| Zadanie 2: Tímový projekt (issues, testy, review, merge) | 9 | 12 | Full R01-R12 + C01, C02 |
| Aktivita na cvičeniach | 2 | ongoing | - |

**Key differences from DevOps**:
- Lower review requirements (1 reviewer vs 2) - smaller teams in SE course
- CI/CD pipeline optional (`require_test_job: false`) - not all ZSI projects have CI
- Lower R12 weight (0.04 vs 0.08) - CI is less central to ZSI
- Focus on analysis and design in first 7 weeks (Zadanie 1)
- Check weight sum: R01-R12 + C01-C02 = **1.00**

### DevOps (Základy DevOps)

**Grading Structure**: 20 pts exercises (min 11) - 10 pts test (week 7) + 10 pts team project

| Component | Points | Week Due | GitPulse Mapping |
|-----------|--------|----------|-------------|
| Test | 10 | 7 | - (written test, not tracked by GitPulse) |
| Tímový projekt | 10 | 12 | Full R01-R12 + C01-C04 |

**Key differences from ZSI**:
- Higher review requirements (2 reviewers, min 30 words) - stronger team collaboration focus
- CI/CD pipeline mandatory (`require_test_job: true`) - core of DevOps
- Higher R12 weight (0.08) - pipeline is key DevOps indicator
- 4 custom checks (C01-C04) including Dockerfile quality and CI/CD configuration
- MR template required with 4 sections - enforces documentation
- Check weight sum: R01-R12 + C01-C04 = **1.00**

---

## Project Access Tokens

Two project access tokens were created for bot reviewers:

| Token Name | User ID | Purpose |
|-----------|---------|---------|
| `reviewer-bot` | 14260 | First reviewer for R06 |
| `reviewer-bot-2` | 14261 | Second reviewer for R06 |

Both expire: 2026-12-31.

---

## Summary

The test repo has complete data for verifying:
- **12 Compliance Rules** (R01-R12): 10/12 pass, 2 N/A (team-only rules)
- **Docker Verification**: Dockerfile scores high on all lint rules
- **Pipeline Analysis**: 2 successful pipelines with test jobs
- **Gaming Detection**: No false positives triggered
- **Tracking/Telemetry**: All data structured for GitPulse import
- **JSON Import Flow**: 3 pre-built course configs (generic, ZSI, DevOps)
- **Weight Validation**: All configs sum to exactly 1.00
- **Weekly Deadlines**: Progressive check expectations weeks 1-12
- **Rubric**: Category-based scoring with week weight overrides
