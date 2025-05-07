import logging
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from . import models
from breachwatch.api.v1 import schemas # For Pydantic schemas

logger = logging.getLogger(__name__)

# --- CrawlJob CRUD ---

def get_crawl_job(db: Session, job_id: uuid.UUID) -> Optional[models.CrawlJob]:
    return db.query(models.CrawlJob).filter(models.CrawlJob.id == job_id).first()

def get_crawl_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[models.CrawlJob]:
    return db.query(models.CrawlJob).order_by(models.CrawlJob.created_at.desc()).offset(skip).limit(limit).all()

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
        settings_request_delay_seconds=int(crawl_job_in.settings.request_delay_seconds), # Assuming int storage
        settings_use_search_engines=crawl_job_in.settings.use_search_engines,
        settings_max_results_per_dork=crawl_job_in.settings.max_results_per_dork
    )
    db.add(db_crawl_job)
    db.commit()
    db.refresh(db_crawl_job)
    logger.info(f"CrawlJob created in DB: ID {db_crawl_job.id}, Name: {db_crawl_job.name}")
    return db_crawl_job

def update_crawl_job_status(db: Session, job_id: uuid.UUID, status: str) -> Optional[models.CrawlJob]:
    db_crawl_job = get_crawl_job(db, job_id)
    if db_crawl_job:
        db_crawl_job.status = status
        db_crawl_job.updated_at = datetime.utcnow() # Manually update if onupdate not working as expected or not set
        db.commit()
        db.refresh(db_crawl_job)
        logger.info(f"CrawlJob {job_id} status updated to: {status}")
    return db_crawl_job

def delete_crawl_job(db: Session, job_id: uuid.UUID) -> Optional[models.CrawlJob]:
    db_crawl_job = get_crawl_job(db, job_id)
    if db_crawl_job:
        # Consider what to do with associated DownloadedFile records (cascade delete, nullify FK, or disallow)
        # For now, direct delete. Add cascade options in model relationships if needed.
        db.delete(db_crawl_job)
        db.commit()
        logger.info(f"CrawlJob {job_id} deleted.")
    return db_crawl_job


# --- DownloadedFile CRUD ---

def get_downloaded_file(db: Session, file_id: uuid.UUID) -> Optional[models.DownloadedFile]:
    return db.query(models.DownloadedFile).filter(models.DownloadedFile.id == file_id).first()

def get_downloaded_files(db: Session, skip: int = 0, limit: int = 100) -> List[models.DownloadedFile]:
    return db.query(models.DownloadedFile).order_by(models.DownloadedFile.downloaded_at.desc()).offset(skip).limit(limit).all()

def get_downloaded_files_by_job(db: Session, job_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.DownloadedFile]:
    return db.query(models.DownloadedFile).filter(models.DownloadedFile.crawl_job_id == job_id).order_by(models.DownloadedFile.downloaded_at.desc()).offset(skip).limit(limit).all()

def create_downloaded_file(db: Session, downloaded_file: schemas.DownloadedFileSchema) -> models.DownloadedFile:
    db_downloaded_file = models.DownloadedFile(
        id=downloaded_file.id, # Use ID from schema if provided (e.g. from downloader)
        source_url=str(downloaded_file.source_url),
        file_url=str(downloaded_file.file_url),
        file_type=downloaded_file.file_type,
        keywords_found=downloaded_file.keywords_found,
        downloaded_at=downloaded_file.downloaded_at,
        local_path=downloaded_file.local_path,
        file_size_bytes=downloaded_file.file_size_bytes,
        checksum_md5=downloaded_file.checksum_md5,
        crawl_job_id=downloaded_file.crawl_job_id,
        date_found=downloaded_file.date_found # When it was first identified
    )
    db.add(db_downloaded_file)
    db.commit()
    db.refresh(db_downloaded_file)
    logger.info(f"DownloadedFile created in DB: ID {db_downloaded_file.id}, URL: {db_downloaded_file.file_url}")
    return db_downloaded_file

def delete_downloaded_file(db: Session, file_id: uuid.UUID) -> Optional[models.DownloadedFile]:
    db_file = get_downloaded_file(db, file_id)
    if db_file:
        # Note: This only deletes the DB record. The actual file on disk is not deleted here.
        # File deletion logic should be handled separately if required.
        db.delete(db_file)
        db.commit()
        logger.info(f"DownloadedFile record {file_id} deleted from DB.")
    return db_file
