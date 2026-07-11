from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PrinterDriverType


class PrinterBase(BaseModel):
    name: str
    driver_type: PrinterDriverType
    host: str | None = None
    port: int | None = None
    serial_number: str | None = None
    location: str | None = None


class PrinterCreate(PrinterBase):
    access_code: str | None = None


class PrinterUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    serial_number: str | None = None
    location: str | None = None
    access_code: str | None = None
    is_active: bool | None = None


class PrinterOut(PrinterBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    has_access_code: bool = False


class PrinterStatusOut(BaseModel):
    status: str
    progress: float
    nozzle_actual: float
    nozzle_target: float
    bed_actual: float
    bed_target: float
    current_job_id: uuid.UUID | None = None


class PrinterTestResult(BaseModel):
    success: bool
    message: str
