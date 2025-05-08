
import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB # Use JSONB for better performance with JSON in PostgreSQL
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func, select
from datetime import timezone

from .database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Added length constraint (255 seems reasonable for a name)
    name = Column(String(255), index=True)
    status = Column(String(50), default="pending", index=True) # Added length constraint

    # Crawler settings directly on the job model (using JSONB for flexibility)
    settings_keywords = Column(JSONB)
    settings_file_extensions = Column(JSONB)
    settings_seed_urls = Column(JSONB) # Store as list of strings
    settings_search_dorks = Column(JSONB)
    settings_crawl_depth = Column(Integer)
    settings_respect_robots_txt = Column(Boolean)
    settings_request_delay_seconds = Column(Float)
    settings_use_search_engines = Column(Boolean)
    settings_max_results_per_dork = Column(Integer, nullable=True)
    settings_max_concurrent_requests_per_domain = Column(Integer, nullable=True)
    # Added length constraint
    settings_custom_user_agent = Column(String(255), nullable=True)

    # Scheduling settings
    settings_schedule_type = Column(String(20), nullable=True) # 'one-time' or 'recurring' - Added length constraint
    settings_schedule_cron_expression = Column(String(100), nullable=True) # Added length constraint
    settings_schedule_run_at = Column(DateTime(timezone=True), nullable=True) # For one-time (stores target UTC time)
    settings_schedule_timezone = Column(String(50), nullable=True) # User's intended timezone for CRON interpretation - Added length constraint

    # Job run information
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True) # Calculated next run time (UTC)
    last_run_at = Column(DateTime(timezone=True), nullable=True, index=True) # Timestamp of the last actual run start (UTC)

    # Timestamps with timezone support
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Automatically update updated_at timestamp whenever the record is modified
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to DownloadedFile records
    # cascade="all, delete-orphan": ensures downloaded files are deleted when job is deleted
    # lazy="selectin": efficiently loads files when accessing the job object (good for lists)
    downloaded_files = relationship("DownloadedFile", back_populates="crawl_job", cascade="all, delete-orphan", lazy="selectin")

    # Property to calculate summary dynamically (not stored in DB)
    @property
    def results_summary(self) -> dict:
        # Check if the relationship is loaded to avoid extra DB query if possible
        if hasattr(self, '_sa_instance_state') and 'downloaded_files' in self._sa_instance_state.committed_state:
             # Access loaded relationship directly
             return {"files_found": len(self.downloaded_files)}
        # Fallback if not loaded (might trigger a query if lazy='selectin' wasn't used or expired)
        # This path is less likely with lazy='selectin' but good for robustness
        elif self.id: # Check if the instance has an ID (meaning it's persisted)
            # You could potentially perform a count query here if needed, but selectinload is preferred
            # For simplicity, assume selectinload worked or rely on it triggering load
            return {"files_found": len(self.downloaded_files) if self.downloaded_files is not None else 0}
        return {"files_found": 0}


    def __repr__(self):
        return f"<CrawlJob(id={self.id}, name='{self.name}', status='{self.status}')>"


class DownloadedFile(Base):
    __tablename__ = "downloaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # URLs stored as strings - Added length constraints (adjust if longer URLs are expected)
    source_url = Column(String(2048), nullable=False, index=True)
    file_url = Column(String(2048), nullable=False, index=True) # Not unique, same file might be found via different jobs/sources

    file_type = Column(String(50), index=True) # Store identified extension or MIME type part
    keywords_found = Column(JSONB) # List of keywords that triggered the download/interest

    # Timestamps with timezone support
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now()) # Time processing finished
    date_found = Column(DateTime(timezone=True), nullable=False, server_default=func.now()) # Time initially discovered

    # Added length constraints
    local_path = Column(String(1024), nullable=True) # Path on the server where the file is stored
    file_size_bytes = Column(Integer, nullable=True)
    checksum_md5 = Column(String(32), nullable=True, index=True)

    # Foreign key relationship to CrawlJob
    crawl_job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    crawl_job = relationship("CrawlJob", back_populates="downloaded_files")


    def __repr__(self):
        return f"<DownloadedFile(id={self.id}, file_url='{self.file_url}', type='{self.file_type}')>"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Added length constraint
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # Added length constraint
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    # Added length constraint
    role = Column(String(50), default="user", index=True) # e.g., "user", "admin"

    # Timestamps with timezone support
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # One-to-one relationship with UserPreference
    # cascade="all, delete-orphan": Deletes preferences when user is deleted
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

class UserPreference(Base):
    __tablename__ = "user_preferences"

    # Primary key is also the foreign key to User
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    default_items_per_page = Column(Integer, default=10, nullable=False)
    receive_email_notifications = Column(Boolean, default=True, nullable=False)
    # Add other preference fields here (e.g., theme, default filters)

    # Timestamp with timezone support
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship back to User
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, items_per_page={self.default_items_per_page})>"

