from typing import Optional, List
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
