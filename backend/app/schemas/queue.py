from __future__ import annotations

import uuid

from pydantic import BaseModel


class QueueReorderRequest(BaseModel):
    ordered_job_ids: list[uuid.UUID]
