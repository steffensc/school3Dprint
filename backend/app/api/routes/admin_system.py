"""Admin system status + version info (Section 10.4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.system import SystemStatusOut, VersionOut
from app.services import version_service
from app.services.system_status_service import get_system_status

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])


@router.get("/status", response_model=SystemStatusOut)
def system_status(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    status = get_system_status(db)
    return SystemStatusOut(
        cpu_percent=status.cpu_percent,
        ram_total_bytes=status.ram_total_bytes,
        ram_used_bytes=status.ram_used_bytes,
        ram_percent=status.ram_percent,
        disk_total_bytes=status.disk_total_bytes,
        disk_used_bytes=status.disk_used_bytes,
        disk_free_bytes=status.disk_free_bytes,
        uploads_bytes=status.uploads_bytes,
        sliced_bytes=status.sliced_bytes,
        uptime_seconds=status.uptime_seconds,
    )


@router.get("/version", response_model=VersionOut)
def version_info(_: User = Depends(require_admin)):
    return VersionOut(
        backend_version=version_service.get_backend_version(),
        frontend_version=version_service.get_frontend_version(),
        container_version=version_service.get_container_version(),
        git_commit=version_service.get_git_commit(),
        environment=version_service.get_environment(),
    )
