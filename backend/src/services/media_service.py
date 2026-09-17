import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.api.schemas.media import MediaCardDTO, MediaType
from src.services.jikan_client import JikanClient

logger = logging.getLogger(__name__)

class MediaService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_media_catalog(
        self, 
        account_id: str, 
        media_type: MediaType, 
        status_group: Optional[str] = None,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        letter: Optional[str] = None,
        sort_by: str = "title",
        order: str = "asc"
    ) -> List[dict]:
        
        # 1. First, build the query for user_progress based on status_group if provided
        # For US1, we care about tracking status.
        progress_query = {"account_id": account_id, "media_type": media_type}
        
        if status_group == "favorites":
            progress_query["is_favorite"] = True
        elif status_group:
            progress_query["status"] = status_group

        # Fetch progress matching criteria
        progress_docs = await self.db["user_progress"].find(progress_query).to_list(None)
        
        # Build a map of mal_id -> progress for quick lookup
        progress_map = {doc["media_mal_id"]: doc for doc in progress_docs}
        
        # 2. If status_group was specified, we ONLY want media that is in progress_map
        media_query = {"type": media_type}
        if status_group:
            if not progress_map:
                return [] # No progress matching this status, so no media to return
            media_query["mal_id"] = {"$in": list(progress_map.keys())}
            
        # Execute media query
        media_cursor = self.db["media"].find(media_query)
        
        # Sort logic
        sort_field = "title_japanese" if sort_by == "title" else sort_by
        sort_direction = 1 if order == "asc" else -1
        media_cursor.sort(sort_field, sort_direction)
        
        media_docs = await media_cursor.to_list(None)
        
        # 3. Assemble results
        results = []
        for media in media_docs:
            prog = progress_map.get(media["mal_id"])
            if prog:
                # Convert ObjectId to string to avoid serialization issues
                prog["_id"] = str(prog["_id"])
            
            # The schema expects 'user_progress'
            media["user_progress"] = prog
            
            # _id to id mapping for Pydantic if needed
            media["id"] = str(media["_id"])
            
            results.append(media)
            
        return results

    async def get_media_detail(
        self,
        account_id: str,
        media_type: MediaType,
        mal_id: int,
    ) -> Optional[dict]:
        """
        Fetch a single media item's full detail, resolving sibling franchise seasons
        via shared franchise_root_id, and attaching the account's user_progress.

        Returns None if the media item is not found.
        """
        # 1. Fetch the primary media document
        media = await self.db["media"].find_one({"mal_id": mal_id, "type": media_type})
        if media is None:
            return None

        # 2. Resolve franchise siblings (same franchise_root_id, different mal_id)
        franchise_root_id = media.get("franchise_root_id")
        related_seasons: List[dict] = []
        if franchise_root_id is not None:
            sibling_cursor = self.db["media"].find({
                "franchise_root_id": franchise_root_id,
                "mal_id": {"$ne": mal_id},
                "type": media_type,
            }).sort("year", 1)
            siblings = await sibling_cursor.to_list(None)
            for sibling in siblings:
                # Convert ObjectId fields to strings to ensure JSON-safe payload
                sibling["_id"] = str(sibling["_id"])
                sibling["id"] = sibling["_id"]
                # Fetch progress for each sibling so the frontend card can show state
                sibling_prog = await self.db["user_progress"].find_one({
                    "account_id": account_id,
                    "media_mal_id": sibling["mal_id"],
                })
                if sibling_prog:
                    sibling_prog["_id"] = str(sibling_prog["_id"])
                sibling["user_progress"] = sibling_prog
                related_seasons.append(sibling)

        # 3. Fetch user progress for the primary item
        progress = await self.db["user_progress"].find_one({
            "account_id": account_id,
            "media_mal_id": mal_id,
        })
        if progress:
            progress["_id"] = str(progress["_id"])

        # 4. Assemble detail payload
        media["id"] = str(media["_id"])
        media["user_progress"] = progress
        media["related_seasons"] = related_seasons

        return media

    # ------------------------------------------------------------------
    # US3: Jikan sync helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_jikan_to_media(raw: Dict[str, Any], media_type: str) -> Dict[str, Any]:
        """
        Normalise a raw Jikan API object into the internal media document schema.

        Args:
            raw:        Raw dict from Jikan API (anime or manga endpoint).
            media_type: 'anime', 'manga', or 'light_novel'.

        Returns:
            Dict ready to be inserted into the `media` collection.
        """
        images = raw.get("images", {})
        webp = images.get("webp", {})
        jpg = images.get("jpg", {})
        cover_url: str = (
            webp.get("large_image_url")
            or jpg.get("large_image_url")
            or webp.get("image_url")
            or jpg.get("image_url")
            or ""
        )

        # Relations: filter for direct lineage types only
        raw_relations: List[Dict[str, Any]] = raw.get("relations", [])
        relations: List[Dict[str, Any]] = []
        lineage_types = {"Sequel", "Prequel", "Alternative version", "Parent story"}
        for rel in raw_relations:
            rel_type = rel.get("relation", "")
            for entry in rel.get("entry", []):
                if rel_type in lineage_types:
                    relations.append({
                        "mal_id": entry.get("mal_id"),
                        "type": entry.get("type", media_type),
                        "relation_type": rel_type,
                        "title": entry.get("name", ""),
                    })

        # Published status mapping
        status_raw: str = raw.get("status", "")
        status_map = {
            "Currently Airing": "Currently Airing",
            "Finished Airing": "Finished",
            "Not yet aired": "Not yet aired",
            "Publishing": "Publishing",
            "Finished": "Finished",
            "Discontinued": "Finished",
            "On Hiatus": "Finished",
        }
        published_status: str = status_map.get(status_raw, "Finished")

        # Genres: combine genres + themes tags
        genres: List[str] = [g["name"] for g in raw.get("genres", [])]
        genres += [t["name"] for t in raw.get("themes", [])]

        now = datetime.now(timezone.utc)

        return {
            "mal_id": raw["mal_id"],
            "type": media_type,
            "title_japanese": raw.get("title_japanese") or raw.get("title") or "",
            "title_english": raw.get("title_english"),
            "title_default": raw.get("title") or "",
            "synopsis": raw.get("synopsis"),
            "cover_image_url": cover_url,
            "gallery_image_urls": [],
            "published_status": published_status,
            "total_units": raw.get("episodes") or raw.get("chapters"),
            "season": raw.get("season"),
            "year": raw.get("year") or (raw.get("aired", {}) or {}).get("prop", {}).get("from", {}).get("year"),
            "genres": genres,
            "score_public": raw.get("score"),
            "franchise_root_id": None,
            "relations": relations,
            "created_at": now,
            "updated_at": now,
        }

    async def sync_seasonal_anime(
        self,
        year: int,
        season: str,
        jikan: Optional[JikanClient] = None,
    ) -> Dict[str, int]:
        """
        Sync a specific anime season from Jikan into the local catalog.

        Implements the Ignore & Skip policy:
        - Existing mal_ids are skipped entirely — user_progress is untouched.
        - New items are inserted.

        Args:
            year:   Season year (e.g. 2024).
            season: Season name: "winter", "spring", "summer", or "fall".
            jikan:  Optional pre-existing JikanClient (used in tests / batch worker).

        Returns:
            Summary dict: {"imported": int, "skipped": int, "failed": int}.
        """
        summary: Dict[str, int] = {"imported": 0, "skipped": 0, "failed": 0}

        async def _run(client: JikanClient) -> None:
            raw_items = await client.get_seasonal_anime(year, season)
            logger.info(
                "Seasonal sync %s/%s: %d items fetched from Jikan.", year, season, len(raw_items)
            )
            for raw in raw_items:
                mal_id = raw.get("mal_id")
                if not mal_id:
                    summary["failed"] += 1
                    continue
                try:
                    existing = await self.db["media"].find_one({"mal_id": mal_id}, {"_id": 1})
                    if existing:
                        logger.debug("Skipping existing anime mal_id=%d.", mal_id)
                        summary["skipped"] += 1
                        continue
                    doc = self._map_jikan_to_media(raw, "anime")
                    await self.db["media"].insert_one(doc)
                    logger.debug("Imported anime mal_id=%d (%s).", mal_id, doc.get("title_default"))
                    summary["imported"] += 1
                except Exception as exc:
                    logger.error("Failed to import anime mal_id=%d: %s", mal_id, exc)
                    summary["failed"] += 1

        if jikan is not None:
            await _run(jikan)
        else:
            async with JikanClient() as client:
                await _run(client)

        logger.info(
            "Seasonal anime sync %s/%s complete — imported=%d, skipped=%d, failed=%d.",
            year, season, summary["imported"], summary["skipped"], summary["failed"],
        )
        return summary

    async def sync_manga_ln(
        self,
        media_type: str,
        jikan: Optional[JikanClient] = None,
    ) -> Dict[str, int]:
        """
        Sync currently publishing manga/light novels from Jikan into the local catalog.

        Paginates through all publishing titles. Implements the same Ignore & Skip
        policy: existing entries are skipped; new ones are inserted.

        Args:
            media_type: 'manga' or 'light_novel'.
            jikan:      Optional pre-existing JikanClient.

        Returns:
            Summary dict: {"imported": int, "skipped": int, "failed": int}.
        """
        if media_type not in ("manga", "light_novel"):
            raise ValueError(
                f"sync_manga_ln only accepts 'manga' or 'light_novel', got: {media_type}"
            )

        summary: Dict[str, int] = {"imported": 0, "skipped": 0, "failed": 0}

        async def _run(client: JikanClient) -> None:
            page = 1
            while True:
                data = await client.get_manga_publishing(page=page)
                items: List[Dict[str, Any]] = data.get("data", [])
                if not items:
                    break

                for raw in items:
                    mal_id = raw.get("mal_id")
                    if not mal_id:
                        summary["failed"] += 1
                        continue
                    try:
                        existing = await self.db["media"].find_one({"mal_id": mal_id}, {"_id": 1})
                        if existing:
                            logger.debug("Skipping existing %s mal_id=%d.", media_type, mal_id)
                            summary["skipped"] += 1
                            continue
                        doc = self._map_jikan_to_media(raw, media_type)
                        await self.db["media"].insert_one(doc)
                        logger.debug(
                            "Imported %s mal_id=%d (%s).", media_type, mal_id, doc.get("title_default")
                        )
                        summary["imported"] += 1
                    except Exception as exc:
                        logger.error("Failed to import %s mal_id=%d: %s", media_type, mal_id, exc)
                        summary["failed"] += 1

                pagination = data.get("pagination", {})
                if not pagination.get("has_next_page", False):
                    break
                page += 1

        if jikan is not None:
            await _run(jikan)
        else:
            async with JikanClient() as client:
                await _run(client)

        logger.info(
            "%s periodic sync complete — imported=%d, skipped=%d, failed=%d.",
            media_type, summary["imported"], summary["skipped"], summary["failed"],
        )
        return summary
