
import logging
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Tuple
import uuid
from datetime import datetime, timezone # Ensure timezone import

from . import models
from breachwatch.api.v1 import schemas # For Pydantic schemas
from breachwatch.core.security import get_password_hash, verify_password # Import security utils

logger = logging.getLogger(__name__)

# --- Authentication Helper ---
def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    Authenticates a user by email and password.
    Returns the user object if authentication is successful, otherwise None.
    """
    user = get_user_by_email(db, email)
    if not user:
        logger.debug(f"Authentication failed: User with email {email} not found.")
        return None
    if not verify_password(password, user.hashed_password):
        logger.debug(f"Authentication failed: Incorrect password for user {email}.")
        return None
    logger.debug(f"Authentication successful for user {email}.")
    return user


# --- CrawlJob CRUD ---

def get_crawl_job(db: Session, job_id: uuid.UUID) -> Optional[models.CrawlJob]:
    """Fetches a single crawl job, eagerly loading its downloaded_files for summary."""
    # Eagerly load downloaded_files relationship using selectinload for efficiency
    job = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files)
    ).filter(models.CrawlJob.id == job_id).first()
    # The results_summary property on the model will calculate based on loaded files
    return job


def get_crawl_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[models.CrawlJob]:
    """Fetches a list of crawl jobs, eagerly loading downloaded_files for summary."""
    # Eagerly load downloaded_files for all jobs in the list
    jobs = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files)
    ).order_by(models.CrawlJob.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


def create_crawl_job(db: Session, crawl_job_in: schemas.CrawlJobCreateSchema) -> models.CrawlJob:
    settings = crawl_job_in.settings

    initial_status = "pending"
    next_run_time_for_job = None

    # Handle schedule processing if present
    if settings.schedule:
        schedule = settings.schedule
        initial_status = "scheduled" # If schedule info exists, assume scheduled initially
        if schedule.type == "one-time" and schedule.run_at:
            try:
                # Parse ISO string from frontend (assumed UTC or timezone specified)
                # SQLAlchemy handles timezone-aware datetime objects correctly with TIMESTAMP WITH TIME ZONE
                run_at_dt = datetime.fromisoformat(schedule.run_at.replace('Z', '+00:00'))
                # Ensure it's timezone-aware (UTC)
                if run_at_dt.tzinfo is None:
                    run_at_dt = run_at_dt.replace(tzinfo=timezone.utc)
                next_run_time_for_job = run_at_dt.astimezone(timezone.utc)
                logger.info(f"One-time job scheduled for: {next_run_time_for_job}")
            except ValueError:
                 logger.error(f"Invalid run_at format '{schedule.run_at}' for one-time schedule. Setting job to failed.")
                 initial_status = "failed"

        elif schedule.type == "recurring" and schedule.cron_expression:
            try:
                from croniter import croniter # type: ignore
                from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # type: ignore

                tz_str = schedule.timezone or 'UTC' # Default to UTC if not provided
                try:
                    tz = ZoneInfo(tz_str)
                except ZoneInfoNotFoundError:
                    logger.warning(f"Invalid timezone '{tz_str}' in schedule. Defaulting to UTC.")
                    tz = ZoneInfo('UTC')

                # Calculate next run based on current time in the target timezone
                base_time = datetime.now(tz)
                iter = croniter(schedule.cron_expression, base_time)
                next_run_dt_local = iter.get_next(datetime)
                # Convert the calculated local time back to UTC for storage
                next_run_time_for_job = next_run_dt_local.astimezone(timezone.utc)
                logger.info(f"Calculated next run time for cron '{schedule.cron_expression}' in tz '{tz_str}': {next_run_time_for_job} UTC")

            except ImportError:
                logger.error("Libraries 'croniter' or 'tzdata' (for zoneinfo) not installed. Cannot calculate next run time. Please install them.")
                initial_status = "failed" # Mark job as failed if scheduling libraries missing
            except Exception as e:
                logger.error(f"Could not calculate next run time for cron '{schedule.cron_expression}' with timezone '{schedule.timezone}': {e}", exc_info=True)
                initial_status = "failed"
        else:
             # If schedule object exists but type/data is invalid for scheduling
             logger.warning(f"Invalid schedule configuration provided: type='{schedule.type}', cron='{schedule.cron_expression}', run_at='{schedule.run_at}'. Setting job to pending.")
             initial_status = "pending" # Fallback to pending if schedule data is unusable

    # Create the CrawlJob model instance
    db_crawl_job = models.CrawlJob(
        name=crawl_job_in.name or f"Crawl Job - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}", # Default name if not provided
        status=initial_status,
        # Map settings from Pydantic schema to model fields (snake_case assumed)
        settings_keywords=settings.keywords,
        settings_file_extensions=settings.file_extensions,
        settings_seed_urls=[str(url) for url in settings.seed_urls], # Store as list of strings
        settings_search_dorks=settings.search_dorks,
        settings_crawl_depth=settings.crawl_depth,
        settings_respect_robots_txt=settings.respect_robots_txt,
        settings_request_delay_seconds=settings.request_delay_seconds,
        settings_use_search_engines=settings.use_search_engines,
        settings_max_results_per_dork=settings.max_results_per_dork,
        settings_max_concurrent_requests_per_domain=settings.max_concurrent_requests_per_domain,
        settings_custom_user_agent=settings.custom_user_agent,
        # Map schedule settings
        settings_schedule_type=settings.schedule.type if settings.schedule else None,
        settings_schedule_cron_expression=settings.schedule.cron_expression if settings.schedule and settings.schedule.type == 'recurring' else None,
        settings_schedule_run_at=next_run_time_for_job if settings.schedule and settings.schedule.type == 'one-time' else None, # Store calculated UTC run time for one-time
        settings_schedule_timezone=settings.schedule.timezone if settings.schedule else None,
        next_run_at=next_run_time_for_job, # Store calculated next run time (UTC)
        last_run_at=None # Not run yet
    )
    db.add(db_crawl_job)
    db.commit()
    db.refresh(db_crawl_job)
    # Refresh relationship explicitly if needed after commit, though selectinload should handle it
    # db.refresh(db_crawl_job, attribute_names=['downloaded_files'])
    logger.info(f"CrawlJob created in DB: ID {db_crawl_job.id}, Name: {db_crawl_job.name}, Status: {db_crawl_job.status}")
    return db_crawl_job


def update_crawl_job_status(db: Session, job_id: uuid.UUID, status: str, next_run_at: Optional[datetime] = None, last_run_at: Optional[datetime] = None) -> Optional[models.CrawlJob]:
    """Updates the status and optionally the next/last run times for a crawl job."""
    db_crawl_job = get_crawl_job(db, job_id) # Use existing getter which loads relationships if needed
    if db_crawl_job:
        db_crawl_job.status = status
        db_crawl_job.updated_at = datetime.now(timezone.utc) # Use UTC now

        if next_run_at is not None: # Explicitly check for None to allow clearing
            # Ensure datetime is timezone-aware (UTC) before saving
            if next_run_at.tzinfo is None:
                logger.warning(f"Received naive datetime {next_run_at} for next_run_at, assuming UTC.")
                db_crawl_job.next_run_at = next_run_at.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if it's not already
                db_crawl_job.next_run_at = next_run_at.astimezone(timezone.utc)
        # Only set next_run_at to None if specifically passed as None (e.g., job failed and shouldn't reschedule)
        # Removed the implicit else block that set it to None if not provided

        if last_run_at:
             # Ensure datetime is timezone-aware (UTC) before saving
            if last_run_at.tzinfo is None:
                logger.warning(f"Received naive datetime {last_run_at} for last_run_at, assuming UTC.")
                db_crawl_job.last_run_at = last_run_at.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC
                db_crawl_job.last_run_at = last_run_at.astimezone(timezone.utc)

        try:
            db.commit()
            db.refresh(db_crawl_job)
            # Optionally refresh relationships if they might have changed concurrently, though unlikely here
            # db.refresh(db_crawl_job, attribute_names=['downloaded_files'])
            logger.info(f"CrawlJob {job_id} status updated to: {status}")
        except Exception as e:
            logger.error(f"Database error updating job {job_id}: {e}", exc_info=True)
            db.rollback() # Rollback transaction on error
            return None
    return db_crawl_job


def delete_crawl_job_and_get_file_paths(db: Session, job_id: uuid.UUID) -> Tuple[Optional[models.CrawlJob], List[str]]:
    """Deletes a crawl job and its associated DownloadedFile records.
    Returns the deleted job object (or None) and a list of local_paths of its files."""
    # Eagerly load only the local_path from the downloaded_files relationship
    db_crawl_job = db.query(models.CrawlJob).options(
        selectinload(models.CrawlJob.downloaded_files).load_only(models.DownloadedFile.local_path)
    ).filter(models.CrawlJob.id == job_id).first()

    if db_crawl_job:
        # Extract local paths before deletion
        local_file_paths = [
            file.local_path for file in db_crawl_job.downloaded_files if file.local_path
        ]

        try:
            db.delete(db_crawl_job) # Cascade delete should handle downloaded_files due to relationship config
            db.commit()
            logger.info(f"CrawlJob {job_id} and its DB file records deleted.")
            # Return the object state *before* deletion (it's expired after commit)
            # Or just return True/paths? Let's return the paths.
            return db_crawl_job, local_file_paths # Object state might be unreliable after deletion
        except Exception as e:
             logger.error(f"Database error deleting job {job_id}: {e}", exc_info=True)
             db.rollback()
             return None, []
    return None, []


# --- DownloadedFile CRUD ---

def get_downloaded_file(db: Session, file_id: uuid.UUID) -> Optional[models.DownloadedFile]:
    return db.query(models.DownloadedFile).filter(models.DownloadedFile.id == file_id).first()

def get_downloaded_files(db: Session, skip: int = 0, limit: int = 100) -> List[models.DownloadedFile]:
    return db.query(models.DownloadedFile).order_by(models.DownloadedFile.downloaded_at.desc()).offset(skip).limit(limit).all()

def get_downloaded_files_by_job(db: Session, job_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.DownloadedFile]:
    return db.query(models.DownloadedFile).filter(models.DownloadedFile.crawl_job_id == job_id).order_by(models.DownloadedFile.downloaded_at.desc()).offset(skip).limit(limit).all()

def create_downloaded_file(db: Session, downloaded_file: schemas.DownloadedFileSchema) -> models.DownloadedFile:
    """Creates a DownloadedFile record in the database."""
    db_downloaded_file = models.DownloadedFile(
        # Map fields from the Pydantic schema to the SQLAlchemy model
        id=downloaded_file.id,
        source_url=str(downloaded_file.source_url), # Ensure URL is string
        file_url=str(downloaded_file.file_url),     # Ensure URL is string
        file_type=downloaded_file.file_type,
        keywords_found=downloaded_file.keywords_found,
        downloaded_at=downloaded_file.downloaded_at, # Assumed timezone-aware from download logic
        local_path=downloaded_file.local_path,
        file_size_bytes=downloaded_file.file_size_bytes,
        checksum_md5=downloaded_file.checksum_md5,
        crawl_job_id=downloaded_file.crawl_job_id,
        date_found=downloaded_file.date_found # Assumed timezone-aware from crawl logic
    )
    try:
        db.add(db_downloaded_file)
        db.commit()
        db.refresh(db_downloaded_file)
        logger.info(f"DownloadedFile created in DB: ID {db_downloaded_file.id}, URL: {db_downloaded_file.file_url}")
        return db_downloaded_file
    except Exception as e:
        logger.error(f"Database error creating DownloadedFile for URL {downloaded_file.file_url}: {e}", exc_info=True)
        db.rollback()
        raise # Re-raise the exception to be handled by the caller


def delete_downloaded_file(db: Session, file_id: uuid.UUID) -> Optional[models.DownloadedFile]:
    """Deletes a DownloadedFile record from the database."""
    db_file = get_downloaded_file(db, file_id)
    if db_file:
        try:
            db.delete(db_file)
            db.commit()
            logger.info(f"DownloadedFile record {file_id} deleted from DB.")
            return db_file # Return the object state before deletion
        except Exception as e:
             logger.error(f"Database error deleting DownloadedFile {file_id}: {e}", exc_info=True)
             db.rollback()
             return None
    return None # Return None if file not found initially

# --- Scheduled Job Specific CRUD (Conceptual) ---
def get_due_scheduled_jobs(db: Session, now_utc: Optional[datetime] = None) -> List[models.CrawlJob]:
    """Fetches scheduled jobs whose next_run_at is due."""
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)
    elif now_utc.tzinfo is None: # Ensure provided time is timezone-aware
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    else:
         now_utc = now_utc.astimezone(timezone.utc) # Convert to UTC

    return db.query(models.CrawlJob).filter(
        models.CrawlJob.status == "scheduled",
        models.CrawlJob.next_run_at <= now_utc
    ).order_by(models.CrawlJob.next_run_at).all()


# --- User CRUD ---

def get_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """Fetches a user by their ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Fetches a user by their email (case-insensitive)."""
    # Use func.lower for case-insensitive comparison if DB supports it (PostgreSQL does)
    return db.query(models.User).filter(func.lower(models.User.email) == func.lower(email)).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Fetches a list of users with pagination."""
    return db.query(models.User).order_by(models.User.created_at).offset(skip).limit(limit).all()

def create_user(db: Session, user_in: schemas.UserCreateSchema) -> models.User:
    """Creates a new user and their default preferences."""
    hashed_password = get_password_hash(user_in.password)
    db_user = models.User(
        email=user_in.email.lower(), # Store email in lowercase for consistency
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=user_in.is_active, # Should default to True or based on settings
        role=user_in.role if user_in.role in ["user", "admin"] else "user" # Ensure valid role, default to user
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # Create default preferences after user is successfully created
        try:
            create_default_user_preferences(db, db_user.id)
        except Exception as pref_e:
            # Log error but don't necessarily fail user creation if preference creation fails
            logger.error(f"Failed to create default preferences for new user {db_user.id}: {pref_e}", exc_info=True)

        logger.info(f"User created: {db_user.email} (ID: {db_user.id})")
        return db_user
    except Exception as e:
         logger.error(f"Database error creating user {user_in.email}: {e}", exc_info=True)
         db.rollback()
         raise # Re-raise the exception


def update_user_role(db: Session, user_id: uuid.UUID, role: str) -> Optional[models.User]:
    """Updates the role for a specific user."""
    db_user = get_user(db, user_id)
    if db_user:
        if role not in ["user", "admin"]:
             logger.warning(f"Attempted to set invalid role '{role}' for user {user_id}. Ignoring.")
             return db_user # Or raise error? For now, ignore invalid role update.
        db_user.role = role
        db_user.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
            db.refresh(db_user)
            logger.info(f"Updated role for user {user_id} to {role}")
            return db_user
        except Exception as e:
            logger.error(f"Database error updating role for user {user_id}: {e}", exc_info=True)
            db.rollback()
            return None
    return None # User not found

def update_user_status(db: Session, user_id: uuid.UUID, is_active: bool) -> Optional[models.User]:
    """Updates the active status for a specific user."""
    db_user = get_user(db, user_id)
    if db_user:
        db_user.is_active = is_active
        db_user.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
            db.refresh(db_user)
            logger.info(f"Updated active status for user {user_id} to {is_active}")
            return db_user
        except Exception as e:
            logger.error(f"Database error updating status for user {user_id}: {e}", exc_info=True)
            db.rollback()
            return None
    return None # User not found

def update_user_password(db: Session, user_id: uuid.UUID, hashed_password: str) -> Optional[models.User]:
    """Updates the hashed password for a specific user."""
    db_user = get_user(db, user_id)
    if db_user:
        db_user.hashed_password = hashed_password
        db_user.updated_at = datetime.now(timezone.utc)
        try:
            db.commit()
            db.refresh(db_user)
            logger.info(f"Updated password for user {user_id}")
            return db_user
        except Exception as e:
            logger.error(f"Database error updating password for user {user_id}: {e}", exc_info=True)
            db.rollback()
            return None
    return None # User not found

def delete_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """Deletes a user by their ID. Cascade should handle preferences."""
    db_user = get_user(db, user_id)
    if db_user:
        try:
            db.delete(db_user)
            db.commit()
            logger.info(f"User {user_id} deleted from DB.")
            return db_user # Return object state before deletion
        except Exception as e:
            logger.error(f"Database error deleting user {user_id}: {e}", exc_info=True)
            db.rollback()
            return None
    return None # User not found


# --- UserPreference CRUD ---

def get_user_preferences(db: Session, user_id: uuid.UUID) -> Optional[models.UserPreference]:
    """Fetches preferences for a specific user."""
    return db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).first()

def update_or_create_user_preferences(db: Session, user_id: uuid.UUID, preferences_in: schemas.UserPreferenceUpdateSchema) -> Optional[models.UserPreference]:
    """Updates existing preferences or creates new ones if they don't exist."""
    db_prefs = get_user_preferences(db, user_id)
    if db_prefs:
        # Update existing preferences
        updated = False
        if db_prefs.default_items_per_page != preferences_in.default_items_per_page:
             db_prefs.default_items_per_page = preferences_in.default_items_per_page
             updated = True
        if db_prefs.receive_email_notifications != preferences_in.receive_email_notifications:
             db_prefs.receive_email_notifications = preferences_in.receive_email_notifications
             updated = True
        # Update other fields from preferences_in as needed

        if updated:
            db_prefs.updated_at = datetime.now(timezone.utc)
            logger.info(f"Updating preferences for user {user_id}")
        else:
             logger.debug(f"No changes detected for user {user_id} preferences. Skipping update.")
             return db_prefs # Return existing object if no changes
    else:
        # Create new preferences
        logger.info(f"Creating new preferences for user {user_id}")
        db_prefs = models.UserPreference(
            user_id=user_id,
            default_items_per_page=preferences_in.default_items_per_page,
            receive_email_notifications=preferences_in.receive_email_notifications,
            # Set other fields from preferences_in or defaults
        )
        db.add(db_prefs)

    try:
        db.commit()
        db.refresh(db_prefs)
        return db_prefs
    except Exception as e:
         logger.error(f"Database error saving preferences for user {user_id}: {e}", exc_info=True)
         db.rollback()
         return None # Return None on error


def create_default_user_preferences(db: Session, user_id: uuid.UUID) -> models.UserPreference:
    """Creates default preferences for a user, usually upon creation. Assumes user exists."""
    existing_prefs = get_user_preferences(db, user_id)
    if existing_prefs:
        logger.debug(f"Default preferences already exist for user {user_id}. Skipping creation.")
        return existing_prefs

    logger.info(f"Creating default preferences for user {user_id}")
    default_prefs_schema = schemas.UserPreferenceUpdateSchema() # Gets defaults from schema definition
    db_prefs = models.UserPreference(
        user_id=user_id,
        default_items_per_page=default_prefs_schema.default_items_per_page,
        receive_email_notifications=default_prefs_schema.receive_email_notifications
    )
    try:
        db.add(db_prefs)
        db.commit()
        db.refresh(db_prefs)
        return db_prefs
    except Exception as e:
         logger.error(f"Database error creating default preferences for user {user_id}: {e}", exc_info=True)
         db.rollback()
         raise # Re-raise exception as this might be critical during user setup
