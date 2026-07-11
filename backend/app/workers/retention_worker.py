"""Daily retention scheduler (Section 9.9): wraps `run_retention` in an
APScheduler background job so cleanup happens automatically without an
admin having to remember to click "Run now" every day."""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.retention_service import run_retention

logger = logging.getLogger("schoolprint.retention")
settings = get_settings()

_scheduler: BackgroundScheduler | None = None


def _run_retention_job() -> None:
    db = SessionLocal()
    try:
        result = run_retention(db, actor_id=None)
        logger.info(
            "Scheduled retention run deleted %d job file(s), freed %d bytes",
            result.deleted_job_count,
            result.bytes_freed,
        )
    except Exception:  # pragma: no cover - defensive: never crash the scheduler thread
        logger.exception("Scheduled retention run failed")
    finally:
        db.close()


def start_retention_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    if not settings.retention_scheduler_enabled:
        return None
    if _scheduler is not None:
        return _scheduler

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _run_retention_job,
        trigger=CronTrigger(hour=settings.retention_scheduler_hour_utc, minute=0),
        id="daily-retention",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_retention_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
