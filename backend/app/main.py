"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import (
    admin_jobs,
    admin_printers,
    admin_queue,
    admin_settings,
    admin_system,
    admin_updates,
    admin_users,
    auth,
    user_uploads,
)
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.user_service import bootstrap_initial_admin
from app.workers.retention_worker import start_retention_scheduler, stop_retention_scheduler

logger = logging.getLogger("schoolprint")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.sliced_dir.mkdir(parents=True, exist_ok=True)
    settings.previews_dir.mkdir(parents=True, exist_ok=True)
    settings.backups_dir.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        result = bootstrap_initial_admin(db)
        if result is not None:
            _admin, password = result
            logger.warning(
                "Bootstrapped initial admin user 'admin' with password: %s "
                "(change this immediately after first login)",
                password,
            )
    finally:
        db.close()

    start_retention_scheduler()

    yield

    stop_retention_scheduler()


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Local school 3D-print management server.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(user_uploads.router)
app.include_router(admin_jobs.router)
app.include_router(admin_queue.router)
app.include_router(admin_printers.router)
app.include_router(admin_settings.router)
app.include_router(admin_system.router)
app.include_router(admin_updates.router)


@app.get("/api/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
