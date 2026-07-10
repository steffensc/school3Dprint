from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.print_job import PrintJobLiveStatusOut, PrintJobOut
from app.services import job_service, print_service
from app.services.upload_service import UploadValidationError, create_upload_and_job

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/uploads", response_model=PrintJobOut, status_code=status.HTTP_201_CREATED)
async def create_upload(
    title: str = Form(...),
    student_note: str | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = await file.read()
    try:
        job = create_upload_and_job(
            db,
            owner=current_user,
            original_filename=file.filename or "upload.stl",
            content_type=file.content_type,
            data=data,
            title=title,
            student_note=student_note,
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return job_service.get_job(db, job.id)


@router.get("/jobs", response_model=list[PrintJobOut])
def list_my_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return job_service.list_jobs_for_owner(db, current_user.id)


@router.get("/jobs/{job_id}", response_model=PrintJobOut)
def get_my_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = job_service.get_job(db, job_id)
    if job is None or job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/live-status", response_model=PrintJobLiveStatusOut)
def get_my_job_live_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = job_service.get_job(db, job_id)
    if job is None or job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return print_service.get_live_progress(job)
