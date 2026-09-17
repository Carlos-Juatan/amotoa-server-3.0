"""
T031: ProgressService — all US6 progress management operations.

Handles progress upsert, external links, personal tags, and
anime-exclusive franchise movie management against the
`user_progress` MongoDB collection, isolated by account_id.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.schemas.progress import ExternalLink, FranchiseMovie, ProgressStatus
from src.api.schemas.media import MediaType

logger = logging.getLogger(__name__)


class ProgressService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_progress(self, account_id: str, media_mal_id: int) -> Optional[dict]:
        """Fetch a user_progress document; returns None if not found."""
        return await self.db["user_progress"].find_one(
            {"account_id": account_id, "media_mal_id": media_mal_id}
        )

    async def _upsert_progress(
        self,
        account_id: str,
        media_mal_id: int,
        media_type: str,
        update_fields: dict,
    ) -> dict:
        """
        Upsert the user_progress document and return the updated document.
        Always refreshes `last_interacted_at`.

        Uses an explicit find + insert-or-update strategy to avoid mongomock's
        bug where $set fields are ignored when combined with $setOnInsert on
        newly inserted documents.
        """
        now = datetime.now(timezone.utc)
        update_fields["last_interacted_at"] = now

        existing = await self.db["user_progress"].find_one(
            {"account_id": account_id, "media_mal_id": media_mal_id}
        )

        if existing is None:
            # Build a complete new document with defaults + caller overrides
            new_doc = {
                "account_id": account_id,
                "media_mal_id": media_mal_id,
                "media_type": media_type,
                "current_unit": 0,
                "status": ProgressStatus.PLAN_TO_WATCH,
                "is_favorite": False,
                "personal_score": None,
                "personal_tags": [],
                "external_links": [],
                "franchise_movies": [],
                "completed_at": None,
            }
            new_doc.update(update_fields)  # caller fields win over defaults
            await self.db["user_progress"].insert_one(new_doc)
        else:
            await self.db["user_progress"].update_one(
                {"account_id": account_id, "media_mal_id": media_mal_id},
                {"$set": update_fields},
            )

        result = await self.db["user_progress"].find_one(
            {"account_id": account_id, "media_mal_id": media_mal_id}
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def _get_media(self, media_type: str, mal_id: int) -> Optional[dict]:
        """Fetch a media document; returns None if not found."""
        return await self.db["media"].find_one({"mal_id": mal_id, "type": media_type})

    # ------------------------------------------------------------------
    # US6: Update progress, status, score, favorite
    # ------------------------------------------------------------------

    async def update_progress(
        self,
        account_id: str,
        media_type: str,
        mal_id: int,
        current_unit: Optional[int] = None,
        status: Optional[str] = None,
        is_favorite: Optional[bool] = None,
        personal_score: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Update tracking progress for a given media item under an account.

        Validation:
        - `current_unit` must be between 0 and `total_units` (inclusive).
        - If `current_unit` reaches `total_units`, `status` is forced to 'completed'.
        Returns None if media is not found (caller raises 404).
        Raises ValueError on constraint violations.
        """
        media = await self._get_media(media_type, mal_id)
        if media is None:
            return None

        total_units = media.get("total_units")
        fields: dict = {}

        if current_unit is not None:
            if current_unit < 0:
                raise ValueError("current_unit must be >= 0")
            if total_units is not None and total_units > 0 and current_unit > total_units:
                raise ValueError(
                    f"current_unit ({current_unit}) exceeds total_units ({total_units})"
                )
            fields["current_unit"] = current_unit
            # Auto-complete when the last unit is reached
            if total_units is not None and current_unit >= total_units and total_units > 0:
                fields["status"] = ProgressStatus.COMPLETED
                fields["completed_at"] = datetime.now(timezone.utc)

        if status is not None and "status" not in fields:
            fields["status"] = status
            if status == ProgressStatus.COMPLETED:
                fields["completed_at"] = datetime.now(timezone.utc)

        if is_favorite is not None:
            fields["is_favorite"] = is_favorite

        if personal_score is not None:
            fields["personal_score"] = personal_score

        return await self._upsert_progress(account_id, mal_id, media_type, fields)

    # ------------------------------------------------------------------
    # US6: External links
    # ------------------------------------------------------------------

    async def update_links(
        self,
        account_id: str,
        media_type: str,
        mal_id: int,
        links: List[dict],
    ) -> Optional[dict]:
        """
        Replace the entire external_links list for a given media/account pair.
        Returns None if media is not found.
        """
        media = await self._get_media(media_type, mal_id)
        if media is None:
            return None

        # Normalize to serializable dicts
        normalized = [{"label": lk["label"], "url": lk["url"]} for lk in links]
        return await self._upsert_progress(
            account_id, mal_id, media_type, {"external_links": normalized}
        )

    # ------------------------------------------------------------------
    # US6: Personal tags
    # ------------------------------------------------------------------

    async def update_tags(
        self,
        account_id: str,
        media_type: str,
        mal_id: int,
        tags: List[str],
    ) -> Optional[dict]:
        """
        Replace the entire personal_tags list for a given media/account pair.
        Returns None if media is not found.
        """
        media = await self._get_media(media_type, mal_id)
        if media is None:
            return None

        return await self._upsert_progress(
            account_id, mal_id, media_type, {"personal_tags": tags}
        )

    # ------------------------------------------------------------------
    # US6: Franchise movies (anime-exclusive)
    # ------------------------------------------------------------------

    async def add_franchise_movie(
        self,
        account_id: str,
        mal_id: int,
        title: str,
        cover_image_url: Optional[str] = None,
        release_year: Optional[int] = None,
    ) -> Optional[dict]:
        """
        Add a new franchise movie entry to the progress document.
        Media type is always 'anime'; caller must enforce this constraint.
        Returns None if media not found.
        """
        media = await self._get_media("anime", mal_id)
        if media is None:
            return None

        new_movie = {
            "movie_id": str(uuid.uuid4()),
            "title": title,
            "cover_image_url": cover_image_url,
            "watched": False,
            "release_year": release_year,
        }

        now = datetime.now(timezone.utc)
        existing = await self.db["user_progress"].find_one(
            {"account_id": account_id, "media_mal_id": mal_id}
        )

        if existing is None:
            # Insert a brand-new progress doc with the first movie
            new_doc = {
                "account_id": account_id,
                "media_mal_id": mal_id,
                "media_type": "anime",
                "current_unit": 0,
                "status": ProgressStatus.PLAN_TO_WATCH,
                "is_favorite": False,
                "personal_score": None,
                "personal_tags": [],
                "external_links": [],
                "franchise_movies": [new_movie],
                "completed_at": None,
                "last_interacted_at": now,
            }
            await self.db["user_progress"].insert_one(new_doc)
        else:
            await self.db["user_progress"].update_one(
                {"account_id": account_id, "media_mal_id": mal_id},
                {
                    "$push": {"franchise_movies": new_movie},
                    "$set": {"last_interacted_at": now},
                },
            )

        result = await self.db["user_progress"].find_one(
            {"account_id": account_id, "media_mal_id": mal_id}
        )
        if result:
            result["_id"] = str(result["_id"])
        return result

    async def toggle_movie_watched(
        self,
        account_id: str,
        mal_id: int,
        movie_id: str,
        watched: bool,
    ) -> Optional[dict]:
        """
        Toggle watched status on a specific franchise movie by `movie_id`.
        Returns None if the progress document or movie_id is not found.
        """
        progress = await self._get_progress(account_id, mal_id)
        if progress is None:
            return None

        movies = progress.get("franchise_movies") or []
        movie_index = next(
            (i for i, m in enumerate(movies) if m["movie_id"] == movie_id), None
        )
        if movie_index is None:
            return None

        now = datetime.now(timezone.utc)
        await self.db["user_progress"].update_one(
            {
                "account_id": account_id,
                "media_mal_id": mal_id,
                "franchise_movies.movie_id": movie_id,
            },
            {
                "$set": {
                    "franchise_movies.$.watched": watched,
                    "last_interacted_at": now,
                }
            },
        )
        result = await self.db["user_progress"].find_one(
            {"account_id": account_id, "media_mal_id": mal_id}
        )
        if result is None:
            return None
        result["_id"] = str(result["_id"])
        return result

    # ------------------------------------------------------------------
    # US7: Daily Progress Tracking
    # ------------------------------------------------------------------

    async def get_active_progress(
        self, account_id: str, media_type: str
    ) -> List[dict]:
        """
        Returns a list of media documents of `media_type` that are currently active
        ("Currently Airing" for anime, "Publishing" for manga/light_novel) AND have
        an existing user_progress record for the account.
        The progress record is embedded in the media document under `user_progress`.
        """
        active_status = "Currently Airing" if media_type == "anime" else "Publishing"

        # Find active media
        cursor = self.db["media"].find(
            {"type": media_type, "published_status": active_status}
        )
        media_list = await cursor.to_list(length=None)
        if not media_list:
            return []

        mal_ids = [m["mal_id"] for m in media_list]

        # Find corresponding progress for this account
        prog_cursor = self.db["user_progress"].find(
            {"account_id": account_id, "media_mal_id": {"$in": mal_ids}}
        )
        prog_list = await prog_cursor.to_list(length=None)
        prog_map = {p["media_mal_id"]: p for p in prog_list}

        # Embed progress into media, only return media that actually have progress tracked
        result = []
        for m in media_list:
            if m["mal_id"] in prog_map:
                m["_id"] = str(m["_id"])
                p = prog_map[m["mal_id"]]
                p["_id"] = str(p["_id"])
                m["user_progress"] = p
                result.append(m)

        return result

    async def increment_unit(
        self, account_id: str, media_type: str, mal_id: int
    ) -> Optional[dict]:
        """
        Increments current_unit by 1 for an existing progress record.
        Automatically clamps to total_units if known, and marks as completed
        if it reaches the total.
        Returns the updated user_progress document, or None if media/progress not found.
        """
        media = await self._get_media(media_type, mal_id)
        if not media:
            return None
        
        progress = await self._get_progress(account_id, mal_id)
        if not progress:
            return None

        current = progress.get("current_unit", 0)
        new_unit = current + 1

        # update_progress already handles clamping and auto-completion
        return await self.update_progress(
            account_id,
            media_type,
            mal_id,
            current_unit=new_unit
        )
