import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For server-side default timestamps

from .database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    status = Column(String, default="pending", index=True) # pending, running, completed, failed, completed_empty
    
    # Store settings as JSON for flexibility or individual columns for querying
    settings_keywords = Column(JSON) # List[str]
    settings_file_extensions = Column(JSON) # List[str]
    settings_seed_urls = Column(JSON) # List[HttpUrl as str]
    settings_search_dorks = Column(JSON) # List[str]
    settings_crawl_depth = Column(Integer)
    settings_respect_robots_txt = Column(Boolean)
    settings_request_delay_seconds = Column(Float) 
    settings_use_search_engines = Column(Boolean)
    settings_max_results_per_dork = Column(Integer, nullable=True)
    settings_max_concurrent_requests_per_domain = Column(Integer, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationship to downloaded files
    downloaded_files = relationship("DownloadedFile", back_populates="crawl_job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CrawlJob(id={self.id}, name='{self.name}', status='{self.status}')>"


class DownloadedFile(Base):
    __tablename__ = "downloaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    
    source_url = Column(String, nullable=False, index=True) 
    file_url = Column(String, nullable=False, unique=False, index=True) 
    
    file_type = Column(String(50), index=True) 
    keywords_found = Column(JSON) 
    
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())
    local_path = Column(String, nullable=True, unique=False) # Path relative to project root or a configured base
    file_size_bytes = Column(Integer, nullable=True)
    checksum_md5 = Column(String(32), nullable=True, index=True)

    crawl_job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    crawl_job = relationship("CrawlJob", back_populates="downloaded_files")

    date_found = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<DownloadedFile(id={self.id}, file_url='{self.file_url}', type='{self.file_type}')>"
