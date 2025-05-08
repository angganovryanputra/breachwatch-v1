import logging
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Tuple
import uuid
from datetime import datetime

from . import models
from breachwatch.api.v1 import schemas # For Pydantic schemas

logger = logging.getLogger(__name__)

# --- CrawlJob CRUD ---

def get_crawl_job(db: Session, job_id: uuid.UUID) -> Optional[models.CrawlJob]:
    """Fetches a single crawl job, eagerly loading its downloaded_files for summary."""
    job = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files)
    ).filter(models.CrawlJob.id == job_id).first()
    
    # Pydantic schema will derive results_summary from loaded downloaded_files
    return job


def get_crawl_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[models.CrawlJob]:
    """Fetches a list of crawl jobs, eagerly loading downloaded_files for summary."""
    jobs = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files) 
    ).order_by(models.CrawlJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


def create_crawl_job(db: Session, crawl_job_in: schemas.CrawlJobCreateSchema) -> models.CrawlJob:
    settings = crawl_job_in.settings
    
    initial_status = "pending"
    next_run_time_for_job = None

    if settings.schedule:
        initial_status = "scheduled"
        if settings.schedule.type == "one-time" and settings.schedule.run_at:
            next_run_time_for_job = settings.schedule.run_at
        elif settings.schedule.type == "recurring" and settings.schedule.cron_expression:
            # Placeholder for CRON parsing and next run time calculation
            # This would typically involve a library like `croniter`
            # For now, we'll set it to a future time or leave it to a scheduler service to update
            # from croniter import croniter
            # from datetime import datetime, timezone
            # try:
            #     iter = croniter(settings.schedule.cron_expression, datetime.now(timezone.utc))
            #     next_run_time_for_job = iter.get_next(datetime)
            # except Exception as e:
            #     logger.error(f"Could not calculate next run time for cron '{settings.schedule.cron_expression}': {e}")
            #     initial_status = "failed" # Or handle error differently
            logger.warning(f"Recurring job created with cron '{settings.schedule.cron_expression}'. Next run time calculation needs robust implementation.")
            # For now, as a placeholder, let's assume a scheduler will pick it up based on cron.
            # Or, if one-time, `run_at` is already a datetime.

    db_crawl_job = models.CrawlJob(
        name=crawl_job_in.name,
        status=initial_status,
        settings_keywords=settings.keywords,
        settings_file_extensions=settings.file_extensions,
        settings_seed_urls=[str(url) for url in settings.seed_urls],
        settings_search_dorks=settings.search_dorks,
        settings_crawl_depth=settings.crawl_depth,
        settings_respect_robots_txt=settings.respect_robots_txt,
        settings_request_delay_seconds=settings.request_delay_seconds,
        settings_use_search_engines=settings.use_search_engines,
        settings_max_results_per_dork=settings.max_results_per_dork,
        settings_max_concurrent_requests_per_domain=settings.max_concurrent_requests_per_domain,
        settings_custom_user_agent=settings.custom_user_agent,
        settings_schedule_type=settings.schedule.type if settings.schedule else None,
        settings_schedule_cron_expression=settings.schedule.cron_expression if settings.schedule else None,
        settings_schedule_run_at=settings.schedule.run_at if settings.schedule else None,
        settings_schedule_timezone=settings.schedule.timezone if settings.schedule else None,
        next_run_at=next_run_time_for_job,
        last_run_at=None
    )
    db.add(db_crawl_job)
    db.commit()
    db.refresh(db_crawl_job) 
    db.refresh(db_crawl_job, attribute_names=['downloaded_files'])
    logger.info(f"CrawlJob created in DB: ID {db_crawl_job.id}, Name: {db_crawl_job.name}, Status: {db_crawl_job.status}")
    return db_crawl_job

def update_crawl_job_status(db: Session, job_id: uuid.UUID, status: str, next_run_at: Optional[datetime] = None, last_run_at: Optional[datetime] = None) -> Optional[models.CrawlJob]:
    db_crawl_job = get_crawl_job(db, job_id) 
    if db_crawl_job:
        db_crawl_job.status = status
        db_crawl_job.updated_at = datetime.utcnow() 
        if next_run_at is not None: # Explicitly check for None to allow clearing
            db_crawl_job.next_run_at = next_run_at
        if last_run_at:
            db_crawl_job.last_run_at = last_run_at
        
        db.commit()
        db.refresh(db_crawl_job)
        db.refresh(db_crawl_job, attribute_names=['downloaded_files']) 
        logger.info(f"CrawlJob {job_id} status updated to: {status}")
    return db_crawl_job

def delete_crawl_job_and_get_file_paths(db: Session, job_id: uuid.UUID) -> Tuple[Optional[models.CrawlJob], List[str]]:
    """Deletes a crawl job and its associated DownloadedFile records.
    Returns the deleted job object (or None) and a list of local_paths of its files."""
    db_crawl_job = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files).load_only(models.DownloadedFile.local_path)
    ).filter(models.CrawlJob.id == job_id).first()

    if db_crawl_job:
        local_file_paths = [
            file.local_path for file in db_crawl_job.downloaded_files if file.local_path
        ]
        
        db.delete(db_crawl_job)
        db.commit()
        logger.info(f"CrawlJob {job_id} and its DB file records deleted.")
        return db_crawl_job, local_file_paths
    return None, []


# --- DownloadedFile CRUD ---

def get_downloaded_file(db: Session, file_id: uuid.UUID) -> Optional[models.DownloadedFile]:
    return db.query(models.DownloadedFile).filter(models.DownloadedFile.id == file_id).first()

def get_downloaded_files(db: Session, skip: int = 0, limit: int = 100) -> List[models.DownloadedFile]:
    return db.query(models.DownloadedFile).order_by(models.DownloadedFile.downloaded_at.desc()).offset(skip).limit(limit).all()

def get_downloaded_files_by_job(db: Session, job_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.DownloadedFile]:
    return db.query(models.DownloadedFile).filter(models.DownloadedFile.crawl_job_id == job_id).order_by(models.DownloadedFile.downloaded_at.desc()).offset(skip).limit(limit).all()

def create_downloaded_file(db: Session, downloaded_file: schemas.DownloadedFileSchema) -> models.DownloadedFile:
    db_downloaded_file = models.DownloadedFile(
        id=downloaded_file.id, 
        source_url=str(downloaded_file.source_url),
        file_url=str(downloaded_file.file_url),
        file_type=downloaded_file.file_type,
        keywords_found=downloaded_file.keywords_found,
        downloaded_at=downloaded_file.downloaded_at,
        local_path=downloaded_file.local_path,
        file_size_bytes=downloaded_file.file_size_bytes,
        checksum_md5=downloaded_file.checksum_md5,
        crawl_job_id=downloaded_file.crawl_job_id,
        date_found=downloaded_file.date_found 
    )
    db.add(db_downloaded_file)
    db.commit()
    db.refresh(db_downloaded_file)
    logger.info(f"DownloadedFile created in DB: ID {db_downloaded_file.id}, URL: {db_downloaded_file.file_url}")
    return db_downloaded_file

def delete_downloaded_file(db: Session, file_id: uuid.UUID) -> Optional[models.DownloadedFile]:
    db_file = get_downloaded_file(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
        logger.info(f"DownloadedFile record {file_id} deleted from DB.")
    return db_file

# --- Scheduled Job Specific CRUD (Conceptual) ---
def get_due_scheduled_jobs(db: Session, now_utc: Optional[datetime] = None) -> List[models.CrawlJob]:
    """Fetches scheduled jobs whose next_run_at is due."""
    if now_utc is None:
        now_utc = datetime.now(uuid.uuid1().node) # Simplistic UTC now, better to pass from scheduler
    
    return db.query(models.CrawlJob).filter(
        models.CrawlJob.status == "scheduled",
        models.CrawlJob.next_run_at <= now_utc
    ).order_by(models.CrawlJob.next_run_at).all()

# Example: To update next_run_at after a job runs (or if croniter is used)
# def update_job_next_run(db: Session, job_id: uuid.UUID, new_next_run_at: datetime):
#     job = db.query(models.CrawlJob).filter(models.CrawlJob.id == job_id).first()
#     if job:
#         job.next_run_at = new_next_run_at
#         job.last_run_at = datetime.utcnow() # Assuming job just ran
#         db.commit()
#         db.refresh(job)
#     return job