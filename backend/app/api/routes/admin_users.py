from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import PasswordResetRequest, UserCreate, UserOut, UserUpdate
from app.services import user_service
from app.services.user_service import UsernameAlreadyExistsError

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def _get_user_or_404(db: Session, user_id: uuid.UUID) -> User:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return user_service.list_users(db)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    try:
        return user_service.create_user(db, payload, actor_id=admin.id)
    except UsernameAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Username '{exc}' already exists"
        ) from exc


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return _get_user_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = _get_user_or_404(db, user_id)
    return user_service.update_user(db, user, payload, actor_id=admin.id)


@router.post("/{user_id}/reset-password", response_model=UserOut)
def reset_password(
    user_id: uuid.UUID,
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = _get_user_or_404(db, user_id)
    return user_service.reset_password(db, user, payload.new_password, actor_id=admin.id)


@router.post("/{user_id}/disable", response_model=UserOut)
def disable_user(
    user_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = _get_user_or_404(db, user_id)
    return user_service.set_user_active(db, user, is_active=False, actor_id=admin.id)


@router.post("/{user_id}/enable", response_model=UserOut)
def enable_user(
    user_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = _get_user_or_404(db, user_id)
    return user_service.set_user_active(db, user, is_active=True, actor_id=admin.id)
