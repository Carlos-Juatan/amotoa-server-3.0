"""
T032: Progress Router — US6 endpoints for progress, links, tags, and franchise movies.

Implements:
  PUT  /api/media/{media_type}/{mal_id}/progress
  PUT  /api/media/{media_type}/{mal_id}/links
  PUT  /api/media/{media_type}/{mal_id}/tags
  POST /api/media/{media_type}/{mal_id}/movies       (anime only)
  PATCH /api/media/{media_type}/{mal_id}/movies/{movie_id} (anime only)
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Path
from typing import List, Optional
from pydantic import BaseModel, Field

from src.core.database import get_database
from src.api.schemas.media import MediaType
from src.api.schemas.media import UserProgressDTO, MediaCardDTO
from src.services.progress_service import ProgressService

router = APIRouter(prefix="/api/media", tags=["progress"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_progress_service(db=Depends(get_database)) -> ProgressService:
    return ProgressService(db)


# ---------------------------------------------------------------------------
# Request schemas (local to avoid circular imports with media.py schemas)
# ---------------------------------------------------------------------------

class UpdateProgressRequest(BaseModel):
    current_unit: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    is_favorite: Optional[bool] = None
    personal_score: Optional[int] = Field(None, ge=0, le=10)


class ExternalLinkRequest(BaseModel):
    label: str
    url: str


class UpdateTagsRequest(BaseModel):
    tags: List[str]


class AddMovieRequest(BaseModel):
    title: str
    cover_image_url: Optional[str] = None
    release_year: Optional[int] = None


class ToggleMovieRequest(BaseModel):
    watched: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _progress_or_404(result: Optional[dict], mal_id: int) -> dict:
    """Raise 404 if the service returned None (media not found), else return result."""
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Media with mal_id={mal_id} not found."
        )
    return result


# ---------------------------------------------------------------------------
# PUT /api/media/{media_type}/{mal_id}/progress
# ---------------------------------------------------------------------------

@router.put("/{media_type}/{mal_id}/progress", response_model=UserProgressDTO)
async def update_progress(
    media_type: MediaType,
    mal_id: int,
    body: UpdateProgressRequest,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """Update tracking progress (episodes/chapters), status, score, or favorite state."""
    try:
        result = await service.update_progress(
            account_id=x_active_account,
            media_type=media_type,
            mal_id=mal_id,
            current_unit=body.current_unit,
            status=body.status,
            is_favorite=body.is_favorite,
            personal_score=body.personal_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return _progress_or_404(result, mal_id)


# ---------------------------------------------------------------------------
# PUT /api/media/{media_type}/{mal_id}/links
# ---------------------------------------------------------------------------

@router.put("/{media_type}/{mal_id}/links", response_model=UserProgressDTO)
async def update_links(
    media_type: MediaType,
    mal_id: int,
    links: List[ExternalLinkRequest],
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """Replace the external streaming/reading links for the active account."""
    links_data = [lk.model_dump() for lk in links]
    result = await service.update_links(
        account_id=x_active_account,
        media_type=media_type,
        mal_id=mal_id,
        links=links_data,
    )
    return _progress_or_404(result, mal_id)


# ---------------------------------------------------------------------------
# PUT /api/media/{media_type}/{mal_id}/tags
# ---------------------------------------------------------------------------

@router.put("/{media_type}/{mal_id}/tags", response_model=UserProgressDTO)
async def update_tags(
    media_type: MediaType,
    mal_id: int,
    body: UpdateTagsRequest,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """Replace personal tags for the active account."""
    result = await service.update_tags(
        account_id=x_active_account,
        media_type=media_type,
        mal_id=mal_id,
        tags=body.tags,
    )
    return _progress_or_404(result, mal_id)


# ---------------------------------------------------------------------------
# POST /api/media/{media_type}/{mal_id}/movies  (anime only)
# ---------------------------------------------------------------------------

@router.post("/{media_type}/{mal_id}/movies", response_model=UserProgressDTO, status_code=201)
async def add_franchise_movie(
    media_type: MediaType,
    mal_id: int,
    body: AddMovieRequest,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """Add a franchise movie entry. Restricted to anime media type only."""
    if media_type != MediaType.ANIME:
        raise HTTPException(
            status_code=403,
            detail="Franchise movies are exclusively available for anime media."
        )
    result = await service.add_franchise_movie(
        account_id=x_active_account,
        mal_id=mal_id,
        title=body.title,
        cover_image_url=body.cover_image_url,
        release_year=body.release_year,
    )
    return _progress_or_404(result, mal_id)


# ---------------------------------------------------------------------------
# PATCH /api/media/{media_type}/{mal_id}/movies/{movie_id}  (anime only)
# ---------------------------------------------------------------------------

@router.patch("/{media_type}/{mal_id}/movies/{movie_id}", response_model=UserProgressDTO)
async def toggle_movie_watched(
    media_type: MediaType,
    mal_id: int,
    movie_id: str,
    body: ToggleMovieRequest,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """Toggle watched status of a specific franchise movie. Anime only."""
    if media_type != MediaType.ANIME:
        raise HTTPException(
            status_code=403,
            detail="Franchise movies are exclusively available for anime media."
        )
    result = await service.toggle_movie_watched(
        account_id=x_active_account,
        mal_id=mal_id,
        movie_id=movie_id,
        watched=body.watched,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Movie with movie_id='{movie_id}' not found in progress for mal_id={mal_id}."
        )
    return result

# ---------------------------------------------------------------------------
# US7: GET /api/media/{media_type}/active-progress
# ---------------------------------------------------------------------------

@router.get("/{media_type}/active-progress", response_model=List[MediaCardDTO])
async def get_active_progress(
    media_type: MediaType,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """
    Get all active media of the given type that have a progress record for the active account.
    Active means "Currently Airing" for anime and "Publishing" for manga/LN.
    """
    return await service.get_active_progress(account_id=x_active_account, media_type=media_type)


# ---------------------------------------------------------------------------
# US7: POST /api/media/{media_type}/{mal_id}/increment
# ---------------------------------------------------------------------------

@router.post("/{media_type}/{mal_id}/increment", response_model=UserProgressDTO)
async def increment_progress(
    media_type: MediaType,
    mal_id: int,
    x_active_account: str = Header(default="car-j-home", alias="X-Active-Account"),
    service: ProgressService = Depends(get_progress_service),
):
    """
    Quickly increment the current unit by 1. 
    Clamps to total_units if known and automatically marks as completed.
    """
    result = await service.increment_unit(
        account_id=x_active_account,
        media_type=media_type,
        mal_id=mal_id
    )
    return _progress_or_404(result, mal_id)
