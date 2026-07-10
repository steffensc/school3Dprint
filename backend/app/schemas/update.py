from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import UpdateRunStatus


class UpdateCheckResult(BaseModel):
    current_version: str
    latest_version: str | None
    update_available: bool
    release_url: str | None = None
    release_notes: str | None = None
    published_at: datetime | None = None
    checked_at: datetime
    error: str | None = None


class UpdateRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: UpdateRunStatus
    from_version: str
    to_version: str | None
    log: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
