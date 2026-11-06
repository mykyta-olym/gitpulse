---
title: "Testing"
description: "GitPulse project testing guide"
---
{{< details >}}
- For: Developer
- Requires: A local environment, per the developer guide
{{< /details >}}
This page lists the current local test workflow for GitPulse.

## Baseline

```bash
python scripts/build_bundle.py --check
python scripts/check_static_artifacts.py
ruff check src tests scripts
ruff format --check src tests scripts
mypy src/app
pytest -q
```

## Targeted Runs

```bash
pytest tests/unit/
pytest tests/unit/test_compliance_engine.py
pytest tests/unit/test_sweep_automation.py -q
pytest tests/unit/test_compliance_history_and_support_feedback.py -q
pytest -m "not performance"
```

## Test Structure

```text
tests/
+-- unit/
|   +-- test_compliance_engine.py
|   +-- test_dynamic_checks.py
|   +-- test_sweep_automation.py
|   +-- test_compliance_history_and_support_feedback.py
|   +-- test_security.py
|   +-- test_frontend_resilience.py
+-- integration/
+-- load/
```

## Frontend Assets

Do not edit generated bundles by hand. Change source files under:

- `src/app/templates/static/js/_parts/`
- `src/app/templates/static/js/*.js`
- `src/app/templates/static/css/_parts/`
- `src/app/templates/static/css/pages/`

Then rebuild into `dist/` (content-hashed files + `dist/manifest.json`; never committed, the Docker image and CI build their own):

```bash
python scripts/build_bundle.py          # or --watch while developing
python scripts/check_static_artifacts.py
```

## Regression Focus

- sync/job lifecycle states across navigation
- cache invalidation after sync/import/webhook updates
- server-rendered pages without stale client-only placeholders
- support forms and compliance and support schemas
- optional LLM flows
