import logging
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Tuple
import uuid
from datetime import datetime, timezone # Ensure timezone import

from . import models
from breachwatch.api.v1 import schemas # For Pydantic schemas
from breachwatch.core.security import get_password_hash # Import security utils

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
        schedule = settings.schedule
        initial_status = "scheduled"
        if schedule.type == "one-time" and schedule.run_at:
            next_run_time_for_job = schedule.run_at
        elif schedule.type == "recurring" and schedule.cron_expression:
            try:
                from croniter import croniter # type: ignore
                from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # type: ignore
                
                tz_str = schedule.timezone or 'UTC'
                try:
                    tz = ZoneInfo(tz_str)
                except ZoneInfoNotFoundError:
                    logger.warning(f"Invalid timezone '{tz_str}' in schedule. Defaulting to UTC.")
                    tz = ZoneInfo('UTC')
                    
                base_time = datetime.now(tz) # Calculate next run based on current time in target timezone
                iter = croniter(schedule.cron_expression, base_time)
                next_run_dt_local = iter.get_next(datetime)
                # Convert the calculated local time back to UTC for storage
                next_run_time_for_job = next_run_dt_local.astimezone(timezone.utc) 
                logger.info(f"Calculated next run time for cron '{schedule.cron_expression}' in tz '{tz_str}': {next_run_time_for_job} UTC")
            except ImportError:
                logger.error("croniter library not installed. Cannot calculate next run time for recurring jobs. Please install with 'pip install croniter zoneinfo'.")
                initial_status = "failed" # Mark job as failed if scheduling fails
            except Exception as e:
                logger.error(f"Could not calculate next run time for cron '{schedule.cron_expression}' with timezone '{schedule.timezone}': {e}")
                initial_status = "failed" 

    db_crawl_job = models.CrawlJob(
        name=crawl_job_in.name,
        status=initial_status,
        settings_keywords=settings.keywords,
        settings_file_extensions=settings.file_extensions,
        settings_seed_urls=[str(url) for url in settings.seed_urls], # Store as string list
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
        settings_schedule_run_at=settings.schedule.run_at if settings.schedule and settings.schedule.type == 'one-time' else None, # Store original run_at only for one-time
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
        db_crawl_job.updated_at = datetime.now(timezone.utc) # Use UTC now 
        if next_run_at is not None: # Explicitly check for None to allow clearing
             # Ensure datetime is timezone-aware (UTC) before saving
            if next_run_at.tzinfo is None:
                logger.warning(f"Received naive datetime {next_run_at} for next_run_at, assuming UTC.")
                db_crawl_job.next_run_at = next_run_at.replace(tzinfo=timezone.utc)
            else:
                db_crawl_job.next_run_at = next_run_at.astimezone(timezone.utc)
        else: # Allow clearing next_run_at if None is passed
            db_crawl_job.next_run_at = None 
            
        if last_run_at:
             # Ensure datetime is timezone-aware (UTC) before saving
            if last_run_at.tzinfo is None:
                logger.warning(f"Received naive datetime {last_run_at} for last_run_at, assuming UTC.")
                db_crawl_job.last_run_at = last_run_at.replace(tzinfo=timezone.utc)
            else:
                db_crawl_job.last_run_at = last_run_at.astimezone(timezone.utc)
        
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
        now_utc = datetime.now(timezone.utc) 
    
    return db.query(models.CrawlJob).filter(
        models.CrawlJob.status == "scheduled",
        models.CrawlJob.next_run_at <= now_utc
    ).order_by(models.CrawlJob.next_run_at).all()


# --- User CRUD ---

def get_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(func.lower(models.User.email) == func.lower(email)).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).order_by(models.User.created_at).offset(skip).limit(limit).all()

def create_user(db: Session, user_in: schemas.UserCreateSchema) -> models.User:
    hashed_password = get_password_hash(user_in.password) 
    db_user = models.User(
        email=user_in.email.lower(), # Store email in lowercase for consistency
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Optionally create default preferences for the new user
    create_default_user_preferences(db, db_user.id)
    logger.info(f"User created: {db_user.email} (ID: {db_user.id})")
    return db_user

def update_user_role(db: Session, user_id: uuid.UUID, role: str) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db_user.role = role
        db_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Updated role for user {user_id} to {role}")
    return db_user
    
def update_user_status(db: Session, user_id: uuid.UUID, is_active: bool) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db_user.is_active = is_active
        db_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Updated active status for user {user_id} to {is_active}")
    return db_user

def update_user_password(db: Session, user_id: uuid.UUID, hashed_password: str) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if db_user:
        db_user.hashed_password = hashed_password
        db_user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Updated password for user {user_id}")
    return db_user

def delete_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """Deletes a user by their ID."""
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
        logger.info(f"User {user_id} deleted from DB.")
    return db_user


# --- UserPreference CRUD ---

def get_user_preferences(db: Session, user_id: uuid.UUID) -> Optional[models.UserPreference]:
    return db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).first()

def update_or_create_user_preferences(db: Session, user_id: uuid.UUID, preferences_in: schemas.UserPreferenceUpdateSchema) -> Optional[models.UserPreference]:
    db_prefs = get_user_preferences(db, user_id)
    if db_prefs:
        # Update existing preferences
        db_prefs.default_items_per_page = preferences_in.default_items_per_page
        db_prefs.receive_email_notifications = preferences_in.receive_email_notifications
        # Update other fields from preferences_in as needed
        db_prefs.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updating preferences for user {user_id}")
    else:
        # Create new preferences
        db_prefs = models.UserPreference(
            user_id=user_id,
            default_items_per_page=preferences_in.default_items_per_page,
            receive_email_notifications=preferences_in.receive_email_notifications,
            # Set other fields from preferences_in or defaults
        )
        db.add(db_prefs)
        logger.info(f"Creating new preferences for user {user_id}")
    
    db.commit()
    db.refresh(db_prefs)
    return db_prefs

def create_default_user_preferences(db: Session, user_id: uuid.UUID) -> models.UserPreference:
    """Creates default preferences for a user, usually upon creation."""
    existing_prefs = get_user_preferences(db, user_id)
    if existing_prefs:
        logger.debug(f"Default preferences already exist for user {user_id}. Skipping creation.")
        return existing_prefs
        
    default_prefs = schemas.UserPreferenceUpdateSchema() # Gets defaults from schema
    db_prefs = models.UserPreference(
        user_id=user_id,
        default_items_per_page=default_prefs.default_items_per_page,
        receive_email_notifications=default_prefs.receive_email_notifications
    )
    db.add(db_prefs)
    db.commit()
    db.refresh(db_prefs)
    logger.info(f"Created default preferences for user {user_id}")
    return db_prefs

