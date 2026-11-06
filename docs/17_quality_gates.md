# Quality Gates Documentation

> **Documentation Status (2026-06-05):** Verified against current implementation.
>
> - **Source of truth (API):** `src/app/api/*`, `src/app/schemas/*`, runtime `/openapi.json`.
> - **Source of truth (CI/quality gates):** `.gitlab-ci.yml`, `pyproject.toml`.
> - **Local gate baseline:** `python scripts/build_bundle.py --check`, `python scripts/check_static_artifacts.py`, `ruff check src tests scripts`, `ruff format --check src tests scripts`, `mypy src/app`, `pytest -q`.

This document is the authoritative description of current CI quality gates and local verification commands.

## Version Baseline

The production application version is `2026.6.5.post2`.

Versioning rationale:

1. The repository started as a full-codebase initial commit, not as a tagged
   `0.1.0` release.
2. The repository has no historical release tags, so SemVer cannot be
   reconstructed honestly from history.
3. Before the 2026-05-15 version normalization commit the repo had `1875`
   commits, 48 Alembic migration files, and Alembic head `047`. By the
   2026-05-16 dashboard-scoping release the repository had grown past `1900`
   commits, which remains audit context rather than a version component.
4. Commit counts and migration counts are operational context, not a stable
   public version. They change on every commit and do not encode compatibility.
5. The current baseline therefore uses Calendar Versioning (`YYYY.M.D`) so the
   public version records the production release date without pretending to know
   historical SemVer boundaries.

Future releases should move from this baseline as:

- same-day follow-up: `YYYY.M.D.post1`, `YYYY.M.D.post2`, `YYYY.M.D.post3`, ...
- next dated release: `YYYY.M.D` only when the calendar date changes;
  otherwise use the current date with `.postN`.
- breaking changes: document explicitly in release notes and rollout docs

## Frontend Loading Contract

Every waiting state in the app is the one spinner (the tanuki mark) with a
label. There are three shapes of it and no other:

- `block_loading(height, label)` (`components/loaders.html`) for a region whose
  content arrives after first paint - a chart, the health dashboard. It reserves
  the height the content will take, so nothing below it moves, and hands off to
  the content through `GP.revealAfterLoading` (a cross-fade in place).
- `sk_table_loading(cols, label)` / `GP.tableLoading(tbody, cols)` for a table
  body. A table that already has rows keeps them and dims them (`.is-refreshing`);
  only an empty tbody shows the centred loading row, in the same box the empty
  state uses. Writing the new rows releases the state.
- `GP.renderLoaderHtml(label)` for JS-built content (the User Info modal, the
  project intelligence cards).
- Tables whose first payload is inlined (`data_table(reserve_rows=...)`) paint
  on load with no loading state at all; the reservation holds their height
  until the rows land.
- No placeholder may draw a fake version of the content (grey bars, ghost rows,
  a grey block over a chart). Do not combine two loading states for one region.
- Any change to loader CSS, page modules, service worker cache, or static
  manifests requires `python scripts/build_bundle.py` and
  `python scripts/build_bundle.py --check` before release.

## Pipeline Stages

The GitLab pipeline stages are:

1. `lint`
2. `security`
3. `test-fast`
4. `build`
5. `scan`
6. `test-heavy`
7. `publish`

## Lint Stage (Blocking)

Jobs in `lint` stage must pass for merge/deploy flow:

1. `ruff-check`
2. `ruff-format`
3. `bundle-check`
4. `static-artifact-guard`
5. `mypy`

Exact CI commands:

```bash
python scripts/build_bundle.py --check
python scripts/check_static_artifacts.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
mypy src/app/
```

Local equivalents:

```bash
python scripts/build_bundle.py --check
python scripts/vendor_alpine_csp.py --check
python scripts/check_static_artifacts.py
python scripts/dead_code_report.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
mypy src/app
```

## Security Stage (Non-blocking)

Current security jobs run with `allow_failure: true`:

1. `dependency-scan` (`pip-audit`, CycloneDX export)
2. `sbom-generate` (CycloneDX SBOM)

These jobs produce artifacts but do not block pipeline success.

## Test-fast Stage

Primary quality gate for code behavior.

1. `unit-tests` (coverage-enforced)
2. `contract-tests`
3. `integration-tests` (runs on MR/default branch)

Coverage threshold is controlled by CI variable `COVERAGE_THRESHOLD`.
Current default in `.gitlab-ci.yml` is:

```yaml
COVERAGE_THRESHOLD: "40"
```

## Build and Scan Stages

1. `docker-build` builds API and worker images with provenance labels.
2. `container-scan-api` and `container-scan-worker` run Trivy scans (`allow_failure: true`).

## Test-heavy Stage (Feature-flagged)

Heavy jobs are disabled by default and enabled via CI variables:

1. `mutation-testing` (`MUTATION_TESTING_ENABLED=true`)
2. `mutation-testing-full` (`MUTATION_TESTING_FULL=true`)
3. `performance-benchmarks` (`PERFORMANCE_TESTING_ENABLED=true`)
4. `load-testing` (`LOAD_TESTING_ENABLED=true`)
5. `quality-gate-summary` (report aggregation)

## Publish Stage

1. `deploy` (manual on default branch)
2. `publish-artifacts` (optional publishing)
3. `security-summary` (informational)

## Current Gate Matrix

| Gate | Command / Job | Blocking |
| ------ | ---------------- | ---------- |
| Ruff lint | `ruff check src/ tests/ scripts/` | Yes |
| Ruff format | `ruff format --check src/ tests/ scripts/` | Yes |
| Bundle drift | `python scripts/build_bundle.py --check` | Yes |
| Alpine CSP vendor drift | `python scripts/vendor_alpine_csp.py --check` | Yes locally / covered by bundle discipline |
| Static artifact guard | `python scripts/check_static_artifacts.py` | Yes |
| Dead-code report | `python scripts/dead_code_report.py` | No |
| Type check | `mypy src/app` | Yes |
| Unit tests | `pytest tests/unit/ ... --cov-fail-under=${COVERAGE_THRESHOLD}` | Yes |
| Contract tests | `pytest tests/unit/test_webhook_contracts.py -m contract` | Yes |
| Integration tests | `pytest tests/integration/ -m integration` | Yes (when job runs) |
| Dependency scan | `dependency-scan` | No |
| SBOM generation | `sbom-generate` | No |
| Container scans | `container-scan-*` | No |
| Heavy quality jobs | `test-heavy` jobs | No (feature-flagged) |

## Local Pre-Push Checklist

A pre-push Git hook (via `pre-commit`) runs unit tests automatically before
every `git push`. Install with:

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
```

Additionally, run this exact sequence before opening MR:

```bash
python scripts/build_bundle.py --check
python scripts/vendor_alpine_csp.py --check
python scripts/check_static_artifacts.py
python scripts/dead_code_report.py
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
mypy src/app
pytest -q
```

If Docker and services are available, also run:

```bash
pytest tests/integration -q -m integration --no-cov
```

## Troubleshooting

1. `ruff check` fails:

   - Run `ruff check src/ tests/ scripts/ --fix`.
   - Re-run `ruff format src/ tests/ scripts/`.

1. `ruff format --check` fails:

   - Run `ruff format src/ tests/ scripts/`.

1. `mypy` fails:

   - Fix typing issue in code; do not suppress globally.
   - Keep compatibility with current strict config in `pyproject.toml`.

1. Coverage fails:

   - Add/adjust unit tests until the current threshold passes.

## Authoritative References

1. `.gitlab-ci.yml`
2. `pyproject.toml`
3. `README.md`
4. `docs/06-test-plan.md`
