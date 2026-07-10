from __future__ import annotations

from pydantic import BaseModel


class VersionOut(BaseModel):
    """Version info shown on the admin System page (Section 10.4)."""

    backend_version: str
    frontend_version: str
    container_version: str
    git_commit: str | None = None
    environment: str


class SystemStatusOut(BaseModel):
    """Live host metrics shown on the admin System page (Section 10.4)."""

    cpu_percent: float
    ram_total_bytes: int
    ram_used_bytes: int
    ram_percent: float
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    uploads_bytes: int
    sliced_bytes: int
    uptime_seconds: float
