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
    
    if job:
        # Populate results_summary (Pydantic schema will use this if field exists)
        # This is more for direct model manipulation; Pydantic schema can do this too.
        # For schemas.CrawlJobSchema, if `results_summary` is a field,
        # and `from_attributes = True`, it will try to access `job.results_summary`.
        # We can prepare it here or let the schema handle it via a property/validator if needed.
        # The current CrawlJobSchema expects results_summary to be populated.
        # We'll rely on the relationship being loaded and Pydantic accessing `job.downloaded_files`.
        # The schema needs to compute this, or we add a property to the model.
        # For simplicity, we let Pydantic schema do the count:
        # job.results_summary = {"files_found": len(job.downloaded_files)}
        pass # Pydantic schema will derive it from loaded downloaded_files if set up to do so

    return job


def get_crawl_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[models.CrawlJob]:
    """Fetches a list of crawl jobs, eagerly loading downloaded_files for summary."""
    jobs = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files)  # Eagerly load for summaries
    ).order_by(models.CrawlJob.created_at.desc()).offset(skip).limit(limit).all()
    
    # for job in jobs:
    # Pydantic schema will derive it from loaded downloaded_files.
    # job.results_summary = {"files_found": len(job.downloaded_files)}
    return jobs


def create_crawl_job(db: Session, crawl_job_in: schemas.CrawlJobCreateSchema) -> models.CrawlJob:
    db_crawl_job = models.CrawlJob(
        name=crawl_job_in.name,
        status="pending", # Initial status
        settings_keywords=crawl_job_in.settings.keywords,
        settings_file_extensions=crawl_job_in.settings.file_extensions,
        settings_seed_urls=[str(url) for url in crawl_job_in.settings.seed_urls], # Store as strings
        settings_search_dorks=crawl_job_in.settings.search_dorks,
        settings_crawl_depth=crawl_job_in.settings.crawl_depth,
        settings_respect_robots_txt=crawl_job_in.settings.respect_robots_txt,
        settings_request_delay_seconds=crawl_job_in.settings.request_delay_seconds, # Store as float
        settings_use_search_engines=crawl_job_in.settings.use_search_engines,
        settings_max_results_per_dork=crawl_job_in.settings.max_results_per_dork,
        settings_max_concurrent_requests_per_domain=crawl_job_in.settings.max_concurrent_requests_per_domain
    )
    db.add(db_crawl_job)
    db.commit()
    db.refresh(db_crawl_job) # Refresh to get DB defaults like ID, created_at
    # Load downloaded_files for consistency, though it will be empty for a new job
    db.refresh(db_crawl_job, attribute_names=['downloaded_files'])
    logger.info(f"CrawlJob created in DB: ID {db_crawl_job.id}, Name: {db_crawl_job.name}")
    return db_crawl_job

def update_crawl_job_status(db: Session, job_id: uuid.UUID, status: str) -> Optional[models.CrawlJob]:
    db_crawl_job = get_crawl_job(db, job_id) # This will load downloaded_files
    if db_crawl_job:
        db_crawl_job.status = status
        db_crawl_job.updated_at = datetime.utcnow() 
        db.commit()
        db.refresh(db_crawl_job)
        db.refresh(db_crawl_job, attribute_names=['downloaded_files']) # Ensure relationship is fresh for schema
        logger.info(f"CrawlJob {job_id} status updated to: {status}")
    return db_crawl_job

def delete_crawl_job_and_get_file_paths(db: Session, job_id: uuid.UUID) -> Tuple[Optional[models.CrawlJob], List[str]]:
    """Deletes a crawl job and its associated DownloadedFile records.
    Returns the deleted job object (or None) and a list of local_paths of its files."""
    db_crawl_job = db.query(models.CrawlJob).options(
        # Load only local_path from downloaded_files for efficiency
        selectinload(models.CrawlJob.downloaded_files).load_only(models.DownloadedFile.local_path)
    ).filter(models.CrawlJob.id == job_id).first()

    if db_crawl_job:
        local_file_paths = [
            file.local_path for file in db_crawl_job.downloaded_files if file.local_path
        ]
        
        # Deletion of DownloadedFile records is handled by cascade delete due to relationship setting.
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

```