"""Read-side helpers for `PrintJob` shared by user and admin endpoints."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.print_job import PrintJob


def get_job(db: Session, job_id: uuid.UUID) -> PrintJob | None:
    return db.execute(
        select(PrintJob)
        .options(joinedload(PrintJob.uploaded_file), joinedload(PrintJob.owner))
        .where(PrintJob.id == job_id)
    ).scalar_one_or_none()


def list_jobs_for_owner(db: Session, owner_id: uuid.UUID) -> list[PrintJob]:
    return list(
        db.execute(
            select(PrintJob)
            .options(joinedload(PrintJob.uploaded_file), joinedload(PrintJob.owner))
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
            .options(joinedload(PrintJob.uploaded_file), joinedload(PrintJob.owner))
            .order_by(PrintJob.created_at.desc())
        )
        .unique()
        .scalars()
    )
