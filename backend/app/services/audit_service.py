"""Central helper for writing `AuditLog` rows (Section 9 / 15)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    *,
    actor_id: uuid.UUID | None,
    action: AuditAction,
    entity_type: str,
    entity_id: str | uuid.UUID | None = None,
    metadata: dict | None = None,
    commit: bool = False,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        metadata_json=metadata,
    )
    db.add(entry)
    if commit:
        db.commit()
    else:
        db.flush()
    return entry
