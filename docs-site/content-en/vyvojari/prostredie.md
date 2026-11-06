---
title: "Local environment"
description: "Setting up the development environment for GitPulse"
---
{{< details >}}
- For: Developer
- Requires: A local environment, per the developer guide
{{< /details >}}
This page guides you through setting up a development environment to work on the GitPulse.

## Prerequisites

### Mandatory

| Tool | Version | Installation |
| --------- | -------- | ------------ |
| Python | 3.12+ | [python.org](https://python.org) |
| Docker | 24+ | [docker.com](https://docker.com) |
| Git | 2.40+ | [git-scm.com](https://git-scm.com) |

### Recommended

| Tool | Purpose |
| --------- | ------ |
| VS Code | IDE with Python extension |
| uv | Fast package manager |
| pre-commit | Git hooks |

## Installation

### 1. Cloning the repository

```bash
git clone https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/workspace/workspace.git gitpulse
cd gitpulse
```

### 2. Python environment

{{< tabs >}}

{{< tab title="venv (standard)" >}}

```bash
  python -m venv .venv
  source .venv/bin/activate  # Linux/Mac
  .venv\Scripts\activate     # Windows PowerShell
  ```

{{< /tab >}}

{{< tab title="uv (recommended)" >}}

```bash
  uv venv
  source .venv/bin/activate
  ```

{{< /tab >}}

{{< tab title="condo" >}}

```bash
  conda create -n gitpulse python=3.12
  conda activate gitpulse
  ```

{{< /tab >}}

{{< /tabs >}}
### 3. Installing dependencies

```bash
# Production dependencies
pip install --constraint requirements.lock -e ".[otel]"

# Development dependencies (tests, linting)
pip install --constraint requirements.lock -e ".[dev,otel]"

# Load tests
pip install --constraint requirements.lock -e ".[load,otel]"

# Common local full setup
pip install --constraint requirements.lock -e ".[dev,otel,security]"
```

The production lockfile constrains application dependencies on every platform;
optional dependencies still follow their platform markers. Documentation uses
Hugo, not Python extras: run `docker compose up -d --build gitpulse-docs`.

### 4. Starting Services

```bash
# Spustenie PostgreSQL a Redis
docker compose up -d postgres redis

# Overenie
docker compose ps
```

### 5. Configuration

Create a file `.env` in the root directory:

```bash
# .env
DATABASE_URL=postgresql+asyncpg://gitpulse:gitpulse@localhost:5432/gitpulse
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=development-secret-key-change-in-production
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat_placeholder_token

# Feature flags
FEATURE_RBAC=true
```

### 6. Database

```bash
# Spustenie migrácií
alembic upgrade head

# Overenie
docker compose exec postgres psql -U gitpulse -c "\dt"
```

### 7. Starting the application

{{< tabs >}}

{{< tab title="PowerShell script (recommended)" >}}

```powershell
  # Rýchly štart s Docker
  .\start-dev.ps1

  # Bez Docker (ak sú služby už spustené)
  .\start-dev.ps1 -SkipDocker

  # S iným portom
  .\start-dev.ps1 -Port 8080

  # Bez cleanup po ukončení
  .\start-dev.ps1 -NoCleanup
  ```

{{< /tab >}}

{{< tab title="Manual (uvicorn)" >}}

```bash
  # Nastavenie environment premenných
  export DATABASE_URL="postgresql+asyncpg://gitpulse:gitpulse@localhost:5432/gitpulse"
  export SECRET_KEY="dev-secret-key"
  export TEACHER_API_TOKEN="dev-token"
  export PYTHONPATH="$PWD/src"

  # Spustenie
  uvicorn app.main:create_app --factory --reload --port 8000
  ```

{{< /tab >}}

{{< tab title="Docker Compose" >}}

```bash
  docker compose -f docker-compose.dev.yml up -d
  ```

{{< /tab >}}

{{< /tabs >}}
## Installation verification

```bash
# API health check
curl http://localhost:8000/health

# Swagger UI
open http://localhost:8000/docs

# Dashboard
open http://localhost:8000/dashboard
```

## VS Code setup

### Recommended extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml"
  ]
}
```

### Workspace settings

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  },
  "ruff.lint.args": ["--config=pyproject.toml"]
}
```

## Pre-commit hooks

```bash
# Installation
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push   # pre-push unit tests

# Manual run
pre-commit run --all-files
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert]

  - repo: local
    hooks:
      - id: pre-push-tests
        name: Run unit tests before push
        language: system
        entry: python -m pytest tests/unit/ -x -q --no-header --tb=short
        pass_filenames: false
        stages: [pre-push]
        always_run: true
```

## Troubleshooting

### Port already in use

```bash
# Nájdenie procesu
lsof -i :8000
netstat -ano | findstr :8000  # Windows

# Ukončenie procesu
kill -9 <PID>
```

### Database connection failed

```bash
# Overenie, že PostgreSQL beží
docker compose ps postgres

# Reštart
docker compose restart postgres

# Log
docker compose logs postgres
```

### Import errors

```bash
# Reinstall v editable mode
pip install --constraint requirements.lock -e ".[dev,otel]"

# Overenie PYTHONPATH
echo $PYTHONPATH
export PYTHONPATH=$PWD/src
```

## Further reading

- [Project structure](struktura.md)
- [Testing](testovanie.md)
- [Contributing](prispievanie.md)

