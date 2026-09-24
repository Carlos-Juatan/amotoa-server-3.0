from fastapi import APIRouter, BackgroundTasks, HTTPException
from src.api.schemas.batch import BackupResponse, BackupCreateResponse
from src.services.backup_service import BackupService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/backups", tags=["Admin"])

@router.get("", response_model=list[BackupResponse])
async def list_backups():
    """List all available compressed backups."""
    try:
        return BackupService.list_backups()
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail="Could not list backups")

@router.post("", response_model=BackupCreateResponse)
async def create_backup(background_tasks: BackgroundTasks):
    """Trigger a new manual backup asynchronously."""
    async def task_wrapper():
        try:
            await BackupService.create_backup()
        except Exception as e:
            logger.error(f"Error creating backup in background: {e}")

    background_tasks.add_task(task_wrapper)
    return BackupCreateResponse(message="Backup job triggered successfully")
