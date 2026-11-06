param(
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "restart", "api", "worker", "migrations", "docs", "checks", "help", "clean")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"


function Write-Color {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Color "==============================================================" "Cyan"
    Write-Color "  $Text" "Cyan"
    Write-Color "==============================================================" "Cyan"
    Write-Host ""
}

function Show-Help {
    Write-Header "GitPulse - Dev Script"
    Write-Color "Usage: .\start-dev.ps1 [command]" "Yellow"
    Write-Host ""
    Write-Color "Commands:" "White"
    Write-Color "  restart     - Full clean restart (wipe DB, start all services)" "Green"
    Write-Color "  up          - Start dev containers (Postgres, Redis, Mailpit) + Docs" "White"
    Write-Color "  down        - Stop all services, wipe local DB" "White"
    Write-Color "  clean       - Same as down" "White"
    Write-Color "  docs        - Start Documentation Site (http://localhost:8001)" "White"
    Write-Color "  api         - Start API Server locally" "White"
    Write-Color "  worker      - Start Worker locally" "White"
    Write-Color "  migrations  - Run Database Migrations" "White"
    Write-Color "  checks      - Health-check all services" "White"
    Write-Color "  help        - Show this help message" "White"
}

function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Color "ERROR: Docker is not installed" "Red"; exit 1
    }
    $dockerOk = $false
    $ErrorActionPreference = "Continue"
    docker info *>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
    $ErrorActionPreference = "Stop"
    if (-not $dockerOk) {
        Write-Color "ERROR: Docker daemon is not running" "Red"; exit 1
    }
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Color "ERROR: Python is not installed" "Red"; exit 1
    }
    if (-not (Test-Path "$ProjectRoot\.env")) {
        Write-Color "ERROR: .env file not found" "Red"; exit 1
    }
    Write-Color "[OK] Prerequisites met" "Green"
}

function Import-EnvFile {
    if (Test-Path "$ProjectRoot\.env") {
        Get-Content "$ProjectRoot\.env" | ForEach-Object {
            if ($_ -match "^([^#][^=]+)=(.*)$") {
                $name = $Matches[1].Trim()
                $value = $Matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
            }
        }
    }
}

function Stop-All {
    Write-Header "Stopping All Services and Cleaning Volumes"
    Set-Location $ProjectRoot

    # Stop monitoring stack (Prometheus, Grafana, Jaeger) if running
    Write-Color "  Stopping monitoring containers..." "Yellow"
    docker compose --profile monitoring down --remove-orphans 2>&1 | Out-Null

    # Kill leftover API (uvicorn) and Worker (rq) python processes from
    # previous restart windows so they don't hold stale DB connections.
    Write-Color "  Stopping leftover Python processes (uvicorn / worker)..." "Yellow"
    Get-Process -Name python -ErrorAction SilentlyContinue |
        Where-Object {
            try {
                $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
                $cmd -match 'uvicorn|app\.workers\.main|rq\.cli'
            } catch { $false }
        } |
        ForEach-Object {
            Write-Color "    Killing PID $($_.Id)" "Yellow"
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    # Brief pause so OS fully releases file handles from killed processes
    Start-Sleep -Seconds 2

    # Purge Python bytecode caches so the new server always loads fresh
    # .py source instead of stale .pyc compiled files.
    Write-Color "  Cleaning __pycache__ directories..." "Yellow"
    $cacheDirs = Get-ChildItem -Path $ProjectRoot -Directory -Recurse -Filter '__pycache__' -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notlike '*\.venv*' -and $_.FullName -notlike '*node_modules*' }
    $cacheCount = ($cacheDirs | Measure-Object).Count
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Color "  [OK] Removed $cacheCount __pycache__ directories" "Green"

    # Wipe the dev database (DROP + CREATE inside the compose container -
    # no local psql needed) so restart always begins with a clean schema
    # populated only by migrations. Dev infra lives in docker-compose.dev.yml
    # (Postgres :5433, Redis :6379, Mailpit :1025/:8025).
    Import-EnvFile
    $pgUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "gitpulse" }
    $pgDb   = if ($env:POSTGRES_DB)   { $env:POSTGRES_DB }   else { "gitpulse" }
    $composeDev = @("compose", "-f", "$ProjectRoot\docker-compose.dev.yml")
    docker @composeDev ps --status running 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Color "  Resetting dev database '$pgDb'..." "Yellow"
        $terminateSql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$pgDb' AND pid<>pg_backend_pid();"
        docker @composeDev exec -T postgres psql -U $pgUser -d postgres -c $terminateSql 2>&1 | Out-Null
        docker @composeDev exec -T postgres psql -U $pgUser -d postgres -c "DROP DATABASE IF EXISTS $pgDb;" 2>&1 | Out-Null
        docker @composeDev exec -T postgres psql -U $pgUser -d postgres -c "CREATE DATABASE $pgDb OWNER $pgUser;" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Color "  [OK] Database '$pgDb' recreated" "Green"
        } else {
            Write-Color "  [WARN] Failed to recreate database '$pgDb' (is the postgres container up?)" "Yellow"
        }
    } else {
        Write-Color "  [SKIP] Dev containers not running - nothing to reset" "Yellow"
    }

    # Flush RQ queues in Redis so stale jobs from the previous session
    # (which reference now-deleted DB rows) don't get picked up by the
    # new worker after DB wipe.
    if ($env:REDIS_URL) {
        Write-Color "  Flushing RQ queues in Redis..." "Yellow"
        $flushScript = @"
import sys
try:
    from redis import Redis
    conn = Redis.from_url('$($env:REDIS_URL)')
    # Use raw Redis commands - importing rq triggers
    # multiprocessing.get_context('fork') which fails on Windows.
    for q in ('high', 'default', 'low'):
        conn.delete(f'rq:queue:{q}')
        print(f'    Queue {q}: flushed')
    # Clear registries (sorted sets)
    for q in ('high', 'default', 'low'):
        for reg in ('failed', 'started', 'scheduled', 'deferred', 'canceled'):
            conn.delete(f'rq:{reg}:{q}')
    print('    Registries cleaned')
except Exception as e:
    print(f'    [WARN] Could not flush Redis queues: {e}', file=sys.stderr)
"@
        $env:PYTHONPATH = "$ProjectRoot\src"
        & $VenvPython -c $flushScript
    }

    $DocsDir = Join-Path $ProjectRoot "docs-site"
    if (Test-Path "$DocsDir\docker-compose.docs.yml") {
        Write-Color "  Stopping docs-site containers..." "Yellow"
        Set-Location $DocsDir
        docker compose -f docker-compose.docs.yml down -v --remove-orphans 2>&1 | Out-Null
        Set-Location $ProjectRoot
    }

    # Stop the dev infra containers last (DB reset above needed them alive).
    Write-Color "  Stopping dev containers (Postgres, Redis, Mailpit)..." "Yellow"
    docker compose -f "$ProjectRoot\docker-compose.dev.yml" stop 2>&1 | Out-Null

    Write-Color "[OK] All stopped and cleaned" "Green"
}

function Start-Database {
    Write-Header "Starting Dev Containers (Postgres + Redis + Mailpit)"
    Set-Location $ProjectRoot

    # docker-compose.dev.yml owns the whole local infra: Postgres on 5433,
    # Redis on 6379, and Mailpit (SMTP :1025, UI :8025) matching .env.
    # --wait blocks until every healthcheck passes.
    docker compose -f docker-compose.dev.yml up -d --wait
    if ($LASTEXITCODE -ne 0) {
        Write-Color "ERROR: dev containers failed to start (docker compose -f docker-compose.dev.yml up)" "Red"
        exit 1
    }
    Write-Color "[OK] Postgres ready on localhost:5433" "Green"
    Write-Color "[OK] Redis ready on localhost:6379" "Green"
    Write-Color "[OK] Mailpit ready - SMTP :1025, UI http://localhost:8025" "Green"
}

function Start-Docs {
    Write-Header "Starting Documentation Site"
    $DocsDir = Join-Path $ProjectRoot "docs-site"
    if (-not (Test-Path $DocsDir)) {
        Write-Color "ERROR: docs-site directory not found" "Red"
        return
    }
    Set-Location $DocsDir
    docker compose -f docker-compose.docs.yml up -d --build --force-recreate docs-dev
    Set-Location $ProjectRoot

    Write-Color "Waiting for docs site (port 8001)..." "Yellow"
    $retries = 30
    while ($retries -gt 0) {
        try {
            $conn = Test-NetConnection -ComputerName localhost -Port 8001 -WarningAction SilentlyContinue
            if ($conn.TcpTestSucceeded) {
                Write-Host ""
                Write-Color "[OK] Docs site ready at http://localhost:8001" "Green"
                return
            }
        }
        catch { }
        Start-Sleep -Seconds 2
        $retries--
        Write-Host -NoNewline "."
    }
    Write-Host ""
    Write-Color "WARNING: Docs site not reachable yet (may still be building)" "Yellow"
}

function Invoke-Migrations {
    Write-Header "Running Database Migrations"
    Set-Location $ProjectRoot
    Import-EnvFile
    $env:PYTHONPATH = "$ProjectRoot\src"
    & $VenvPython -m alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        Write-Color "[OK] Migrations completed" "Green"
    }
    else {
        Write-Color "ERROR: Migrations failed" "Red"
        exit 1
    }
}

function Build-Bundles {
    Write-Header "Building JS/CSS Bundles"
    Set-Location $ProjectRoot
    & $VenvPython scripts/build_bundle.py
    if ($LASTEXITCODE -eq 0) {
        Write-Color "[OK] Bundles built" "Green"
    }
    else {
        Write-Color "ERROR: Bundle build failed" "Red"
        exit 1
    }
}

function Start-ApiServer {
    Write-Header "Starting API Server"
    Set-Location $ProjectRoot
    Import-EnvFile
    $env:PYTHONPATH = "$ProjectRoot\src"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    Write-Color "Starting uvicorn on http://localhost:8000" "Green"
    Write-Color "API Docs: http://localhost:8000/docs" "Cyan"
    # --reload only watches *.py by default. The check registry lives in
    # compliance/builtin_checks.json and is read at import, so without this an
    # edit there is silently ignored until the server is restarted by hand.
    & $VenvPython -m uvicorn app.main:create_app --factory --reload --reload-dir src --reload-include "*.json" --host 0.0.0.0 --port 8000
}

function Start-Worker {
    Write-Header "Starting Background Worker"
    Set-Location $ProjectRoot
    Import-EnvFile
    $env:PYTHONPATH = "$ProjectRoot\src"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    Write-Color "Starting RQ worker..." "Green"
    & $VenvPython -m app.workers.main
}

function Test-Health {
    Write-Header "Checking System Health"

    Import-EnvFile
    $checks = @(
        @{Name = "Postgres"; Port = 5433; Host = "localhost"},
        @{Name = "Mailpit"; Port = 8025; Host = "localhost"},
        @{Name = "Docs"; Port = 8001; Host = "localhost"},
        @{Name = "API"; Port = 8000; Host = "localhost"}
    )

    # Redis from .env (local compose container by default)
    if ($env:REDIS_URL) {
        try {
            $uri = [System.Uri]$env:REDIS_URL
            $checks += @{Name = "Redis"; Port = $uri.Port; Host = $uri.Host}
        } catch {}
    }

    foreach ($check in $checks) {
        try {
            $conn = Test-NetConnection -ComputerName $check.Host -Port $check.Port -WarningAction SilentlyContinue
            if ($conn.TcpTestSucceeded) {
                Write-Color "[OK]   $($check.Name) on port $($check.Port)" "Green"
            }
            else {
                Write-Color "[WARN] $($check.Name) NOT listening on port $($check.Port)" "Yellow"
            }
        }
        catch {
            Write-Color "[FAIL] Error checking $($check.Name)" "Red"
        }
    }
}

function Invoke-FullRestart {
    Write-Header "FULL CLEAN RESTART"

    Stop-All
    Test-Prerequisites
    Start-Database
    Start-Docs
    Invoke-Migrations
    Build-Bundles

    Write-Header "Launching API and Worker in new windows"

    # Start ONLY the monitoring stack (Prometheus + Grafana + Jaeger) in Docker.
    # Use --no-deps so Docker does not pull in the api/postgres/redis services
    # (which would conflict with the locally-launched API and Worker).
    # The monitoring-dev override swaps Prometheus target from "api:8000"
    # (Docker service) to "host.docker.internal:8000" (host machine).
    Write-Color "Starting monitoring stack..." "Cyan"
    Set-Location $ProjectRoot
    docker compose -f docker-compose.yml -f docker-compose.monitoring-dev.yml --profile monitoring up -d --no-deps grafana prometheus jaeger 2>&1 | Out-Null
    Write-Color "[OK] Monitoring stack started (Grafana :3000, Prometheus :9090, Jaeger :16686)" "Green"

    $scriptPath = Join-Path $ProjectRoot "start-dev.ps1"

    Write-Color "Spawning API server..." "Cyan"
    $apiArgs = @("-NoExit", "-File", $scriptPath, "api")
    Start-Process powershell -ArgumentList $apiArgs

    Write-Color "Spawning Worker..." "Cyan"
    $workerArgs = @("-NoExit", "-File", $scriptPath, "worker")
    Start-Process powershell -ArgumentList $workerArgs

    Write-Color "Waiting 10 seconds for services to start..." "Yellow"
    Start-Sleep -Seconds 10

    Test-Health

    Write-Header "System Ready"
    Write-Color "Dashboard: http://localhost:8000/dashboard" "Cyan"
    Write-Color "API Docs:  http://localhost:8000/docs" "Cyan"
    Write-Color "Docs Site: http://localhost:8001" "Cyan"
    Write-Color "Grafana:   http://localhost:3000" "Cyan"
    Write-Color "Prometheus:http://localhost:9090" "Cyan"
    Write-Color "Jaeger:    http://localhost:16686" "Cyan"
}

switch ($Command) {
    "restart"    { Invoke-FullRestart }
    "up"         { Test-Prerequisites; Start-Database; Start-Docs }
    "down"       { Stop-All }
    "clean"      { Stop-All }
    "api"        { Test-Prerequisites; Import-EnvFile; Start-ApiServer }
    "worker"     { Test-Prerequisites; Import-EnvFile; Start-Worker }
    "migrations" { Test-Prerequisites; Import-EnvFile; Invoke-Migrations }
    "docs"       { Start-Docs }
    "checks"     { Test-Health }
    "help"       { Show-Help }
    Default      { Show-Help }
}
