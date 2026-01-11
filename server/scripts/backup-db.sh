#!/bin/bash
# Database backup script for Roam PostgreSQL database
# Usage: ./backup-db.sh [output_file]

set -e

# Configuration
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-roam}"
DB_USER="${DATABASE_USERNAME:-roam}"
DB_PASSWORD="${DATABASE_PASSWORD:-roam}"

# Default backup file name with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./server/scripts/backup"
BACKUP_FILE="${1:-${BACKUP_DIR}/roam_backup_${TIMESTAMP}.sql}"

# Create backup directory if it doesn't exist
mkdir -p "$(dirname "$BACKUP_FILE")"

echo "Starting database backup..."
echo "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "Output file: ${BACKUP_FILE}"

# Perform backup using pg_dump
PGPASSWORD="${DB_PASSWORD}" pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  -F p \
  -f "${BACKUP_FILE}"

# Compress the backup
gzip -f "${BACKUP_FILE}"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "Backup completed successfully!"
echo "Backup file: ${BACKUP_FILE}"
echo "Size: $(du -h "${BACKUP_FILE}" | cut -f1)"

# Optional: Keep only the last 10 backups
cd "$(dirname "$BACKUP_FILE")"
ls -t roam_backup_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm
echo "Old backups cleaned up (keeping last 10)"
