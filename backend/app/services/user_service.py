"""User CRUD and admin-bootstrap logic (Section 9.1 / 9.2)."""

from __future__ import annotations

import os
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit_service import log_action


class UsernameAlreadyExistsError(Exception):
    pass


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()


def list_users(db: Session) -> list[User]:
    return list(db.execute(select(User).order_by(User.username)).scalars())


def create_user(
    db: Session, data: UserCreate, *, actor_id: uuid.UUID | None = None
) -> User:
    if get_user_by_username(db, data.username) is not None:
        raise UsernameAlreadyExistsError(data.username)

    user = User(
        username=data.username,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
        role=data.role,
        class_name=data.class_name,
    )
    db.add(user)
    db.flush()
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.USER_CREATED,
        entity_type="user",
        entity_id=user.id,
        metadata={"username": user.username, "role": user.role.value},
    )
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session, user: User, data: UserUpdate, *, actor_id: uuid.UUID | None = None
) -> User:
    changed: dict[str, object] = {}
    for field in ("display_name", "role", "class_name", "is_active"):
        value = getattr(data, field)
        if value is not None and getattr(user, field) != value:
            setattr(user, field, value)
            changed[field] = value if not isinstance(value, UserRole) else value.value

    if changed:
        log_action(
            db,
            actor_id=actor_id,
            action=AuditAction.USER_UPDATED,
            entity_type="user",
            entity_id=user.id,
            metadata=changed,
        )
    db.commit()
    db.refresh(user)
    return user


def set_user_active(
    db: Session, user: User, *, is_active: bool, actor_id: uuid.UUID | None = None
) -> User:
    user.is_active = is_active
    action = AuditAction.USER_ENABLED if is_active else AuditAction.USER_DISABLED
    log_action(db, actor_id=actor_id, action=action, entity_type="user", entity_id=user.id)
    db.commit()
    db.refresh(user)
    return user


def reset_password(
    db: Session, user: User, new_password: str, *, actor_id: uuid.UUID | None = None
) -> User:
    user.password_hash = hash_password(new_password)
    log_action(
        db,
        actor_id=actor_id,
        action=AuditAction.PASSWORD_RESET,
        entity_type="user",
        entity_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


def bootstrap_initial_admin(db: Session) -> tuple[User, str] | None:
    """Creates the first admin account if no users exist yet.

    The generated password is returned once (also printed to stdout/logs)
    so an operator can log in and change it immediately. If a
    `SCHOOLPRINT_INITIAL_ADMIN_PASSWORD` env var is set, it is used instead
    of a random password (useful for scripted/CI setups).
    """

    existing = db.execute(select(User).limit(1)).scalar_one_or_none()
    if existing is not None:
        return None

    password = os.environ.get("SCHOOLPRINT_INITIAL_ADMIN_PASSWORD") or secrets.token_urlsafe(12)
    admin = User(
        username="admin",
        display_name="Administrator",
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.flush()
    log_action(
        db,
        actor_id=admin.id,
        action=AuditAction.USER_CREATED,
        entity_type="user",
        entity_id=admin.id,
        metadata={"username": admin.username, "bootstrap": True},
    )
    db.commit()
    db.refresh(admin)
    return admin, password
