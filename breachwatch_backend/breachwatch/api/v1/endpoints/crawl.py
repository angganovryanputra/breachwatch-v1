import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body, Response, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import asyncio
from fastapi_cache.decorator import cache # Import cache decorator

from breachwatch.api.v1 import schemas
from breachwatch.storage.database import get_db, SessionLocal
from breachwatch.storage import crud, models # Import models
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
        db.commit() # Commit status change before starting long process

        crawler = MasterCrawler(job_id=job_id, crawl_settings=settings_schema, db=db)
        active_crawlers[job_id] = crawler

        files_processed_count = 0
        initial_urls_found_by_crawler = False # Track if crawler found URLs from seeds/dorks
        async for downloaded_file_schema in crawler.start_crawling():
            if downloaded_file_schema:
                files_processed_count +=1
                logger.info(f"Job {job_id} processed and stored: {downloaded_file_schema.file_url} (ID: {downloaded_file_schema.id})")
            # Check if the crawler found initial URLs after start_crawling begins
            if crawler.initial_urls_found:
                initial_urls_found_by_crawler = True
            # Check for stop signal periodically within the loop if needed
            if await crawler._check_if_stopped(): # Access internal check method (consider making it public if preferred)
                logger.info(f"process_crawl_job: Stop signal detected during crawling for job {job_id}.")
                break

        # Re-fetch job status after crawl attempt completes/stops
        job_final_status_obj = crud.get_crawl_job(db, job_id)
        final_status = "completed" # Default assumption if not stopped/failed

        # Only update if status wasn't externally set to failed/stopping during the run
        if job_final_status_obj and job_final_status_obj.status == "running":
            if files_processed_count == 0 and not initial_urls_found_by_crawler: # Check if crawler found any initial URLs and processed files
                 final_status = "completed_empty"
            # Set to completed if files were processed or initial URLs were found but no files matched
            elif files_processed_count > 0 or initial_urls_found_by_crawler:
                 final_status = "completed"
            else: # Should not happen if status was running, but as fallback
                 final_status = "failed" # Consider it failed if it was running but found nothing AND processed nothing.

        elif job_final_status_obj: # Status was already changed (e.g., 'failed' or 'stopping')
            final_status = job_final_status_obj.status # Keep the existing status (like 'stopping' or 'failed')
            logger.info(f"Job {job_id} status was already {final_status} before final update.")
        else:
             logger.error(f"Job {job_id} object not found in DB at the end of processing. Cannot update final status.")
             final_status = "unknown" # Mark as unknown if object vanished

        next_run = None
        if job_final_status_obj and job_final_status_obj.settings_schedule_type == "recurring" and job_final_status_obj.settings_schedule_cron_expression:
            # Reschedule only if completed successfully
            if final_status in ["completed", "completed_empty"]:
                try:
                    from croniter import croniter # type: ignore
                    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # type: ignore

                    tz_str = job_final_status_obj.settings_schedule_timezone or 'UTC'
                    try:
                        tz = ZoneInfo(tz_str)
                    except ZoneInfoNotFoundError:
                        logger.warning(f"Invalid timezone '{tz_str}' for job {job_id}. Defaulting to UTC.")
                        tz = ZoneInfo('UTC')

                    # Use last_run_at if available, otherwise use updated_at as base
                    base_time = job_final_status_obj.last_run_at or job_final_status_obj.updated_at
                    if not base_time: # Fallback if somehow both are None
                        base_time = datetime.now(timezone.utc)
                    base_time = base_time.astimezone(tz) # Ensure correct timezone for calculation

                    iter = croniter(job_final_status_obj.settings_schedule_cron_expression, base_time)
                    next_run_local = iter.get_next(datetime)
                    # Convert back to UTC for storage
                    next_run = next_run_local.astimezone(timezone.utc)
                    final_status = "scheduled" # Reschedule it
                    logger.info(f"Job {job_id} is recurring. Calculated next run: {next_run} UTC.")
                except ImportError:
                    logger.error("croniter library not installed. Cannot calculate next run time for recurring jobs. Please install with 'pip install croniter'.")
                    final_status = "failed" # Fail if cannot schedule next run
                except Exception as e:
                     logger.error(f"Error calculating next run time for job {job_id} with cron '{job_final_status_obj.settings_schedule_cron_expression}': {e}", exc_info=True)
                     final_status = "failed" # Fail if calculation fails
            else:
                # If recurring job failed or stopped, don't reschedule automatically
                logger.info(f"Recurring job {job_id} finished with status {final_status}. Not rescheduling.")
                # Keep final_status as failed/stopping etc.

        # Update job status in DB only if it's not 'unknown'
        if final_status != "unknown":
            crud.update_crawl_job_status(db=db, job_id=job_id, status=final_status, next_run_at=next_run)
            db.commit() # Commit the final status update
            logger.info(f"Crawl job {job_id} processing finished. Final status set to: {final_status}. Files processed: {files_processed_count}")
        else:
            logger.error(f"Final status for job {job_id} is 'unknown'. Skipping final DB update.")


    except Exception as e:
        logger.error(f"Error during background crawl job {job_id}: {e}", exc_info=True)
        try:
            # Attempt to mark as failed on error
            crud.update_crawl_job_status(db=db, job_id=job_id, status="failed")
            db.commit()
        except Exception as db_e:
            logger.error(f"Failed to update job status to 'failed' for job {job_id} after error: {db_e}", exc_info=True)
            db.rollback() # Rollback if update fails
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
            crawl_job_in.name = f"Crawl Job - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"

        db_crawl_job = crud.create_crawl_job(db=db, crawl_job_in=crawl_job_in)
        logger.info(f"Crawl job {db_crawl_job.id} created with status {db_crawl_job.status}")

        # If the job is not scheduled (i.e., status is 'pending' for immediate run), add to background tasks.
        # Scheduled jobs will be picked up by a separate scheduler mechanism (not implemented here).
        if db_crawl_job.status == "pending":
            settings_dict = crawl_job_in.settings.model_dump(mode='json') # Ensure proper serialization

            # Convert date/time in schedule if present
            if 'schedule' in settings_dict and settings_dict['schedule']:
                 if 'run_at' in settings_dict['schedule'] and settings_dict['schedule']['run_at']:
                      # Assuming run_at is already a datetime object in the Pydantic model
                      # Convert to ISO string for background task serialization
                      dt_obj = getattr(crawl_job_in.settings.schedule, 'run_at', None)
                      if isinstance(dt_obj, datetime):
                          settings_dict['schedule']['run_at'] = dt_obj.isoformat()
                      else: # If it's already a string, keep it; otherwise, handle unexpected type
                           logger.warning(f"Unexpected type for run_at in settings_dict: {type(dt_obj)}")
                           settings_dict['schedule']['run_at'] = str(dt_obj) if dt_obj else None


            background_tasks.add_task(process_crawl_job, db_crawl_job.id, settings_dict, SessionLocal)
            logger.info(f"Immediate crawl job {db_crawl_job.id} added to background tasks.")
        elif db_crawl_job.status == "scheduled":
             logger.info(f"Crawl job {db_crawl_job.id} is scheduled. Next run: {db_crawl_job.next_run_at}. It will be processed by the scheduler.")

        # Fetch again to include potential relationship data if needed by the schema
        db_crawl_job_with_summary = crud.get_crawl_job(db, db_crawl_job.id)
        return db_crawl_job_with_summary
    except Exception as e:
        logger.error(f"Error creating crawl job: {e}", exc_info=True)
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create crawl job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=schemas.CrawlJobSchema)
@cache(expire=60) # Cache for 60 seconds
async def get_specific_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    db_crawl_job = crud.get_crawl_job(db=db, job_id=job_id)
    if db_crawl_job is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found")

    # Manually construct the response schema to ensure downloaded_files summary is calculated
    # This might be redundant if the Pydantic model with Config.from_attributes handles it correctly via the property
    # job_data = schemas.CrawlJobSchema.from_orm(db_crawl_job) # Requires Config.orm_mode=True or from_attributes=True
    # job_data.results_summary = {"files_found": len(db_crawl_job.downloaded_files)} # Explicitly set if needed

    return db_crawl_job # Return the ORM model directly, Pydantic handles conversion

@router.get("/jobs", response_model=List[schemas.CrawlJobSchema])
@cache(expire=60) # Cache job list for 60 seconds
async def list_all_crawl_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    crawl_jobs = crud.get_crawl_jobs(db=db, skip=skip, limit=limit)
    # Ensure summary is calculated for each job (Pydantic should handle this with relationship loading)
    return crawl_jobs


@router.delete("/jobs/{job_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_crawl_job_endpoint(job_id: uuid.UUID, db: Session = Depends(get_db)):
    logger.info(f"Request to delete crawl job with ID: {job_id}")

    if job_id in active_crawlers:
        crawler_instance = active_crawlers[job_id]
        logger.info(f"Job {job_id} is active. Attempting to stop crawler before deletion.")
        await crawler_instance.stop_crawler() # This will also update job status to 'stopping' or 'failed'
        # Give a moment for the crawler to acknowledge stop. Consider more robust waiting if needed.
        await asyncio.sleep(2)

    # Fetch the job details including file paths *before* deleting the job record
    deleted_job_model, local_file_paths = crud.delete_crawl_job_and_get_file_paths(db=db, job_id=job_id)

    if deleted_job_model is None:
        logger.warning(f"Crawl job not found for deletion: {job_id}")
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Crawl job not found.")

    # Now delete the associated physical directory after DB deletion is confirmed
    if delete_job_directory(job_id):
        logger.info(f"Successfully deleted download directory for job {job_id}")
    else:
        logger.warning(f"Failed to delete download directory for job {job_id}, or directory didn't exist.")

    logger.info(f"Successfully deleted crawl job {job_id} and its associated DB records.")
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

    new_status = "stopping" # Target status

    if job_id in active_crawlers:
        crawler_instance = active_crawlers[job_id]
        # Set DB status first before signaling crawler
        crud.update_crawl_job_status(db=db, job_id=job_id, status=new_status)
        db.commit()
        await crawler_instance.stop_crawler()
        logger.info(f"Stop signal sent to active crawler for job {job_id} and DB status updated to '{new_status}'.")
        return schemas.MessageResponseSchema(message=f"Stop signal sent to crawl job {job_id}. It may take a moment to fully stop.")
    else:
        # If crawler isn't active (e.g., task finished, server restarted, or job is scheduled/pending but not yet in active_crawlers)
        # Update DB status directly to prevent execution or indicate cancellation.
        # Use 'failed' as the terminal state for cancelled pending/scheduled jobs.
        if job.status == "pending" or job.status == "scheduled":
            new_status = "failed" # Indicate it was cancelled before running
            crud.update_crawl_job_status(db=db, job_id=job_id, status=new_status)
            db.commit()
            logger.info(f"Job {job_id} was {job.status} and not active. Status set to '{new_status}' in DB to prevent execution.")
            return schemas.MessageResponseSchema(message=f"Crawl job {job_id} status set to '{new_status}'. It will not run.")
        else:
             # If job status is something else (e.g., completed, failed already), don't change it.
             logger.info(f"Job {job_id} not active and status is '{job.status}'. No action taken.")
             return schemas.MessageResponseSchema(message=f"Job {job_id} is not currently running or stoppable (status: {job.status}).")


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
    if job.status == "pending":
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Job {job_id} is already pending execution.")
    if job_id in active_crawlers:
         raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Job {job_id} is already in active crawlers list (likely about to run or running).")

    # Prepare settings from the stored job
    schedule_data = None
    if job.settings_schedule_type:
        schedule_data = schemas.ScheduleSchema(
            type=job.settings_schedule_type,
            cron_expression=job.settings_schedule_cron_expression,
            # Convert stored datetime back to datetime object if needed, assuming UTC storage
            run_at=job.settings_schedule_run_at if job.settings_schedule_run_at else None,
            timezone=job.settings_schedule_timezone
        )

    job_settings_schema = schemas.CrawlSettingsSchema(
        keywords=job.settings_keywords or [], # Ensure lists are not None
        file_extensions=job.settings_file_extensions or [],
        # Convert HttpUrl fields back to strings if needed for Pydantic model init
        seed_urls=job.settings_seed_urls or [], # Assuming stored as list of strings
        search_dorks=job.settings_search_dorks or [],
        crawl_depth=job.settings_crawl_depth,
        respect_robots_txt=job.settings_respect_robots_txt,
        request_delay_seconds=job.settings_request_delay_seconds,
        use_search_engines=job.settings_use_search_engines,
        max_results_per_dork=job.settings_max_results_per_dork,
        max_concurrent_requests_per_domain=job.settings_max_concurrent_requests_per_domain,
        custom_user_agent=job.settings_custom_user_agent,
        schedule=None # Manual run ignores original schedule for this instance, set to None explicitly
    )
    settings_dict = job_settings_schema.model_dump(mode='json') # Use mode='json' for proper serialization

    # Set job status to pending before adding to task queue
    crud.update_crawl_job_status(db=db, job_id=job.id, status="pending", next_run_at=None) # Clear next_run_at for manual run
    db.commit() # Commit status change

    # Schedule the job execution in the background
    background_tasks.add_task(process_crawl_job, job.id, settings_dict, SessionLocal)
    logger.info(f"Manual run for job {job.id} added to background tasks with status 'pending'.")

    # Fetch again to show updated status (it will be pending initially)
    updated_job = crud.get_crawl_job(db, job.id)
    return updated_job


@router.post("/jobs/{job_id}/pause", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_501_NOT_IMPLEMENTED)
async def pause_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    raise HTTPException(status_code=http_status.HTTP_501_NOT_IMPLEMENTED, detail="Pausing jobs is not yet implemented.")

@router.post("/jobs/{job_id}/resume", response_model=schemas.MessageResponseSchema, status_code=http_status.HTTP_501_NOT_IMPLEMENTED)
async def resume_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    raise HTTPException(status_code=http_status.HTTP_501_NOT_IMPLEMENTED, detail="Resuming jobs is not yet implemented.")


@router.get("/results/downloaded", response_model=List[schemas.DownloadedFileSchema])
@cache(expire=60) # Cache results for 60 seconds
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
        db.commit() # Commit deletion of the record
        logger.info(f"Successfully deleted downloaded file record from DB: {file_id}")
        if delete_physical and local_file_path_to_delete:
          if delete_physical_file(local_file_path_to_delete):
              logger.info(f"Successfully deleted physical file: {local_file_path_to_delete}")
          else:
              # Log warning but don't raise error, DB record deletion was the primary goal
              logger.warning(f"Failed to delete physical file or file not found: {local_file_path_to_delete} (DB record was still deleted).")
        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
    else:
        # This case should technically not be reached if get_downloaded_file found it,
        # but handle defensively.
        db.rollback() # Rollback if deletion failed for some reason
        logger.error(f"Deletion of file record {file_id} reported as unsuccessful by CRUD, but should have been found earlier.")
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting file record from DB.")

# Import asyncio for the sleep in delete_crawl_job_endpoint
