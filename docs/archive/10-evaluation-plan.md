# 10. Evaluation Plan

> **Documentation Status (2026-02-09):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `ruff check src tests`, `ruff format --check src tests`, `mypy src/app`.


Formal plan for evaluating the GitPulse during and
after a pilot deployment in the ZSI course at TUKE KPI.

---

## 10.1 Evaluation Goals

| Goal | Research Question |
| ---- | ----------------- |
| G1 - Accuracy | Does GitPulse produce compliance scores that agree with expert (teacher) grading? |
| G2 - Efficiency | Does GitPulse reduce the time a teacher spends grading teamwork assignments? |
| G3 - Reliability | Does the system operate without data loss or significant downtime during the evaluation window? |
| G4 - Usability | Can a teacher effectively use the dashboard and reports for grading without extensive training? |
| G5 - Fairness | Do the 12 automated checks treat all student workflow patterns equitably, without systemic bias? |

---

## 10.2 Data Collection Plan

### 10.2.1 Quantitative Data (Automated)

All metrics are collected automatically; no manual intervention required.

| Data Point | Source | Collection Frequency | Storage |
| ---------- | ------ | -------------------- | ------- |
| Webhook events received | Prometheus: `webhook_events_received_total` | Continuous (15s scrape) | Prometheus TSDB (30d retention) |
| Webhook events processed | Prometheus: `webhook_events_processed_total` | Continuous | Prometheus TSDB |
| Event processing latency | Prometheus: `webhook_processing_duration_seconds` | Continuous | Prometheus TSDB |
| Queue depth per priority | Prometheus: `rq_queue_depth` | Continuous | Prometheus TSDB |
| Failed jobs | Prometheus: `rq_failed_jobs_total` | Continuous | Prometheus TSDB |
| API response latency | Prometheus: `http_request_duration_seconds` | Continuous | Prometheus TSDB |
| System uptime | Health endpoint (`/health`) polled externally | Every 1 minute | External monitoring log |
| DB pool utilization | Prometheus: `db_pool_checked_out` | Continuous | Prometheus TSDB |
| Per-student compliance scores | `metric_snapshots` table | Every 1 hour (scheduled) | PostgreSQL |
| Per-team aggregate scores | `team_metric_snapshots` table | Every 1 hour (scheduled) | PostgreSQL |
| Check pass/fail per student | `metric_snapshots.r01_*` through `r12_*` | Every 1 hour | PostgreSQL |
| Communication indicators | `metric_snapshots` (6 columns) | Every 1 hour | PostgreSQL |
| Report generation count/duration | Prometheus: `report_generation_duration_seconds` | On demand | Prometheus TSDB |

### 10.2.2 Qualitative Data (Manual Collection)

| Data Point | Collection Method | When | Respondent |
| ---------- | ----------------- | ---- | ---------- |
| Dashboard usability | Feedback Form #1 (Likert 1-5 + open text) | Week 8 (preview) | Teacher |
| Grading experience | Feedback Form #2 (Likert 1-5 + open text) | Week 13 (post-pilot) | Teacher |
| Time spent grading (with GitPulse) | Teacher self-report log | Weeks 10-12 | Teacher |
| Time spent grading (without GitPulse, historical) | Teacher recall / prior records | Week 13 | Teacher |
| False positives observed | Teacher annotates GitPulse report disagreements | Week 12 | Teacher |
| False negatives observed | Teacher annotates missed issues GitPulse did not flag | Week 12 | Teacher |
| Student perception (optional) | Anonymous survey (5 questions) | Week 13 | Students |

### 10.2.3 Comparison Baseline

To measure accuracy (G1), a **manual grading sample** is required:

1. **Sample size:** 10 teams (≈33% of 30 teams), randomly selected
2. **Procedure:** Teacher grades 10 teams independently using the existing rubric, without consulting GitPulse
3. **Timing:** Week 12, before viewing GitPulse reports for those teams
4. **Comparison:** After manual grading, compare per-student scores with GitPulse's `weighted_score` and per-check pass/fail

| Comparison Metric | Formula |
| ----------------- | ------- |
| Score correlation (Pearson r) | `r(manual_score, gp_score)` across all students in sample |
| Check agreement rate | `count(manual_check == gp_check) / total_checks` |
| Mean absolute error | `mean(abs(manual_score - gp_score))` |
| False positive rate | `FP / (FP + TN)` per check |
| False negative rate | `FN / (FN + TP)` per check |

---

## 10.3 Success Criteria

### 10.3.1 Quantitative Thresholds

| Criterion | Metric | Target | Fail Threshold |
| --------- | ------ | ------ | -------------- |
| **Uptime** | % time health check returns OK during weeks 10-12 | ≥ 99.0% | < 95% |
| **Event completeness** | processed / received ratio | ≥ 95% | < 90% |
| **Processing latency** | p95 event processing time | ≤ 5 seconds | > 30 seconds |
| **Score accuracy** | Pearson r (GitPulse vs manual) | ≥ 0.85 | < 0.70 |
| **Check agreement** | per-check agreement rate | ≥ 90% | < 80% |
| **Mean absolute error** | MAE of weighted scores | ≤ 10 points (0-100 scale) | > 20 points |
| **False positive rate** | per-check FP rate | ≤ 10% | > 20% |
| **False negative rate** | per-check FN rate | ≤ 10% | > 20% |
| **Report generation** | 100% teams produce all 4 formats | 100% | < 95% |
| **Zero data loss** | webhook count in GitLab delivery log vs stored events | 100% match | Any mismatch |

### 10.3.2 Qualitative Thresholds

| Criterion | Metric | Target | Fail Threshold |
| --------- | ------ | ------ | -------------- |
| **Teacher satisfaction** | "Would you use GitPulse again?" (Likert 1-5) | ≥ 4.0 | < 3.0 |
| **Time savings** | Teacher self-report hours saved per team | ≥ 0.5h | 0h (no savings) |
| **Dashboard clarity** | "Is the dashboard intuitive?" (Likert 1-5) | ≥ 3.5 | < 2.5 |
| **Report usefulness** | "Did reports help with grading?" (Likert 1-5) | ≥ 4.0 | < 3.0 |
| **Check alignment** | "Do the 12 checks match your expectations?" (Likert 1-5) | ≥ 3.5 | < 2.5 |

### 10.3.3 Student Feedback (Optional, Informational)

| Question | Scale |
| -------- | ----- |
| Were the GitLab workflow requirements clear? | Likert 1-5 |
| Did you feel the evaluation process was fair? | Likert 1-5 |
| Were you aware of the automated tracking tool? | Yes/No |
| Did awareness of tracking change your behavior? | Not at all / Slightly / Significantly |
| Any comments on the evaluation process? | Free text |

---

## 10.4 Threats to Validity

### 10.4.1 Internal Validity

| Threat | Description | Mitigation |
| ------ | ----------- | ---------- |
| **Hawthorne effect** | Students may behave differently knowing they are observed by an automated tool | Do not announce GitPulse until after the evaluation window; compare behavior with prior semesters |
| **Teacher bias in manual grading** | Teacher's manual grading may be influenced by prior GitPulse exposure | Grade manual sample BEFORE viewing GitPulse reports for those teams |
| **Selection bias in sample** | 10-team sample may not be representative | Random selection; stratify by team size if needed |
| **Instrumentation bias** | GitPulse checks may favor specific workflow styles over equally valid alternatives | Review check definitions with a second teacher; document any patterns flagged incorrectly |
| **History threat** | External events (GitLab outage, network issues) may affect data | Log all external incidents; exclude affected time windows from uptime calculation |

### 10.4.2 External Validity

| Threat | Description | Mitigation |
| ------ | ----------- | ---------- |
| **Single course** | Results from ZSI may not generalize to other courses | Clearly scope conclusions to ZSI; plan second pilot for Základy DevOps |
| **Single teacher** | Usability/satisfaction data reflects one teacher's experience | Acknowledge as limitation; plan multi-teacher pilot in improvement phase |
| **TUKE GitLab specifics** | Departmental GitLab may have unique configuration | Design adapter layer in GitLab client; test with gitlab.com in CI |
| **Small sample** | 150 students is small for statistical significance | Report effect sizes with confidence intervals; avoid over-claiming |

### 10.4.3 Construct Validity

| Threat | Description | Mitigation |
| ------ | ----------- | ---------- |
| **"Meaningful review" definition** | 20-word threshold is arbitrary | Analyze word count distribution; adjust threshold if bimodal |
| **Weighted score as proxy for quality** | Passing 12 checks ≠ high-quality work | Communication indicators add nuance; teacher retains final judgment |
| **Time savings measurement** | Self-reported, not objectively measured | Use structured time log (per-team start/stop); compare with historical records |

---

## 10.5 Evaluation Timeline

| Week | Evaluation Activity | Deliverable |
| ---- | ------------------- | ----------- |
| 8 | Teacher preview of dashboard; complete Feedback Form #1 | Form #1 responses |
| 10 | Begin automated data collection for evaluation window | - |
| 11 | Mid-point check: verify data completeness, queue health | Status report |
| 12 | Teacher grades 10-team sample manually (without GitPulse); then compares with GitPulse | Manual grades spreadsheet |
| 12 | Generate reports for all 30 teams | 30 × HTML/PDF/CSV/JSON reports |
| 13 | Teacher completes Feedback Form #2; time savings log | Form #2 responses + time log |
| 13 | Export all Prometheus metrics (week 10-12 window) | Metrics CSV dump |
| 13 | Export all MetricSnapshots and TeamMetricSnapshots | DB export (JSON) |
| 14 | Analyze: compute accuracy metrics, summarize feedback, write evaluation chapter | Evaluation report |

---

## 10.6 Analysis Methods

### 10.6.1 Accuracy Analysis

```
Input:  manual_grades.csv (student_id, manual_score, manual_r01..r12)
        gp_export.json   (student_id, weighted_score, r01..r12)

Step 1: Join on student_id
Step 2: Compute Pearson r for (manual_score, weighted_score)
Step 3: For each check R01-R12:
          TP = both TRUE
          FP = GitPulse TRUE, manual FALSE
          FN = GitPulse FALSE, manual TRUE
          TN = both FALSE
          Agreement = (TP + TN) / (TP + FP + FN + TN)
          FP_rate = FP / (FP + TN)
          FN_rate = FN / (FN + TP)
Step 4: Report per-check and aggregate results
Step 5: Identify systematic disagreements -> input to weight recalibration
```

### 10.6.2 Efficiency Analysis

```
Input:  time_log.csv (team_id, grading_minutes_with_dta)
        historical_avg_minutes_per_team (from teacher recall)

Step 1: Compute mean grading time with GitPulse
Step 2: Compare with historical average
Step 3: Compute time savings = historical - DTA_mean
Step 4: Report total semester savings = savings_per_team × 30
```

### 10.6.3 Reliability Analysis

```
Input:  prometheus_export.csv (timestamp, metric_name, value)
        health_check_log.csv (timestamp, status)

Step 1: Compute uptime % for weeks 10-12
Step 2: Compute event completeness = processed / received
Step 3: Compute p50, p95, p99 processing latency
Step 4: Count failed jobs, manual interventions
Step 5: Report SLA compliance
```

---

## 10.7 Post-Pilot Improvements Backlog

Prioritized using MoSCoW method based on evaluation findings.

### 10.7.1 Must Have (Before Next Semester)

| # | Improvement | Trigger Condition | Effort |
| - | ----------- | ----------------- | ------ |
| P1 | **Recalibrate check weights** based on accuracy analysis | MAE > 10 or r < 0.85 | 1d |
| P2 | **Fix false positive checks** identified in comparison | FP rate > 10% for any check | 2d |
| P3 | **Fix false negative checks** identified in comparison | FN rate > 10% for any check | 2d |
| P4 | **GitLab OAuth login** for dashboard | Teacher requests multi-user access | 3d |
| P5 | **Bulk CSV import** for teams/students | Teacher reports setup is tedious for 30 teams | 1d |

### 10.7.2 Should Have (Within Academic Year)

| # | Improvement | Trigger Condition | Effort |
| - | ----------- | ----------------- | ------ |
| P6 | **Auto-discover teams** from GitLab group membership | Teacher requests | 2d |
| P7 | **Historical trend charts** per student | Teacher wants progress visibility | 3d |
| P8 | **Integration tests** with testcontainers | Coverage drifts near/below active CI threshold (`COVERAGE_THRESHOLD`, default 40%) | 3d |
| P9 | **Adjust meaningful review threshold** | Word count distribution shows 20 is too low/high | 0.5d |
| P10 | **Add email alerts** when team drops to RED | Teacher requests proactive notifications | 2d |

### 10.7.3 Could Have (Future Semesters)

| # | Improvement | Trigger Condition | Effort |
| - | ----------- | ----------------- | ------ |
| P11 | **LLM review quality analysis** | Teacher wants deeper review assessment; ethics approved | 5d |
| P12 | **Student self-service dashboard** (read-only) | Student feedback requests visibility | 3d |
| P13 | **Základy DevOps course support** | Second course adopts GitPulse | 5d |
| P14 | **Moodle grade export** | Department requires Moodle integration | 2d |
| P15 | **Comparative team view** | Teacher wants side-by-side comparison | 2d |

### 10.7.4 Won't Have (Descoped)

| # | Feature | Reason |
| - | ------- | ------ |
| W1 | Kubernetes deployment | Docker Compose sufficient for scale; adds complexity |
| W2 | Real-time WebSocket dashboard | SSR + HTMX polling sufficient; unnecessary complexity |
| W3 | Automated grade submission | Teacher must retain final judgment; liability risk |
| W4 | Student-facing gamification | Out of scope; could incentivize gaming metrics |

---

## 10.8 Feedback Instruments

### 10.8.1 Feedback Form #1 - Dashboard Preview (Week 8)

```
GitPulse - Teacher Preview Feedback
====================================================

Date: ___________
Course: ZSI 2025/2026

Please rate the following on a scale of 1 (strongly disagree) to 5 (strongly agree):

1. The dashboard layout is clear and intuitive.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

2. The course -> team -> student navigation makes sense.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

3. The 12 compliance checks (R01-R12) are aligned with my grading expectations.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

4. The traffic-light statuses (GREEN/YELLOW/RED) are immediately understandable.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

5. I would use this tool for actual grading if the data were complete.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

6. What information is missing from the dashboard?
   _______________________________________________________________

7. What information is unnecessary or confusing?
   _______________________________________________________________

8. Any other suggestions?
   _______________________________________________________________
```

### 10.8.2 Feedback Form #2 - Post-Pilot Evaluation (Week 13)

```
GitPulse - Post-Pilot Evaluation
==================================================

Date: ___________
Course: ZSI 2025/2026
Teams graded with GitPulse: _____ / 30

A. EFFICIENCY

1. Did GitPulse save you time in grading?
   [ ] Yes, significantly  [ ] Yes, somewhat  [ ] No difference  [ ] It took more time

2. Estimated hours saved per team compared to manual grading:
   [ ] 0 (no savings)  [ ] 0.5h  [ ] 1h  [ ] 1.5h  [ ] 2h+

3. Total estimated hours saved this semester: _____

B. ACCURACY

4. How many teams had scores you disagreed with (significantly)?
   _____ / 30

5. How many individual FALSE POSITIVES did you notice?
   (GitPulse flagged as FAIL something you would grade as PASS)
   _____

6. How many individual FALSE NEGATIVES did you notice?
   (GitPulse flagged as PASS something you would grade as FAIL)
   _____

7. Which checks were most often wrong? (list R01-R12 codes)
   _______________________________________________________________

C. USABILITY

8. The dashboard was easy to use for grading.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

9. The exported reports (HTML/PDF/CSV) were useful.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

10. The communication indicators provided useful additional insight.
    [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

D. OVERALL

11. I would use GitPulse again next semester.
    [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

12. I would recommend GitPulse to a colleague.
    [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

13. What is the single most important improvement?
    _______________________________________________________________

14. Any bugs or issues encountered?
    _______________________________________________________________

15. Additional comments:
    _______________________________________________________________
```

### 10.8.3 Student Survey (Optional, Anonymous)

```
GitLab Teamwork Process - Student Feedback (Anonymous)
======================================================

Course: ZSI 2025/2026
Team: ___________ (optional)

1. The GitLab workflow requirements (issue -> branch -> MR -> review -> merge)
   were clearly communicated.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

2. The evaluation criteria for teamwork were fair.
   [ 1 ]  [ 2 ]  [ 3 ]  [ 4 ]  [ 5 ]

3. Were you aware that an automated tool was tracking GitLab activity?
   [ ] Yes  [ ] No

4. If yes, did this awareness change how you used GitLab?
   [ ] Not at all  [ ] Slightly  [ ] Significantly

5. Any suggestions for improving the teamwork evaluation process?
   _______________________________________________________________
```

