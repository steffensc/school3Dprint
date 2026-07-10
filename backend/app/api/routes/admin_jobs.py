from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.print_job import (
    JobActionRequest,
    PrintJobLiveStatusOut,
    PrintJobOut,
    StartPrintRequest,
)
from app.services import job_service, print_service, printer_service, queue_service
from app.services.job_status import InvalidStatusTransitionError
from app.services.print_service import PrintServiceError
from app.services.queue_service import QueueError
from app.slicer.service import SlicingFailedError, slice_print_job

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


@router.post("/{job_id}/slice", response_model=PrintJobOut)
def slice_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return slice_print_job(db, job, actor_id=admin.id)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except SlicingFailedError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


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


@router.post("/{job_id}/start-print", response_model=PrintJobOut)
def start_print(
    job_id: uuid.UUID,
    payload: StartPrintRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    printer = printer_service.get_printer(db, payload.printer_id)
    if printer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    try:
        return print_service.start_print(db, job, printer, actor_id=admin.id)
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PrintServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/{job_id}/pause-print", response_model=PrintJobOut)
def pause_print(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return print_service.pause_print(db, job, actor_id=admin.id)
    except PrintServiceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/resume-print", response_model=PrintJobOut)
def resume_print(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return print_service.resume_print(db, job, actor_id=admin.id)
    except PrintServiceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/cancel-print", response_model=PrintJobOut)
def cancel_print(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    try:
        return print_service.cancel_print(db, job, actor_id=admin.id)
    except PrintServiceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{job_id}/live-status", response_model=PrintJobLiveStatusOut)
def live_status(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    job = _get_job_or_404(db, job_id)
    return print_service.get_live_progress(job)
