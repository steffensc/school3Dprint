from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.print_job import PrintJobOut
from app.schemas.queue import QueueReorderRequest
from app.services import job_service, queue_service
from app.services.queue_service import QueueError

router = APIRouter(prefix="/api/admin/queue", tags=["admin-queue"])


@router.get("", response_model=list[PrintJobOut])
def get_queue(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return queue_service.get_queue(db)


@router.post("/reorder", response_model=list[PrintJobOut])
def reorder_queue(
    payload: QueueReorderRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return queue_service.reorder_queue(db, payload.ordered_job_ids, actor_id=admin.id)
    except QueueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/move-up", response_model=list[PrintJobOut])
def move_job_up(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    try:
        return queue_service.move_job(db, job, direction=-1, actor_id=admin.id)
    except QueueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{job_id}/move-down", response_model=list[PrintJobOut])
def move_job_down(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    try:
        return queue_service.move_job(db, job, direction=1, actor_id=admin.id)
    except QueueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
