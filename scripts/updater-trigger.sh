#!/usr/bin/env bash
# Pulls the latest SchoolPrint container images and restarts the Podman
# Compose stack (Section 9.10 of the design doc).
#
# This script only ever runs inside the dedicated `updater` container
# (see deploy/compose.yaml / deploy/updater/), which is the *only*
# component with Podman access. The main backend container never gets a
# podman socket or host root access -- it just makes a local HTTP call
# to the updater container (see app/services/updater_runner.py), which
# in turn runs this script. It can also be run manually from the host
# for troubleshooting: `./scripts/updater-trigger.sh`.
set -euo pipefail

COMPOSE_FILE="${SCHOOLPRINT_COMPOSE_FILE:-/deploy/compose.yaml}"
COMPOSE_BIN="${SCHOOLPRINT_COMPOSE_BIN:-podman-compose}"

echo "[updater] pulling latest images for ${COMPOSE_FILE}"
"${COMPOSE_BIN}" -f "${COMPOSE_FILE}" pull

echo "[updater] restarting stack"
"${COMPOSE_BIN}" -f "${COMPOSE_FILE}" up -d

echo "[updater] done"
