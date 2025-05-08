import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB # Use JSONB for better performance with JSON in PostgreSQL
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func, select 

from .database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    status = Column(String, default="pending", index=True) # pending, running, completed, failed, stopping, completed_empty, scheduled
    
    # Crawler settings directly on the job model
    settings_keywords = Column(JSONB) 
    settings_file_extensions = Column(JSONB) 
    settings_seed_urls = Column(JSONB) 
    settings_search_dorks = Column(JSONB) 
    settings_crawl_depth = Column(Integer)
    settings_respect_robots_txt = Column(Boolean)
    settings_request_delay_seconds = Column(Float) 
    settings_use_search_engines = Column(Boolean)
    settings_max_results_per_dork = Column(Integer, nullable=True)
    settings_max_concurrent_requests_per_domain = Column(Integer, nullable=True)
    settings_custom_user_agent = Column(String, nullable=True)

    # Scheduling settings
    settings_schedule_type = Column(String, nullable=True) # 'one-time' or 'recurring'
    settings_schedule_cron_expression = Column(String, nullable=True)
    settings_schedule_run_at = Column(DateTime(timezone=True), nullable=True) # For one-time
    settings_schedule_timezone = Column(String, nullable=True)

    # Job run information
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True) # Calculated next run time for scheduled jobs
    last_run_at = Column(DateTime(timezone=True), nullable=True, index=True) # Timestamp of the last actual run

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    downloaded_files = relationship("DownloadedFile", back_populates="crawl_job", cascade="all, delete-orphan", lazy="selectin")

    @property
    def results_summary(self) -> dict:
        if hasattr(self, '_sa_instance_state') and not self._sa_instance_state.expired and 'downloaded_files' in self.__dict__:
             return {"files_found": len(self.downloaded_files)}
        if self.downloaded_files is not None: 
            return {"files_found": len(self.downloaded_files)}
        return {"files_found": 0}


    def __repr__(self):
        return f"<CrawlJob(id={self.id}, name='{self.name}', status='{self.status}')>"


class DownloadedFile(Base):
    __tablename__ = "downloaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    
    source_url = Column(String, nullable=False, index=True) 
    file_url = Column(String, nullable=False, unique=False, index=True) 
    
    file_type = Column(String(50), index=True) 
    keywords_found = Column(JSONB) 
    
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())
    local_path = Column(String, nullable=True, unique=False) 
    file_size_bytes = Column(Integer, nullable=True)
    checksum_md5 = Column(String(32), nullable=True, index=True)

    crawl_job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    crawl_job = relationship("CrawlJob", back_populates="downloaded_files")

    date_found = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<DownloadedFile(id={self.id}, file_url='{self.file_url}', type='{self.file_type}')>"

# TODO: Add User and Role models for authentication and RBAC later
# class User(Base):
#     __tablename__ = "users"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     email = Column(String, unique=True, index=True, nullable=False)
#     hashed_password = Column(String, nullable=False)
#     full_name = Column(String, nullable=True)
#     is_active = Column(Boolean, default=True)
#     role = Column(String, default="user") # e.g., "user", "admin"
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
