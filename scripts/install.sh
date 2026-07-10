#!/usr/bin/env bash
# Installs SchoolPrint on a Raspberry Pi (or any Podman-capable Linux host).
#
# This script is intentionally conservative: it prepares directories and
# config, but does not silently overwrite an existing .env or start
# unattended long-running background jobs.
set -euo pipefail

INSTALL_DIR="${SCHOOLPRINT_INSTALL_DIR:-/opt/schoolprint}"
DATA_ROOT="${SCHOOLPRINT_DATA_ROOT:-/var/lib/schoolprint}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Installing SchoolPrint"
echo "    repo:        $REPO_DIR"
echo "    install dir: $INSTALL_DIR"
echo "    data root:   $DATA_ROOT"

command -v podman >/dev/null 2>&1 || {
  echo "ERROR: podman is not installed. See https://podman.io/docs/installation" >&2
  exit 1
}
command -v podman-compose >/dev/null 2>&1 || {
  echo "ERROR: podman-compose is not installed (pip install podman-compose)." >&2
  exit 1
}

sudo mkdir -p "$DATA_ROOT"/{uploads,sliced,previews,postgres,backups}
sudo chown -R "$(id -u):$(id -g)" "$DATA_ROOT"

sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$REPO_DIR/deploy" "$INSTALL_DIR/deploy"
sudo chown -R "$(id -u):$(id -g)" "$INSTALL_DIR"

if [ ! -f "$INSTALL_DIR/deploy/.env" ]; then
  cp "$INSTALL_DIR/deploy/.env.example" "$INSTALL_DIR/deploy/.env"
  echo "==> Created $INSTALL_DIR/deploy/.env from example."
  echo "    Edit it now and set POSTGRES_PASSWORD and SCHOOLPRINT_SECRET_KEY"
  echo "    before starting the stack."
else
  echo "==> $INSTALL_DIR/deploy/.env already exists, leaving it untouched."
fi

if command -v systemctl >/dev/null 2>&1; then
  sudo cp "$INSTALL_DIR/deploy/systemd/schoolprint.service" /etc/systemd/system/schoolprint.service
  sudo systemctl daemon-reload
  echo "==> Installed systemd unit 'schoolprint.service' (not started/enabled yet)."
  echo "    Run: sudo systemctl enable --now schoolprint"
fi

echo "==> Done. Next steps:"
echo "    1. Review $INSTALL_DIR/deploy/.env"
echo "    2. cd $INSTALL_DIR/deploy && podman-compose -f compose.yaml --env-file .env up -d"
