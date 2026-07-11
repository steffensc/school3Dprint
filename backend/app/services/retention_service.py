"""Retention & cleanup worker (Section 9.9).

Runs daily (via APScheduler, see `app.workers.retention_worker`) or on
demand from the admin UI. For each terminal-state job whose relevant
timestamp is older than the configured retention window, it:

- deletes the uploaded STL and any sliced artifacts from disk,
- marks `UploadedFile.deleted_at`,
- moves the job to `DELETED`,
- writes an `AuditLog` entry per job plus a summary `RETENTION_RUN` entry.

Per Section 9.9's recommendation, DB metadata (the `PrintJob` row itself)
is kept rather than hard-deleted, so admins can still see history/counts
after cleanup; only the files and their disk space are reclaimed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import AuditAction
from app.models.enums import PrintJobStatus as Status
from app.models.print_job import PrintJob
from app.services.audit_service import log_action
from app.services.job_status import assert_transition_allowed
from app.services.system_settings_service import get_retention_settings

# Which terminal statuses are subject to retention, which timestamp
# column on `PrintJob` marks when that state was entered, and which
# system-setting key holds the configured number of days (Section 9.9's
# three explicit rules; CANCELLED/EXPIRED aren't covered by the doc).
_RETENTION_RULES: dict[Status, tuple[str, str]] = {
    Status.FINISHED: ("finished_at", "retention_days_finished"),
    Status.FAILED: ("failed_at", "retention_days_failed"),
    Status.REJECTED: ("rejected_at", "retention_days_rejected"),
}


@dataclass
class RetentionResult:
    deleted_job_ids: list[uuid.UUID] = field(default_factory=list)
    bytes_freed: int = 0

    @property
    def deleted_job_count(self) -> int:
        return len(self.deleted_job_ids)


def _delete_file_if_exists(path_str: str | None) -> int:
    if not path_str:
        return 0
    path = Path(path_str)
    if not path.exists() or not path.is_file():
        return 0
    size = path.stat().st_size
    path.unlink()
    return size


def find_retention_candidates(db: Session) -> list[PrintJob]:
    """Jobs that *would* be cleaned up if `run_retention` ran right now;
    used both by the worker itself and by the storage overview to show
    "N jobs pending cleanup" without mutating anything."""
    thresholds = get_retention_settings(db)
    now = datetime.now(UTC)
    candidates: list[PrintJob] = []

    for status, (timestamp_field, setting_key) in _RETENTION_RULES.items():
        cutoff = now - timedelta(days=thresholds[setting_key])
        timestamp_column = getattr(PrintJob, timestamp_field)
        jobs = (
            db.execute(
                select(PrintJob)
                .options(
                    joinedload(PrintJob.uploaded_file),
                    joinedload(PrintJob.sliced_artifacts),
                )
                .where(PrintJob.status == status)
                .where(timestamp_column.isnot(None))
                .where(timestamp_column < cutoff)
            )
            .unique()
            .scalars()
        )
        candidates.extend(jobs)

    return candidates


def run_retention(db: Session, *, actor_id: uuid.UUID | None) -> RetentionResult:
    now = datetime.now(UTC)
    result = RetentionResult()

    for job in find_retention_candidates(db):
        freed = 0
        if job.uploaded_file is not None and job.uploaded_file.deleted_at is None:
            freed += _delete_file_if_exists(job.uploaded_file.storage_path)
            job.uploaded_file.deleted_at = now

        for artifact in job.sliced_artifacts:
            freed += _delete_file_if_exists(artifact.file_path)

        previous_status = job.status
        assert_transition_allowed(previous_status, Status.DELETED)
        job.status = Status.DELETED
        result.bytes_freed += freed
        result.deleted_job_ids.append(job.id)

        log_action(
            db,
            actor_id=actor_id,
            action=AuditAction.RETENTION_DELETED,
            entity_type="print_job",
            entity_id=job.id,
            metadata={"previous_status": previous_status.value, "bytes_freed": freed},
        )

    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.RETENTION_RUN,
        entity_type="retention",
        entity_id=None,
        metadata={
            "deleted_count": result.deleted_job_count,
            "bytes_freed": result.bytes_freed,
        },
    )
    db.commit()
    return result
