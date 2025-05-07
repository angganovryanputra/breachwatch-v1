import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # For server-side default timestamps

from .database import Base

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    status = Column(String, default="pending", index=True) # pending, running, completed, failed
    
    # Store settings as JSON for flexibility
    settings_keywords = Column(JSON) # List[str]
    settings_file_extensions = Column(JSON) # List[str]
    settings_seed_urls = Column(JSON) # List[HttpUrl]
    settings_search_dorks = Column(JSON) # List[str]
    settings_crawl_depth = Column(Integer)
    settings_respect_robots_txt = Column(Boolean)
    settings_request_delay_seconds = Column(Integer) # Or Float
    settings_use_search_engines = Column(Boolean)
    settings_max_results_per_dork = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationship to downloaded files
    downloaded_files = relationship("DownloadedFile", back_populates="crawl_job")

    def __repr__(self):
        return f"<CrawlJob(id={self.id}, name='{self.name}', status='{self.status}')>"


class DownloadedFile(Base):
    __tablename__ = "downloaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) # This is the PK for this table
    
    source_url = Column(String, nullable=False, index=True) # The URL from which the file was found/downloaded
    file_url = Column(String, nullable=False, unique=False, index=True) # The actual file URL (might be same as source_url)
    
    file_type = Column(String(50), index=True) # Determined extension
    keywords_found = Column(JSON) # List of keywords that triggered the download/matched
    
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())
    local_path = Column(String, nullable=True, unique=True) # Path on the server where file is stored
    file_size_bytes = Column(Integer, nullable=True)
    checksum_md5 = Column(String(32), nullable=True, index=True) # MD5 hash of the file

    # Content snippet or analysis results could be added here
    # content_snippet = Column(Text, nullable=True)
    # analysis_status = Column(String, default="pending") # e.g. pending, analyzed_safe, analyzed_risky

    # Foreign Key to CrawlJob
    crawl_job_id = Column(UUID(as_uuid=True), ForeignKey("crawl_jobs.id"), nullable=False)
    crawl_job = relationship("CrawlJob", back_populates="downloaded_files")

    # Original breach data fields (date_found might be slightly different from downloaded_at)
    # These might be redundant if DownloadedFile *is* the primary record of a breach.
    # For simplicity, we're making DownloadedFile the main record that links to a CrawlJob.
    # 'date_found' would be when crawler first identified it, 'downloaded_at' when download completed.
    date_found = Column(DateTime(timezone=True), nullable=False, server_default=func.now()) # This is more like "identified_at"

    def __repr__(self):
        return f"<DownloadedFile(id={self.id}, file_url='{self.file_url}', type='{self.file_type}')>"

# If you add new models, make sure they are imported somewhere (e.g., in database.py before create_all,
# or in an __init__.py that gets imported) so that Base.metadata knows about them.
# For this setup, importing models in crud.py will suffice as crud.py is used by endpoints.
