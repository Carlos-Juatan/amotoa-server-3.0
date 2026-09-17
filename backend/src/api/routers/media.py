from fastapi import APIRouter, Header, Depends, Query
from typing import List, Optional
from src.core.database import get_database
from src.api.schemas.media import MediaCardDTO, MediaType
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
