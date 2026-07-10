"""Orchestrates manual print start/pause/resume/cancel through a
`PrinterDriver`, and reconciles job status against real driver state
(Section 9.7 / 11 — printing is always started manually by a teacher,
never automatically)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.enums import AuditAction
from app.models.enums import PrintJobStatus as Status
from app.models.print_job import PrintJob
from app.models.printer import Printer
from app.printer_drivers.base import PrinterDriverError, PrinterStatus
from app.printer_drivers.factory import get_driver
from app.services.audit_service import log_action
from app.services.job_status import assert_transition_allowed
from app.services.queue_service import renumber_queue


class PrintServiceError(Exception):
    pass


def _select_artifact_path(job: PrintJob) -> Path:
    if job.sliced_artifacts:
        latest = max(job.sliced_artifacts, key=lambda a: a.created_at)
        return Path(latest.file_path)
    return Path(job.uploaded_file.storage_path)


def _remote_name(artifact_path: Path) -> str:
    """Derives the filename to use on the printer's own storage from the
    local artifact path, so real drivers (BambuLanDriver) see the same
    `.gcode.3mf` extension OrcaSlicer produced rather than an arbitrary
    one."""
    return artifact_path.name


def start_print(
    db: Session, job: PrintJob, printer: Printer, *, actor_id: uuid.UUID
) -> PrintJob:
    if not printer.is_active:
        raise PrintServiceError(f"Printer '{printer.name}' is not active.")

    assert_transition_allowed(job.status, Status.READY_TO_PRINT)
    job.status = Status.READY_TO_PRINT
    assert_transition_allowed(job.status, Status.PRINTING)

    artifact_path = _select_artifact_path(job)
    remote_name = _remote_name(artifact_path)
    driver = get_driver(printer)

    try:
        driver.upload_artifact(artifact_path, remote_name)
        driver.start_print(remote_name)
    except (PrinterDriverError, OSError, ValueError) as exc:
        raise PrintServiceError(f"Failed to start print: {exc}") from exc

    job.printer_id = printer.id
    job.status = Status.PRINTING
    job.started_at = datetime.now(UTC)
    had_queue_position = job.queue_position is not None
    job.queue_position = None

    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PRINT_STARTED,
        entity_type="print_job",
        entity_id=job.id,
        metadata={"printer_id": str(printer.id)},
    )
    db.commit()
    if had_queue_position:
        renumber_queue(db)
    db.refresh(job)
    return job


def pause_print(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    if job.status != Status.PRINTING or job.printer is None:
        raise PrintServiceError("Job is not currently printing.")
    driver = get_driver(job.printer)
    try:
        driver.pause()
    except (PrinterDriverError, ValueError) as exc:
        raise PrintServiceError(str(exc)) from exc
    job.status = Status.PAUSED
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PRINT_PAUSED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


def resume_print(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    if job.status != Status.PAUSED or job.printer is None:
        raise PrintServiceError("Job is not currently paused.")
    driver = get_driver(job.printer)
    try:
        driver.resume()
    except (PrinterDriverError, ValueError) as exc:
        raise PrintServiceError(str(exc)) from exc
    job.status = Status.PRINTING
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PRINT_RESUMED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


def cancel_print(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    if job.status not in (Status.PRINTING, Status.PAUSED) or job.printer is None:
        raise PrintServiceError("Job is not currently printing or paused.")
    driver = get_driver(job.printer)
    try:
        driver.cancel_print()
    except (PrinterDriverError, ValueError) as exc:
        raise PrintServiceError(str(exc)) from exc
    job.status = Status.CANCELLED
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PRINT_CANCELLED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


def sync_job_with_driver(db: Session, job: PrintJob) -> PrintJob:
    """Pulls current status/progress from the printer and reconciles the
    job's state. Called lazily on read, since the MVP has no background
    poller yet."""
    if job.status not in (Status.PRINTING, Status.PAUSED) or job.printer is None:
        return job

    driver = get_driver(job.printer)
    driver_status = driver.get_status()

    if driver_status == PrinterStatus.FINISHED:
        job.status = Status.FINISHED
        job.finished_at = datetime.now(UTC)
        log_action(
            db,
            actor_id=job.owner_id,
            action=AuditAction.PRINT_FINISHED,
            entity_type="print_job",
            entity_id=job.id,
        )
        db.commit()
        db.refresh(job)
    elif driver_status == PrinterStatus.ERROR:
        job.status = Status.FAILED
        job.failed_at = datetime.now(UTC)
        log_action(
            db,
            actor_id=job.owner_id,
            action=AuditAction.PRINT_FAILED,
            entity_type="print_job",
            entity_id=job.id,
        )
        db.commit()
        db.refresh(job)

    return job


def get_live_progress(job: PrintJob) -> dict[str, float | str | None]:
    if job.printer is None:
        return {"status": job.status.value, "progress": 0.0}
    driver = get_driver(job.printer)
    temps = driver.get_temperatures()
    return {
        "status": driver.get_status().value,
        "progress": driver.get_progress(),
        "nozzle_actual": temps.nozzle_actual,
        "nozzle_target": temps.nozzle_target,
        "bed_actual": temps.bed_actual,
        "bed_target": temps.bed_target,
    }
