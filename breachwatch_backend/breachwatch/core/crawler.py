import logging
import asyncio
import httpx # Modern async HTTP client, preferred over requests for async code
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional, Tuple, Dict, AsyncGenerator
from datetime import datetime
import re
import time
import random

from breachwatch.api.v1 import schemas # For type hinting if needed for settings
from breachwatch.utils.config_loader import get_settings
from breachwatch.core import file_identifier, keyword_matcher, downloader
from breachwatch.strategies import search_engine_driver, direct_probe, recursive
from breachwatch.storage import crud # For saving results
from sqlalchemy.orm import Session
import uuid

logger = logging.getLogger(__name__)
config_settings = get_settings()


class DomainLimiter:
    """Limits requests to a specific domain to respect politeness policies."""
    def __init__(self, delay_seconds: float, max_concurrent: int):
        self.delay_seconds = delay_seconds
        self.max_concurrent = max_concurrent
        self.last_request_time: float = 0
        self.active_requests: int = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while self.active_requests >= self.max_concurrent:
                await asyncio.sleep(0.1) # Wait if max concurrent requests are active

            current_time = time.monotonic()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.delay_seconds:
                await asyncio.sleep(self.delay_seconds - time_since_last_request)
            
            self.last_request_time = time.monotonic()
            self.active_requests += 1

    async def release(self):
        async with self._lock:
            self.active_requests -= 1

class MasterCrawler:
    """
    Orchestrates the crawling process using various strategies.
    Manages visited URLs, depth, and delegates to specific crawlers.
    """
    def __init__(self, job_id: uuid.UUID, crawl_settings: schemas.CrawlSettingsSchema, db: Session):
        self.job_id = job_id
        self.settings = crawl_settings
        self.db = db
        self.visited_urls: Set[str] = set()
        self.domain_limiters: Dict[str, DomainLimiter] = {}
        self.user_agent = config_settings.DEFAULT_USER_AGENT
        self.request_timeout = config_settings.REQUEST_TIMEOUT
        
        # Initialize HTTP client (consider using a session for connection pooling)
        # Limits can be configured more granularly if needed
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        self.http_client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=self.request_timeout,
            follow_redirects=True,
            limits=limits
        )
        logger.info(f"MasterCrawler for job {self.job_id} initialized.")
        logger.info(f"Keywords: {self.settings.keywords[:5]}..., Extensions: {self.settings.file_extensions[:5]}...")
        logger.info(f"Crawl Depth: {self.settings.crawl_depth}, Dorks: {len(self.settings.search_dorks)}")


    async def _get_domain_limiter(self, url: str) -> DomainLimiter:
        domain = urlparse(url).netloc
        if domain not in self.domain_limiters:
            # Potentially customize delay per domain from config or dynamic adjustment
            self.domain_limiters[domain] = DomainLimiter(
                delay_seconds=self.settings.request_delay_seconds, # Use job-specific delay
                max_concurrent=2 # Default max concurrent, can be from config_settings.crawler.max_concurrent_requests_per_domain
            )
        return self.domain_limiters[domain]

    async def fetch_page_content(self, url: str) -> Optional[Tuple[str, str]]:
        """Fetches page content and content type, respecting robots.txt and politeness."""
        if url in self.visited_urls:
            logger.debug(f"URL already visited: {url}")
            return None
        self.visited_urls.add(url)

        if self.settings.respect_robots_txt:
            # TODO: Implement robots.txt checking (e.g. using urllib.robotparser or a library)
            # For now, assume allowed
            pass
        
        limiter = await self._get_domain_limiter(url)
        await limiter.acquire()
        try:
            logger.debug(f"Fetching URL: {url} with User-Agent: {self.user_agent}")
            response = await self.http_client.get(url)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            content_type = response.headers.get("content-type", "").lower()
            
            # Heuristic to check if content is likely HTML before trying to parse
            if "text/html" in content_type:
                return await response.aread(), content_type # Read as bytes, then decode
            elif any(ext in url.lower() for ext in self.settings.file_extensions):
                 # If it's a target file extension, we might want to process it directly
                 # For now, we assume it's binary or non-HTML text.
                 # Downloader will handle it.
                 return await response.aread(), content_type # Return bytes and content_type
            else:
                logger.debug(f"Skipping non-HTML content type {content_type} for URL: {url} (unless it's a target file)")
                return None # Or return bytes if all content should be processed

        except httpx.RequestError as e:
            logger.warning(f"HTTP request error fetching {url}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP status error fetching {url}: {e.response.status_code} - {e.response.reason_phrase}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
            return None
        finally:
            await limiter.release()

    async def process_url(self, url: str, current_depth: int) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """
        Processes a single URL:
        1. Fetches content.
        2. Identifies if it's a target file or HTML page.
        3. If file: checks keywords, downloads, records.
        4. If HTML: extracts links, checks for keywords in links/page, continues crawl if depth allows.
        Yields DownloadedFileSchema for each potential breach found and downloaded.
        """
        if current_depth > self.settings.crawl_depth:
            logger.debug(f"Max depth {self.settings.crawl_depth} reached for {url}")
            return

        logger.info(f"Processing URL: {url} at depth {current_depth}")
        content_data = await self.fetch_page_content(url)

        if not content_data:
            return
        
        raw_content_bytes, content_type = content_data

        # 1. File Identification (based on URL, Content-Type, and potentially magic numbers)
        file_meta = file_identifier.identify_file_type_and_name(url, content_type, raw_content_bytes)
        
        is_target_file = file_meta.extension.lower() in [ext.lstrip('.').lower() for ext in self.settings.file_extensions]

        if is_target_file:
            logger.info(f"Target file type '{file_meta.extension}' identified: {url}")
            # 2. Keyword Matching (for file content if possible, or filename/metadata)
            # For simplicity now, let's assume keyword matching on filename or metadata
            # Advanced: stream content and match, or download and analyze
            
            keywords_in_filename = keyword_matcher.match_keywords_in_text(file_meta.name, self.settings.keywords)
            # Add more checks if needed, e.g. on snippets of content if text-based
            
            if keywords_in_filename: # Or other criteria indicating a potential breach
                logger.info(f"Keywords {keywords_in_filename} found in/for file: {url}")
                
                # 3. Download File (simulated or actual) and record
                try:
                    download_result = await downloader.download_and_store_file(
                        self.http_client, # Pass the client
                        url,
                        file_meta,
                        self.job_id,
                        self.settings.keywords # Pass relevant keywords for the record
                    )
                    if download_result:
                        # Store in DB via CRUD
                        db_downloaded_file = crud.create_downloaded_file(db=self.db, downloaded_file=download_result)
                        logger.info(f"Recorded downloaded file: {db_downloaded_file.id} from {url}")
                        yield db_downloaded_file # Yield the DB schema
                except Exception as e:
                    logger.error(f"Failed to download or record file {url}: {e}", exc_info=True)
        
        # 4. If HTML content, extract links and continue crawl
        if "text/html" in content_type:
            try:
                html_content = raw_content_bytes.decode('utf-8', errors='replace') # Decode bytes to string
            except UnicodeDecodeError:
                logger.warning(f"Could not decode HTML content from {url} as UTF-8.")
                return

            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Keyword check in page title or meta description (optional, can be noisy)
            page_text_for_keywords = soup.title.string if soup.title else ""
            # meta_desc = soup.find("meta", attrs={"name": "description"})
            # if meta_desc and meta_desc.get("content"):
            #    page_text_for_keywords += " " + meta_desc.get("content")
            
            # keywords_in_page = keyword_matcher.match_keywords_in_text(page_text_for_keywords, self.settings.keywords)
            # if keywords_in_page:
            #    logger.info(f"Keywords {keywords_in_page} found in page metadata: {url}")
            #    # Could record this as a "source_url" of interest even if no direct file found yet

            # Extract links for further crawling
            if current_depth < self.settings.crawl_depth:
                links_on_page = recursive.extract_links_from_html(html_content, url)
                tasks = []
                for link_url in links_on_page:
                    if link_url not in self.visited_urls:
                        # Check if keywords are in link text or URL itself
                        # link_text = "" # Need to get link text from soup for this specific link
                        # keywords_in_link = keyword_matcher.match_keywords_in_text(link_url + " " + link_text, self.settings.keywords)
                        # if keywords_in_link:
                        #    logger.info(f"Keywords {keywords_in_link} found in link: {link_url}")
                        
                        tasks.append(self.process_url(link_url, current_depth + 1))
                
                # Process sub-links concurrently
                for task_gen in asyncio.as_completed(tasks):
                    async for found_file_schema in await task_gen: # Iterate over async generator results
                         yield found_file_schema


    async def start_crawling(self) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """
        Main entry point to start the crawling process.
        Iterates through seed URLs and search engine dorks.
        Yields DownloadedFileSchema for each potential breach found and downloaded.
        """
        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="running")
        logger.info(f"Starting crawl for job {self.job_id}")

        # Process Seed URLs
        seed_url_tasks = []
        for seed_url in self.settings.seed_urls:
            seed_url_tasks.append(self.process_url(str(seed_url), 0)) # Start at depth 0
        
        # Process Search Engine Dorks
        dork_tasks = []
        if self.settings.use_search_engines:
            for dork in self.settings.search_dorks:
                logger.info(f"Executing search dork: {dork}")
                try:
                    # search_engine_driver would internally use http_client or its own
                    # and should also yield URLs to be processed or directly process them.
                    # For now, let's assume it yields URLs.
                    async for dork_result_url in search_engine_driver.execute_dork(
                        dork, 
                        self.http_client, 
                        max_results=self.settings.max_results_per_dork or 20
                    ):
                        if dork_result_url not in self.visited_urls:
                             # Dork results are typically direct file links or highly relevant pages
                             # Process them at depth 0 or 1 depending on strategy
                            dork_tasks.append(self.process_url(dork_result_url, 0))
                except Exception as e:
                    logger.error(f"Error executing dork '{dork}': {e}", exc_info=True)
        
        # Combine all initial tasks and process them
        all_initial_tasks = seed_url_tasks + dork_tasks
        
        # Use asyncio.gather for top-level tasks, but process_url itself handles recursion
        # and yields results as they are found.
        # Since process_url is an async generator, we need to iterate through its results.
        
        async def run_and_yield(task_generator):
            async for item in task_generator:
                yield item

        gathered_generators = [run_and_yield(gen) for gen in all_initial_tasks]

        for completed_generator_task in asyncio.as_completed(gathered_generators):
            try:
                async for found_file in await completed_generator_task:
                    yield found_file
            except Exception as e:
                logger.error(f"Error in a top-level crawl task for job {self.job_id}: {e}", exc_info=True)

        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="completed")
        logger.info(f"Crawl job {self.job_id} finished processing initial tasks.")
        await self.http_client.aclose() # Close the HTTP client session

# Example of how it might be called by the API endpoint's background task
# async def run_crawl_job_task(job_id: uuid.UUID, settings_dict: dict, db: Session):
#     logger.info(f"Background task started for job {job_id}")
#     crawl_settings = schemas.CrawlSettingsSchema(**settings_dict)
#     crawler = MasterCrawler(job_id=job_id, crawl_settings=crawl_settings, db=db)
#     async for downloaded_file_schema in crawler.start_crawling():
#         logger.info(f"Job {job_id} found and processed: {downloaded_file_schema.file_url}")
#     logger.info(f"Background task finished for job {job_id}")
