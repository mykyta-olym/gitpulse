# -- Stage 1: build dependencies --
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip
# Pin uv to a specific version so image builds are reproducible.
RUN pip install --no-cache-dir 'uv==0.5.30'

# Release metadata changes on every deploy; only the locked dependencies
# determine this layer. Keep pyproject.toml in the runtime stage below.
COPY requirements.lock ./
RUN uv pip sync --no-cache --compile-bytecode requirements.lock

# -- Stage 2: the JS and CSS the browser receives (dist/) --
# Built from the sources here, never committed (scripts/build_bundle.py). The
# two minifiers are pinned so a rebuild of the same commit serves the same files.
FROM python:3.12-slim-bookworm AS assets

WORKDIR /build
RUN pip install --no-cache-dir 'rjsmin==1.2.5' 'rcssmin==1.2.2'
COPY scripts/build_bundle.py ./scripts/
COPY src/app/ ./src/app/
RUN python scripts/build_bundle.py

# -- Stage 3: shared runtime base --
FROM python:3.12-slim-bookworm AS base

ENV DEBIAN_FRONTEND=noninteractive

# WeasyPrint system deps
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
        libffi-dev libcairo2 shared-mime-info && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# The official Python image also omits standard-library bytecode. Compile it
# here, before release metadata, so read-only processes reuse this build layer.
RUN /opt/venv/bin/python -m compileall -q /usr/local/lib/python3.12

COPY pyproject.toml requirements.lock ./
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/
# Beside src/, not under templates/: production mounts templates/ from the host.
COPY --from=assets /build/dist/ ./dist/
# Allowlist of admin/maintenance scripts that operators run via
# ``docker compose exec`` against the running container.  Dev-only
# helpers (mutation_test.py, load_test_scale.py, find_*.py,
# debug_sync_failed.py, build_bundle.py, security_scan.py, *.sh, *.sql)
# are deliberately NOT shipped to production images.
COPY scripts/create_admin.py \
     scripts/encrypt_legacy_tokens.py \
     scripts/import_course_configs.py \
     ./scripts/
COPY docs/fixtures/ ./docs/fixtures/

# Writable directories for non-root user
RUN mkdir -p /app/reports && chown -R app:app /app/reports

ENV PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv" \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Reuse Jinja and Python bytecode across all four API processes and restarts.
# Keep Jinja's cache outside the host-mounted templates directory.
RUN python -m app.template_cache && python -m compileall -q src/app

USER app

# -- API server target --
FROM base AS api
EXPOSE 8000
# Import and construct the app once before forking. Database/Redis connections
# and async warm-up still start separately in each worker's ASGI lifespan.
CMD ["gunicorn", "app.main:create_app()", "--worker-class", "uvicorn_worker.UvicornWorker", "--workers", "4", "--preload", "--no-control-socket", "--bind", "0.0.0.0:8000", "--keep-alive", "5"]

# -- Worker target --
FROM base AS worker
CMD ["python", "-m", "app.workers.main"]
