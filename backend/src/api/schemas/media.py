from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class MediaType(str, Enum):
    ANIME = "anime"
    MANGA = "manga"
    LIGHT_NOVEL = "light_novel"

class PublishedStatus(str, Enum):
    PUBLISHING = "Publishing"
    FINISHED = "Finished"
    CURRENTLY_AIRING = "Currently Airing"
    NOT_YET_AIRED = "Not yet aired"

class Season(str, Enum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"

class Relation(BaseModel):
    mal_id: int
    type: str
    relation_type: str
    title: str

class ExternalLink(BaseModel):
    label: str
    url: str

class FranchiseMovie(BaseModel):
    movie_id: str
    title: str
    cover_image_url: Optional[str] = None
    watched: bool = False
    release_year: Optional[int] = None

class UserProgressDTO(BaseModel):
    account_id: str
    media_mal_id: int
    current_unit: int
    status: str
    is_favorite: bool
    personal_score: Optional[int] = None
    personal_tags: List[str] = []
    external_links: List[ExternalLink] = []
    franchise_movies: Optional[List[FranchiseMovie]] = None

    class Config:
        populate_by_name = True

class MediaBase(BaseModel):
    mal_id: int
    type: MediaType
    title_japanese: str
    title_english: Optional[str] = None
    title_default: str
    synopsis: Optional[str] = None
    cover_image_url: str
    gallery_image_urls: Optional[List[str]] = None
    published_status: PublishedStatus
    total_units: Optional[int] = None
    season: Optional[Season] = None
    year: Optional[int] = None
    genres: Optional[List[str]] = None
    score_public: Optional[float] = None
    franchise_root_id: Optional[int] = None
    relations: Optional[List[Relation]] = None

class MediaCreate(MediaBase):
    pass

class MediaResponse(MediaBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class MediaCardDTO(BaseModel):
    """Lightweight card representation used in carousels and related_seasons lists."""
    mal_id: int
    type: MediaType
    title_japanese: str
    title_english: Optional[str] = None
    title_default: str
    cover_image_url: str
    synopsis: Optional[str] = None
    score_public: Optional[float] = None
    total_units: Optional[int] = None
    year: Optional[int] = None
    genres: Optional[List[str]] = None
    published_status: PublishedStatus
    user_progress: Optional[UserProgressDTO] = None

    class Config:
        populate_by_name = True

class MediaDetailDTO(BaseModel):
    """Full detail representation including franchise seasons and user progress."""
    mal_id: int
    type: MediaType
    title_japanese: str
    title_english: Optional[str] = None
    title_default: str
    synopsis: Optional[str] = None
    cover_image_url: str
    gallery_image_urls: Optional[List[str]] = None
    published_status: PublishedStatus
    total_units: Optional[int] = None
    season: Optional[Season] = None
    year: Optional[int] = None
    genres: Optional[List[str]] = None
    score_public: Optional[float] = None
    franchise_root_id: Optional[int] = None
    related_seasons: List[Any] = []  # List[MediaCardDTO] – using Any to avoid circular ref
    user_progress: Optional[UserProgressDTO] = None

    class Config:
        populate_by_name = True

