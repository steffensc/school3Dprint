#!/usr/bin/env bash
# Creates a timestamped backup of the SchoolPrint database and uploaded
# files under $DATA_ROOT/backups. Metadata is dumped via `pg_dump`; files
# are archived directly from the filesystem (never stored as DB blobs, so
# this stays a simple tar).
set -euo pipefail

DATA_ROOT="${SCHOOLPRINT_DATA_ROOT:-/var/lib/schoolprint}"
BACKUP_DIR="$DATA_ROOT/backups"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_NAME="schoolprint-backup-$TIMESTAMP"
WORK_DIR="$(mktemp -d)"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-schoolprint-postgres}"
POSTGRES_USER="${POSTGRES_USER:-schoolprint}"
POSTGRES_DB="${POSTGRES_DB:-schoolprint}"

trap 'rm -rf "$WORK_DIR"' EXIT

mkdir -p "$BACKUP_DIR"

echo "==> Dumping database from container '$POSTGRES_CONTAINER'"
podman exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > "$WORK_DIR/database.sql"

echo "==> Archiving uploads/sliced/previews"
tar -C "$DATA_ROOT" -czf "$WORK_DIR/files.tar.gz" uploads sliced previews

echo "==> Writing combined archive"
tar -C "$WORK_DIR" -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" database.sql files.tar.gz

echo "==> Backup written to $BACKUP_DIR/$BACKUP_NAME.tar.gz"
