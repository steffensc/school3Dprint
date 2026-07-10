from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.print_job import JobActionRequest, PrintJobOut
from app.services import job_service, queue_service
from app.services.job_status import InvalidStatusTransitionError
from app.services.queue_service import QueueError

router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])


def _get_job_or_404(db: Session, job_id: uuid.UUID):
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.get("", response_model=list[PrintJobOut])
def list_jobs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return job_service.list_all_jobs(db)


@router.get("/{job_id}", response_model=PrintJobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return _get_job_or_404(db, job_id)


@router.post("/{job_id}/approve", response_model=PrintJobOut)
def approve_job(
    job_id: uuid.UUID,
    payload: JobActionRequest = JobActionRequest(),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return job_service.approve_job(
            db, job, teacher_note=payload.teacher_note, actor_id=admin.id
        )
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/reject", response_model=PrintJobOut)
def reject_job(
    job_id: uuid.UUID,
    payload: JobActionRequest = JobActionRequest(),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return job_service.reject_job(
            db, job, teacher_note=payload.teacher_note, actor_id=admin.id
        )
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/unapprove", response_model=PrintJobOut)
def unapprove_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return job_service.unapprove_job(db, job, actor_id=admin.id)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/enqueue", response_model=PrintJobOut)
def enqueue_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return queue_service.enqueue_job(db, job, actor_id=admin.id)
    except (InvalidStatusTransitionError, QueueError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/remove-from-queue", response_model=PrintJobOut)
def remove_job_from_queue(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return queue_service.remove_from_queue(db, job, actor_id=admin.id)
    except (InvalidStatusTransitionError, QueueError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
