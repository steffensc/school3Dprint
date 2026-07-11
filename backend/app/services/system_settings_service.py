"""Typed access to the `system_settings` key/value store (Section 9.9).

Values fall back to the corresponding `Settings` (env var) default until
an admin overrides them via the API, so the system is usable out of the
box without requiring an initial settings round trip.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.system_setting import SystemSetting

settings = get_settings()

RETENTION_DAYS_FINISHED_KEY = "retention_days_finished"
RETENTION_DAYS_REJECTED_KEY = "retention_days_rejected"
RETENTION_DAYS_FAILED_KEY = "retention_days_failed"

_RETENTION_DEFAULTS: dict[str, int] = {
    RETENTION_DAYS_FINISHED_KEY: settings.retention_days_finished,
    RETENTION_DAYS_REJECTED_KEY: settings.retention_days_rejected,
    RETENTION_DAYS_FAILED_KEY: settings.retention_days_failed,
}


def get_int_setting(db: Session, key: str, default: int) -> int:
    row = db.get(SystemSetting, key)
    if row is None:
        return default
    try:
        return int(row.value)
    except ValueError:
        return default


def set_int_setting(db: Session, key: str, value: int) -> None:
    row = db.get(SystemSetting, key)
    if row is None:
        db.add(SystemSetting(key=key, value=str(value)))
    else:
        row.value = str(value)


def get_retention_settings(db: Session) -> dict[str, int]:
    return {key: get_int_setting(db, key, default) for key, default in _RETENTION_DEFAULTS.items()}


def set_retention_settings(
    db: Session,
    *,
    retention_days_finished: int | None = None,
    retention_days_rejected: int | None = None,
    retention_days_failed: int | None = None,
) -> dict[str, int]:
    updates = {
        RETENTION_DAYS_FINISHED_KEY: retention_days_finished,
        RETENTION_DAYS_REJECTED_KEY: retention_days_rejected,
        RETENTION_DAYS_FAILED_KEY: retention_days_failed,
    }
    for key, value in updates.items():
        if value is not None:
            set_int_setting(db, key, value)
    db.commit()
    return get_retention_settings(db)
