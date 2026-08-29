"""Periodic ingestion scheduler.

Reference implementation uses APScheduler for simplicity. The interface is
deliberately thin (`start_scheduler(app)` / one job per vendor) so it can be
swapped for Celery beat or a Temporal workflow without touching adapter or
ingestion code — see docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.adapters import ADAPTERS
from app.config import settings
from app.db import AsyncSessionLocal
from app.ingestion import run_ingestion

logger = logging.getLogger("patch_radar.scheduler")

_scheduler: AsyncIOScheduler | None = None


async def _ingest_vendor_job(vendor_id: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await run_ingestion(vendor_id, db)
        logger.info("Scheduled ingestion for %s: %s", vendor_id, result)


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    for vendor_id in ADAPTERS:
        _scheduler.add_job(
            _ingest_vendor_job,
            "interval",
            hours=settings.ingestion_interval_hours,
            args=[vendor_id],
            id=f"ingest_{vendor_id}",
            next_run_time=None,  # first run scheduled INGESTION_INTERVAL_HOURS out;
                                  # use POST /ingest/{vendor} for an immediate run
        )
    _scheduler.start()
    logger.info(
        "Scheduler started: %d vendor jobs every %dh",
        len(ADAPTERS), settings.ingestion_interval_hours,
    )
    return _scheduler


def stop_scheduler() -> None:
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
