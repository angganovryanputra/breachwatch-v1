from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

# --- Schedule Schemas ---
class ScheduleSchema(BaseModel):
    type: str = Field(..., pattern="^(one-time|recurring)$") # Enforce specific values
    cron_expression: Optional[str] = Field(default=None, description="Standard CRON expression for recurring jobs. E.g., '0 0 * * *' for daily at midnight.")
    run_at: Optional[datetime] = Field(default=None, description="Specific UTC datetime for one-time jobs.")
    timezone: Optional[str] = Field(default=None, description="Timezone for the schedule, e.g., 'Asia/Jakarta'. Important for cron interpretation.")

    @field_validator('cron_expression')
    @classmethod
    def validate_cron_expression(cls, value: Optional[str], values: Any) -> Optional[str]:
        data = values.data # Access the model's data
        if data.get('type') == 'recurring' and not value:
            raise ValueError("cron_expression is required for recurring schedules")
        if data.get('type') == 'one-time' and value:
            raise ValueError("cron_expression should not be set for one-time schedules")
        # TODO: Add more sophisticated cron validation if needed
        return value

    @field_validator('run_at')
    @classmethod
    def validate_run_at(cls, value: Optional[datetime], values: Any) -> Optional[datetime]:
        data = values.data
        if data.get('type') == 'one-time' and not value:
            raise ValueError("run_at is required for one-time schedules")
        if data.get('type') == 'recurring' and value:
            raise ValueError("run_at should not be set for recurring schedules")
        return value
        
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, value: Optional[str], values: Any) -> Optional[str]:
        # Could add validation against a list of known timezones if necessary
        # from zoneinfo import available_timezones # Python 3.9+
        # if value and value not in available_timezones():
        #     raise ValueError(f"Invalid timezone: {value}")
        return value


# --- Settings Schemas ---
class CrawlSettingsSchema(BaseModel):
    keywords: List[str] = Field(..., example=["password", "NIK", "confidential"])
    file_extensions: List[str] = Field(..., example=[".txt", ".sql", ".zip"])
    seed_urls: List[HttpUrl] = Field(..., example=["https://example.com/forum", "https://pastebin.com"])
    search_dorks: List[str] = Field(..., example=['filetype:sql "passwords"', 'intitle:"index of" "backup"'])
    crawl_depth: int = Field(default=2, ge=0, le=10)
    respect_robots_txt: bool = True
    request_delay_seconds: float = Field(default=1.0, ge=0, le=30) # Max delay up to 30s
    use_search_engines: bool = True 
    max_results_per_dork: Optional[int] = Field(default=20, ge=1, le=100)
    max_concurrent_requests_per_domain: Optional[int] = Field(default=2, ge=1, le=10)
    custom_user_agent: Optional[str] = Field(default=None, max_length=255)
    schedule: Optional[ScheduleSchema] = Field(default=None)


class GlobalSettingsSchema(CrawlSettingsSchema):
    output_directory: str = "data/downloaded_files"

# --- Crawl Job Schemas ---
class CrawlJobCreateSchema(BaseModel):
    name: Optional[str] = Field(default_factory=lambda: f"Crawl Job - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    settings: CrawlSettingsSchema 

class CrawlJobSchema(CrawlJobCreateSchema):
    id: uuid.UUID
    status: str = "pending" # e.g., pending, running, completed, failed, stopping, completed_empty, scheduled
    created_at: datetime
    updated_at: datetime
    results_summary: Optional[Dict[str, int]] = Field(default_factory=dict) 
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None


    class Config:
        from_attributes = True 

# --- Result Schemas ---
class BreachDataSchema(BaseModel):
    id: uuid.UUID
    source_url: HttpUrl
    file_url: HttpUrl
    file_type: str
    date_found: datetime
    keywords_found: List[str]
    crawl_job_id: uuid.UUID

    class Config:
        from_attributes = True

class DownloadedFileSchema(BreachDataSchema):
    downloaded_at: datetime
    local_path: Optional[str] = None 
    file_size_bytes: Optional[int] = None
    checksum_md5: Optional[str] = None

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
