from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PrintJobStatus


class UploadedFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_size_bytes: int
    sha256: str
    created_at: datetime


class PrintJobOwnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    class_name: str | None = None


class JobActionRequest(BaseModel):
    teacher_note: str | None = None


class StartPrintRequest(BaseModel):
    printer_id: uuid.UUID


class PrintJobPrinterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class PrintJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: PrintJobStatus
    queue_position: int | None = None
    student_note: str | None = None
    teacher_note: str | None = None
    estimated_print_time_seconds: int | None = None
    estimated_filament_grams: float | None = None
    created_at: datetime
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    failed_at: datetime | None = None
    expires_at: datetime | None = None
    uploaded_file: UploadedFileOut
    owner: PrintJobOwnerOut | None = None
    printer: PrintJobPrinterOut | None = None


class PrintJobLiveStatusOut(BaseModel):
    status: str
    progress: float = 0.0
    nozzle_actual: float | None = None
    nozzle_target: float | None = None
    bed_actual: float | None = None
    bed_target: float | None = None
