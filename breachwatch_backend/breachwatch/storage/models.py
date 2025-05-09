
import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB 
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func, select
from datetime import timezone, datetime # Ensure datetime is imported

from .database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), index=True, nullable=True) # Allow nullable name for now
    status = Column(String(50), default="pending", index=True) 

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
    settings_custom_user_agent = Column(String(512), nullable=True) # Increased length for UA
    settings_proxies = Column(JSONB, nullable=True) # Store list of proxy strings

    settings_schedule_type = Column(String(20), nullable=True) 
    settings_schedule_cron_expression = Column(String(100), nullable=True) 
    settings_schedule_run_at = Column(DateTime(timezone=True), nullable=True) 
    settings_schedule_timezone = Column(String(50), nullable=True) 

    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True) 
    last_run_at = Column(DateTime(timezone=True), nullable=True, index=True) 

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    downloaded_files = relationship("DownloadedFile", back_populates="crawl_job", cascade="all, delete-orphan", lazy="selectin")

    @property
    def results_summary(self) -> dict:
        if hasattr(self, '_sa_instance_state') and 'downloaded_files' in self._sa_instance_state.committed_state:
             return {"files_found": len(self.downloaded_files)}
        elif self.id: 
            # Fallback to count query if files not loaded; requires active session
            # This path is less ideal, selectinload is preferred.
            # For robustness, it might count, but this could be slow if called often without preloading.
            # db_session = Session.object_session(self)
            # if db_session:
            #    count = db_session.query(func.count(DownloadedFile.id)).filter(DownloadedFile.crawl_job_id == self.id).scalar()
            #    return {"files_found": count}
            return {"files_found": len(self.downloaded_files) if self.downloaded_files is not None else 0} # Relies on lazy load if not preloaded
        return {"files_found": 0}


    def __repr__(self):
        return f"<CrawlJob(id={self.id}, name='{self.name}', status='{self.status}')>"


class DownloadedFile(Base):
    __tablename__ = "downloaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url = Column(String(2048), nullable=False, index=True)
    file_url = Column(String(2048), nullable=False, index=True) 
    file_type = Column(String(50), index=True) 
    keywords_found = Column(JSONB) 

    downloaded_at = Column(DateTime(timezone=True), server_default=func.now()) 
    date_found = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    local_path = Column(String(1024), nullable=True) 
    file_size_bytes = Column(Integer, nullable=True)
    checksum_md5 = Column(String(32), nullable=True, index=True)

    crawl_job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    crawl_job = relationship("CrawlJob", back_populates="downloaded_files")


    def __repr__(self):
        return f"<DownloadedFile(id={self.id}, file_url='{self.file_url}', type='{self.file_type}')>"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False) # Increased length for flexibility with hashing algos
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default="user", index=True) 

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    default_items_per_page = Column(Integer, default=10, nullable=False)
    receive_email_notifications = Column(Boolean, default=True, nullable=False)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, items_per_page={self.default_items_per_page})>"

    