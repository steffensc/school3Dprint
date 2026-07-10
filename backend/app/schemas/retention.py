from __future__ import annotations

from pydantic import BaseModel, Field


class RetentionSettingsOut(BaseModel):
    retention_days_finished: int
    retention_days_rejected: int
    retention_days_failed: int


class RetentionSettingsUpdate(BaseModel):
    retention_days_finished: int | None = Field(default=None, ge=1, le=3650)
    retention_days_rejected: int | None = Field(default=None, ge=1, le=3650)
    retention_days_failed: int | None = Field(default=None, ge=1, le=3650)


class RetentionRunResult(BaseModel):
    deleted_job_count: int
    bytes_freed: int


class StorageOverviewOut(BaseModel):
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    uploads_bytes: int
    sliced_bytes: int
    active_uploaded_files: int
    jobs_pending_retention: int
