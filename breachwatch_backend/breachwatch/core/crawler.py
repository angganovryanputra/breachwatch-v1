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
        logger.debug(f"DomainLimiter initialized with delay: {delay_seconds}s, max_concurrent: {max_concurrent}")

    async def acquire(self):
        async with self._lock:
            while self.active_requests >= self.max_concurrent:
                logger.debug(f"DomainLimiter: Max concurrent ({self.max_concurrent}) reached, waiting...")
                await asyncio.sleep(0.1) # Wait if max concurrent requests are active

            current_time = time.monotonic()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.delay_seconds:
                wait_time = self.delay_seconds - time_since_last_request
                logger.debug(f"DomainLimiter: Delaying for {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.monotonic()
            self.active_requests += 1
            logger.debug(f"DomainLimiter: Acquired. Active requests: {self.active_requests}")


    async def release(self):
        async with self._lock:
            self.active_requests -= 1
            logger.debug(f"DomainLimiter: Released. Active requests: {self.active_requests}")


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
        
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100) # General client limits
        self.http_client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=self.request_timeout,
            follow_redirects=True,
            limits=limits
        )
        logger.info(f"MasterCrawler for job {self.job_id} initialized.")
        logger.info(f"Keywords: {self.settings.keywords[:5]}..., Extensions: {self.settings.file_extensions[:5]}...")
        logger.info(f"Crawl Depth: {self.settings.crawl_depth}, Dorks: {len(self.settings.search_dorks)}")
        logger.info(f"Request Delay: {self.settings.request_delay_seconds}s, Max Concurrent per Domain: {self.settings.max_concurrent_requests_per_domain}")


    async def _get_domain_limiter(self, url: str) -> DomainLimiter:
        domain = urlparse(url).netloc
        if not domain: # Should not happen for valid http/https URLs
            logger.warning(f"Could not parse domain from URL: {url}. Using default limiter.")
            domain = "__default__"

        if domain not in self.domain_limiters:
            self.domain_limiters[domain] = DomainLimiter(
                delay_seconds=self.settings.request_delay_seconds,
                max_concurrent=self.settings.max_concurrent_requests_per_domain or 2 # Fallback if not set
            )
        return self.domain_limiters[domain]

    async def fetch_page_content(self, url: str) -> Optional[Tuple[bytes, str]]: # Return bytes
        """Fetches page content and content type, respecting robots.txt and politeness. Returns (content_bytes, content_type_header)"""
        # Visited check is now at the start of process_url
        # if url in self.visited_urls:
        #     logger.debug(f"URL already visited (fetch_page_content): {url}")
        #     return None
        # self.visited_urls.add(url) # Added in process_url

        # TODO: Implement actual robots.txt checking more thoroughly if self.settings.respect_robots_txt.
        # This would involve fetching /robots.txt for the domain and parsing it.
        # For now, we assume allowed if respect_robots_txt is True, which isn't strictly correct.
        # A library like `reppy` or `robotexclusionrulesparser` could be used.
        
        limiter = await self._get_domain_limiter(url)
        await limiter.acquire()
        try:
            logger.debug(f"Fetching URL: {url} with User-Agent: {self.user_agent}")
            response = await self.http_client.get(url)
            response.raise_for_status() 
            
            content_type = response.headers.get("content-type", "").lower()
            content_bytes = await response.aread() # Read full content as bytes
            
            logger.debug(f"Fetched {url}, Status: {response.status_code}, Content-Type: {content_type}, Size: {len(content_bytes)} bytes")
            return content_bytes, content_type

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
        if url in self.visited_urls:
            logger.debug(f"URL already visited: {url}, skipping.")
            return
        self.visited_urls.add(url)

        if current_depth > self.settings.crawl_depth:
            logger.debug(f"Max depth {self.settings.crawl_depth} reached for {url}")
            return

        logger.info(f"Processing URL: {url} at depth {current_depth}")
        content_data_tuple = await self.fetch_page_content(url)

        if not content_data_tuple:
            return
        
        raw_content_bytes, content_type_header = content_data_tuple

        file_meta = file_identifier.identify_file_type_and_name(url, content_type_header, raw_content_bytes[:1024]) # Pass first KB for magic
        
        is_target_file_extension = file_meta.extension.lower() in [ext.lstrip('.').lower() for ext in self.settings.file_extensions]

        if is_target_file_extension:
            logger.info(f"Target file type '{file_meta.extension}' identified: {url}")
            
            keywords_in_filename_or_metadata = keyword_matcher.match_keywords_in_text(file_meta.name, self.settings.keywords)
            # TODO: Advanced content-based keyword matching for text-based files can be added here.
            # For now, download is triggered by filename/metadata keywords.
            
            if keywords_in_filename_or_metadata:
                logger.info(f"Keywords {keywords_in_filename_or_metadata} found in/for file: {url}. Proceeding to download.")
                try:
                    # Using the passed http_client for the downloader as well
                    download_result_schema = await downloader.download_and_store_file(
                        self.http_client,
                        url,
                        file_meta, # Pass full FileMetadata
                        self.job_id,
                        list(keywords_in_filename_or_metadata), # Pass keywords that triggered
                        raw_content_bytes if len(raw_content_bytes) < (5 * 1024 * 1024) else None # Pass content if small, for efficiency
                    )
                    if download_result_schema:
                        db_downloaded_file = crud.create_downloaded_file(db=self.db, downloaded_file=download_result_schema)
                        logger.info(f"Recorded downloaded file in DB: {db_downloaded_file.id} from {url}")
                        yield db_downloaded_file
                except Exception as e:
                    logger.error(f"Failed to download or record file {url}: {e}", exc_info=True)
        
        # If HTML content, extract links and continue crawl, regardless of whether it was also a "target file" (e.g. .html in extensions)
        # This allows crawling HTML files that might also be listed as downloadable targets.
        if "text/html" in content_type_header:
            try:
                html_content_str = raw_content_bytes.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                logger.warning(f"Could not decode HTML content from {url} as UTF-8.")
                # Attempt fallback decoding if critical, or just return
                try:
                    html_content_str = raw_content_bytes.decode('latin-1', errors='replace')
                    logger.info(f"Successfully decoded HTML from {url} using latin-1 fallback.")
                except UnicodeDecodeError:
                    logger.error(f"Failed to decode HTML content from {url} with UTF-8 and latin-1.")
                    return # Cannot process further without decodable HTML

            # Optional: Check for keywords in page text/metadata
            # soup = BeautifulSoup(html_content_str, 'html.parser')
            # page_text_for_keywords = soup.title.string if soup.title else ""
            # ... (keyword matching logic for page content)

            if current_depth < self.settings.crawl_depth:
                links_on_page = recursive.extract_links_from_html(html_content_str, url)
                logger.debug(f"Found {len(links_on_page)} links on {url} to process for next depth.")
                
                sub_tasks = []
                for link_url in links_on_page:
                    # The visited_urls check at the start of process_url will handle duplicates
                    sub_tasks.append(self.process_url(link_url, current_depth + 1))
                
                # Process sub-links and yield their findings
                for completed_task_gen in asyncio.as_completed(sub_tasks):
                    try:
                        async for found_file_schema in await completed_task_gen:
                            yield found_file_schema
                    except Exception as e_inner:
                        logger.error(f"Error processing a sub-link generator from {url}: {e_inner}", exc_info=True)

    async def _run_generator_and_put_to_queue(self, generator: AsyncGenerator, queue: asyncio.Queue):
        """Helper to run an async generator and put its items into an asyncio.Queue."""
        try:
            async for item in generator:
                await queue.put(item)
        except Exception as e:
            logger.error(f"Error in sub-generator task: {e}", exc_info=True)
            # Optionally put an error marker or specific error object in the queue
            # await queue.put(e) 
        finally:
            pass # The generator is exhausted or errored

    async def start_crawling(self) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="running")
        logger.info(f"Starting deep crawl for job {self.job_id}")

        initial_urls_to_process: Set[str] = set()

        # 1. Collect Seed URLs
        for seed_url_obj in self.settings.seed_urls:
            seed_url_str = str(seed_url_obj)
            if seed_url_str not in self.visited_urls: # Basic initial check
                initial_urls_to_process.add(seed_url_str)
            else:
                logger.debug(f"Seed URL {seed_url_str} already in initial visited set, skipping as a direct start point.")
        logger.info(f"Collected {len(initial_urls_to_process)} unique seed URLs.")


        # 2. Collect URLs from Search Engine Dorks concurrently
        if self.settings.use_search_engines and self.settings.search_dorks:
            logger.info(f"Executing {len(self.settings.search_dorks)} search dorks...")
            dork_fetch_tasks = []
            for dork in self.settings.search_dorks:
                dork_fetch_tasks.append(
                    search_engine_driver.execute_dork(
                        dork, 
                        self.http_client, 
                        max_results=self.settings.max_results_per_dork or 20
                    )
                )
            
            dork_results_urls_temp: List[List[str]] = await asyncio.gather(*[self._collect_async_gen(gen) for gen in dork_fetch_tasks], return_exceptions=True)

            for i, dork_url_list_or_exc in enumerate(dork_results_urls_temp):
                dork_query = self.settings.search_dorks[i]
                if isinstance(dork_url_list_or_exc, Exception):
                    logger.error(f"Error executing dork '{dork_query}': {dork_url_list_or_exc}")
                    continue
                
                added_from_dork = 0
                for dork_url in dork_url_list_or_exc:
                    if dork_url not in self.visited_urls and dork_url not in initial_urls_to_process:
                        initial_urls_to_process.add(dork_url)
                        added_from_dork +=1
                logger.info(f"Dork '{dork_query}' yielded {len(dork_url_list_or_exc)} URLs, {added_from_dork} new added to process queue.")
        
        logger.info(f"Total unique initial URLs to process (seeds + dorks): {len(initial_urls_to_process)}")

        if not initial_urls_to_process:
            logger.warning(f"No initial URLs to process for job {self.job_id}. Crawl will stop.")
            crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="completed_empty") # Or a new status
            await self.http_client.aclose()
            return

        # 3. Start processing initial URLs
        # Create a queue to hold results from all concurrent process_url calls
        results_queue = asyncio.Queue()
        
        # Keep track of active tasks to know when all initial processing paths are done
        active_tasks_count = len(initial_urls_to_process)
        
        async def task_wrapper(url: str, queue: asyncio.Queue, depth: int):
            nonlocal active_tasks_count
            try:
                async for item in self.process_url(url, depth):
                    await queue.put(item)
            except Exception as e:
                logger.error(f"Error in task_wrapper for URL {url}: {e}", exc_info=True)
            finally:
                active_tasks_count -= 1
                if active_tasks_count == 0:
                    await queue.put(None) # Sentinel to signal completion of all initial tasks

        # Launch tasks for each initial URL
        for url in initial_urls_to_process:
            # Depth 0 for initial URLs from seeds/dorks
            asyncio.create_task(task_wrapper(url, results_queue, 0))

        # Consume from the queue until all tasks are done and sentinel is received
        while True:
            item = await results_queue.get()
            if item is None: # Sentinel received
                results_queue.task_done() # Signal that this "None" item is processed
                break
            yield item
            results_queue.task_done()

        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="completed")
        logger.info(f"Crawl job {self.job_id} finished processing all tasks.")
        await self.http_client.aclose()

    async def _collect_async_gen(self, agen: AsyncGenerator[str, None]) -> List[str]:
        """Helper to collect all items from an async generator into a list."""
        items = []
        try:
            async for item in agen:
                items.append(item)
        except Exception as e:
            logger.error(f"Error collecting from async generator: {e}", exc_info=True)
            # Depending on policy, you might want to re-raise or just return collected items so far
        return items

# Example of how it might be called by the API endpoint's background task
# async def run_crawl_job_task(job_id: uuid.UUID, settings_dict: dict, db: Session):
#     logger.info(f"Background task started for job {job_id}")
#     crawl_settings = schemas.CrawlSettingsSchema(**settings_dict)
#     crawler = MasterCrawler(job_id=job_id, crawl_settings=crawl_settings, db=db)
#     async for downloaded_file_schema in crawler.start_crawling():
#         logger.info(f"Job {job_id} found and processed: {downloaded_file_schema.file_url}")
#     logger.info(f"Background task finished for job {job_id}")
