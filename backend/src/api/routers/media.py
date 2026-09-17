from fastapi import APIRouter, Header, Depends, Query, HTTPException
from typing import List, Optional
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

