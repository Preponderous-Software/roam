#!/bin/bash
# Database backup script for Roam PostgreSQL database
# Usage: ./backup-db.sh [output_file]

set -e

# Configuration
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-roam}"
DB_USER="${DATABASE_USERNAME:-roam}"
DB_PASSWORD="${DATABASE_PASSWORD:-}"

# Require an explicit, non-trivial database password to avoid using insecure defaults
WEAK_PASSWORDS=("password" "admin" "123456" "12345678" "qwerty" "letmein" "${DB_USER}" "${DB_NAME}")

is_weak_password=0
for weak in "${WEAK_PASSWORDS[@]}"; do
  if [ -n "${weak}" ] && [ "${DB_PASSWORD}" = "${weak}" ]; then
    is_weak_password=1
    break
  fi
done

password_length=${#DB_PASSWORD}
if [ -z "${DB_PASSWORD}" ] || [ "${password_length}" -lt 8 ] || [ "${is_weak_password}" -eq 1 ]; then
  echo "Error: DATABASE_PASSWORD environment variable is not set to a sufficiently strong value." >&2
  echo "Refusing to run backup with an empty, too-short, or commonly used database password." >&2
  echo "Please set DATABASE_PASSWORD to a stronger password (at least 8 characters, not a common or trivial value) and rerun this script." >&2
  exit 1
fi

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
