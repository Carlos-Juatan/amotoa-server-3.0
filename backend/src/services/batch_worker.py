"""
BatchWorker: Background batch import service for historical year-range ingestion.

Architecture:
- MongoDB-backed state (batch_import_jobs collection) provides durable pause/resume.
- For anime: iterates year × season (winter/spring/summer/fall) chunks.
- For manga/LN: paginates through Jikan's publishing endpoint.
- Before each chunk, reads current job status from DB; if 'paused', exits cleanly.
- Discrete error logging: per-item failures are appended to error_logs and never
  crash the outer batch loop.
- current_cursor is persisted after every chunk so resume can start from where
  the batch left off.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.services.jikan_client import JikanClient
from src.services.media_service import MediaService

logger = logging.getLogger(__name__)

# Seasons in iteration order
ANIME_SEASONS: List[str] = ["winter", "spring", "summer", "fall"]


class BatchWorker:
    """
    Orchestrates long-running historical batch imports.

    Usage:
        worker = BatchWorker(db=db)
        job = await worker.create_job("anime", 2005, 2010)
        asyncio.create_task(worker.run_job(job["job_id"]))
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self._media_service = MediaService(db=db)

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    async def create_job(
        self,
        media_type: str,
        year_start: int,
        year_end: int,
    ) -> Dict[str, Any]:
        """
        Create and persist a new batch import job in 'pending' state.

        Returns the job document (without MongoDB's _id).
        """
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        doc: Dict[str, Any] = {
            "job_id": job_id,
            "media_type": media_type,
            "year_start": year_start,
            "year_end": year_end,
            "status": "pending",
            "current_cursor": {"year": year_start, "season_index": 0, "page": 1},
            "progress": {
                "total_discovered": 0,
                "imported": 0,
                "skipped": 0,
                "failed": 0,
            },
            "error_logs": [],
            "created_at": now,
            "updated_at": now,
        }
        await self.db["batch_import_jobs"].insert_one(doc)
        logger.info(
            "BatchWorker: created job %s (%s %d–%d)",
            job_id,
            media_type,
            year_start,
            year_end,
        )
        # Return a clean copy without the internal _id
        doc.pop("_id", None)
        return doc

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a job document from MongoDB by job_id."""
        return await self.db["batch_import_jobs"].find_one({"job_id": job_id})

    async def _set_status(self, job_id: str, status: str) -> None:
        await self.db["batch_import_jobs"].update_one(
            {"job_id": job_id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        )

    async def _update_progress(
        self,
        job_id: str,
        cursor: Dict[str, Any],
        progress_delta: Dict[str, int],
        error_entries: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Persist cursor position and progress increment after each chunk.
        Appends any discrete error entries to the error_logs array.
        """
        update: Dict[str, Any] = {
            "$set": {
                "current_cursor": cursor,
                "updated_at": datetime.now(timezone.utc),
            },
            "$inc": {
                f"progress.{k}": v for k, v in progress_delta.items()
            },
        }
        if error_entries:
            update["$push"] = {"error_logs": {"$each": error_entries}}

        await self.db["batch_import_jobs"].update_one({"job_id": job_id}, update)

    # ------------------------------------------------------------------
    # Public run / resume API
    # ------------------------------------------------------------------

    async def run_job(self, job_id: str) -> None:
        """
        Start executing a pending job from the beginning.
        Marks the job as 'running' then delegates to _execute_job.
        """
        job = await self.get_job(job_id)
        if job is None:
            logger.error("BatchWorker.run_job: job %s not found.", job_id)
            return

        await self._set_status(job_id, "running")
        job["status"] = "running"
        await self._execute_job(job)

    async def resume_job(self, job_id: str) -> None:
        """
        Resume a paused job from its saved current_cursor.
        Marks the job as 'running' then delegates to _execute_job.
        """
        job = await self.get_job(job_id)
        if job is None:
            logger.error("BatchWorker.resume_job: job %s not found.", job_id)
            return
        if job.get("status") not in ("paused", "failed"):
            logger.warning(
                "BatchWorker.resume_job: job %s is in status '%s', cannot resume.",
                job_id,
                job.get("status"),
            )
            return

        await self._set_status(job_id, "running")
        job["status"] = "running"
        await self._execute_job(job)

    # ------------------------------------------------------------------
    # Internal execution
    # ------------------------------------------------------------------

    async def _execute_job(self, job: Dict[str, Any]) -> None:
        """
        Core execution loop. Dispatches to anime or manga/LN worker
        based on media_type. Handles top-level error → marks job as failed.
        """
        job_id: str = job["job_id"]
        media_type: str = job["media_type"]

        try:
            if media_type == "anime":
                await self._run_anime_batch(job)
            else:
                await self._run_manga_ln_batch(job)

            # Re-read status: the loop may have stopped due to pause
            refreshed = await self.get_job(job_id)
            if refreshed and refreshed.get("status") == "running":
                await self._set_status(job_id, "completed")
                logger.info("BatchWorker: job %s completed.", job_id)

        except Exception as exc:
            logger.exception("BatchWorker: job %s failed with unhandled error: %s", job_id, exc)
            await self._set_status(job_id, "failed")

    # ------------------------------------------------------------------
    # Anime batch: year × season chunks
    # ------------------------------------------------------------------

    async def _run_anime_batch(self, job: Dict[str, Any]) -> None:
        job_id = job["job_id"]
        year_start: int = job["year_start"]
        year_end: int = job["year_end"]
        cursor: Dict[str, Any] = dict(job.get("current_cursor") or {})

        start_year: int = cursor.get("year", year_start)
        start_season_index: int = cursor.get("season_index", 0)

        async with JikanClient() as jikan:
            for year in range(start_year, year_end + 1):
                # Determine starting season index for this year
                season_start = start_season_index if year == start_year else 0

                for season_index in range(season_start, len(ANIME_SEASONS)):
                    # Pause check before each chunk
                    refreshed = await self.get_job(job_id)
                    if refreshed and refreshed.get("status") == "paused":
                        logger.info(
                            "BatchWorker: job %s paused at year=%d season_index=%d",
                            job_id, year, season_index,
                        )
                        return

                    season = ANIME_SEASONS[season_index]
                    logger.info(
                        "BatchWorker [%s]: processing anime %d/%s", job_id, year, season
                    )

                    chunk_progress, chunk_errors = await self._sync_anime_season(
                        jikan=jikan, media_type="anime", year=year, season=season
                    )

                    # Save cursor to the NEXT position
                    next_season_index = season_index + 1
                    next_year = year
                    if next_season_index >= len(ANIME_SEASONS):
                        next_season_index = 0
                        next_year = year + 1

                    new_cursor = {
                        "year": next_year,
                        "season_index": next_season_index,
                        "page": 1,
                    }
                    await self._update_progress(
                        job_id=job_id,
                        cursor=new_cursor,
                        progress_delta=chunk_progress,
                        error_entries=chunk_errors or None,
                    )

    async def _sync_anime_season(
        self,
        jikan: JikanClient,
        media_type: str,
        year: int,
        season: str,
    ) -> tuple:
        """
        Fetch and import a single anime season chunk.
        Returns (progress_delta, error_entries).
        """
        progress_delta = {"total_discovered": 0, "imported": 0, "skipped": 0, "failed": 0}
        error_entries: List[Dict[str, Any]] = []

        try:
            raw_items = await jikan.get_seasonal_anime(year, season)
        except Exception as exc:
            logger.error(
                "BatchWorker: failed to fetch %d/%s from Jikan: %s", year, season, exc
            )
            error_entries.append({
                "mal_id": 0,
                "title": f"Fetch error {year}/{season}",
                "reason": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return progress_delta, error_entries

        progress_delta["total_discovered"] += len(raw_items)

        for raw in raw_items:
            mal_id = raw.get("mal_id")
            if not mal_id:
                progress_delta["failed"] += 1
                error_entries.append({
                    "mal_id": 0,
                    "title": raw.get("title", "Unknown"),
                    "reason": "Missing mal_id in Jikan response",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            try:
                existing = await self.db["media"].find_one({"mal_id": mal_id}, {"_id": 1})
                if existing:
                    progress_delta["skipped"] += 1
                    continue

                doc = self._media_service._map_jikan_to_media(raw, media_type)
                await self.db["media"].insert_one(doc)
                progress_delta["imported"] += 1
                logger.debug("BatchWorker: imported anime mal_id=%d (%s)", mal_id, doc.get("title_default"))

            except Exception as exc:
                logger.error("BatchWorker: error importing anime mal_id=%d: %s", mal_id, exc)
                progress_delta["failed"] += 1
                error_entries.append({
                    "mal_id": mal_id,
                    "title": raw.get("title", "Unknown"),
                    "reason": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        return progress_delta, error_entries

    # ------------------------------------------------------------------
    # Manga/LN batch: paginated publishing endpoint
    # ------------------------------------------------------------------

    async def _run_manga_ln_batch(self, job: Dict[str, Any]) -> None:
        job_id = job["job_id"]
        media_type = job["media_type"]
        cursor = dict(job.get("current_cursor") or {})
        start_page: int = cursor.get("page", 1)

        async with JikanClient() as jikan:
            page = start_page
            while True:
                # Pause check
                refreshed = await self.get_job(job_id)
                if refreshed and refreshed.get("status") == "paused":
                    logger.info("BatchWorker: job %s paused at page=%d", job_id, page)
                    return

                logger.info("BatchWorker [%s]: processing %s page %d", job_id, media_type, page)

                chunk_progress, chunk_errors, has_next = await self._sync_manga_page(
                    jikan=jikan, media_type=media_type, page=page
                )

                new_cursor = {"year": job["year_start"], "season_index": 0, "page": page + 1}
                await self._update_progress(
                    job_id=job_id,
                    cursor=new_cursor,
                    progress_delta=chunk_progress,
                    error_entries=chunk_errors or None,
                )

                if not has_next:
                    break
                page += 1

    async def _sync_manga_page(
        self,
        jikan: JikanClient,
        media_type: str,
        page: int,
    ) -> tuple:
        """
        Fetch and import a single paginated manga/LN chunk.
        Returns (progress_delta, error_entries, has_next_page).
        """
        progress_delta = {"total_discovered": 0, "imported": 0, "skipped": 0, "failed": 0}
        error_entries: List[Dict[str, Any]] = []
        has_next = False

        try:
            data = await jikan.get_manga_publishing(page=page)
            raw_items = data.get("data", [])
            pagination = data.get("pagination", {})
            has_next = pagination.get("has_next_page", False)
        except Exception as exc:
            logger.error("BatchWorker: failed to fetch %s page %d: %s", media_type, page, exc)
            error_entries.append({
                "mal_id": 0,
                "title": f"Fetch error page {page}",
                "reason": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            return progress_delta, error_entries, False

        progress_delta["total_discovered"] += len(raw_items)

        for raw in raw_items:
            mal_id = raw.get("mal_id")
            if not mal_id:
                progress_delta["failed"] += 1
                error_entries.append({
                    "mal_id": 0,
                    "title": raw.get("title", "Unknown"),
                    "reason": "Missing mal_id in Jikan response",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            try:
                existing = await self.db["media"].find_one({"mal_id": mal_id}, {"_id": 1})
                if existing:
                    progress_delta["skipped"] += 1
                    continue

                doc = self._media_service._map_jikan_to_media(raw, media_type)
                await self.db["media"].insert_one(doc)
                progress_delta["imported"] += 1
                logger.debug("BatchWorker: imported %s mal_id=%d", media_type, mal_id)

            except Exception as exc:
                logger.error("BatchWorker: error importing %s mal_id=%d: %s", media_type, mal_id, exc)
                progress_delta["failed"] += 1
                error_entries.append({
                    "mal_id": mal_id,
                    "title": raw.get("title", "Unknown"),
                    "reason": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        return progress_delta, error_entries, has_next
