import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func, select # For server-side default timestamps and subqueries

from .database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    status = Column(String, default="pending", index=True) # pending, running, completed, failed, stopping, completed_empty
    
    settings_keywords = Column(JSON) 
    settings_file_extensions = Column(JSON) 
    settings_seed_urls = Column(JSON) 
    settings_search_dorks = Column(JSON) 
    settings_crawl_depth = Column(Integer)
    settings_respect_robots_txt = Column(Boolean)
    settings_request_delay_seconds = Column(Float) 
    settings_use_search_engines = Column(Boolean)
    settings_max_results_per_dork = Column(Integer, nullable=True)
    settings_max_concurrent_requests_per_domain = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    downloaded_files = relationship("DownloadedFile", back_populates="crawl_job", cascade="all, delete-orphan", lazy="selectin")

    # This provides a way for the Pydantic schema to get the summary if the relationship is loaded.
    # Note: This is a Python property. If you need this count in SQL queries directly,
    # you'd use a column_property with a correlated subquery, but that's more complex and
    # often less performant for lists than loading the relationship and counting in Python.
    # For Pydantic `from_attributes=True`, it will try to access this property.
    @property
    def results_summary(self) -> dict:
        if hasattr(self, '_sa_instance_state') and not self._sa_instance_state.expired and 'downloaded_files' in self.__dict__:
            # If downloaded_files relationship is loaded and not expired
             return {"files_found": len(self.downloaded_files)}
        # Fallback if not loaded (though CRUD operations try to ensure it is)
        # This would trigger a lazy load if not already loaded, which might be undesirable in some contexts.
        # However, for schema serialization, it's acceptable.
        # Or, you could return a default/empty summary if you want to avoid lazy loads strictly.
        # For now, assume it should be loaded by the time schema needs it.
        # If it's critical to avoid lazy load, ensure `selectinload` is always used in queries.
        if self.downloaded_files is not None: # Check if None, not just empty list
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
    keywords_found = Column(JSON) 
    
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())
    local_path = Column(String, nullable=True, unique=False) 
    file_size_bytes = Column(Integer, nullable=True)
    checksum_md5 = Column(String(32), nullable=True, index=True)

    crawl_job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False)
    crawl_job = relationship("CrawlJob", back_populates="downloaded_files")

    date_found = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<DownloadedFile(id={self.id}, file_url='{self.file_url}', type='{self.file_type}')>"

```