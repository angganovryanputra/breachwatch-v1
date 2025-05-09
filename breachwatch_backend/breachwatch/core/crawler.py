
import logging
import asyncio
import httpx # Modern async HTTP client, preferred over requests for async code
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional, Tuple, Dict, AsyncGenerator, Union
from datetime import datetime, timezone
import re
import time
import random
import uuid
import xml.etree.ElementTree as ET # For parsing sitemaps
from urllib.robotparser import RobotFileParser


from breachwatch.api.v1 import schemas # For type hinting if needed for settings
from breachwatch.utils.config_loader import get_settings
from breachwatch.core import file_identifier, keyword_matcher, downloader
from breachwatch.strategies import search_engine_driver, direct_probe, recursive # direct_probe and recursive are now less directly used from here
from breachwatch.storage import crud, models # Import models
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)
config_settings = get_settings()

# List of common user agents for rotation
COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.58 Mobile Safari/537.36",
    "BreachWatchResearchBot/1.1 (compatible; +https://example.com/botinfo) Python-httpx/0.2x.x" # Adding our custom bot too
]

class DomainLimiter:
    """Limits requests to a specific domain to respect politeness policies."""
    def __init__(self, delay_seconds: float, max_concurrent: int):
        self.delay_seconds = delay_seconds
        self.max_concurrent = max_concurrent
        self.last_request_time: float = 0
        self.active_requests: int = 0
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock) # Condition for efficient waiting
        logger.debug(f"DomainLimiter initialized with delay: {delay_seconds}s, max_concurrent: {max_concurrent}")

    async def acquire(self):
        async with self._lock:
            while self.active_requests >= self.max_concurrent:
                logger.debug(f"DomainLimiter: Max concurrent ({self.max_concurrent}) reached for domain, waiting...")
                await self._condition.wait() # Wait until notified

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
            self._condition.notify() # Notify one waiting task


class MasterCrawler:
    """
    Orchestrates the crawling process using various strategies.
    Manages visited URLs, depth, and delegates to specific crawlers.
    Includes robust error handling and graceful shutdown mechanisms.
    Enhanced with User-Agent rotation, robots.txt respect, and sitemap parsing.
    """
    def __init__(self, job_id: uuid.UUID, crawl_settings: schemas.CrawlSettingsSchema, db: Session):
        self.job_id = job_id
        self.settings = crawl_settings
        self.db = db
        self.visited_urls: Set[str] = set()
        self.domain_limiters: Dict[str, DomainLimiter] = {}
        
        self.user_agents = COMMON_USER_AGENTS
        if self.settings.custom_user_agent: # Prepend custom UA if provided
            self.user_agents = [self.settings.custom_user_agent] + self.user_agents
        self.current_user_agent = self._get_random_user_agent() # Initial UA

        self.request_timeout = config_settings.REQUEST_TIMEOUT
        self._should_stop_event = asyncio.Event() # Event to signal graceful shutdown
        self.initial_urls_found = False # Track if any URLs were found from seeds/dorks initially
        
        self.robots_parsers_cache: Dict[str, Optional[RobotFileParser]] = {} # Cache for robots.txt parsers
        self.processed_sitemap_urls: Set[str] = set() # To avoid reprocessing sitemaps

        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100) # General client limits
        self.http_client = httpx.AsyncClient(
            # Headers will be set per request to allow User-Agent rotation
            timeout=self.request_timeout,
            follow_redirects=True,
            limits=limits,
            verify=False # Consider adding SSL verification control if needed config_settings.VERIFY_SSL?
        )
        logger.info(f"MasterCrawler for job {self.job_id} initialized. Respect robots.txt: {self.settings.respect_robots_txt}")
        logger.info(f"Keywords: {self.settings.keywords[:5]}..., Extensions: {self.settings.file_extensions[:5]}...")
        logger.info(f"Crawl Depth: {self.settings.crawl_depth}, Dorks: {len(self.settings.search_dorks)}")
        logger.info(f"Request Delay: {self.settings.request_delay_seconds}s, Max Concurrent per Domain: {self.settings.max_concurrent_requests_per_domain}")


    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    async def _check_if_stopped(self) -> bool:
        """Checks if the stop signal has been received or job status is 'stopping'."""
        if self._should_stop_event.is_set():
            return True
        if random.randint(1, 100) > 98: 
            try:
                job_status = self.db.query(models.CrawlJob.status).filter(models.CrawlJob.id == self.job_id).scalar() 
                if job_status == "stopping":
                    self._should_stop_event.set()
                    logger.info(f"Job {self.job_id} stop signal received via DB status 'stopping'.")
                    return True
            except SQLAlchemyError as db_err:
                 logger.error(f"Database error checking job status for {self.job_id}: {db_err}", exc_info=True)
            except Exception as e:
                 logger.error(f"Unexpected error checking job status for {self.job_id}: {e}", exc_info=True)
        return False

    async def stop_crawler(self):
        """Signals the crawler to stop gracefully."""
        if not self._should_stop_event.is_set():
            logger.info(f"MasterCrawler for job {self.job_id} received stop signal.")
            self._should_stop_event.set()
            try:
                crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="stopping")
            except Exception as e:
                 logger.error(f"Failed to update job {self.job_id} status to 'stopping' in DB after signal: {e}")

    async def _get_domain_limiter(self, url: str) -> DomainLimiter:
        try:
            domain = urlparse(url).netloc
            if not domain: domain = "__no_domain__"
        except ValueError: domain = "__parse_error__"
        if domain not in self.domain_limiters:
            self.domain_limiters[domain] = DomainLimiter(
                delay_seconds=self.settings.request_delay_seconds,
                max_concurrent=self.settings.max_concurrent_requests_per_domain or 2
            )
        return self.domain_limiters[domain]

    async def _fetch_robots_txt_parser(self, domain_url_str: str) -> Optional[RobotFileParser]:
        """Fetches and parses robots.txt for a domain, caching the parser."""
        parsed_domain_url = urlparse(domain_url_str)
        domain_base = f"{parsed_domain_url.scheme}://{parsed_domain_url.netloc}"
        robots_url = urljoin(domain_base, "/robots.txt")

        if domain_base in self.robots_parsers_cache:
            logger.debug(f"Using cached robots.txt parser for {domain_base}")
            return self.robots_parsers_cache[domain_base]

        logger.info(f"Fetching robots.txt from {robots_url}")
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        current_ua_for_robots = self._get_random_user_agent() # Use a UA for fetching robots.txt
        try:
            response = await self.http_client.get(robots_url, headers={"User-Agent": current_ua_for_robots}, timeout=self.request_timeout / 2) # Shorter timeout for robots
            if response.status_code == 200:
                content = await response.text()
                parser.parse(content.splitlines())
                self.robots_parsers_cache[domain_base] = parser
                logger.info(f"Successfully fetched and parsed robots.txt for {domain_base}")
                return parser
            elif response.status_code == 404:
                 logger.info(f"No robots.txt found (404) for {domain_base}. Allowing all.")
                 self.robots_parsers_cache[domain_base] = None # Cache as None to indicate checked, not found
                 return None # No rules, so effectively allow all
            else:
                logger.warning(f"Failed to fetch robots.txt for {domain_base}, status: {response.status_code}. Assuming allow for this URL path if error is temporary.")
                # Don't cache on non-404 errors to allow retries later if it was temporary
                return None # Assume allow if fetch fails for other reasons
        except Exception as e:
            logger.error(f"Error fetching or parsing robots.txt for {domain_base}: {e}. Assuming allow for this URL path.", exc_info=True)
            return None # Assume allow on error

    async def is_allowed_by_robots(self, url: str) -> bool:
        if not self.settings.respect_robots_txt:
            return True
        
        parser = await self._fetch_robots_txt_parser(url)
        if parser is None: # No robots.txt found or error fetching/parsing it
            return True # Default to allow if robots.txt is missing or unparsable
        
        # Use a consistent user-agent for checking against the parser, ideally the one used for crawling that domain
        # For simplicity, we'll use the crawler's *current_user_agent* at time of check
        is_allowed = parser.can_fetch(self.current_user_agent, url)
        logger.debug(f"Robots.txt check for '{url}' with UA '{self.current_user_agent}': {'Allowed' if is_allowed else 'Disallowed'}")
        return is_allowed

    async def fetch_page_content(self, url: str) -> Optional[Tuple[bytes, str]]:
        """Fetches URL content, handling errors and rate limiting, uses rotated UA."""
        limiter = await self._get_domain_limiter(url)
        await limiter.acquire()
        self.current_user_agent = self._get_random_user_agent() # Rotate UA for this request
        headers = {"User-Agent": self.current_user_agent}
        
        try:
            logger.debug(f"Fetching URL: {url} (UA: {self.current_user_agent})")
            response = await self.http_client.get(url, headers=headers) 
            response.raise_for_status() 
            content_type = response.headers.get("content-type", "").lower()
            content_bytes = await response.aread()
            logger.debug(f"Fetched {url}, Status: {response.status_code}, Content-Type: {content_type}, Size: {len(content_bytes)} bytes")
            return content_bytes, content_type
        except httpx.TimeoutException: logger.warning(f"Timeout fetching {url}")
        except httpx.ConnectError: logger.warning(f"Connection error fetching {url}")
        except httpx.ReadError: logger.warning(f"Read error fetching {url}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404: logger.info(f"HTTP 404 Not Found for {url}")
            elif e.response.status_code == 403: logger.warning(f"HTTP 403 Forbidden for {url}")
            else: logger.warning(f"HTTP status error {e.response.status_code} fetching {url}: {e.response.reason_phrase}")
        except httpx.RequestError as e: logger.warning(f"HTTP request error fetching {url}: {type(e).__name__} - {e}")
        except Exception as e: logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
        finally: await limiter.release()
        return None

    async def _extract_sitemap_urls_from_html(self, html_content: str, base_url: str) -> List[str]:
        """Extracts sitemap URLs from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        sitemap_urls = []
        # Look for <link rel="sitemap" href="...">
        for link_tag in soup.find_all('link', attrs={'rel': 'sitemap'}):
            href = link_tag.get('href')
            if href:
                sitemap_urls.append(urljoin(base_url, href))
        # Look for common sitemap paths like /sitemap.xml, /sitemap_index.xml in <a> tags (less reliable)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and ('sitemap.xml' in href or 'sitemap_index.xml' in href):
                 sitemap_urls.append(urljoin(base_url, href))

        # Also, try to guess common sitemap paths directly if no explicit links found
        if not sitemap_urls:
            parsed_base = urlparse(base_url)
            domain_base = f"{parsed_base.scheme}://{parsed_base.netloc}"
            common_sitemap_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap.txt"]
            for path in common_sitemap_paths:
                 # Before adding, check if this path is allowed by robots.txt
                 # This is tricky here, as is_allowed_by_robots expects full URL.
                 # For simplicity, we'll add it and let process_url handle robots check.
                 sitemap_urls.append(urljoin(domain_base, path))


        unique_sitemap_urls = list(set(sitemap_urls)) # Deduplicate
        if unique_sitemap_urls:
            logger.info(f"Found potential sitemap URLs on {base_url}: {unique_sitemap_urls}")
        return unique_sitemap_urls

    async def _fetch_and_parse_sitemap(self, sitemap_url: str) -> AsyncGenerator[str, None]:
        """Fetches and parses a sitemap (XML or TXT), yielding URLs. Handles sitemap indexes."""
        if sitemap_url in self.processed_sitemap_urls or await self._check_if_stopped():
            return
        self.processed_sitemap_urls.add(sitemap_url)

        logger.info(f"Fetching sitemap: {sitemap_url}")
        sitemap_content_tuple = await self.fetch_page_content(sitemap_url)
        if not sitemap_content_tuple:
            return

        sitemap_bytes, sitemap_content_type = sitemap_content_tuple
        
        # Handle TXT sitemaps
        if "text/plain" in sitemap_content_type:
            try:
                sitemap_text = sitemap_bytes.decode('utf-8', errors='replace')
                for line in sitemap_text.splitlines():
                    url = line.strip()
                    if url and (url.startswith("http://") or url.startswith("https://")):
                        yield url
                return # Finished processing TXT sitemap
            except Exception as e:
                logger.error(f"Error decoding/parsing TXT sitemap {sitemap_url}: {e}")
                return


        # Handle XML sitemaps
        if "xml" in sitemap_content_type or sitemap_url.endswith(".xml"):
            try:
                sitemap_text = sitemap_bytes.decode('utf-8', errors='replace') # Ensure it's text for XML parser
                root = ET.fromstring(sitemap_text)
                
                # Determine namespace (sitemaps often use one)
                namespace = ''
                if root.tag.startswith('{'):
                    namespace = root.tag.split('}')[0] + '}'

                # Check if it's a sitemap index
                if root.tag == f'{namespace}sitemapindex':
                    logger.info(f"Processing sitemap index: {sitemap_url}")
                    sitemap_tasks = []
                    for sitemap_element in root.findall(f'{namespace}sitemap'):
                        loc_element = sitemap_element.find(f'{namespace}loc')
                        if loc_element is not None and loc_element.text:
                            sub_sitemap_url = loc_element.text.strip()
                            if sub_sitemap_url not in self.processed_sitemap_urls:
                                # Recursively process sub-sitemaps
                                sitemap_tasks.append(self._fetch_and_parse_sitemap(sub_sitemap_url))
                    
                    for task_gen in asyncio.as_completed(sitemap_tasks):
                        async for url_from_sub_sitemap in await task_gen:
                            yield url_from_sub_sitemap

                # Standard sitemap with <url> elements
                elif root.tag == f'{namespace}urlset':
                    logger.info(f"Processing URL set sitemap: {sitemap_url}")
                    for url_element in root.findall(f'{namespace}url'):
                        loc_element = url_element.find(f'{namespace}loc')
                        if loc_element is not None and loc_element.text:
                            url = loc_element.text.strip()
                            if url:
                                yield url
                else:
                    logger.warning(f"Unknown root tag '{root.tag}' in XML sitemap: {sitemap_url}")

            except ET.ParseError as e:
                logger.error(f"XML parsing error for sitemap {sitemap_url}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error processing XML sitemap {sitemap_url}: {e}", exc_info=True)
        else:
             logger.debug(f"Skipping sitemap processing for {sitemap_url} due to unsupported content type: {sitemap_content_type}")


    async def process_url(self, url: str, current_depth: int) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """Processes a single URL: fetches, identifies, downloads (if matches), and finds links/sitemaps."""
        if await self._check_if_stopped():
            logger.info(f"Stopping URL processing for {url} at depth {current_depth} due to stop signal.")
            return

        try:
             parsed_url_obj = urlparse(url)
             normalized_url = parsed_url_obj._replace(fragment="").geturl()
        except ValueError:
             logger.warning(f"Failed to parse/normalize URL: {url}. Skipping.")
             return

        if normalized_url in self.visited_urls:
            logger.debug(f"URL already visited: {normalized_url}, skipping.")
            return
        self.visited_urls.add(normalized_url)

        if current_depth > self.settings.crawl_depth:
            logger.debug(f"Max depth {self.settings.crawl_depth} reached for {url}")
            return

        if not await self.is_allowed_by_robots(url):
             logger.info(f"Skipping {url} due to robots.txt disallow rule.")
             return

        logger.info(f"Processing URL: {url} at depth {current_depth}")
        content_data_tuple = await self.fetch_page_content(url)

        if not content_data_tuple: return 

        raw_content_bytes, content_type_header = content_data_tuple
        file_meta = file_identifier.identify_file_type_and_name(url, content_type_header, raw_content_bytes[:1024])
        target_extensions_set = {ext.lstrip('.').lower() for ext in self.settings.file_extensions}
        is_target_file_extension = file_meta.extension.lower() in target_extensions_set

        if is_target_file_extension:
            logger.info(f"Target file type '{file_meta.extension}' identified: {url}")
            keywords_in_filename_or_metadata = keyword_matcher.match_keywords_in_text(file_meta.name, self.settings.keywords)
            should_download = False
            if keywords_in_filename_or_metadata:
                 logger.info(f"Keywords {keywords_in_filename_or_metadata} found in filename/metadata for: {url}. Proceeding to download.")
                 should_download = True
            
            # TODO: Add optional content keyword check for text-based files if needed.
            # This would require decoding raw_content_bytes based on guessed encoding.
            
            if should_download:
                try:
                    keywords_for_record = list(keywords_in_filename_or_metadata) 
                    download_result_schema = await downloader.download_and_store_file(
                        self.http_client, url, file_meta, self.job_id, keywords_for_record,
                        raw_content_bytes if len(raw_content_bytes) < (5 * 1024 * 1024) else None
                    )
                    if download_result_schema:
                        try:
                            db_downloaded_file = crud.create_downloaded_file(db=self.db, downloaded_file=download_result_schema)
                            logger.info(f"Recorded downloaded file in DB: {db_downloaded_file.id} from {url}")
                            yield db_downloaded_file
                        except SQLAlchemyError as db_err: logger.error(f"Database error recording downloaded file from {url}: {db_err}", exc_info=True)
                        except Exception as db_e: logger.error(f"Unexpected error recording downloaded file from {url}: {db_e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Failed during download/storage process for {url}: {e}", exc_info=True)

        # If it's an HTML page, extract links and look for sitemaps
        if "text/html" in content_type_header:
            if await self._check_if_stopped(): return
            try:
                html_content_str = raw_content_bytes.decode('utf-8', errors='replace')
            except Exception as decode_err:
                 logger.error(f"Failed to decode HTML content from {url}: {decode_err}")
                 return

            # 1. Extract and process sitemap URLs from this HTML page
            sitemap_urls_on_page = await self._extract_sitemap_urls_from_html(html_content_str, url)
            sitemap_processing_tasks = []
            for sitemap_url_found in sitemap_urls_on_page:
                if sitemap_url_found not in self.processed_sitemap_urls and sitemap_url_found not in self.visited_urls: # Also check visited_urls for sitemap itself
                     sitemap_processing_tasks.append(self._process_sitemap_and_its_urls(sitemap_url_found, current_depth)) # Pass depth

            if sitemap_processing_tasks:
                logger.info(f"Found {len(sitemap_processing_tasks)} new sitemaps to process from {url}.")
                for task_gen in asyncio.as_completed(sitemap_processing_tasks):
                    if await self._check_if_stopped(): break
                    try:
                        async for found_file_schema_from_sitemap in await task_gen:
                            yield found_file_schema_from_sitemap
                    except Exception as e_sitemap_proc:
                        logger.error(f"Error processing URLs from a sitemap generator originating from {url}: {e_sitemap_proc}", exc_info=True)


            # 2. Extract and process regular links if not at max depth
            if current_depth < self.settings.crawl_depth:
                try:
                    links_on_page = recursive.extract_links_from_html(html_content_str, url)
                    logger.debug(f"Found {len(links_on_page)} regular links on {url} to process for depth {current_depth + 1}.")
                    sub_tasks = []
                    for link_url in links_on_page:
                        if await self._check_if_stopped(): break
                        if link_url not in self.visited_urls:
                           sub_tasks.append(self.process_url(link_url, current_depth + 1))
                    if await self._check_if_stopped(): return
                    for completed_task_gen in asyncio.as_completed(sub_tasks):
                        if await self._check_if_stopped(): break
                        try:
                            async for found_file_schema in await completed_task_gen:
                                yield found_file_schema
                        except Exception as e_inner:
                            logger.error(f"Error processing a sub-link generator from {url}: {e_inner}", exc_info=True)
                except Exception as parse_err:
                     logger.error(f"Error parsing HTML or processing regular links from {url}: {parse_err}", exc_info=True)
    
    async def _process_sitemap_and_its_urls(self, sitemap_url: str, current_page_depth: int) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """Helper to process a sitemap and then process each URL found within it."""
        if await self._check_if_stopped(): return
        
        # Add sitemap URL itself to visited to avoid fetching it as a regular page if linked elsewhere.
        # This is a simplified way; ideally, sitemap_url might already be in self.visited_urls if it was found via a regular link.
        # self.visited_urls.add(sitemap_url) # Potentially redundant if sitemap_url was already visited.

        url_processing_tasks = []
        async for url_from_sitemap in self._fetch_and_parse_sitemap(sitemap_url):
            if await self._check_if_stopped(): break
            if url_from_sitemap not in self.visited_urls:
                 # URLs from sitemap are typically depth 0 relative to their discovery point (the sitemap).
                 # Or, you might want them to inherit current_page_depth if they are just pointers to content
                 # that would have been found by regular crawling from the sitemap's parent page.
                 # For simplicity, let's treat them as depth 0 or 1 relative to site root, or related to `current_page_depth`.
                 # A common approach is to process them at `current_page_depth` or `current_page_depth + 1`
                 # if the sitemap is considered part of the page's content.
                 # Let's use current_page_depth, assuming sitemap URLs are direct content links.
                 url_processing_tasks.append(self.process_url(url_from_sitemap, current_page_depth)) # Use current_page_depth
        
        if url_processing_tasks:
            logger.info(f"Processing {len(url_processing_tasks)} URLs found in sitemap {sitemap_url}")
            for task_gen in asyncio.as_completed(url_processing_tasks):
                if await self._check_if_stopped(): break
                try:
                    async for file_schema in await task_gen:
                        yield file_schema
                except Exception as e_sitemap_url_proc:
                    logger.error(f"Error processing a URL from sitemap {sitemap_url}: {e_sitemap_url_proc}", exc_info=True)


    async def _run_sub_task(self, coro): # Not currently used, but can be a helper
        """Wrapper to run a sub-task and handle potential errors."""
        try: return await coro
        except Exception as e: logger.error(f"Error in sub-task execution: {e}", exc_info=True); return []

    async def start_crawling(self) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """Main entry point to start the crawl job."""
        start_time = time.monotonic()
        files_found_count = 0
        if await self._check_if_stopped():
            logger.info(f"Crawl job {self.job_id} is already stopping/stopped. Not starting.")
            await self.http_client.aclose()
            return

        try:
            crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="running", last_run_at=datetime.now(timezone.utc))
            logger.info(f"Starting deep crawl for job {self.job_id}")
            initial_urls_to_process: Set[str] = set()

            for seed_url_str in self.settings.seed_urls:
                if await self._check_if_stopped(): break
                try:
                    parsed = urlparse(seed_url_str)
                    if parsed.scheme in ['http', 'https'] and parsed.netloc:
                         normalized = parsed._replace(fragment="").geturl()
                         if normalized not in self.visited_urls: initial_urls_to_process.add(normalized)
                    else: logger.warning(f"Skipping invalid seed URL: {seed_url_str}")
                except ValueError: logger.warning(f"Skipping invalid seed URL format: {seed_url_str}")
            logger.info(f"Collected {len(initial_urls_to_process)} unique, valid seed URLs.")
            if await self._check_if_stopped(): raise asyncio.CancelledError("Job stopped during seed URL processing")

            if self.settings.use_search_engines and self.settings.search_dorks:
                logger.info(f"Executing {len(self.settings.search_dorks)} search dorks...")
                dork_tasks = [
                    search_engine_driver.execute_dork(
                        dork, self.http_client, max_results=self.settings.max_results_per_dork or 20
                    ) for dork in self.settings.search_dorks if not await self._check_if_stopped()
                ]
                if not await self._check_if_stopped() and dork_tasks:
                    dork_results_list_of_lists = await asyncio.gather(*[self._collect_async_gen(gen) for gen in dork_tasks], return_exceptions=True)
                    urls_from_dorks_count = 0
                    for i, result_or_exc in enumerate(dork_results_list_of_lists):
                         dork_query = self.settings.search_dorks[i]
                         if isinstance(result_or_exc, Exception): logger.error(f"Error executing dork '{dork_query}': {result_or_exc}"); continue
                         added_count = 0
                         for dork_url in result_or_exc: # result_or_exc is List[str] here
                             try:
                                 parsed = urlparse(dork_url); normalized = parsed._replace(fragment="").geturl()
                                 if parsed.scheme in ['http', 'https'] and parsed.netloc and normalized not in self.visited_urls and normalized not in initial_urls_to_process:
                                      initial_urls_to_process.add(normalized); added_count += 1
                             except ValueError: logger.warning(f"Skipping invalid URL from dork '{dork_query}': {dork_url}")
                         urls_from_dorks_count += added_count
                         logger.info(f"Dork '{dork_query}' added {added_count} new URLs. (Found: {len(result_or_exc)})")
                    logger.info(f"Added {urls_from_dorks_count} unique URLs from dork results.")

            if await self._check_if_stopped(): raise asyncio.CancelledError("Job stopped during dork processing")

            if not initial_urls_to_process:
                logger.warning(f"No initial URLs found for job {self.job_id}. Crawl will stop.")
            else: self.initial_urls_found = True

            logger.info(f"Total unique initial URLs to process: {len(initial_urls_to_process)}")

            if initial_urls_to_process:
                processing_tasks = [self.process_url(url, 0) for url in initial_urls_to_process]
                for task_gen_completed in asyncio.as_completed(processing_tasks):
                    if await self._check_if_stopped(): break
                    try:
                        async for file_schema in await task_gen_completed:
                             if await self._check_if_stopped(): break
                             files_found_count += 1; yield file_schema
                    except asyncio.CancelledError: logger.info(f"A processing task for job {self.job_id} was cancelled."); break
                    except Exception as task_err: logger.error(f"Error in a main URL processing task for job {self.job_id}: {task_err}", exc_info=True)

        except asyncio.CancelledError:
            logger.info(f"Crawl job {self.job_id} was cancelled/stopped.")
            # Status will be updated to 'stopping' by stop_crawler or 'failed' in final block
        except Exception as e:
            logger.error(f"Critical error during crawl job {self.job_id}: {e}", exc_info=True)
            try: crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="failed")
            except Exception as db_e: logger.error(f"Failed to update job status to 'failed' for job {self.job_id} after critical error: {db_e}")
        finally:
            if not self._should_stop_event.is_set(): # If not stopped externally
                final_status_to_set = "failed" 
                try:
                    current_db_status = self.db.query(models.CrawlJob.status).filter(models.CrawlJob.id == self.job_id).scalar()
                    if current_db_status == "running":
                        if files_found_count > 0: final_status_to_set = "completed"
                        elif self.initial_urls_found: final_status_to_set = "completed_empty"
                        else: final_status_to_set = "completed_empty" 
                        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status=final_status_to_set)
                        logger.info(f"Crawl job {self.job_id} finished naturally. Final status: {final_status_to_set}. Files yielded: {files_found_count}")
                    else: logger.info(f"Job {self.job_id} status was '{current_db_status}' (not 'running'). Not overriding final status from crawl completion logic.")
                except Exception as final_status_err: logger.error(f"Error during final status update for job {self.job_id}: {final_status_err}", exc_info=True)
            elif self.db.query(models.CrawlJob.status).filter(models.CrawlJob.id == self.job_id).scalar() == "stopping":
                 # If it was set to 'stopping', mark as 'failed' as it didn't complete normally
                 crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="failed")
                 logger.info(f"Crawl job {self.job_id} was stopped and marked as 'failed'.")


            if self.http_client and not self.http_client.is_closed:
                await self.http_client.aclose()
                logger.info(f"HTTP client closed for job {self.job_id}.")
            end_time = time.monotonic()
            logger.info(f"Total execution time for job {self.job_id}: {end_time - start_time:.2f} seconds.")

    async def _collect_async_gen(self, agen: AsyncGenerator[str, None]) -> List[str]:
        """Helper to collect items from an async generator into a list, respecting stop signal."""
        items = []
        try:
            async for item in agen:
                if await self._check_if_stopped(): break
                items.append(item)
        except Exception as e: logger.error(f"Error collecting from an async generator: {e}", exc_info=True)
        return items

