import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body
from sqlalchemy.orm import Session
from typing import List, Optional # Added Optional
import uuid
from datetime import datetime # Added datetime for default job name

from breachwatch.api.v1 import schemas
from breachwatch.storage.database import get_db, SessionLocal # Import SessionLocal
from breachwatch.storage import crud
from breachwatch.core.crawler import MasterCrawler # Actual crawler import
# from breachwatch.tasks.crawl_tasks import run_crawl_job_task # For Celery or background tasks

logger = logging.getLogger(__name__)
router = APIRouter()


async def process_crawl_job(job_id: uuid.UUID, settings_data: dict, db_session_maker):
    """
    Background task runner for a crawl job.
    Requires a session maker to create a new session for this task.
    Uses the real MasterCrawler.
    """
    db: Session = db_session_maker()
    try:
        logger.info(f"process_crawl_job: Starting for job_id {job_id}")
        # The settings_data should already be a dict from model_dump()
        settings_schema = schemas.CrawlSettingsSchema(**settings_data)
        logger.debug(f"process_crawl_job: Parsed settings: {settings_schema}")
        
        crawler = MasterCrawler(job_id=job_id, crawl_settings=settings_schema, db=db)
        
        # The MasterCrawler.start_crawling() is an async generator.
        # We need to iterate through it to make it execute.
        async for downloaded_file_schema in crawler.start_crawling():
            if downloaded_file_schema:
                logger.info(f"Job {job_id} processed and stored: {downloaded_file_schema.file_url} (ID: {downloaded_file_schema.id})")
            else:
                logger.debug(f"Job {job_id} yielded a None value from crawler (possibly end or empty iteration).")
        
        logger.info(f"Crawl job {job_id} fully processed by MasterCrawler.")
        # Status is updated within MasterCrawler now, but can be re-confirmed or set to a final "processed" state here if needed.
        # crud.update_crawl_job_status(db=db, job_id=job_id, status="completed") # Ensure it's marked completed

    except Exception as e:
        logger.error(f"Error during background crawl job {job_id}: {e}", exc_info=True)
        try:
            crud.update_crawl_job_status(db=db, job_id=job_id, status="failed")
        except Exception as db_e:
            logger.error(f"Failed to update job status to 'failed' for job {job_id} after error: {db_e}", exc_info=True)
    finally:
        db.close()
        logger.info(f"process_crawl_job: DB session closed for job_id {job_id}")


@router.post("/jobs", response_model=schemas.CrawlJobSchema, status_code=202)
async def create_new_crawl_job( # Renamed from create_crawl_job to avoid conflict with conceptual one
    crawl_job_in: schemas.CrawlJobCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new crawl job with specific settings and start it in the background.
    This is the primary endpoint for initiating crawls from the frontend.
    """
    logger.info(f"Received request to create new crawl job: {crawl_job_in.name}")
    try:
        # Ensure name is set if not provided
        if not crawl_job_in.name:
            crawl_job_in.name = f"Crawl Job - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        db_crawl_job = crud.create_crawl_job(db=db, crawl_job_in=crawl_job_in)
        logger.info(f"Crawl job {db_crawl_job.id} created with status {db_crawl_job.status}")

        # Settings need to be passed as a dict to the background task
        settings_dict = crawl_job_in.settings.model_dump()

        background_tasks.add_task(process_crawl_job, db_crawl_job.id, settings_dict, SessionLocal)
        
        logger.info(f"Crawl job {db_crawl_job.id} added to background tasks.")
        return db_crawl_job
    except Exception as e:
        logger.error(f"Error creating crawl job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create crawl job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=schemas.CrawlJobSchema)
async def get_specific_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)): # Renamed
    """
    Get details of a specific crawl job.
    """
    db_crawl_job = crud.get_crawl_job(db=db, job_id=job_id)
    if db_crawl_job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return db_crawl_job

@router.get("/jobs", response_model=List[schemas.CrawlJobSchema])
async def list_all_crawl_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): # Renamed
    """
    List all crawl jobs.
    """
    crawl_jobs = crud.get_crawl_jobs(db=db, skip=skip, limit=limit)
    return crawl_jobs

@router.get("/results/downloaded", response_model=List[schemas.DownloadedFileSchema])
async def list_all_downloaded_files( # Renamed
    job_id: Optional[uuid.UUID] = None, # Query parameter for filtering by job_id
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    List all downloaded files, optionally filtered by a specific job_id.
    """
    logger.debug(f"Listing downloaded files. Job ID: {job_id}, Skip: {skip}, Limit: {limit}")
    if job_id:
        files = crud.get_downloaded_files_by_job(db=db, job_id=job_id, skip=skip, limit=limit)
    else:
        files = crud.get_downloaded_files(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(files)} downloaded file records.")
    return files


# Placeholder for DELETE endpoint, actual file deletion on disk is not handled by CRUD
# This would need a corresponding service in file_handler.py and more logic.
@router.delete("/results/downloaded/{file_id}", status_code=204)
async def delete_single_downloaded_file_record( # Renamed
    file_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Deletes the database record for a specific downloaded file.
    NOTE: This does NOT delete the physical file from disk.
    """
    logger.info(f"Request to delete downloaded file record with ID: {file_id}")
    db_file = crud.get_downloaded_file(db=db, file_id=file_id)
    if db_file is None:
        logger.warning(f"Downloaded file record not found for deletion: {file_id}")
        raise HTTPException(status_code=404, detail="Downloaded file record not found.")
    
    # Store local_path before deleting DB record if physical deletion is intended later
    # local_file_path_to_delete = db_file.local_path 

    deleted_file_record = crud.delete_downloaded_file(db=db, file_id=file_id)
    if deleted_file_record:
        logger.info(f"Successfully deleted downloaded file record from DB: {file_id}")
        # If physical file deletion is desired, trigger it here:
        # if local_file_path_to_delete:
        #   from breachwatch.storage.file_handler import delete_physical_file
        #   if delete_physical_file(local_file_path_to_delete):
        #       logger.info(f"Successfully deleted physical file: {local_file_path_to_delete}")
        #   else:
        #       logger.warning(f"Failed to delete physical file or file not found: {local_file_path_to_delete}")
        return # Returns 204 No Content on success
    else:
        # This case should ideally be caught by the check above, but as a safeguard:
        logger.error(f"Deletion of file record {file_id} reported as unsuccessful by CRUD, but should have been found.")
        raise HTTPException(status_code=500, detail="Error deleting file record.")


# The "/trigger" endpoint was conceptual and its functionality is now covered by POST /jobs
# So, it can be removed or kept if a distinct "quick trigger" functionality is needed later.
# For now, let's comment it out to avoid confusion.
# @router.post("/trigger", summary="Trigger a new crawl with specific settings (conceptual)")
# async def trigger_custom_crawl(
#     settings: schemas.CrawlSettingsSchema = Body(...), 
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """
#     Conceptual: Trigger a new crawl with custom settings.
#     This would create a new CrawlJob.
#     """
#     crawl_job_in = schemas.CrawlJobCreateSchema(settings=settings, name=f"Custom Crawl - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
#     db_crawl_job = crud.create_crawl_job(db=db, crawl_job_in=crawl_job_in)
#     background_tasks.add_task(process_crawl_job, db_crawl_job.id, crawl_job_in.settings.model_dump(), SessionLocal)
#     return {"message": "Custom crawl job started", "job_id": db_crawl_job.id}

