# Podman-specific configuration

This directory is reserved for Podman-specific assets that don't fit into
the generic `compose.yaml` (for example rootless Podman Quadlet unit files,
or `containers.conf` overrides for the Raspberry Pi host).

## Updater-Service privilege separation

Section 9.10 / 20 of the design doc call out that the backend container
must not get unrestricted root/Podman access to the host. This repo
implements that as a dedicated `updater` service (see
`deploy/updater/`):

* `updater` is the **only** container with access to the Podman socket
  (`/run/podman/podman.sock`) and to `deploy/compose.yaml`.
* It exposes a single, unauthenticated-but-internal-only HTTP endpoint
  (`POST /run`) on the Compose-internal network — there is no published
  port, so it is unreachable from outside the host.
* The `backend` container only ever makes an HTTP call to
  `http://updater:8090/run` (see `app/services/updater_runner.py`); it
  never gets a socket mount or elevated privileges itself.
* `updater` runs `scripts/updater-trigger.sh`, which does
  `podman-compose pull` + `podman-compose up -d` for the whole stack.

On a rootless Podman host, make sure the user running Podman has a
`podman.sock` available at the path referenced in `compose.yaml` (start
it with `systemctl --user enable --now podman.socket`), and adjust the
volume path in `deploy/compose.yaml` accordingly if your distro places it
elsewhere (e.g. `$XDG_RUNTIME_DIR/podman/podman.sock`).
