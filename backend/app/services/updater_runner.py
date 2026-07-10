"""Client for the separate, minimally-privileged Updater-Service
(Section 9.10 / Section 20 Architekturentscheidungen).

The backend deliberately never runs `podman pull` / `podman compose up
-d` itself and never gets a podman socket or host root access. It makes
one local HTTP call to the `updater` container (see deploy/updater/),
which is the only component with Podman access, and relays its result.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class UpdaterResult:
    returncode: int
    stdout: str
    stderr: str = ""


class UpdaterServiceUnavailableError(Exception):
    """The updater service could not be reached or timed out."""


def run_updater(*, timeout_seconds: int | None = None) -> UpdaterResult:
    settings = get_settings()
    timeout = timeout_seconds or settings.updater_timeout_seconds
    url = f"{settings.updater_service_url.rstrip('/')}/run"

    try:
        response = httpx.post(url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise UpdaterServiceUnavailableError(
            f"Could not reach the updater service at {url}: {exc}"
        ) from exc

    return UpdaterResult(
        returncode=int(payload.get("returncode", 1)),
        stdout=str(payload.get("log", "")),
    )
