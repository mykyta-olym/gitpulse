#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------------------
# Database Backup Script
# --------------------------------------------------------------
# Usage:
#   ./scripts/backup.sh                  # default: ./backups/
#   ./scripts/backup.sh /mnt/backups     # custom directory
#
# Cron (daily at 02:00):
#   0 2 * * * cd /opt/gitpulse && ./scripts/backup.sh >> /var/log/gitpulse-backup.log 2>&1
# --------------------------------------------------------------

BACKUP_DIR="${1:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_USER="${POSTGRES_USER:-gitpulse}"
DB_NAME="${POSTGRES_DB:-gitpulse}"
FILENAME="gitpulse_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

echo "[$(date -Iseconds)] Starting backup..."

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Check postgres container is running
if ! docker compose ps postgres --status running --format '{{.Name}}' 2>/dev/null | grep -q .; then
    echo "ERROR: postgres container is not running"
    exit 1
fi

# Dump with custom format for parallel restore, gzipped
docker compose exec -T postgres pg_dump \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    --format=plain \
    --verbose \
    2>/dev/null \
    | gzip > "${BACKUP_DIR}/${FILENAME}"

# Verify the backup is not empty
FILESIZE=$(stat -f%z "${BACKUP_DIR}/${FILENAME}" 2>/dev/null || stat -c%s "${BACKUP_DIR}/${FILENAME}" 2>/dev/null || echo 0)
if [ "$FILESIZE" -lt 100 ]; then
    echo "ERROR: Backup file is suspiciously small (${FILESIZE} bytes)"
    rm -f "${BACKUP_DIR}/${FILENAME}"
    exit 1
fi

# Verify gzip integrity
if ! gzip -t "${BACKUP_DIR}/${FILENAME}" 2>/dev/null; then
    echo "ERROR: Backup file failed gzip integrity check"
    rm -f "${BACKUP_DIR}/${FILENAME}"
    exit 1
fi

echo "[$(date -Iseconds)] Backup saved: ${BACKUP_DIR}/${FILENAME} ($(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1))"

# Compute SHA256 checksum
sha256sum "${BACKUP_DIR}/${FILENAME}" > "${BACKUP_DIR}/${FILENAME}.sha256" 2>/dev/null || \
    shasum -a 256 "${BACKUP_DIR}/${FILENAME}" > "${BACKUP_DIR}/${FILENAME}.sha256" 2>/dev/null || true

# Prune backups older than retention period
PRUNED=$(find "$BACKUP_DIR" -name "gitpulse_*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete 2>/dev/null | wc -l)
if [ "$PRUNED" -gt 0 ]; then
    echo "[$(date -Iseconds)] Pruned $PRUNED backup(s) older than ${RETENTION_DAYS} days"
fi

# List recent backups
echo "[$(date -Iseconds)] Recent backups:"
ls -lh "$BACKUP_DIR"/gitpulse_*.sql.gz 2>/dev/null | tail -5

echo "[$(date -Iseconds)] Backup complete."
