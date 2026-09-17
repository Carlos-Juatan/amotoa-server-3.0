from fastapi import APIRouter, Header, Depends, Query, HTTPException, BackgroundTasks
from typing import Dict, List, Optional
from src.core.database import get_database
from src.api.schemas.media import MediaCardDTO, MediaDetailDTO, MediaType
from src.services.media_service import MediaService

router = APIRouter(prefix="/api/media", tags=["media"])

def get_media_service(db = Depends(get_database)) -> MediaService:
    return MediaService(db)

@router.get("/{media_type}", response_model=List[MediaCardDTO])
async def list_media(
    media_type: MediaType,
    status_group: Optional[str] = Query(None, description="Filter by user tracking status"),
    search: Optional[str] = None,
    genre: Optional[str] = None,
    year: Optional[int] = None,
    letter: Optional[str] = None,
    sort_by: str = Query("title", description="Field to sort by"),
    order: str = Query("asc", description="Sort order (asc or desc)"),
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    media_service: MediaService = Depends(get_media_service)
):
    results = await media_service.get_media_catalog(
        account_id=x_active_account,
        media_type=media_type,
        status_group=status_group,
        search=search,
        genre=genre,
        year=year,
        letter=letter,
        sort_by=sort_by,
        order=order
    )
    return results

@router.get("/{media_type}/{mal_id}", response_model=MediaDetailDTO)
async def get_media_detail(
    media_type: MediaType,
    mal_id: int,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    media_service: MediaService = Depends(get_media_service)
):
    """Return full detail for a single media item, including franchise seasons and user progress."""
    detail = await media_service.get_media_detail(
        account_id=x_active_account,
        media_type=media_type,
        mal_id=mal_id,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail=f"{media_type} with mal_id={mal_id} not found.")
    return detail


@router.post("/sync/{media_type}", response_model=Dict[str, int], tags=["sync"])
async def trigger_sync(
    media_type: MediaType,
    year: Optional[int] = Query(None, description="Season year (anime only, e.g. 2024)"),
    season: Optional[str] = Query(
        None,
        description="Season name for anime: winter | spring | summer | fall",
    ),
    media_service: MediaService = Depends(get_media_service),
):
    """
    Manually trigger a catalog sync from Jikan API v4.

    - **Anime**: Provide `year` and `season` (e.g. `?year=2024&season=winter`) to sync
      that specific seasonal batch. If omitted, defaults to the current calendar season.
    - **Manga / Light Novel**: Syncs all currently publishing titles (paginated). `year`
      and `season` are ignored.

    Returns a summary with counts of `imported`, `skipped`, and `failed` items.
    """
    from datetime import date

    if media_type == MediaType.ANIME:
        # Determine year/season defaults
        if year is None or season is None:
            today = date.today()
            year = year or today.year
            if season is None:
                month = today.month
                if month in (1, 2, 3):
                    season = "winter"
                elif month in (4, 5, 6):
                    season = "spring"
                elif month in (7, 8, 9):
                    season = "summer"
                else:
                    season = "fall"

        valid_seasons = {"winter", "spring", "summer", "fall"}
        if season not in valid_seasons:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid season '{season}'. Must be one of: {sorted(valid_seasons)}",
            )

        summary = await media_service.sync_seasonal_anime(year=year, season=season)
    else:
        # manga or light_novel
        summary = await media_service.sync_manga_ln(media_type=media_type.value)

    return summary
