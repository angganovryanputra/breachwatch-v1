import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Response, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional 
import uuid
from datetime import datetime 

from breachwatch.api.v1 import schemas
from breachwatch.storage.database import get_db, SessionLocal 
from breachwatch.storage import crud
from breachwatch.storage.file_handler import delete_physical_file, delete_job_directory
from breachwatch.core.crawler import MasterCrawler 

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for crawler instances (simplified for BackgroundTasks)
# In a distributed setup, this would need a more robust mechanism (e.g., Celery task IDs and control)
active_crawlers: dict[uuid.UUID, MasterCrawler] = {}


async def process_crawl_job(job_id: uuid.UUID, settings_data: dict, db_session_maker):
    """
    Background task runner for a crawl job.
    """
    db: Session = db_session_maker()
    crawler = None
    try:
        logger.info(f"process_crawl_job: Starting for job_id {job_id}")
        settings_schema = schemas.CrawlSettingsSchema(**settings_data)
        logger.debug(f"process_crawl_job: Parsed settings: {settings_schema}")
        
        crawler = MasterCrawler(job_id=job_id, crawl_settings=settings_schema, db=db)
        active_crawlers[job_id] = crawler # Store instance
        
        async for downloaded_file_schema in crawler.start_crawling():
            if downloaded_file_schema:
                logger.info(f"Job {job_id} processed and stored: {downloaded_file_schema.file_url} (ID: {downloaded_file_schema.id})")
            else:
                logger.debug(f"Job {job_id} yielded a None value from crawler (possibly end or empty iteration).")
        
        # If crawler finished without being stopped, status is 'completed' or 'completed_empty'
        # If it was stopped, start_crawling should handle setting to 'failed' or 'stopped'
        job_final_status = crud.get_crawl_job(db, job_id)
        if job_final_status and job_final_status.status not in ["failed", "stopping", "completed_empty"]: # if not already set to a final state by crawler
             crud.update_crawl_job_status(db=db, job_id=job_id, status="completed")

        logger.info(f"Crawl job {job_id} fully processed by MasterCrawler or stopped.")

    except Exception as e:
        logger.error(f"Error during background crawl job {job_id}: {e}", exc_info=True)
        try:
            crud.update_crawl_job_status(db=db, job_id=job_id, status="failed")
        except Exception as db_e:
            logger.error(f"Failed to update job status to 'failed' for job {job_id} after error: {db_e}", exc_info=True)
    finally:
        if job_id in active_crawlers:
            del active_crawlers[job_id] # Clean up
        db.close()
        logger.info(f"process_crawl_job: DB session closed for job_id {job_id}")


@router.post("/jobs", response_model=schemas.CrawlJobSchema, status_code=http_status.HTTP_202_ACCEPTED)
async def create_new_crawl_job( 
    crawl_job_in: schemas.CrawlJobCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    logger.info(f"Received request to create new crawl job: {crawl_job_in.name}")
    try:
        if not crawl_job_in.name:
            crawl_job_in.name = f"Crawl Job - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        db_crawl_job = crud.create_crawl_job(db=db, crawl_job_in=crawl_job_in)
        logger.info(f"Crawl job {db_crawl_job.id} created with status {db_crawl_job.status}")

        settings_dict = crawl_job_in.settings.model_dump()
        background_tasks.add_task(process_crawl_job, db_crawl_job.id, settings_dict, SessionLocal)
        
        logger.info(f"Crawl job {db_crawl_job.id} added to background tasks.")
        # Re-fetch to ensure relationships are loaded for schema conversion
        db_crawl_job_with_summary = crud.get_crawl_job(db, db_crawl_job.id)
        return db_crawl_job_with_summary
    except Exception as e:
        logger.error(f"Error creating crawl job: {e}", exc_info=True)
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create crawl job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=schemas.CrawlJobSchema)
async def get_specific_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)): 
    db_crawl_job = crud.get_crawl_job(db=db, job_id=job_id)
    if db_crawl_job is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found")
    # The schema will handle generating results_summary from the loaded downloaded_files
    return db_crawl_job

@router.get("/jobs", response_model=List[schemas.CrawlJobSchema])
async def list_all_crawl_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
    crawl_jobs = crud.get_crawl_jobs(db=db, skip=skip, limit=limit)
    # The schema will handle generating results_summary for each job
    return crawl_jobs


@router.delete("/jobs/{job_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_crawl_job_endpoint(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Deletes a crawl job, its associated database records for downloaded files,
    and the physical files and directory for that job.
    """
    logger.info(f"Request to delete crawl job with ID: {job_id}")

    # First, stop the crawler if it's running
    if job_id in active_crawlers:
        crawler_instance = active_crawlers[job_id]
        logger.info(f"Job {job_id} is active. Attempting to stop crawler before deletion.")
        await crawler_instance.stop_crawler()
        # Give a moment for the crawler to acknowledge stop.
        # In a real system, you might wait for the background task to exit or status to change.
        await asyncio.sleep(2) # Simplified wait

    # Delete DB records and get file paths
    deleted_job_model, physical_file_paths = crud.delete_crawl_job_and_get_file_paths(db=db, job_id=job_id)

    if deleted_job_model is None:
        logger.warning(f"Crawl job not found for deletion: {job_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")

    # Delete physical files (this is now redundant if we delete the whole directory)
    # for file_path in physical_file_paths:
    #     if delete_physical_file(file_path):
    #         logger.info(f"Successfully deleted physical file: {file_path} for job {job_id}")
    #     else:
    #         logger.warning(f"Failed to delete physical file or file not found: {file_path} for job {job_id}")
    
    # Delete the job's entire download directory
    if delete_job_directory(job_id):
        logger.info(f"Successfully deleted download directory for job {job_id}")
    else:
        logger.warning(f"Failed to delete download directory for job {job_id}, or directory didn't exist.")

    logger.info(f"Successfully deleted crawl job {job_id} and its associated data.")
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@router.post("/jobs/{job_id}/stop", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_200_OK)
async def stop_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Signals a running crawl job to stop gracefully."""
    logger.info(f"Received request to stop crawl job: {job_id}")
    
    job = crud.get_crawl_job(db, job_id)
    if not job:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")

    if job.status not in ["running", "pending"]: # Can only stop running or pending jobs
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Job {job_id} is not in a stoppable state (current: {job.status}).")

    if job_id in active_crawlers:
        crawler_instance = active_crawlers[job_id]
        await crawler_instance.stop_crawler() # This also updates DB status to 'stopping'
        logger.info(f"Stop signal sent to active crawler for job {job_id}.")
        return schemas.MessageResponseSchema(message=f"Stop signal sent to crawl job {job_id}. It may take a moment to fully stop.")
    else:
        # If crawler isn't in active_crawlers (e.g., task finished, or server restarted)
        # but DB status is 'running' or 'pending', update DB status directly.
        # The crawler, upon its next check or if it's about to start, should see this.
        crud.update_crawl_job_status(db=db, job_id=job_id, status="stopping")
        logger.info(f"Crawler for job {job_id} not in active memory. Status set to 'stopping' in DB.")
        return schemas.MessageResponseSchema(message=f"Crawl job {job_id} status set to 'stopping'. If it was running, it will attempt to stop.")


@router.post("/jobs/{job_id}/pause", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_501_NOT_IMPLEMENTED)
async def pause_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Placeholder for pausing a crawl job."""
    # Pausing is complex: would require crawler to save state and stop, then resume.
    # Not implemented in current MasterCrawler.
    raise HTTPException(status_code=http_status.HTTP_501_NOT_IMPLEMENTED, detail="Pausing jobs is not yet implemented.")

@router.post("/jobs/{job_id}/resume", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_501_NOT_IMPLEMENTED)
async def resume_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """Placeholder for resuming a paused crawl job."""
    # Resuming is complex, needs state restoration.
    # Not implemented.
    raise HTTPException(status_code=http_status.HTTP_501_NOT_IMPLEMENTED, detail="Resuming jobs is not yet implemented.")


@router.get("/results/downloaded", response_model=List[schemas.DownloadedFileSchema])
async def list_all_downloaded_files( 
    job_id: Optional[uuid.UUID] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    logger.debug(f"Listing downloaded files. Job ID: {job_id}, Skip: {skip}, Limit: {limit}")
    if job_id:
        files = crud.get_downloaded_files_by_job(db=db, job_id=job_id, skip=skip, limit=limit)
    else:
        files = crud.get_downloaded_files(db=db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(files)} downloaded file records.")
    return files


@router.delete("/results/downloaded/{file_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_single_downloaded_file_record( 
    file_id: uuid.UUID,
    delete_physical: bool = Body(False, embed=True), # Optional: query param to delete physical file
    db: Session = Depends(get_db)
):
    """
    Deletes the database record for a specific downloaded file.
    Optionally, also deletes the physical file from disk if `delete_physical` is true.
    """
    logger.info(f"Request to delete downloaded file record with ID: {file_id}. Delete physical: {delete_physical}")
    db_file = crud.get_downloaded_file(db=db, file_id=file_id)
    if db_file is None:
        logger.warning(f"Downloaded file record not found for deletion: {file_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Downloaded file record not found.")
    
    local_file_path_to_delete = db_file.local_path 

    deleted_file_record = crud.delete_downloaded_file(db=db, file_id=file_id) # Deletes DB record

    if deleted_file_record:
        logger.info(f"Successfully deleted downloaded file record from DB: {file_id}")
        if delete_physical and local_file_path_to_delete:
          if delete_physical_file(local_file_path_to_delete):
              logger.info(f"Successfully deleted physical file: {local_file_path_to_delete}")
          else:
              logger.warning(f"Failed to delete physical file or file not found: {local_file_path_to_delete} (DB record was still deleted).")
        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
    else:
        logger.error(f"Deletion of file record {file_id} reported as unsuccessful by CRUD, but should have been found.")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting file record from DB.")

# Import asyncio for the sleep in delete_crawl_job_endpoint
import asyncio
```