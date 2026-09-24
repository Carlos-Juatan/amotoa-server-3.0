from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from src.api.schemas.media import MediaType

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class ErrorEntry(BaseModel):
    mal_id: int
    title: str
    reason: str
    timestamp: datetime

class JobProgress(BaseModel):
    total_discovered: int = 0
    imported: int = 0
    skipped: int = 0
    failed: int = 0

class BatchImportJobBase(BaseModel):
    job_id: str
    media_type: MediaType
    year_start: int
    year_end: int
    status: JobStatus
    current_cursor: Dict[str, Any]
    progress: JobProgress
    error_logs: List[ErrorEntry] = Field(default_factory=list)

class BatchImportJobCreate(BaseModel):
    media_type: MediaType
    year_start: int
    year_end: int

class BatchImportJobResponse(BatchImportJobBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class BackupResponse(BaseModel):
    filename: str
    size_bytes: int
    created_at: datetime

class BackupCreateResponse(BaseModel):
    message: str
    filename: Optional[str] = None
