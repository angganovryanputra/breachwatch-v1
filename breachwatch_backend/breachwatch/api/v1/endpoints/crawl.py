import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Body
from sqlalchemy.orm import Session
from typing import List
import uuid

from breachwatch.api.v1 import schemas
from breachwatch.storage.database import get_db
from breachwatch.storage import crud
# from breachwatch.core.crawler import MasterCrawler # Placeholder for actual crawler logic
# from breachwatch.tasks.crawl_tasks import run_crawl_job_task # For Celery or background tasks

logger = logging.getLogger(__name__)
router = APIRouter()

# Dummy MasterCrawler for now
class MasterCrawler:
    def __init__(self, job_id: uuid.UUID, settings: schemas.CrawlSettingsSchema, db: Session):
        self.job_id = job_id
        self.settings = settings
        self.db = db
        logger.info(f"MasterCrawler initialized for job {job_id} with settings: {settings.keywords[:2]}...")

    async def start_crawling(self):
        logger.info(f"Starting crawl for job {self.job_id}...")
        # Simulate crawling process
        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="running")
        await self._simulate_finding_data()
        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="completed")
        logger.info(f"Crawl job {self.job_id} completed.")

    async def _simulate_finding_data(self):
        import random
        from datetime import datetime, timedelta

        num_findings = random.randint(0, 5)
        logger.info(f"Simulating {num_findings} findings for job {self.job_id}")

        for i in range(num_findings):
            mock_file_type = random.choice(self.settings.file_extensions) if self.settings.file_extensions else ".txt"
            mock_keyword = random.choice(self.settings.keywords) if self.settings.keywords else "confidential"
            
            breach_data_in = schemas.BreachDataSchema(
                id=uuid.uuid4(), # This should be the DownloadedFile ID eventually
                source_url=f"https://example-source.com/page{random.randint(1,100)}",
                file_url=f"https://example-files.com/data_{random.randint(1000,9999)}{mock_file_type}",
                file_type=mock_file_type.replace('.', ''),
                date_found=datetime.utcnow() - timedelta(days=random.randint(0,5)),
                keywords_found=[mock_keyword, "simulated"],
                crawl_job_id=self.job_id,
            )
            # In a real scenario, this would be a DownloadedFile model instance
            # And a service would handle downloading the file and creating the record.
            # For now, we just log it.
            logger.info(f"Simulated finding: {breach_data_in.file_url} with keywords {breach_data_in.keywords_found}")
            
            # Simulate creating a downloaded file record (this logic would be more complex)
            downloaded_file_in = schemas.DownloadedFileSchema(
                **breach_data_in.model_dump(),
                downloaded_at=datetime.utcnow(),
                local_path=f"/data/downloaded_files/{breach_data_in.file_url.split('/')[-1]}",
                file_size_bytes=random.randint(1024, 1024*1024),
                checksum_md5=uuid.uuid4().hex # mock checksum
            )
            crud.create_downloaded_file(db=self.db, downloaded_file=downloaded_file_in)
            logger.info(f"Simulated downloaded file record created for {downloaded_file_in.file_url}")


async def process_crawl_job(job_id: uuid.UUID, settings_data: dict, db_session_maker):
    """
    Background task runner for a crawl job.
    Requires a session maker to create a new session for this task.
    """
    db: Session = db_session_maker()
    try:
        settings = schemas.CrawlSettingsSchema(**settings_data)
        crawler = MasterCrawler(job_id=job_id, settings=settings, db=db)
        await crawler.start_crawling()
    except Exception as e:
        logger.error(f"Error during crawl job {job_id}: {e}", exc_info=True)
        crud.update_crawl_job_status(db=db, job_id=job_id, status="failed")
    finally:
        db.close()


@router.post("/jobs", response_model=schemas.CrawlJobSchema, status_code=202)
async def create_crawl_job(
    crawl_job_in: schemas.CrawlJobCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new crawl job and start it in the background.
    """
    logger.info(f"Received request to create crawl job: {crawl_job_in.name}")
    try:
        db_crawl_job = crud.create_crawl_job(db=db, crawl_job_in=crawl_job_in)
        logger.info(f"Crawl job {db_crawl_job.id} created with status {db_crawl_job.status}")

        # Add to background tasks (FastAPI's simple background tasks)
        # For more robust production systems, use Celery or RQ.
        from breachwatch.storage.database import SessionLocal # Import session maker
        background_tasks.add_task(process_crawl_job, db_crawl_job.id, crawl_job_in.settings.model_dump(), SessionLocal)
        
        logger.info(f"Crawl job {db_crawl_job.id} added to background tasks.")
        return db_crawl_job
    except Exception as e:
        logger.error(f"Error creating crawl job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create crawl job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=schemas.CrawlJobSchema)
async def get_crawl_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get details of a specific crawl job.
    """
    db_crawl_job = crud.get_crawl_job(db=db, job_id=job_id)
    if db_crawl_job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return db_crawl_job

@router.get("/jobs", response_model=List[schemas.CrawlJobSchema])
async def list_crawl_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all crawl jobs.
    """
    crawl_jobs = crud.get_crawl_jobs(db=db, skip=skip, limit=limit)
    return crawl_jobs

@router.get("/results/downloaded", response_model=List[schemas.DownloadedFileSchema])
async def list_downloaded_files(
    job_id: Optional[uuid.UUID] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    List all downloaded files, optionally filtered by job_id.
    """
    if job_id:
        files = crud.get_downloaded_files_by_job(db=db, job_id=job_id, skip=skip, limit=limit)
    else:
        files = crud.get_downloaded_files(db=db, skip=skip, limit=limit)
    return files

# Placeholder for an endpoint to trigger a crawl with specific settings from the frontend
# This could eventually replace the default settings or create specific crawl jobs
@router.post("/trigger", summary="Trigger a new crawl with specific settings (conceptual)")
async def trigger_custom_crawl(
    settings: schemas.CrawlSettingsSchema = Body(...), # Get settings from request body
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Conceptual: Trigger a new crawl with custom settings.
    This would create a new CrawlJob.
    """
    crawl_job_in = schemas.CrawlJobCreateSchema(settings=settings, name=f"Custom Crawl - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    db_crawl_job = crud.create_crawl_job(db=db, crawl_job_in=crawl_job_in)
    
    from breachwatch.storage.database import SessionLocal
    background_tasks.add_task(process_crawl_job, db_crawl_job.id, crawl_job_in.settings.model_dump(), SessionLocal)
    
    return {"message": "Custom crawl job started", "job_id": db_crawl_job.id}
