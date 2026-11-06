# Teacher Checklist Mapping to Compliance Checks

> **Documentation Status (2026-05-31):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.


This document maps the questions that teachers check on assignments to the existing compliance checks in the GitPulse system.

## Teacher Checklist vs. Compliance Checks

| # | Teacher Question | Check ID | Name | Description |
|---|------------------|----------|------|-------------|
| 1 | **Did the student assign themselves an Issue?** | `R01` | Issue Ownership | `passed ⟺ |assigned_issues| == 1` |
| 2 | **Was a branch and MR created?** | `R02` | Branch Naming | `passed ⟺ |mrs_authored| ≥ 1 ∧ ∀ MR: branch_naming_ok` |
| 3 | **Does the MR have a meaningful description or is it linked to an Issue?** | `R04` | MR-Issue Link | `passed ⟺ ∃ MR: has_issue_link` |
| 3b | (description follows template) | `R05` | MR Template | `passed ⟺ ∃ MR: template_compliant` |
| 4 | **Is the implementation reasonably OK?** | - | *Manual* | LLM can provide recommendations |
| 5 | **Were tests written or modified?** | `R03` | Test Changes | `passed ⟺ ∃ MR: has_test_changes` |
| 6 | **Are commits reasonably OK?** | `R13` | Commit Quality | Flags high web-editor ratio and too few meaningful commits |
| 7 | **Did the student do meaningful code review #1?** | `R07` | Review Duty | `passed ⟺ |meaningful_reviews_given| ≥ threshold` |
| 7b | (review quality) | `R07` | Review Duty | Uses `min_review_word_count` and distinct reviewed MR threshold |
| 8 | **Did the student do meaningful code review #2?** | `R07` | Review Duty | Configurable threshold: `min_distinct_mrs_reviewed` |
| 9 | **Was own code modified after code review?** | `R08` | Response Quality | `passed ⟺ response_rate == 1.0 ∧ contains_commit_ref` |
| 10 | **Did the student merge the MR where they were assignee?** | `R10` | Merged by Author | `passed ⟺ ∃ MR: state=="merged" ∧ merged_by_id is a known team member` (permissive: author OR teammate; fails only for unknown user). Set `cfg.require_self_merge=true` to enforce author-only or `cfg.forbid_self_merge=true` for the reviewer-gates-merge model |
| 11 | **Is the project Pipeline green?** | `R12` | Pipeline Health | `passed ⟺ ∃ pipeline: status=="success" ∧ has_test_job` |
| 12 | **Are commits meaningful (not web-editor spam)?** | `R13` | Commit Quality | `passed ⟺ web_editor_ratio ≤ threshold ∧ commits_total ≥ min` |

## Additional Checks (not in original list)

| Check ID | Name | Description |
|----------|------|-------------|
| `R06` | Review Received | Student received reviews from peers |
| `R09` | Approval Received | MR received approvals |
| `R11` | Closure State | MR and Issue are closed |

## Communication Indicators (Diagnostic metrics)

These metrics are not part of the score but help teachers understand communication patterns:

| Metric | Description |
|--------|-------------|
| `median_first_response_hours` | Median time to first response on MR |
| `median_review_rounds` | Median number of discussion rounds |
| `discussion_resolution_pct` | Percentage of resolved discussions |
| `review_word_depth` | Average word count in review comments |
| `author_response_word_depth` | Average word count in author responses |
| `median_time_to_merge_hours` | Median time from MR creation to merge |

## LLM Analysis (Recommendations for teachers)

When `FEATURE_LLM_SUGGESTIONS=true`, the system can analyze MR communication and provide:

- **Risk Flags**: toxic tone, low-effort, ignoring feedback
- **Recommended Questions**: Questions the teacher should ask the student
- **Confidence Score**: Confidence level of the analysis (0.0-1.0)

> **Important**: LLM provides RECOMMENDATIONS only, not automatic grading!

## CourseSettings Configuration

```python
# Weights for individual checks (sum = 1.0)
weight_issue_ownership = 0.08     # R01
weight_branch_naming = 0.06       # R02
weight_test_changes = 0.10        # R03
weight_mr_issue_link = 0.08       # R04
weight_mr_template = 0.05         # R05
weight_review_count = 0.12        # R06
weight_review_duty = 0.12         # R07
weight_response_complete = 0.10   # R08
weight_approvals = 0.09           # R09
weight_merge_by_author = 0.07     # R10
weight_closure = 0.06             # R11
weight_pipeline_health = 0.07    # R12
weight_commit_quality = 0.00      # R13 (opt-in, default weight 0)

# Thresholds
min_reviews_per_mr = 2            # Minimum number of reviews
min_review_word_count = 15        # Minimum word count per reviewer (was 30 - lowered in migration 039)
min_distinct_mrs_reviewed = 2     # Minimum number of MRs reviewed

# Traffic light
green_threshold = 0.80            # >= 80% = GREEN
yellow_threshold = 0.50           # >= 50% = YELLOW, otherwise RED

# Selectively enable/disable checks
enabled_checks = ["R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R10", "R12", "R13"]
```

## Schedule for DevOps Fundamentals Course

| Week | Area | Relevant Checks |
|------|------|-----------------|
| 2-3 | Git | R02 (branch naming) |
| 4-5 | Docker | - |
| 6 | CI/CD | R12 |
| 7 | Tools Test | - |
| 8 | Issue tracking | R01, R04, R11 |
| 9 | Unit testing | R03, R12 |
| 10-11 | MR, code review, communication | R05, R06, R07, R08, R09, R10, LLM |
| 12 | Evaluation | All active checks |
