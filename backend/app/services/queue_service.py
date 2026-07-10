"""Print queue management (Section 9.5).

For the MVP there is a single global queue (printers/per-printer queues
land in Phase 6); `PrintJob.queue_position` already carries a printer_id
column for forward compatibility, but until real printers exist every
queued job shares one ordering.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import AuditAction
from app.models.enums import PrintJobStatus as Status
from app.models.print_job import PrintJob
from app.services.audit_service import log_action
from app.services.job_status import assert_transition_allowed


class QueueError(Exception):
    pass


def get_queue(db: Session) -> list[PrintJob]:
    return list(
        db.execute(
            select(PrintJob)
            .options(joinedload(PrintJob.uploaded_file), joinedload(PrintJob.owner))
            .where(PrintJob.queue_position.isnot(None))
            .order_by(PrintJob.queue_position.asc())
        )
        .unique()
        .scalars()
    )


def _next_position(db: Session) -> int:
    current_max = db.execute(select(func.max(PrintJob.queue_position))).scalar_one_or_none()
    return (current_max or 0) + 1


def enqueue_job(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    assert_transition_allowed(job.status, Status.QUEUED)
    if job.queue_position is not None:
        raise QueueError("Job is already in the queue.")

    job.status = Status.QUEUED
    job.queue_position = _next_position(db)
    job.queued_at = datetime.now(UTC)
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.JOB_ENQUEUED,
        entity_type="print_job",
        entity_id=job.id,
        metadata={"queue_position": job.queue_position},
    )
    db.commit()
    db.refresh(job)
    return job


def remove_from_queue(db: Session, job: PrintJob, *, actor_id: uuid.UUID) -> PrintJob:
    if job.queue_position is None:
        raise QueueError("Job is not in the queue.")

    assert_transition_allowed(job.status, Status.APPROVED)
    job.status = Status.APPROVED
    job.queue_position = None
    job.queued_at = None
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.JOB_REMOVED_FROM_QUEUE,
        entity_type="print_job",
        entity_id=job.id,
    )
    db.commit()
    _renumber_queue(db)
    db.refresh(job)
    return job


def _renumber_queue(db: Session) -> None:
    """Closes gaps left by removals so positions stay a dense 1..n sequence."""
    queued_jobs = get_queue(db)
    for index, job in enumerate(queued_jobs, start=1):
        job.queue_position = index
    db.commit()


def reorder_queue(
    db: Session, ordered_job_ids: list[uuid.UUID], *, actor_id: uuid.UUID
) -> list[PrintJob]:
    current = get_queue(db)
    current_ids = {job.id for job in current}
    requested_ids = set(ordered_job_ids)

    if current_ids != requested_ids:
        raise QueueError("Reorder request must include exactly the jobs currently in the queue.")

    jobs_by_id = {job.id: job for job in current}
    for index, job_id in enumerate(ordered_job_ids, start=1):
        jobs_by_id[job_id].queue_position = index

    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.QUEUE_REORDERED,
        entity_type="print_job_queue",
        entity_id=None,
        metadata={"order": [str(job_id) for job_id in ordered_job_ids]},
    )
    db.commit()
    return get_queue(db)


def move_job(db: Session, job: PrintJob, *, direction: int, actor_id: uuid.UUID) -> list[PrintJob]:
    """`direction` is +1 to move down (later) or -1 to move up (earlier)."""
    if job.queue_position is None:
        raise QueueError("Job is not in the queue.")

    queue = get_queue(db)
    index = next(i for i, j in enumerate(queue) if j.id == job.id)
    swap_index = index + direction
    if swap_index < 0 or swap_index >= len(queue):
        return queue

    queue[index], queue[swap_index] = queue[swap_index], queue[index]
    ordered_ids = [j.id for j in queue]
    return reorder_queue(db, ordered_ids, actor_id=actor_id)
