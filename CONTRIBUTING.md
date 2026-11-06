# Contributing to GitPulse

Thank you for your interest in contributing to GitPulse! This guide details development workflows, standards, and quality gates to keep the codebase reliable, secure, and performant.

---

## Development Setup

### 1. Prerequisites
- **Python**: 3.12+
- **Docker & Docker Compose**: v2+
- **Git**: 2.40+

### 2. Local Environment
```bash
# Clone the repository
git clone https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/workspace/workspace.git gitpulse
cd gitpulse

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Local Infrastructure (Docker Compose)
Start the PostgreSQL, Redis, and Caddy services:
```bash
docker compose up -d db redis
```

Run database migrations:
```bash
alembic upgrade head
```

Start the local development server:
```bash
uvicorn app.main:app --reload --port 8000
```

---

## Development Workflow & Standards

### Quality Gates (All Must Pass)

Every merge request must satisfy strict automated verification:

1. **Linting & Formatting**:
   ```bash
   ruff check .
   ruff format --check .
   ```
2. **Type Checking**:
   ```bash
   mypy src/app/
   ```
3. **Static Assets & Bundle Integrity**:
   ```bash
   python scripts/build_bundle.py --check
   ```
4. **Test Suite**:
   ```bash
   pytest
   ```
   All 3,850+ unit and integration tests must pass with zero failures.

---

## Commit Guidelines

We enforce the **Conventional Commits** specification:

- `feat:` — A new user-facing feature or enhancement
- `fix:` — A bug fix
- `docs:` — Documentation changes only
- `style:` — Code style changes (formatting, missing semicolons, etc.)
- `refactor:` — Code changes that neither fix bugs nor add features
- `perf:` — Performance improvements
- `test:` — Adding or updating tests
- `chore:` — Build process, dependencies, tooling, or CI updates

**Example**:
```text
feat(analytics): add real-time student engagement index to course dashboard
fix(webhook): resolve hmac timing attack vulnerability during header parsing
```

---

## Branching & Merge Requests

1. **Branch naming**:
   - `feature/<short-description>`
   - `fix/<short-description>`
   - `docs/<short-description>`
2. **Merge Request**:
   - Create MR targeting the `main` branch.
   - Use the default GitLab Merge Request template (`.gitlab/merge_request_templates/Default.md`).
   - Ensure all CI pipeline jobs (`ruff-check`, `ruff-format`, `mypy`, `test`) pass cleanly before requesting review.

---

## Architecture Principles

- **Zero-loss Webhook Ingestion**: Webhook handlers must validate signatures, enqueue background processing, and return `202 Accepted` within `< 20ms`.
- **Async First**: All database operations use `SQLAlchemy 2.0` with `asyncpg`. No blocking synchronous I/O in the request lifecycle.
- **Event-Driven Streaming**: Real-time frontend updates must stream through Server-Sent Events (SSE) backed by Redis Pub/Sub channels.
- **Privacy & Security**: Student identifiers must remain private. Do not log personal tokens, raw secrets, or unredacted author handles in LLM payloads.
