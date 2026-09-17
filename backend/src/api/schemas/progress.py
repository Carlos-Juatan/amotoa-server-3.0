from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from src.api.schemas.media import MediaType

class ProgressStatus(str, Enum):
    WATCHING = "watching"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    DROPPED = "dropped"
    PLAN_TO_WATCH = "plan_to_watch"

class ExternalLink(BaseModel):
    label: str
    url: str

class FranchiseMovie(BaseModel):
    movie_id: str
    title: str
    cover_image_url: str
    watched: bool
    release_year: int

class UserProgressBase(BaseModel):
    account_id: str
    media_mal_id: int
    media_type: MediaType
    current_unit: int = 0
    status: ProgressStatus
    is_favorite: bool = False
    personal_score: Optional[int] = Field(None, ge=0, le=10)
    personal_tags: List[str] = Field(default_factory=list)
    external_links: List[ExternalLink] = Field(default_factory=list)
    franchise_movies: Optional[List[FranchiseMovie]] = None

class UserProgressCreate(UserProgressBase):
    pass

class UserProgressUpdate(BaseModel):
    current_unit: Optional[int] = None
    status: Optional[ProgressStatus] = None
    is_favorite: Optional[bool] = None
    personal_score: Optional[int] = Field(None, ge=0, le=10)
    personal_tags: Optional[List[str]] = None
    external_links: Optional[List[ExternalLink]] = None
    franchise_movies: Optional[List[FranchiseMovie]] = None

class UserProgressResponse(UserProgressBase):
    id: str = Field(alias="_id")
    last_interacted_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
