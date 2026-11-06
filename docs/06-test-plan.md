# 6. Test Plan & CI Pipeline

> **Documentation Status (2026-06-01):** Verified against current implementation.
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.

**Current local suite: 2 596 unit tests collected and passing (`tests/unit`); integration/e2e suites under `tests/integration` and `tests/load` require a live Postgres + Redis fixture and are not part of the default `pytest tests/unit` gate.**

## 6.1 Test Strategy

| Level | Scope | Services Required | Location |
|------|-------|-------------------|----------|
| Unit | Business logic, routers, schemas, utilities | No | `tests/unit/` |
| Contract | Webhook schema compatibility | No | `tests/unit/test_webhook_contracts.py` |
| Integration | DB/Redis-backed behavior | PostgreSQL + Redis | `tests/integration/` |
| Load/Perf | Throughput and latency checks | Running app + infra | `tests/load/`, benchmark tests |

## 6.2 Required Local Quality Checks (Before MR)

Run in repository root:

```bash
python scripts/build_bundle.py --check
python scripts/vendor_alpine_csp.py --check
python scripts/check_static_artifacts.py
python scripts/dead_code_report.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
mypy src/app
pytest tests/unit -q
pytest tests/unit/test_webhook_contracts.py -q -m contract --no-cov
```

Optional but recommended (if services available):

```bash
pytest tests/integration -q -m integration --no-cov
```

## 6.3 CI Pipeline Mapping

Current stage flow:

```text
lint -> security -> test-fast -> build -> scan -> test-heavy -> publish
```

### Lint stage

| Job | Command | Blocking |
|-----|---------|----------|
| `bundle-check` | `python scripts/build_bundle.py --check` | Yes |
| `static-artifact-guard` | `python scripts/check_static_artifacts.py` | Yes |
| `dead-code-report` | `python scripts/dead_code_report.py` | No |
| `ruff-check` | `ruff check src/ tests/ scripts/` | Yes |
| `ruff-format` | `ruff format --check src/ tests/ scripts/` | Yes |
| `mypy` | `mypy src/app/` | Yes |

### test-fast stage

| Job | Command | Blocking |
|-----|---------|----------|
| `unit-tests` | `pytest tests/unit/ ... --cov-fail-under=${COVERAGE_THRESHOLD}` | Yes |
| `contract-tests` | `pytest tests/unit/test_webhook_contracts.py -m contract` | Yes |
| `integration-tests` | `pytest tests/integration/ -m integration --no-cov` | Yes (when job runs by rules) |

### Current default quality thresholds

| Metric | Current default |
|--------|-----------------|
| Coverage threshold | `COVERAGE_THRESHOLD=40` |
| Ruff lint | 0 errors |
| Ruff format | 0 diffs |
| mypy strict | 0 errors |

## 6.4 Heavy / Optional Quality Jobs

Controlled through CI variables:

1. `MUTATION_TESTING_ENABLED`
2. `MUTATION_TESTING_FULL`
3. `PERFORMANCE_TESTING_ENABLED`
4. `LOAD_TESTING_ENABLED`

When disabled (default), these jobs do not run.

## 6.5 Security and Supply-chain Checks

Security jobs are informative (`allow_failure: true`):

1. `dependency-scan` (`pip-audit`)
2. `sbom-generate` (CycloneDX)
3. `container-scan-api` / `container-scan-worker` (Trivy)

## 6.6 Fast Failure Playbook

1. If `ruff-check` fails:
- run `ruff check src/ tests/ scripts/ --fix`
- rerun `ruff check src/ tests/ scripts/`

2. If `bundle-check` or `static-artifact-guard` fails:
- run `python scripts/build_bundle.py` only when source static assets changed intentionally
- remove accidental root/generated artifacts outside `src/app/templates/static`
- rerun `python scripts/build_bundle.py --check` and `python scripts/check_static_artifacts.py`

3. If `ruff-format` fails:
- run `ruff format src/ tests/ scripts/`
- rerun `ruff format --check src/ tests/ scripts/`

4. If `mypy` fails:
- fix annotations/returns/import types in affected file
- rerun `mypy src/app`

5. If unit/contract tests fail:
- run failed test module with `-k` filter locally
- add missing test coverage for regression

## 6.7 Test Coverage by Feature Area

| Feature Area | Test Files | Approx. Tests |
|---|---|---|
| Security (session, CSRF, RBAC, auth) | `test_security.py`, `test_rbac.py`, `test_gitlab_oauth.py` | ~180 |
| Compliance engine (R01-R13 + custom checks) | `test_compliance_engine.py`, `test_dynamic_checks.py` | ~260 |
| Webhook processing & idempotency | `test_webhook_contracts.py`, `test_idempotency.py` | ~60 |
| Dashboard routes & templates | `test_dashboard_*.py` | ~200 |
| API routes & schemas | `test_api_*.py` | ~300 |
| GitLab integration & enrichment | `test_gitlab_client.py`, `test_sync_enrich.py` | ~100 |
| Role hierarchy & membership | `test_roles.py`, `test_member_sync.py` | ~80 |
| Dynamic feedback forms | `test_support_helpers.py` | ~50 |
| Token encryption (Fernet) | `test_token_encryption.py` | ~20 |
| LLM suggestions | `test_llm_module.py` | ~30 |
| Compliance history, support feedback & event pipeline | `test_compliance_history_and_support_feedback.py`, `test_event_pipeline.py` | ~100 |
| Observability (middleware, logging) | `test_middleware.py`, `test_observability.py` | ~60 |
| Frontend features (JS-level, via templates) | `test_frontend_resilience.py` | ~50 |

## 6.8 References

1. `.gitlab-ci.yml`
2. `pyproject.toml`
3. `docs/17_quality_gates.md`
4. `README.md`
