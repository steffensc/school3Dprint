"""Live host metrics for the admin System page (Section 10.4): CPU, RAM,
disk and SchoolPrint's own storage footprint. Reuses the disk/upload/
sliced-artifact accounting already built for the retention/storage
overview (Section 9.9) so the two pages stay consistent."""

from __future__ import annotations

import time
from dataclasses import dataclass

import psutil
from sqlalchemy.orm import Session

from app.services.storage_service import get_storage_overview

_BOOT_TIME = time.time()


@dataclass
class SystemStatus:
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


def get_system_status(db: Session) -> SystemStatus:
    # `interval=None` returns the reading since the last call (or since
    # import) instead of blocking for a sample window, which keeps this
    # endpoint fast enough to poll from the frontend.
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    overview = get_storage_overview(db)

    return SystemStatus(
        cpu_percent=cpu_percent,
        ram_total_bytes=memory.total,
        ram_used_bytes=memory.used,
        ram_percent=memory.percent,
        disk_total_bytes=overview.disk_total_bytes,
        disk_used_bytes=overview.disk_used_bytes,
        disk_free_bytes=overview.disk_free_bytes,
        uploads_bytes=overview.uploads_bytes,
        sliced_bytes=overview.sliced_bytes,
        uptime_seconds=time.time() - _BOOT_TIME,
    )
