#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------------------
# Database Restore Script
# --------------------------------------------------------------
# Usage:
#   ./scripts/restore.sh backups/gitpulse_20260101_020000.sql.gz
#
# WARNING: This will DROP and recreate the database.
# --------------------------------------------------------------

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh backups/gitpulse_*.sql.gz 2>/dev/null || echo "  (none found in ./backups/)"
    exit 1
fi

BACKUP_FILE="$1"
DB_USER="${POSTGRES_USER:-gitpulse}"
DB_NAME="${POSTGRES_DB:-gitpulse}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: File $BACKUP_FILE not found"
    exit 1
fi

# Verify gzip integrity
echo "Verifying backup integrity..."
if ! gzip -t "$BACKUP_FILE"; then
    echo "ERROR: Backup file is corrupt (gzip check failed)"
    exit 1
fi

# Verify checksum if available
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    echo "Verifying SHA256 checksum..."
    if sha256sum -c "$CHECKSUM_FILE" 2>/dev/null || shasum -a 256 -c "$CHECKSUM_FILE" 2>/dev/null; then
        echo "Checksum OK"
    else
        echo "WARNING: Checksum mismatch!"
        read -r -p "Continue anyway? [y/N] " REPLY
        if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Check postgres is running
if ! docker compose ps postgres --status running --format '{{.Name}}' 2>/dev/null | grep -q .; then
    echo "ERROR: postgres container is not running"
    exit 1
fi

# Safety confirmation
echo ""
echo "+======================================================+"
echo "|  WARNING: This will OVERWRITE the current database  |"
echo "+======================================================+"
echo ""
echo "  Database: $DB_NAME"
echo "  Backup:   $BACKUP_FILE"
echo "  Size:     $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""
read -r -p "Are you sure? Type 'yes' to continue: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Stop workers to prevent mid-restore processing
echo "Stopping worker and scheduler containers..."
docker compose stop worker scheduler 2>/dev/null || true

echo "Restoring from $BACKUP_FILE..."

# Drop and recreate the database
docker compose exec -T postgres psql -U "$DB_USER" -d postgres -c "
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
" 2>/dev/null || true

docker compose exec -T postgres psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker compose exec -T postgres psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore
gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres psql \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --quiet

# Run migrations to ensure schema is up to date
echo "Running Alembic migrations..."
docker compose run --rm migrate 2>/dev/null || \
    docker compose exec -T api python -m alembic upgrade head 2>/dev/null || true

# Restart workers
echo "Restarting worker and scheduler..."
docker compose start worker scheduler 2>/dev/null || true

echo ""
echo "Restore complete. Database $DB_NAME restored from $BACKUP_FILE."
