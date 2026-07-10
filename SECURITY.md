# Security Policy

SchoolPrint is designed to run entirely on a school's own local network
(typically a Raspberry Pi), with no cloud dependency. It is used by minors
(students) and staff, so we take its security model seriously even though
it is not internet-facing by design. See [docs/security.md](docs/security.md)
for a detailed description of the threat model and the mitigations
implemented in this repository.

## Supported versions

SchoolPrint is pre-1.0 (MVP). Only the latest commit on the default branch
and the latest tagged release receive security fixes.

## Reporting a vulnerability

If you find a security issue, please **do not open a public GitHub issue**.
Instead, report it privately using GitHub's
["Report a vulnerability"](../../security/advisories/new) flow on this
repository (Security tab → "Report a vulnerability"), or contact the
maintainer directly.

Please include:

- A description of the issue and its potential impact
- Steps to reproduce (a minimal example is very helpful)
- The version/commit you tested against

We aim to acknowledge new reports within a few days and to ship a fix or
mitigation as soon as reasonably possible given this is a small,
volunteer-maintained school project.

## Scope

In scope:

- The `backend/` FastAPI application and its API
- The `frontend/` React application
- The deployment configuration under `deploy/` (Podman Compose, the
  Updater-Service, systemd unit)
- The `scripts/` helpers (install/backup/restore/updater-trigger)

Out of scope:

- The underlying OS, Podman/Docker, or PostgreSQL themselves (please report
  those upstream)
- Physical security of the Raspberry Pi / printer at the school
- Third-party printer firmware (e.g. the Bambu Lab A1 Mini's own firmware)
