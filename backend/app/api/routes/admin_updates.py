"""Admin update check + install (Section 9.10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.update import UpdateCheckResult, UpdateRunOut
from app.services import update_service

router = APIRouter(prefix="/api/admin/updates", tags=["admin-updates"])


@router.get("/check", response_model=UpdateCheckResult)
def check_for_update(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    result = update_service.check_for_update(db, actor_id=admin.id)
    return UpdateCheckResult(
        current_version=result.current_version,
        latest_version=result.latest_version,
        update_available=result.update_available,
        release_url=result.release_url,
        release_notes=result.release_notes,
        published_at=result.published_at,
        checked_at=result.checked_at,
        error=result.error,
    )


@router.post("/install", response_model=UpdateRunOut)
def install_update(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    run = update_service.install_update(db, actor_id=admin.id)
    return UpdateRunOut.model_validate(run)


@router.get("/status", response_model=UpdateRunOut | None)
def update_status(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    run = update_service.get_latest_update_run(db)
    return UpdateRunOut.model_validate(run) if run else None
