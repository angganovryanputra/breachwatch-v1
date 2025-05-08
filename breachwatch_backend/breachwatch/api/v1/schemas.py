from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
from datetime import datetime
import uuid

# --- Settings Schemas ---
class CrawlSettingsSchema(BaseModel):
    keywords: List[str] = Field(..., example=["password", "NIK", "confidential"])
    file_extensions: List[str] = Field(..., example=[".txt", ".sql", ".zip"])
    seed_urls: List[HttpUrl] = Field(..., example=["https://example.com/forum", "https://pastebin.com"])
    search_dorks: List[str] = Field(..., example=['filetype:sql "passwords"', 'intitle:"index of" "backup"'])
    crawl_depth: int = Field(default=2, ge=0, le=10)
    respect_robots_txt: bool = True
    request_delay_seconds: float = Field(default=1.0, ge=0, le=10)
    use_search_engines: bool = True # Whether to use search engine dorks
    max_results_per_dork: Optional[int] = Field(default=20, ge=1)
    max_concurrent_requests_per_domain: Optional[int] = Field(default=2, ge=1, le=10, description="Maximum concurrent requests to a single domain.")

class GlobalSettingsSchema(CrawlSettingsSchema):
    # Potentially add other global settings here, like output paths, API keys, etc.
    output_directory: str = "data/downloaded_files"

# --- Crawl Job Schemas ---
class CrawlJobCreateSchema(BaseModel):
    name: Optional[str] = Field(default_factory=lambda: f"Crawl Job - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    settings: CrawlSettingsSchema # Specific settings for this job

class CrawlJobSchema(CrawlJobCreateSchema):
    id: uuid.UUID
    status: str = "pending" # e.g., pending, running, completed, failed, stopping, completed_empty
    created_at: datetime
    updated_at: datetime
    results_summary: Optional[Dict[str, int]] = Field(default_factory=dict) # e.g. {"files_found": 10}

    class Config:
        from_attributes = True # For SQLAlchemy model conversion (formerly orm_mode)

# --- Result Schemas ---
class BreachDataSchema(BaseModel):
    id: uuid.UUID
    source_url: HttpUrl
    file_url: HttpUrl
    file_type: str
    date_found: datetime
    keywords_found: List[str]
    # content_snippet: Optional[str] = None # For a small preview of content
    # risk_score: Optional[float] = None # Potential future enhancement
    crawl_job_id: uuid.UUID

    class Config:
        from_attributes = True

class DownloadedFileSchema(BreachDataSchema):
    downloaded_at: datetime
    local_path: Optional[str] = None # Path on the server where file is stored
    file_size_bytes: Optional[int] = None
    checksum_md5: Optional[str] = None
    # analysis_status: str = "pending" # e.g., pending, analyzed, error

    class Config:
        from_attributes = True


# --- Generic Response Schemas ---
class MessageResponseSchema(BaseModel):
    message: str

class PaginatedResponseSchema(BaseModel):
    items: List
    total: int
    page: int
    size: int
    pages: int
```