# Full Feature Test Guide

> **Documentation Status (2026-06-05):** Current guide for the active GitPulse feature set.
> Removed subsystems are intentionally absent: legacy upload/report flows, retired scheduled fallbacks, and retired grading/heuristic subsystems.

Use this guide for manual smoke testing after a release and for targeted regression checks before deploy.

## 1. Baseline Gates

Run locally from the repository root:

```bash
python scripts/build_bundle.py --check
python scripts/check_static_artifacts.py
ruff check src tests scripts
ruff format --check src tests scripts
mypy src/app
pytest -q
```

## 2. Course Configuration Import

Use `docs/fixtures/zsi-course-config.json` or `docs/fixtures/devops-course-config.json`.

Expected sections:

- `course`
- `settings`
- `builtin_checks`
- `custom_checks`
- `weekly_deadlines`

Checks:

- Import preview shows only the active sections above.
- Import confirmation does not show skipped removed sections.
- After import, the course settings, checks, and deadlines are visible.
- Re-import is idempotent and reports applied sections without duplicate custom checks.

## 3. GitLab Group Import And Sync

1. Import a GitLab group from the dashboard.
2. Confirm the stream shows teams, students, and projects as they are discovered.
3. Open a course page while sync is still running.
4. Navigate to dashboard and back to the course.

Expected:

- Global job bar preserves queued, running, finishing, and done states across navigation.
- A finishing state remains readable long enough before done or cleanup.
- Done is shown once, not duplicated.
- Course, team, project, activity, and analytics cards refresh from fresh activity/snapshot data after sync completion.
- If a repeated sync has no new data, status text explains that data is already up to date instead of implying new issues/MRs were synced.

## 4. Roster Page

Open `/dashboard/courses/{course_id}/roster`.

Expected:

- Roster is read-only from GitLab-synced users and memberships.
- Search, pagination, role display, and CSV export work.
- No CSV upload/import controls are visible.
- The table paints on load with no loading placeholder and does not include removed upload panels.

## 5. Compliance Checks

Run team recheck and course sync.

Expected:

- R01-R13 and custom checks produce metric snapshots.
- Check details are visible on team, project, student, and analytics pages.
- Semester start/end filters hide old repository history without deleting stored data.
- Manual recheck bypasses stale cache and updates the visible cards.

## 6. Optional Teaching Tools

These feature flags may stay disabled in production until needed:

- `feature_llm_suggestions`

When enabled:

- LLM MR analysis streams findings and keeps provider/API failures visible without breaking the page.

## 7. Telemetry And Support

Expected:

- Support tickets use `/api/v1/support`; compliance history uses `/api/v1/compliance`. Pilot usage tracking, click-savings and flag-resolution telemetry have been removed.
- Weekly compliance snapshots are written without legacy columns.
- Support form grade/evaluation categories reference current grading criteria and checks.
- Service status uses the existing Prometheus stack through `/api/v1/observability/status`; raw monitoring tools require an admin session.

## 8. Admin And Health

Expected:

- System Health shows database, Redis, and session store cards in loading and loaded states.
- `Check Now` shows a stable loading state and does not flash.
- Scheduled-job registry lists only active scheduler jobs.
- Admin user/course/team/project pages do not show removed feature cards or grey-bar placeholders; every loading state is the spinner + label.

## 9. UI Navigation And Cache

Regression path:

1. Start course sync.
2. Navigate between dashboard, course detail, projects, teams, analytics, activity, and project detail.
3. Wait for finishing/done.
4. Refresh the page.

Expected:

- SSE/job polling reconnects after navigation.
- Server-rendered data and client caches reconcile to the latest sync result.
- Stale snapshot data is invalidated after sync/import/webhook updates.
- No page requires a hard refresh to show newly synced teams/projects/activity.
- Toasts are emitted once per terminal job state.
