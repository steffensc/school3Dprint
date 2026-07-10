from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.print_job import PrintJobOut
from app.services import job_service

router = APIRouter(prefix="/api/admin/jobs", tags=["admin-jobs"])


@router.get("", response_model=list[PrintJobOut])
def list_jobs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return job_service.list_all_jobs(db)


@router.get("/{job_id}", response_model=PrintJobOut)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    job = job_service.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job
