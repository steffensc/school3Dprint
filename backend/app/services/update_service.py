"""GitHub Releases update check + install orchestration (Section 9.10).

MVP scope: `install_update` triggers a synchronous updater run (mirrors
the slicer service's synchronous subprocess pattern) and records an
`UpdateRun` row so the admin Updates page can show status/log history.
On real hardware the updater script pulls new images and restarts the
Podman Compose stack, which will terminate this backend process mid
request; the frontend treats "no response" after clicking install as
expected and falls back to polling `/api/admin/updates/status` once the
backend comes back up.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import AuditAction, UpdateRunStatus
from app.models.update_run import UpdateRun
from app.services import updater_runner, version_service
from app.services.audit_service import log_action
from app.services.updater_runner import UpdaterServiceUnavailableError


@dataclass
class UpdateCheck:
    current_version: str
    latest_version: str | None
    update_available: bool
    release_url: str | None
    release_notes: str | None
    published_at: datetime | None
    checked_at: datetime
    error: str | None = None


def _parse_version(tag: str) -> tuple[int, int, int]:
    """Best-effort semver-ish comparison, tolerant of a leading 'v'."""
    cleaned = tag.strip().lstrip("vV")
    segments = cleaned.split(".")[:3]
    parts: list[int] = []
    for segment in segments:
        digits = "".join(ch for ch in segment if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2])


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def check_for_update(db: Session, *, actor_id: uuid.UUID | None = None) -> UpdateCheck:
    settings = get_settings()
    current_version = version_service.get_backend_version()
    checked_at = datetime.now(UTC)
    url = f"{settings.github_api_base_url}/repos/{settings.update_repo}/releases/latest"

    try:
        response = httpx.get(url, headers={"Accept": "application/vnd.github+json"}, timeout=10.0)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        result = UpdateCheck(
            current_version=current_version,
            latest_version=None,
            update_available=False,
            release_url=None,
            release_notes=None,
            published_at=None,
            checked_at=checked_at,
            error=f"Could not reach GitHub Releases: {exc}",
        )
        log_action(
            db,
            actor_id=actor_id,
            action=AuditAction.UPDATE_CHECKED,
            entity_type="update",
            metadata={"error": result.error},
            commit=True,
        )
        return result

    latest_version = str(payload.get("tag_name") or "").strip() or None
    published_at = _parse_github_timestamp(payload.get("published_at"))

    result = UpdateCheck(
        current_version=current_version,
        latest_version=latest_version,
        update_available=bool(latest_version)
        and _is_newer(latest_version, current_version),
        release_url=payload.get("html_url"),
        release_notes=payload.get("body"),
        published_at=published_at,
        checked_at=checked_at,
    )
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.UPDATE_CHECKED,
        entity_type="update",
        metadata={
            "current_version": current_version,
            "latest_version": result.latest_version,
            "update_available": result.update_available,
        },
        commit=True,
    )
    return result


def _parse_github_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_latest_update_run(db: Session) -> UpdateRun | None:
    return db.execute(
        select(UpdateRun).order_by(UpdateRun.created_at.desc()).limit(1)
    ).scalar_one_or_none()


def install_update(db: Session, *, actor_id: uuid.UUID | None) -> UpdateRun:
    current_version = version_service.get_backend_version()
    run = UpdateRun(
        status=UpdateRunStatus.RUNNING,
        from_version=current_version,
        to_version=None,
        triggered_by_id=actor_id,
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()

    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.UPDATE_STARTED,
        entity_type="update_run",
        entity_id=run.id,
        commit=True,
    )

    try:
        result = updater_runner.run_updater()
    except UpdaterServiceUnavailableError as exc:
        run.status = UpdateRunStatus.FAILED
        run.log = str(exc)
        run.finished_at = datetime.now(UTC)
        db.add(run)
        log_action(
            db,
            actor_id=actor_id,
            action=AuditAction.UPDATE_FAILED,
            entity_type="update_run",
            entity_id=run.id,
            metadata={"error": str(exc)},
            commit=True,
        )
        return run

    combined_log = result.stdout
    if result.stderr:
        combined_log = f"{combined_log}\n--- stderr ---\n{result.stderr}"
    run.log = combined_log.strip()
    run.finished_at = datetime.now(UTC)

    if result.returncode == 0:
        run.status = UpdateRunStatus.SUCCEEDED
        action = AuditAction.UPDATE_SUCCEEDED
    else:
        run.status = UpdateRunStatus.FAILED
        action = AuditAction.UPDATE_FAILED

    db.add(run)
    log_action(
        db,
        actor_id=actor_id,
        action=action,
        entity_type="update_run",
        entity_id=run.id,
        metadata={"returncode": result.returncode},
        commit=True,
    )
    return run
