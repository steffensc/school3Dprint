"""Admin retention settings, manual retention trigger, and storage
overview (Section 9.9)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.retention import (
    RetentionRunResult,
    RetentionSettingsOut,
    RetentionSettingsUpdate,
    StorageOverviewOut,
)
from app.services import retention_service, system_settings_service
from app.services.storage_service import get_storage_overview

router = APIRouter(prefix="/api/admin", tags=["admin-settings"])


@router.get("/settings/retention", response_model=RetentionSettingsOut)
def get_retention_settings(
    db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    return system_settings_service.get_retention_settings(db)


@router.put("/settings/retention", response_model=RetentionSettingsOut)
def update_retention_settings(
    payload: RetentionSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return system_settings_service.set_retention_settings(
        db,
        retention_days_finished=payload.retention_days_finished,
        retention_days_rejected=payload.retention_days_rejected,
        retention_days_failed=payload.retention_days_failed,
    )


@router.post("/retention/run", response_model=RetentionRunResult)
def run_retention_now(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = retention_service.run_retention(db, actor_id=admin.id)
    return RetentionRunResult(
        deleted_job_count=result.deleted_job_count, bytes_freed=result.bytes_freed
    )


@router.get("/storage/overview", response_model=StorageOverviewOut)
def storage_overview(
    db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    overview = get_storage_overview(db)
    return StorageOverviewOut(
        disk_total_bytes=overview.disk_total_bytes,
        disk_used_bytes=overview.disk_used_bytes,
        disk_free_bytes=overview.disk_free_bytes,
        uploads_bytes=overview.uploads_bytes,
        sliced_bytes=overview.sliced_bytes,
        active_uploaded_files=overview.active_uploaded_files,
        jobs_pending_retention=overview.jobs_pending_retention,
    )
