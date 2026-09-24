"""
T054: Batch job endpoints for US4 — Historical Import with Pause/Resume.

Endpoints:
  GET  /api/batch-jobs          → List all batch jobs (newest first)
  POST /api/batch-jobs          → Create and start a new batch job
  GET  /api/batch-jobs/{id}     → Get a single job's status and progress
  POST /api/batch-jobs/{id}/pause  → Pause a running job
  POST /api/batch-jobs/{id}/resume → Resume a paused job
"""

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from src.core.database import get_database
from src.api.schemas.batch import BatchImportJobCreate, BatchImportJobResponse
from src.services.batch_worker import BatchWorker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/batch-jobs", tags=["batch-jobs"])


def get_batch_worker(db=Depends(get_database)) -> BatchWorker:
    return BatchWorker(db=db)


def _serialize_job(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a MongoDB document into a JSON-safe dict for responses."""
    doc = dict(doc)
    doc["_id"] = str(doc.pop("_id", ""))
    # Ensure error_logs timestamps are ISO strings (they may already be)
    for entry in doc.get("error_logs", []):
        if hasattr(entry.get("timestamp"), "isoformat"):
            entry["timestamp"] = entry["timestamp"].isoformat()
    return doc


# ---------------------------------------------------------------------------
# GET /api/batch-jobs
# ---------------------------------------------------------------------------

@router.get("", response_model=List[Dict[str, Any]])
async def list_batch_jobs(
    batch_worker: BatchWorker = Depends(get_batch_worker),
):
    """Return all batch jobs sorted by creation date (newest first)."""
    cursor = batch_worker.db["batch_import_jobs"].find({}).sort("created_at", -1)
    docs = await cursor.to_list(100)
    return [_serialize_job(d) for d in docs]


# ---------------------------------------------------------------------------
# POST /api/batch-jobs
# ---------------------------------------------------------------------------

@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_batch_job(
    payload: BatchImportJobCreate,
    background_tasks: BackgroundTasks,
    batch_worker: BatchWorker = Depends(get_batch_worker),
):
    """
    Create and immediately start a new historical batch import job in the
    background. Returns the initial job document with status='pending'.

    The job will transition to 'running' within milliseconds as the
    background task is scheduled.
    """
    if payload.year_start > payload.year_end:
        raise HTTPException(
            status_code=422,
            detail="year_start must be less than or equal to year_end.",
        )

    if payload.year_start < 1950 or payload.year_end > 2100:
        raise HTTPException(
            status_code=422,
            detail="Year range must be between 1950 and 2100.",
        )

    job = await batch_worker.create_job(
        media_type=payload.media_type.value,
        year_start=payload.year_start,
        year_end=payload.year_end,
    )

    background_tasks.add_task(batch_worker.run_job, job["job_id"])

    logger.info(
        "Batch job %s created and scheduled (%s %d–%d).",
        job["job_id"],
        payload.media_type.value,
        payload.year_start,
        payload.year_end,
    )
    return job


# ---------------------------------------------------------------------------
# GET /api/batch-jobs/{job_id}
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_batch_job(
    job_id: str,
    batch_worker: BatchWorker = Depends(get_batch_worker),
):
    """Return the full status, cursor, and progress of a single batch job."""
    job = await batch_worker.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Batch job '{job_id}' not found.")
    return _serialize_job(job)


# ---------------------------------------------------------------------------
# POST /api/batch-jobs/{job_id}/pause
# ---------------------------------------------------------------------------

@router.post("/{job_id}/pause", response_model=Dict[str, Any])
async def pause_batch_job(
    job_id: str,
    batch_worker: BatchWorker = Depends(get_batch_worker),
):
    """
    Signal a running batch job to pause.

    The worker checks this flag before each chunk and will stop cleanly,
    persisting the current cursor position for later resume.
    """
    job = await batch_worker.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Batch job '{job_id}' not found.")

    current_status = job.get("status")
    if current_status != "running":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot pause a job in '{current_status}' state. Only 'running' jobs can be paused.",
        )

    await batch_worker._set_status(job_id, "paused")
    updated = await batch_worker.get_job(job_id)
    return _serialize_job(updated)


# ---------------------------------------------------------------------------
# POST /api/batch-jobs/{job_id}/resume
# ---------------------------------------------------------------------------

@router.post("/{job_id}/resume", response_model=Dict[str, Any])
async def resume_batch_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    batch_worker: BatchWorker = Depends(get_batch_worker),
):
    """
    Resume a paused batch job from its saved cursor position.

    The job is marked 'running' and restarted as a background task.
    """
    job = await batch_worker.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Batch job '{job_id}' not found.")

    current_status = job.get("status")
    if current_status not in ("paused", "failed"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot resume a job in '{current_status}' state. Only 'paused' or 'failed' jobs can be resumed.",
        )

    background_tasks.add_task(batch_worker.resume_job, job_id)

    logger.info("Batch job %s scheduled for resume.", job_id)
    # Return the current state; background task will update status to 'running'
    return _serialize_job(job)
