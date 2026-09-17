from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.api.schemas.media import MediaCardDTO, MediaType

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


