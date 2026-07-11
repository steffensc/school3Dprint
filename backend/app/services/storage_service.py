"""Storage overview for the admin settings page (Section 9.9): disk
usage plus a breakdown of how much of it is SchoolPrint's own files, so
admins can see the effect of retention settings before/after running
them."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.sliced_artifact import SlicedArtifact
from app.models.uploaded_file import UploadedFile
from app.services.retention_service import find_retention_candidates

settings = get_settings()


@dataclass
class StorageOverview:
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    uploads_bytes: int
    sliced_bytes: int
    active_uploaded_files: int
    jobs_pending_retention: int


def _sliced_artifacts_bytes(db: Session) -> int:
    paths = db.execute(select(SlicedArtifact.file_path)).scalars().all()
    total = 0
    for path_str in paths:
        path = Path(path_str)
        if path.exists() and path.is_file():
            total += path.stat().st_size
    return total


def get_storage_overview(db: Session) -> StorageOverview:
    disk_total, disk_used, disk_free = shutil.disk_usage(settings.storage_root)

    uploads_bytes = (
        db.execute(
            select(func.coalesce(func.sum(UploadedFile.file_size_bytes), 0)).where(
                UploadedFile.deleted_at.is_(None)
            )
        ).scalar_one()
        or 0
    )
    active_uploaded_files = (
        db.execute(
            select(func.count(UploadedFile.id)).where(UploadedFile.deleted_at.is_(None))
        ).scalar_one()
        or 0
    )

    return StorageOverview(
        disk_total_bytes=disk_total,
        disk_used_bytes=disk_used,
        disk_free_bytes=disk_free,
        uploads_bytes=int(uploads_bytes),
        sliced_bytes=_sliced_artifacts_bytes(db),
        active_uploaded_files=int(active_uploaded_files),
        jobs_pending_retention=len(find_retention_candidates(db)),
    )
