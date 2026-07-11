"""Read and admin-approval helpers for `PrintJob` (Section 9.4)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import AuditAction
from app.models.enums import PrintJobStatus as Status
from app.models.print_job import PrintJob
from app.services.audit_service import log_action
from app.services.job_status import assert_transition_allowed


def get_job(db: Session, job_id: uuid.UUID) -> PrintJob | None:
    job = db.execute(
        select(PrintJob)
        .options(
            joinedload(PrintJob.uploaded_file),
            joinedload(PrintJob.owner),
            joinedload(PrintJob.printer),
        )
        .where(PrintJob.id == job_id)
    ).scalar_one_or_none()
    needs_sync = job is not None and job.status in (Status.PRINTING, Status.PAUSED)
    if needs_sync and job.printer is not None:
        from app.services.print_service import sync_job_with_driver

        job = sync_job_with_driver(db, job)
    return job


def list_jobs_for_owner(db: Session, owner_id: uuid.UUID) -> list[PrintJob]:
    return list(
        db.execute(
            select(PrintJob)
            .options(
                joinedload(PrintJob.uploaded_file),
                joinedload(PrintJob.owner),
                joinedload(PrintJob.printer),
            )
            .where(PrintJob.owner_id == owner_id)
            .order_by(PrintJob.created_at.desc())
        )
        .unique()
        .scalars()
    )


def list_all_jobs(db: Session) -> list[PrintJob]:
    return list(
        db.execute(
            select(PrintJob)
            .options(
                joinedload(PrintJob.uploaded_file),
                joinedload(PrintJob.owner),
                joinedload(PrintJob.printer),
            )
            .order_by(PrintJob.created_at.desc())
        )
        .unique()
        .scalars()
    )


def approve_job(
    db: Session, job: PrintJob, *, teacher_note: str | None, actor_id: uuid.UUID
) -> PrintJob:
    assert_transition_allowed(job.status, Status.APPROVED)
    job.status = Status.APPROVED
    job.approved_at = datetime.now(UTC)
    if teacher_note is not None:
        job.teacher_note = teacher_note
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.JOB_APPROVED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


def reject_job(
    db: Session, job: PrintJob, *, teacher_note: str | None, actor_id: uuid.UUID
) -> PrintJob:
    assert_transition_allowed(job.status, Status.REJECTED)
    job.status = Status.REJECTED
    job.rejected_at = datetime.now(UTC)
    if teacher_note is not None:
        job.teacher_note = teacher_note
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.JOB_REJECTED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


def unapprove_job(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    assert_transition_allowed(job.status, Status.SUBMITTED)
    job.status = Status.SUBMITTED
    job.approved_at = None
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.JOB_UNAPPROVED,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job
