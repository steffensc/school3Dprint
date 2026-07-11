# Security model

This describes how SchoolPrint implements the minimum security
requirements from the design doc (Section 15, "Sicherheit") and where the
corresponding code lives, so reviewers/admins can verify each claim.

## Threat model

SchoolPrint is meant to run on a school's own LAN (typically a Raspberry
Pi, optionally acting as its own WLAN access point), used by students and
teachers who are physically at the school. It is **not** designed to be
exposed directly to the public internet. The realistic threats are:

- A student trying to access another student's files or another user's
  account
- A student trying to escalate to admin/teacher actions (approving their
  own job, controlling the printer, changing settings)
- A malicious or malformed uploaded `.stl` file trying to escape the
  slicer sandbox or exhaust disk/CPU
- Session hijacking / CSRF from another site open in the same browser
- A compromised backend process being used as a stepping stone to gain
  control of the host (e.g. via the update mechanism)

## Authentication & sessions

- Passwords are hashed with **Argon2** (`passlib[argon2]`), see
  `backend/app/core/security.py`.
- Sessions are a JWT stored in an **HttpOnly, SameSite=Lax** cookie
  (`schoolprint_session`); the frontend never reads or stores it, so it
  can't be exfiltrated via XSS/localStorage (`app/api/routes/auth.py`).
- `SCHOOLPRINT_COOKIE_SECURE=true` in production ensures the cookie is
  only ever sent over HTTPS (see `deploy/.env.example`); set up TLS
  termination (e.g. a reverse proxy) if the school network requires it.
- Login is rate-limited per client (`app/core/rate_limit.py`) to slow
  down credential-guessing.
- The very first admin account is bootstrapped automatically on first
  startup with a random password printed once to the backend logs
  (`app/services/user_service.py::bootstrap_initial_admin`) — there is no
  hardcoded default admin password.

## CSRF protection

Cookie-based auth needs explicit CSRF protection (Section 15). SchoolPrint
uses a **double-submit cookie**:

- On login, the backend sets a second, readable cookie
  (`schoolprint_csrf`) alongside the HttpOnly session cookie.
- The frontend's Axios client (`frontend/src/lib/api.ts`) reads that
  cookie and echoes it back as an `X-CSRF-Token` header on every
  state-changing request (anything other than GET/HEAD/OPTIONS).
- `CSRFMiddleware` (`app/core/csrf.py`) rejects state-changing requests
  that carry a session cookie but a missing/mismatched CSRF header with
  `403`.
- A cross-site attacker page can trigger a cross-origin request that
  *includes* the session cookie (blocked by `SameSite=Lax` for
  fetch/XHR anyway) but **cannot read** the CSRF cookie's value to put it
  in the header, so the double-submit check fails even if `SameSite`
  were bypassed by an older browser.
- Requests with no session cookie at all (not logged in) are left alone —
  there is no session to protect, and this keeps role-check unit tests
  that bypass cookie auth via dependency injection simple.

## Role-based access control

- Two roles: `ADMIN` (teacher) and `USER` (student) — `app/models/enums.py`.
- Every admin-only route depends on `require_admin`
  (`app/api/deps.py`), returning `403` for non-admins.
- User-facing routes (`/api/user/*`) always scope queries to
  `owner_id == current_user.id`; a user can never fetch another user's
  upload or job by guessing an ID.

## Uploads & the slicer sandbox

- Only `.stl` files are accepted; extension **and** file content are
  checked (`app/services/stl_validation.py` verifies the ASCII/binary STL
  structure, not just the extension).
- Upload size is capped (`max_upload_size_mb`, default 50 MB).
- Uploaded files are stored under a random UUID filename
  (`app/services/upload_service.py`) — the original filename is kept only
  as metadata in the DB, never used to build a filesystem path, so a
  crafted filename (`../../etc/passwd`, `; rm -rf /`, …) can't cause path
  traversal or command injection.
- The slicer (`app/slicer/runner.py`) is invoked via `subprocess.run` with
  an explicit argument list — **never** `shell=True` — a fixed timeout,
  and fixed, non-user-editable profile files; no part of the command line
  is derived from user-controlled strings other than the sandboxed input
  file path itself.
- Sliced artifacts, like uploads, live outside PostgreSQL (Section 8/20
  Decision 4) purely on the local filesystem, which keeps backups simple
  and avoids DB bloat, while still staying fully local.

## Printer credentials

- A Bambu Lab printer's LAN "Access Code" is encrypted at rest
  (`app/core/crypto.py`, Fernet symmetric encryption keyed from
  `SCHOOLPRINT_SECRET_KEY`) in the `printers.access_code_encrypted`
  column, and is **never** returned to the frontend — the API only ever
  exposes a `has_access_code: bool` flag
  (`app/schemas/printer.py::PrinterOut`). It can be overwritten but not
  read back.

## Audit log

- Every admin/system action (user management, job approval/rejection,
  queue changes, printer changes, print start/pause/cancel, retention
  runs, update checks/installs, settings changes) is recorded as an
  immutable `AuditLog` row (`app/models/audit_log.py`,
  `app/services/audit_service.py`), including the actor, entity, and a
  JSON metadata blob, for after-the-fact review.

## Update mechanism privilege separation

- The backend container **never** gets a Podman socket or host root
  access. It only makes a local HTTP call
  (`app/services/updater_runner.py`) to a separate, minimal `updater`
  container (`deploy/updater/`) that is the *only* component allowed to
  touch Podman and restart the stack. See
  [docs/setup-raspberry-pi.md](setup-raspberry-pi.md#updater-service) and
  `deploy/podman/README.md` for the full rationale (Section 9.10 / 20).

## Retention & data minimisation

- Files (not metadata) for `FINISHED`/`REJECTED`/`FAILED` jobs are deleted
  automatically after a configurable number of days
  (`app/services/retention_service.py`), reducing how long student work
  and personal data stay on disk. Admins can also trigger cleanup
  manually and see a storage overview before doing so
  (`/admin/settings`).

## Reporting issues

See [SECURITY.md](../SECURITY.md) at the repository root.
