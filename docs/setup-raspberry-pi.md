# Setup guide: SchoolPrint on a Raspberry Pi

This walks through installing SchoolPrint on a Raspberry Pi (or any other
Podman-capable Linux host) from scratch.

## Hardware & OS

- Raspberry Pi 5 (recommended) or Raspberry Pi 4, 64-bit
- Raspberry Pi OS (64-bit) or another recent Debian/Ubuntu-based distro
- A wired network connection to the same LAN as the printer is strongly
  recommended (or run the Pi as its own WLAN access point, see the
  design doc, Section 5)
- At least 4 GB RAM and a decently fast SD card / SSD (an SSD via USB3 is
  recommended for the database and print job files)

## 1. Install Podman and podman-compose

```bash
sudo apt update
sudo apt install -y podman
python3 -m pip install --user podman-compose
```

Verify:

```bash
podman --version
podman-compose --version
```

If you're on rootless Podman (the default and recommended setup), make
sure the Podman socket is available for the `updater` service (see
[below](#updater-service)):

```bash
systemctl --user enable --now podman.socket
```

## 2. Get the code onto the Pi

```bash
git clone https://github.com/<your-fork>/school3Dprint.git
cd school3Dprint
```

## 3. Run the install script

```bash
./scripts/install.sh
```

This:

- Creates `/var/lib/schoolprint/{uploads,sliced,previews,postgres,backups}`
  and makes your user the owner
- Copies `deploy/`, `backend/`, `frontend/`, and `scripts/` to
  `/opt/schoolprint`
- Creates `/opt/schoolprint/deploy/.env` from `.env.example` (if it
  doesn't already exist)
- Installs (but does not enable/start) the `schoolprint.service` systemd
  unit, if `systemctl` is available

Override the install locations with `SCHOOLPRINT_INSTALL_DIR` /
`SCHOOLPRINT_DATA_ROOT` environment variables if needed.

## 4. Configure secrets

Edit `/opt/schoolprint/deploy/.env` and set, at minimum:

```text
POSTGRES_PASSWORD=<a strong random password>
SCHOOLPRINT_SECRET_KEY=<a long random string>
```

`SCHOOLPRINT_SECRET_KEY` signs session JWTs and encrypts printer access
codes (see [docs/security.md](security.md)) — treat it like any other
production secret and don't commit it.

If you plan to use the admin Updates page, also set:

```text
SCHOOLPRINT_UPDATE_REPO=<your-org>/<your-repo>
```

## 5. Start the stack

```bash
cd /opt/schoolprint/deploy
podman-compose -f compose.yaml --env-file .env up -d
```

This builds and starts `postgres`, `backend`, `frontend`, and `updater`.
The first backend startup runs Alembic migrations automatically and
bootstraps an initial `admin` account, printing its generated password to
the container logs:

```bash
podman logs schoolprint-backend | grep -i "Bootstrapped initial admin"
```

Log in at `http://<pi-ip>/` and change that password immediately
(Settings → your account, or `/api/auth/change-password`).

## 6. Enable auto-start on boot

```bash
sudo systemctl enable --now schoolprint
```

This starts the whole Compose stack via `schoolprint.service`
(`deploy/systemd/schoolprint.service`) on every boot and cleanly stops it
on shutdown.

## Updater-Service

The admin **Updates** page (`/admin/updates`) checks GitHub Releases and
can trigger an install. For security, the `backend` container never gets
Podman/host access itself (Section 20 of the design doc). Instead:

- A small, purpose-built `updater` container
  (`deploy/updater/`, built from `deploy/updater/Dockerfile`) is the
  *only* component with a Podman socket mount.
- It exposes one internal-only HTTP endpoint (`POST /run`) that runs
  `scripts/updater-trigger.sh` (`podman-compose pull` + `up -d`).
- The backend just makes a local HTTP call to `http://updater:8090/run`.

See `deploy/podman/README.md` for the rootless-Podman socket path and
further detail. You can also run an update manually from the host at any
time without going through the UI:

```bash
cd /opt/schoolprint
SCHOOLPRINT_COMPOSE_FILE=/opt/schoolprint/deploy/compose.yaml ./scripts/updater-trigger.sh
```

## Backups

```bash
./scripts/backup.sh
```

Writes a timestamped `.tar.gz` (database dump + uploads/sliced/previews)
to `$SCHOOLPRINT_DATA_ROOT/backups`. Consider adding this to `cron` and
copying backups off the Pi (e.g. to a USB drive or network share).

Restore with:

```bash
./scripts/restore.sh /var/lib/schoolprint/backups/schoolprint-backup-<timestamp>.tar.gz
```

## Printer setup

See [docs/bambu-a1-mini.md](bambu-a1-mini.md) for connecting a Bambu Lab
A1 Mini.

## Troubleshooting

- `podman logs schoolprint-backend` / `schoolprint-frontend` /
  `schoolprint-updater` for service logs.
- `podman-compose -f compose.yaml --env-file .env ps` to check container
  health.
- If the frontend can't reach the backend, confirm both containers are on
  the `schoolprint-net` network and that `backend` is healthy
  (`curl http://localhost:8000/api/health` from the Pi itself).
