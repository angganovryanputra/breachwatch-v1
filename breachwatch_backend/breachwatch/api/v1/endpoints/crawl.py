import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Response, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional 
import uuid
from datetime import datetime, timezone
import asyncio

from breachwatch.api.v1 import schemas
from breachwatch.storage.database import get_db, SessionLocal 
from breachwatch.storage import crud
from breachwatch.storage.file_handler import delete_physical_file, delete_job_directory
from breachwatch.core.crawler import MasterCrawler 
# from breachwatch.core.scheduler_logic import calculate_next_run_time # Conceptual import

logger = logging.getLogger(__name__)
router = APIRouter()

active_crawlers: dict[uuid.UUID, MasterCrawler] = {}


async def process_crawl_job(job_id: uuid.UUID, settings_data: dict, db_session_maker):
    """
    Background task runner for a non-scheduled (immediate) crawl job.
    """
    db: Session = db_session_maker()
    crawler = None
    try:
        logger.info(f"process_crawl_job: Starting for job_id {job_id}")
        settings_schema = schemas.CrawlSettingsSchema(**settings_data)
        logger.debug(f"process_crawl_job: Parsed settings: {settings_schema}")
        
        crud.update_crawl_job_status(db=db, job_id=job_id, status="running", last_run_at=datetime.now(timezone.utc))

        crawler = MasterCrawler(job_id=job_id, crawl_settings=settings_schema, db=db)
        active_crawlers[job_id] = crawler 
        
        files_processed_count = 0
        async for downloaded_file_schema in crawler.start_crawling():
            if downloaded_file_schema:
                files_processed_count +=1
                logger.info(f"Job {job_id} processed and stored: {downloaded_file_schema.file_url} (ID: {downloaded_file_schema.id})")
            else:
                logger.debug(f"Job {job_id} yielded a None value from crawler (possibly end or empty iteration).")
        
        job_final_status_obj = crud.get_crawl_job(db, job_id)
        final_status = "completed"
        if job_final_status_obj and job_final_status_obj.status not in ["failed", "stopping"]:
            if files_processed_count == 0 and not crawler.initial_urls_found: # Check if crawler found any initial URLs
                 final_status = "completed_empty"
        elif job_final_status_obj: # Status was 'failed' or 'stopping'
            final_status = job_final_status_obj.status

        # If the job was recurring, calculate and set the next run time
        next_run = None
        if job_final_status_obj and job_final_status_obj.settings_schedule_type == "recurring" and job_final_status_obj.settings_schedule_cron_expression:
            # next_run = calculate_next_run_time(job_final_status_obj.settings_schedule_cron_expression, job_final_status_obj.settings_schedule_timezone)
            # final_status = "scheduled" # Reschedule it
            logger.info(f"Job {job_id} was recurring. Placeholder for rescheduling logic. Next run calculation needed.")
            # For now, if recurring and completed successfully, mark as 'scheduled' for scheduler to pick up
            if final_status in ["completed", "completed_empty"]:
                final_status = "scheduled" 
                # Actual next_run time would be set by a dedicated scheduler service or cron job manager.
                # For now, we'll leave it to be updated by such a service.
                # crud.update_crawl_job_status(db=db, job_id=job_id, status="scheduled", next_run_at=next_run_placeholder)

        
        crud.update_crawl_job_status(db=db, job_id=job_id, status=final_status, next_run_at=next_run)
        logger.info(f"Crawl job {job_id} processing finished. Final status: {final_status}. Files processed: {files_processed_count}")

    except Exception as e:
        logger.error(f"Error during background crawl job {job_id}: {e}", exc_info=True)
        try:
            crud.update_crawl_job_status(db=db, job_id=job_id, status="failed")
        except Exception as db_e:
            logger.error(f"Failed to update job status to 'failed' for job {job_id} after error: {db_e}", exc_info=True)
    finally:
        if job_id in active_crawlers:
            del active_crawlers[job_id] 
        if crawler and crawler.http_client: # Ensure client is closed
            await crawler.http_client.aclose()
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

        # If the job is not scheduled (i.e., status is 'pending' for immediate run), add to background tasks.
        # Scheduled jobs will be picked up by a separate scheduler mechanism (not implemented here).
        if db_crawl_job.status == "pending":
            settings_dict = crawl_job_in.settings.model_dump()
            background_tasks.add_task(process_crawl_job, db_crawl_job.id, settings_dict, SessionLocal)
            logger.info(f"Immediate crawl job {db_crawl_job.id} added to background tasks.")
        elif db_crawl_job.status == "scheduled":
             logger.info(f"Crawl job {db_crawl_job.id} is scheduled. Next run: {db_crawl_job.next_run_at}. It will be processed by the scheduler.")
        
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
    return db_crawl_job

@router.get("/jobs", response_model=List[schemas.CrawlJobSchema])
async def list_all_crawl_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)): 
    crawl_jobs = crud.get_crawl_jobs(db=db, skip=skip, limit=limit)
    return crawl_jobs


@router.delete("/jobs/{job_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_crawl_job_endpoint(job_id: uuid.UUID, db: Session = Depends(get_db)):
    logger.info(f"Request to delete crawl job with ID: {job_id}")

    if job_id in active_crawlers:
        crawler_instance = active_crawlers[job_id]
        logger.info(f"Job {job_id} is active. Attempting to stop crawler before deletion.")
        await crawler_instance.stop_crawler() # This will also update job status to 'stopping' or 'failed'
        # Give a moment for the crawler to acknowledge stop.
        await asyncio.sleep(2) 

    deleted_job_model, _ = crud.delete_crawl_job_and_get_file_paths(db=db, job_id=job_id)

    if deleted_job_model is None:
        logger.warning(f"Crawl job not found for deletion: {job_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")
    
    if delete_job_directory(job_id):
        logger.info(f"Successfully deleted download directory for job {job_id}")
    else:
        logger.warning(f"Failed to delete download directory for job {job_id}, or directory didn't exist.")

    logger.info(f"Successfully deleted crawl job {job_id} and its associated data.")
    return Response(status_code=http_status.HTTP_204_NO_CONTENT)


@router.post("/jobs/{job_id}/stop", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_200_OK)
async def stop_crawl_job_endpoint(job_id: uuid.UUID, db: Session = Depends(get_db)):
    logger.info(f"Received request to stop crawl job: {job_id}")
    
    job = crud.get_crawl_job(db, job_id)
    if not job:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")

    # Can stop running, pending, or even scheduled jobs (to prevent them from running)
    if job.status not in ["running", "pending", "scheduled"]: 
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Job {job_id} is not in a stoppable state (current: {job.status}).")

    if job_id in active_crawlers:
        crawler_instance = active_crawlers[job_id]
        await crawler_instance.stop_crawler() 
        logger.info(f"Stop signal sent to active crawler for job {job_id}.")
        return schemas.MessageResponseSchema(message=f"Stop signal sent to crawl job {job_id}. It may take a moment to fully stop.")
    else:
        # If crawler isn't active (e.g., task finished, server restarted, or job is scheduled/pending but not yet in active_crawlers)
        # Update DB status to 'failed' (or a specific 'cancelled_scheduled' status if it was scheduled)
        # This ensures it won't be picked up by a scheduler or run if pending.
        new_status = "failed" if job.status in ["running", "pending"] else "failed" # or a 'cancelled' status
        crud.update_crawl_job_status(db=db, job_id=job_id, status=new_status)
        logger.info(f"Crawler for job {job_id} not in active memory. Status set to '{new_status}' in DB to prevent execution.")
        return schemas.MessageResponseSchema(message=f"Crawl job {job_id} status set to '{new_status}'. If it was scheduled or pending, it will not run.")

@router.post("/jobs/{job_id}/run", response_model=schemas.CrawlJobSchema, status_code=http_status.HTTP_202_ACCEPTED)
async def manually_run_job(
    job_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Manually triggers a job to run, regardless of its schedule.
    Useful for re-running failed/completed jobs or forcing a scheduled job.
    """
    logger.info(f"Received request to manually run job: {job_id}")
    job = crud.get_crawl_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found")

    if job.status == "running":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Job {job_id} is already running.")
    
    if job_id in active_crawlers:
         raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Job {job_id} is already in active crawlers list (likely about to run or running).")

    # Prepare settings from the stored job
    job_settings_schema = schemas.CrawlSettingsSchema(
        keywords=job.settings_keywords,
        file_extensions=job.settings_file_extensions,
        seed_urls=job.settings_seed_urls, # These are already strings
        search_dorks=job.settings_search_dorks,
        crawl_depth=job.settings_crawl_depth,
        respect_robots_txt=job.settings_respect_robots_txt,
        request_delay_seconds=job.settings_request_delay_seconds,
        use_search_engines=job.settings_use_search_engines,
        max_results_per_dork=job.settings_max_results_per_dork,
        max_concurrent_requests_per_domain=job.settings_max_concurrent_requests_per_domain,
        custom_user_agent=job.settings_custom_user_agent,
        schedule=None # Manual run ignores original schedule for this instance
    )
    settings_dict = job_settings_schema.model_dump()
    
    # crud.update_crawl_job_status(db=db, job_id=job.id, status="pending") # Set to pending before adding to task
    background_tasks.add_task(process_crawl_job, job.id, settings_dict, SessionLocal)
    logger.info(f"Manual run for job {job.id} added to background tasks.")
    
    # Fetch again to show updated status (process_crawl_job will set it to running)
    updated_job = crud.get_crawl_job(db, job.id)
    return updated_job


@router.post("/jobs/{job_id}/pause", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_501_NOT_IMPLEMENTED)
async def pause_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    raise HTTPException(status_code=http_status.HTTP_501_NOT_IMPLEMENTED, detail="Pausing jobs is not yet implemented.")

@router.post("/jobs/{job_id}/resume", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_501_NOT_IMPLEMENTED)
async def resume_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
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
    delete_physical: bool = Body(False, embed=True), 
    db: Session = Depends(get_db)
):
    logger.info(f"Request to delete downloaded file record with ID: {file_id}. Delete physical: {delete_physical}")
    db_file = crud.get_downloaded_file(db=db, file_id=file_id)
    if db_file is None:
        logger.warning(f"Downloaded file record not found for deletion: {file_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Downloaded file record not found.")
    
    local_file_path_to_delete = db_file.local_path 

    deleted_file_record = crud.delete_downloaded_file(db=db, file_id=file_id) 

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
