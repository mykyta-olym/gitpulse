<#
.SYNOPSIS
    GitPulse - Production Deployment (TUKE Cloud)

.DESCRIPTION
    Deploys the application to production using Docker Compose.
    Requires .env.production configuration file.

.PARAMETER Build
    Rebuild Docker images before starting

.PARAMETER Migrate
    Run database migrations after starting

.PARAMETER Stop
    Stop all services

.PARAMETER Monitoring
    Start with monitoring profile (Grafana, Prometheus, Jaeger)

.PARAMETER Logs
    Follow service logs after starting

.EXAMPLE
    .\deploy-production.ps1

.EXAMPLE
    .\deploy-production.ps1 -Build -Migrate

.EXAMPLE
    .\deploy-production.ps1 -Monitoring
#>

param(
    [switch]$Build,
    [switch]$Migrate,
    [switch]$Stop,
    [switch]$Monitoring,
    [switch]$Logs,
    [switch]$ImportConfigs,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# ===============================================================================
#                              SHOW HELP
# ===============================================================================

if ($Help) {
    Write-Host @"

GitPulse - Production Deployment

USAGE:
    .\deploy-production.ps1 [options]

OPTIONS:
    -Build          Rebuild Docker images
    -Migrate        Run database migrations
    -ImportConfigs  Import ZSI + DevOps course configs from fixtures
    -Stop           Stop all services
    -Monitoring     Start with Grafana, Prometheus, Jaeger
    -Logs           Follow logs after starting
    -Help           Show this help message

EXAMPLES:
    .\deploy-production.ps1                                # Start services
    .\deploy-production.ps1 -Build -Migrate -ImportConfigs # Full first deploy
    .\deploy-production.ps1 -ImportConfigs                 # Import course configs only
    .\deploy-production.ps1 -Monitoring                    # Start with monitoring
    .\deploy-production.ps1 -Stop                          # Stop all services

CONFIGURATION:
    Copy .env.production.example to .env.production and fill in:
    - POSTGRES_PASSWORD (generate: openssl rand -hex 16)
    - SECRET_KEY (generate: openssl rand -hex 32)
    - TEACHER_API_TOKEN (generate: openssl rand -hex 24)
    - GITLAB_OAUTH_CLIENT_ID
    - GITLAB_OAUTH_CLIENT_SECRET
    - GITLAB_TOKEN
    - DOMAIN (e.g., gitpulse.tuke.sk)

FIRST DEPLOYMENT:
    .\deploy-production.ps1 -Build -Migrate -ImportConfigs

"@
    exit 0
}

# ===============================================================================
#                              BANNER
# ===============================================================================

Write-Host ""
Write-Host "  +==============================================================+" -ForegroundColor Cyan
Write-Host "  |  GitPulse - Production Deployment                       |" -ForegroundColor Cyan
Write-Host "  |  TUKE Cloud                                                  |" -ForegroundColor Cyan
Write-Host "  +==============================================================+" -ForegroundColor Cyan
Write-Host ""

# ===============================================================================
#                              CHECK CONFIGURATION
# ===============================================================================

if (-not (Test-Path ".env.production")) {
    Write-Host "  [ERROR] .env.production not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Setup instructions:" -ForegroundColor Yellow
    Write-Host "    1. Copy template:  cp .env.production.example .env.production" -ForegroundColor Gray
    Write-Host "    2. Generate secrets:" -ForegroundColor Gray
    Write-Host "       openssl rand -hex 16  -> POSTGRES_PASSWORD" -ForegroundColor Gray
    Write-Host "       openssl rand -hex 32  -> SECRET_KEY" -ForegroundColor Gray
    Write-Host "       openssl rand -hex 24  -> TEACHER_API_TOKEN" -ForegroundColor Gray
    Write-Host "    3. Configure GitLab OAuth in GitLab Admin" -ForegroundColor Gray
    Write-Host "    4. Set DOMAIN to your production domain" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "  [OK] .env.production found" -ForegroundColor Green

# Read domain from .env.production
$domain = "localhost"
Get-Content ".env.production" | ForEach-Object {
    if ($_ -match '^DOMAIN=(.+)$') {
        $domain = $Matches[1].Trim()
    }
}
Write-Host "  [OK] Domain: $domain" -ForegroundColor Green

# ===============================================================================
#                              STOP SERVICES
# ===============================================================================

if ($Stop) {
    Write-Host ""
    Write-Host "  Stopping services..." -ForegroundColor Yellow

    if ($Monitoring) {
        docker compose --env-file .env.production --profile monitoring down
    } else {
        docker compose --env-file .env.production down
    }

    Write-Host ""
    Write-Host "  [OK] Services stopped" -ForegroundColor Green
    exit 0
}

# ===============================================================================
#                              BUILD IMAGES
# ===============================================================================

if ($Build) {
    Write-Host ""
    Write-Host "  Building Docker images..." -ForegroundColor Yellow
    docker compose --env-file .env.production build

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [ERROR] Build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Build complete" -ForegroundColor Green
}

# ===============================================================================
#                              START SERVICES
# ===============================================================================

Write-Host ""
Write-Host "  Starting services..." -ForegroundColor Yellow

if ($Monitoring) {
    docker compose --env-file .env.production --profile monitoring up -d
} else {
    docker compose --env-file .env.production up -d
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] Failed to start services" -ForegroundColor Red
    exit 1
}

Write-Host "  [OK] Services started" -ForegroundColor Green

# Wait for database
Write-Host ""
Write-Host "  Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# ===============================================================================
#                              RUN MIGRATIONS
# ===============================================================================

if ($Migrate) {
    Write-Host ""
    Write-Host "  Running database migrations..." -ForegroundColor Yellow
    docker compose --env-file .env.production exec api alembic upgrade head

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Migrations complete" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Migrations may have failed" -ForegroundColor Yellow
    }
}

# ===============================================================================
#                              IMPORT COURSE CONFIGS
# ===============================================================================

if ($ImportConfigs) {
    Write-Host ""
    Write-Host "  Importing course configurations (ZSI + DevOps)..." -ForegroundColor Yellow
    docker compose --env-file .env.production exec api python -m scripts.import_course_configs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Course configs imported" -ForegroundColor Green
    } else {
        Write-Host "  [WARNING] Config import may have failed - check logs" -ForegroundColor Yellow
    }
}

# ===============================================================================
#                              HEALTH CHECK
# ===============================================================================

Write-Host ""
Write-Host "  Checking health..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
    $status = $health.status
    $color = $(if ($status -eq "healthy") { "Green" } else { "Yellow" })
    Write-Host "  [OK] Health: $status" -ForegroundColor $color
} catch {
    Write-Host "  [WARNING] Health check failed - service may still be starting" -ForegroundColor Yellow
}

# ===============================================================================
#                              SUCCESS MESSAGE
# ===============================================================================

$scheme = $(if ($domain -eq "localhost") { "http" } else { "https" })

Write-Host ""
Write-Host "  +==============================================================+" -ForegroundColor Green
Write-Host "  |  Deployment Complete!                                        |" -ForegroundColor Green
Write-Host "  +==============================================================+" -ForegroundColor Green
Write-Host "  |  Application:                                                |" -ForegroundColor Green
Write-Host "  |  Dashboard:     ${scheme}://${domain}/dashboard/             |" -ForegroundColor Cyan
Write-Host "  |  API Docs:      ${scheme}://${domain}/docs                   |" -ForegroundColor Cyan
Write-Host "  |  Health:        ${scheme}://${domain}/health                 |" -ForegroundColor Cyan

if ($Monitoring) {
    Write-Host "  +==============================================================+" -ForegroundColor Green
    Write-Host "  |  Monitoring (localhost only):                                |" -ForegroundColor Green
    Write-Host "  |  Grafana:       http://localhost:3000  (admin/admin)         |" -ForegroundColor Magenta
    Write-Host "  |  Prometheus:    http://localhost:9090                        |" -ForegroundColor Magenta
    Write-Host "  |  Jaeger:        http://localhost:16686                       |" -ForegroundColor Magenta
}

Write-Host "  +==============================================================+" -ForegroundColor Green
Write-Host ""
Write-Host "  Commands:" -ForegroundColor Cyan
Write-Host "    .\deploy-production.ps1 -Build          # Rebuild images" -ForegroundColor Gray
Write-Host "    .\deploy-production.ps1 -Migrate        # Run migrations" -ForegroundColor Gray
Write-Host "    .\deploy-production.ps1 -ImportConfigs  # Import course configs" -ForegroundColor Gray
Write-Host "    .\deploy-production.ps1 -Monitoring     # Start with monitoring" -ForegroundColor Gray
Write-Host "    .\deploy-production.ps1 -Stop           # Stop services" -ForegroundColor Gray
Write-Host "    .\deploy-production.ps1 -Logs           # Follow logs" -ForegroundColor Gray
Write-Host ""
Write-Host "    docker compose --env-file .env.production logs -f     # View logs" -ForegroundColor Gray
Write-Host "    docker compose --env-file .env.production ps          # Service status" -ForegroundColor Gray
Write-Host ""

# ===============================================================================
#                              FOLLOW LOGS
# ===============================================================================

if ($Logs) {
    Write-Host "  Following logs (Ctrl+C to stop)..." -ForegroundColor Yellow
    Write-Host ""
    docker compose --env-file .env.production logs -f
}
