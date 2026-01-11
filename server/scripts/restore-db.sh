#!/bin/bash
# Database restore script for Roam PostgreSQL database
# Usage: ./restore-db.sh <backup_file>

set -e

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Error: No backup file specified"
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./server/scripts/backup/roam_backup_20260111_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' not found"
    exit 1
fi

# Configuration
DB_HOST="${DATABASE_HOST:-localhost}"
DB_PORT="${DATABASE_PORT:-5432}"
DB_NAME="${DATABASE_NAME:-roam}"
DB_USER="${DATABASE_USERNAME:-roam}"
DB_PASSWORD="${DATABASE_PASSWORD:-}"

# Require an explicit database password to avoid using insecure defaults
if [ -z "${DB_PASSWORD}" ]; then
  echo "Error: DATABASE_PASSWORD environment variable is not set." >&2
  echo "Refusing to run restore with a default or empty database password." >&2
  echo "Please set DATABASE_PASSWORD to the database user's password and rerun this script." >&2
  exit 1
fi

echo "WARNING: This will drop and recreate the database!"
echo "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "Backup file: ${BACKUP_FILE}"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Starting database restore..."

# Drop and recreate database
echo "Dropping existing database..."
PGPASSWORD="${DB_PASSWORD}" psql \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d postgres \
  -c "DROP DATABASE IF EXISTS ${DB_NAME};"

echo "Creating fresh database..."
PGPASSWORD="${DB_PASSWORD}" psql \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d postgres \
  -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# Restore from backup
echo "Restoring from backup..."
if [[ "${BACKUP_FILE}" == *.gz ]]; then
    # Decompress and restore
    gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${DB_PASSWORD}" psql \
      -h "${DB_HOST}" \
      -p "${DB_PORT}" \
      -U "${DB_USER}" \
      -d "${DB_NAME}"
else
    # Restore directly
    PGPASSWORD="${DB_PASSWORD}" psql \
      -h "${DB_HOST}" \
      -p "${DB_PORT}" \
      -U "${DB_USER}" \
      -d "${DB_NAME}" \
      -f "${BACKUP_FILE}"
fi

echo "Database restored successfully!"
echo "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
