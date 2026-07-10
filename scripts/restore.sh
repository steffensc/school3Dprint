#!/usr/bin/env bash
# Restores a SchoolPrint backup produced by backup.sh.
#
# Usage: restore.sh <path-to-backup.tar.gz>
#
# WARNING: this overwrites the current database and uploaded files. Stop
# the backend container before running this.
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-backup.tar.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"
DATA_ROOT="${SCHOOLPRINT_DATA_ROOT:-/var/lib/schoolprint}"
WORK_DIR="$(mktemp -d)"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-schoolprint-postgres}"
POSTGRES_USER="${POSTGRES_USER:-schoolprint}"
POSTGRES_DB="${POSTGRES_DB:-schoolprint}"

trap 'rm -rf "$WORK_DIR"' EXIT

echo "==> Extracting $BACKUP_FILE"
tar -C "$WORK_DIR" -xzf "$BACKUP_FILE"
tar -C "$WORK_DIR" -xzf "$WORK_DIR/files.tar.gz"

read -r -p "This will overwrite the current database and files. Continue? [y/N] " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo "Aborted."
  exit 1
fi

echo "==> Restoring database into container '$POSTGRES_CONTAINER'"
podman exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  < "$WORK_DIR/database.sql"

echo "==> Restoring files into $DATA_ROOT"
for dir in uploads sliced previews; do
  rm -rf "$DATA_ROOT/$dir"
  cp -r "$WORK_DIR/$dir" "$DATA_ROOT/$dir"
done

echo "==> Restore complete."
