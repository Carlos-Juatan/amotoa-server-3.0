"""
Background periodic sync scheduler for Amontoa V3.0 (US3).

Responsibilities:
- Anime: Triggered at the start of each seasonal window (Winter/Spring/Summer/Fall)
  or manually via the API. This module only handles the recurring trigger; the
  actual sync is delegated to MediaService.sync_seasonal_anime().
- Manga / Light Novel: Runs a full publishing-status sync on an interval defined
  by the `MANGA_LN_SYNC_INTERVAL` settings value (in seconds, default 86400 = 1 day).

Design decisions:
- Pure asyncio — no Celery, no Redis, no external broker (Constitution Principle I).
- The scheduler tasks are started as asyncio background tasks inside the FastAPI
  lifespan context and cancelled cleanly on shutdown.
- Concrete sync logic lives in MediaService to keep the scheduler thin and testable.
"""

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Optional

from src.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Season helpers
# ---------------------------------------------------------------------------

SEASON_MONTHS = {
    "winter": (1, 2, 3),
    "spring": (4, 5, 6),
    "summer": (7, 8, 9),
    "fall": (10, 11, 12),
}

SEASON_ORDER = ["winter", "spring", "summer", "fall"]


def current_season_and_year() -> tuple[str, int]:
    """Return the current calendar season name and year."""
    today = date.today()
    month = today.month
    for season, months in SEASON_MONTHS.items():
        if month in months:
            return season, today.year
    return "winter", today.year  # fallback (should never happen)


def next_season_start() -> datetime:
    """
    Compute the UTC datetime of the first day of the next anime season
    (i.e. January 1, April 1, July 1, or October 1).
    """
    today = date.today()
    year = today.year
    season_starts = [
        date(year, 1, 1),
        date(year, 4, 1),
        date(year, 7, 1),
        date(year, 10, 1),
        date(year + 1, 1, 1),  # sentinel for the next year
    ]
    for start in season_starts:
        if start > today:
            return datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    # Fallback: next Jan 1
    return datetime(year + 1, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Scheduler tasks
# ---------------------------------------------------------------------------

async def _anime_seasonal_sync_loop(db) -> None:
    """
    Continuously trigger seasonal anime sync at each season boundary.

    Sleeps until the next season start, then fires sync for the new season,
    and repeats indefinitely.
    """
    # Import here to avoid circular imports at module load time
    from src.services.media_service import MediaService

    service = MediaService(db)

    while True:
        target = next_season_start()
        now = datetime.now(timezone.utc)
        wait_seconds = (target - now).total_seconds()

        if wait_seconds > 0:
            logger.info(
                "Anime seasonal sync scheduled at %s (in %.0f seconds).",
                target.isoformat(),
                wait_seconds,
            )
            try:
                await asyncio.sleep(wait_seconds)
            except asyncio.CancelledError:
                logger.info("Anime seasonal sync loop cancelled.")
                return

        # Trigger sync for the season that just started
        season, year = current_season_and_year()
        logger.info("Starting scheduled seasonal anime sync for %s/%s.", year, season)
        try:
            summary = await service.sync_seasonal_anime(year=year, season=season)
            logger.info(
                "Scheduled anime sync %s/%s complete: %s", year, season, summary
            )
        except asyncio.CancelledError:
            logger.info("Anime seasonal sync loop cancelled during sync.")
            return
        except Exception as exc:
            logger.error("Scheduled seasonal anime sync failed: %s", exc, exc_info=True)

        # Brief pause to avoid re-triggering immediately at season boundary
        await asyncio.sleep(60)


async def _manga_ln_periodic_sync_loop(db, interval_seconds: int) -> None:
    """
    Periodically sync all currently publishing manga and light novels.

    Runs every `interval_seconds` seconds (configured via MANGA_LN_SYNC_INTERVAL).
    """
    from src.services.media_service import MediaService

    service = MediaService(db)

    while True:
        logger.info(
            "Starting periodic manga/LN sync (interval=%ds).", interval_seconds
        )
        for media_type in ("manga", "light_novel"):
            try:
                summary = await service.sync_manga_ln(media_type=media_type)
                logger.info("Periodic %s sync complete: %s", media_type, summary)
            except asyncio.CancelledError:
                logger.info("Manga/LN periodic sync loop cancelled during %s sync.", media_type)
                return
            except Exception as exc:
                logger.error(
                    "Periodic %s sync failed: %s", media_type, exc, exc_info=True
                )

        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Manga/LN periodic sync loop cancelled.")
            return

async def _backup_periodic_loop() -> None:
    """Run daily automated backups."""
    from src.services.backup_service import BackupService
    interval_seconds = 86400  # 1 day

    while True:
        try:
            await asyncio.sleep(interval_seconds)
            logger.info("Starting scheduled daily MongoDB backup.")
            filename = await BackupService.create_backup()
            logger.info(f"Daily backup completed: {filename}")
        except asyncio.CancelledError:
            logger.info("Backup periodic loop cancelled.")
            return
        except Exception as exc:
            logger.error("Scheduled daily backup failed: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# Public API — used from main.py lifespan
# ---------------------------------------------------------------------------

_anime_task: Optional[asyncio.Task] = None
_manga_ln_task: Optional[asyncio.Task] = None
_backup_task: Optional[asyncio.Task] = None


async def start_scheduler(db) -> None:
    """
    Start both background sync loops.

    Call this inside the FastAPI lifespan startup handler after the database
    connection is established.

    Args:
        db: The active AsyncIOMotorDatabase instance from `get_database()`.
    """
    global _anime_task, _manga_ln_task, _backup_task

    interval = settings.MANGA_LN_SYNC_INTERVAL  # seconds (default 86400)

    logger.info(
        "Starting background schedulers — anime: seasonal boundary trigger, "
        "manga/LN: every %ds, backup: daily.",
        interval,
    )

    _anime_task = asyncio.create_task(
        _anime_seasonal_sync_loop(db),
        name="anime_seasonal_sync",
    )
    _manga_ln_task = asyncio.create_task(
        _manga_ln_periodic_sync_loop(db, interval_seconds=interval),
        name="manga_ln_periodic_sync",
    )
    _backup_task = asyncio.create_task(
        _backup_periodic_loop(),
        name="daily_mongodb_backup",
    )


async def stop_scheduler() -> None:
    """
    Cancel all background sync tasks gracefully.

    Call this inside the FastAPI lifespan shutdown handler.
    """
    global _anime_task, _manga_ln_task, _backup_task

    tasks_to_stop = [
        (_anime_task, "anime_seasonal_sync"), 
        (_manga_ln_task, "manga_ln_periodic_sync"),
        (_backup_task, "daily_mongodb_backup")
    ]

    for task, name in tasks_to_stop:
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info("Background task '%s' stopped.", name)

    _anime_task = None
    _manga_ln_task = None
    _backup_task = None
